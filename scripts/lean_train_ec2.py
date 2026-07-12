"""Provision an EC2 spot GPU box, QLoRA-train the trio to Lean 4, push adapters.

Phase 2 of ``notebooks/lean``'s fine-tune plan, for the "provision + train on
AWS" path. The serving provisioner in ``smolbench/evals/ec2.py`` is
*serving-shaped* and cannot be reused as-is for training:

- its idle **watchdog** reads vLLM ``/metrics``; a training box runs no vLLM, so
  after the ~180-min startup grace it reads as idle and ``shutdown -h``s the box
  mid-training (the instance terminates on OS halt);
- its security group opens only the vLLM/agent ports (8000/9000), never **SSH**,
  and it attaches no key pair -- so there is no way to drive training on the box.

So this driver defines a **separate training instance role**: a minimal
cloud-init that mounts the instance-store NVMe (for the HF cache + checkpoints)
and schedules only the max-lifetime backstop -- **no watchdog, no vLLM** -- and
relies on the Deep-Learning AMI's sshd (with a fresh key pair + port 22 opened
to the caller) for control. It reuses ``ec2.py``'s low-level capacity-hunt
primitives (AMI/subnet resolution, the spot type x region x AZ launch loop,
public-IP wait, state file) and isolates its instance/state/SG from the serving
experiments via its own ``lean-train`` tag, ``.ec2_state_lean_train.json`` state
file, and ``smolbench-lean-train`` security group.

The trio is QLoRA'd sequentially on ONE 8-GPU box (p5e.48xlarge = 8xH200), each
model's LoRA adapter pushed to a private Hub repo *as it trains* (durable
against spot interruption -- see ``scripts/lean_lora_sft.py``). QLoRA needs the
**BF16** bases (bitsandbytes 4-bit cannot quantize the FP8 serving repos), so
this pulls ``Qwen/Qwen3-235B-A22B`` (~470 GB), ``nvidia/Llama-3_1-Nemotron-
Ultra-253B-v1`` (~506 GB) and ``meta-llama/Llama-3.1-405B-Instruct`` (~810 GB,
the cost driver) onto the NVMe.

Runs on any interpreter with boto3 (the main ``.venv``): it only orchestrates
AWS + SSH; the heavy training stack lives on the box (installed from
``scripts/requirements-train.txt`` during ``setup``). AWS creds come from the
usual profile/env; ``HF_TOKEN`` is read from the environment or
``notebooks/periodic/keys.env`` and transmitted to the box over SSH (never baked
into user-data, never printed).

Subcommands (drive + observe each phase; each is resumable via the state file):
    provision   hunt spot capacity, launch the box, wait for SSH, save state
                (or --capacity-reservation to launch into a purchased block)
    setup       upload dataset + trainer, build the training venv on the box
    attach-s3   associate the S3-writable instance profile with the box
                (required for the default --checkpoint-dest s3 to sync)
    gpu-smoke   validate the staged --init-adapter path on the box GPU
    train       QLoRA one model (launch detached, poll to completion)
    train-all   train the whole trio sequentially
    status      describe the box + tail the in-flight training log
    teardown    terminate the box and clear state
    cb-search   list purchasable EC2 Capacity Block offerings (read-only)
    cb-purchase buy one offering (DryRun unless --yes; upfront, non-refundable)
    cb-status   live states of the purchased blocks in the local ledger

Capacity Blocks (``cb-*`` + ``provision --capacity-reservation``) exist
because spot p5 boxes get reclaimed mid-stage (twice in one day, 2026-07-10);
a block reserves an interruption-free window for the multi-day stages
(Nemotron-253B / Llama-405B) at a fixed upfront price. Inside the window the
box is never spot-interrupted; AWS still reclaims it at the block's END
(~30 min warning), which the per-stage S3 checkpoint sync already covers.

Example
-------
    set -a; source notebooks/periodic/keys.env; set +a   # HF_TOKEN + AWS_PROFILE
    .venv/bin/python scripts/lean_train_ec2.py provision
    .venv/bin/python scripts/lean_train_ec2.py setup
    .venv/bin/python scripts/lean_train_ec2.py attach-s3   # default checkpoint dest is S3
    .venv/bin/python scripts/lean_train_ec2.py train --model qwen3-235b-a22b --cap 8000
    .venv/bin/python scripts/lean_train_ec2.py teardown
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Isolate this experiment's instance/state/SG BEFORE importing ec2 (the tag and
# SG name are captured into module constants at import time). This keeps the
# training box, its state file, and its port-22 security group separate from the
# serving experiments (periodic/chromatic/lean sweeps).
os.environ.setdefault("EC2_EXPERIMENT_TAG", "lean-train")
os.environ.setdefault("EC2_STATE_FILE", str(_REPO_ROOT / ".ec2_state_lean_train.json"))
os.environ.setdefault("EC2_SECURITY_GROUP_NAME", "smolbench-lean-train")

# The training box's cloud-init template ships from the payloads package.
# Unlike ec2 (whose import captures EC2_* env at import time -- hence the
# setdefaults above and the lazy per-function ec2 imports below), payloads is
# env-independent and safe to import eagerly.
from smolbench.evals.payloads import TRAIN_USER_DATA_TEMPLATE

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: EC2 key pair name + local private-key path (gitignored, 0600). Created on
#: first ``provision`` if absent.
KEY_NAME = os.getenv("LEAN_TRAIN_KEY_NAME", "smolbench-lean-train")
KEY_PATH = Path(os.getenv("LEAN_TRAIN_KEY_PATH", str(_REPO_ROOT / ".ec2_lean_train_key.pem")))

#: OS-halt backstop for SPOT boxes when --max-lifetime is not given (48h). A
#: capacity-block launch instead defaults to the block's end (+margin) -- see
#: ``_provision_capacity_block``.
DEFAULT_MAX_LIFETIME_MIN = 2880

#: Ledger of purchased capacity-block reservations (a JSON list). Named to
#: match the ``.ec2_state*.json`` gitignore glob and repo-anchored like the
#: instance state file, so every session sees the same purchase record.
CB_STATE_PATH = Path(os.getenv("LEAN_TRAIN_CB_STATE", str(_REPO_ROOT / ".ec2_state_lean_train_cb.json")))

#: InstancePlatform for purchase_capacity_block (the DL AMI is Ubuntu).
CB_INSTANCE_PLATFORM = "Linux/UNIX"

#: Artifacts uploaded to the box.
_SFT_DIR = _REPO_ROOT / "notebooks" / "lean" / "data" / "sft"
#: SFT datasets uploaded to the box, keyed by the ``--dataset-file`` name.
#: Two synthetic stage-1 pretrain sets (decontaminated -- see
#: ``scripts/build_lean_synth_sft.py``) and the decontaminated real anneal set
#: (stage 2). The legacy pre-decontam real set is kept for the original
#: real-only recipe / reproducing the earlier cohort.
DATASETS: Dict[str, Path] = {
    "novel_premises_train_stepk1_decontam.jsonl": _SFT_DIR / "novel_premises_train_stepk1_decontam.jsonl",
    "synth_goedel_v2_24k.jsonl": _SFT_DIR / "synth_goedel_v2_24k.jsonl",
    "synth_leannavigator_24k.jsonl": _SFT_DIR / "synth_leannavigator_24k.jsonl",
    "novel_premises_train_stepk1.jsonl": _SFT_DIR / "novel_premises_train_stepk1.jsonl",
}
#: Default dataset for a plain ``train`` (the decontaminated real anneal set).
DEFAULT_DATASET = "novel_premises_train_stepk1_decontam.jsonl"
TRAIN_SCRIPT = _REPO_ROOT / "scripts" / "lean_lora_sft.py"
REQUIREMENTS = _REPO_ROOT / "scripts" / "requirements-train.txt"
#: Resumable on-box Qwen 4-way orchestrator (uploaded by `setup`; launched via nohup).
ORCHESTRATOR = _REPO_ROOT / "scripts" / "lean_qwen_4way.sh"

#: On-box working tree (all on the NVMe mount; see payloads/train_user_data.sh).
REMOTE_ROOT = "/opt/train"
REMOTE_VENV = f"{REMOTE_ROOT}/venv"
REMOTE_HF_CACHE = f"{REMOTE_ROOT}/hf-cache"
REMOTE_OUT = f"{REMOTE_ROOT}/out"
SSH_USER = "ubuntu"  # the DL-base Ubuntu 22.04 AMI's default user

#: The trio, in training order. Qwen first (ungated -> validates the whole
#: train->push loop with zero gated-repo risk), then Nemotron (validates its NAS
#: ``target_modules``), then the 405B (biggest download + tightest 4-bit fit).
#: ``base`` is the BF16 repo (QLoRA quantizes it to NF4 on load); ``suffix`` is
#: the adapter repo name under the ``--org`` namespace.
#: LoRA target sets. Attention-only for the MoE (its experts are fused
#: nn.Parameters -> peft ParamWrapper, whose per-forward delta-weight einsum OOMs;
#: attention-only sidesteps it and is the standard MoE-LoRA choice). Attention+MLP
#: for the dense models (all nn.Linear -> 4-bit-quantized, no ParamWrapper).
_ATTN = "q_proj,k_proj,v_proj,o_proj"
_ATTN_MLP = "q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj"
TRIO: List[Dict[str, object]] = [
    {"key": "qwen3-235b-a22b", "base": "Qwen/Qwen3-235B-A22B", "suffix": "qwen3-235b-a22b-lean-lora",
     "target_modules": _ATTN, "moe": True, "trust_remote_code": False},
    # Nemotron-Ultra's NAS (DeciLM) architecture ships custom modeling code -> needs
    # trust_remote_code. Its 4 giant NAS FFN layers (>=2**31-element matrices) trip
    # bitsandbytes' int32-indexed 4-bit kernel ("invalid argument" in ops.cu); the
    # trainer auto-detects them and keeps just those bf16 (llm_int8_skip_modules)
    # while quantizing the rest -> mixed footprint ~233GiB, fits the 640GB p5 with
    # zero offload (all-bf16 ~506GB packed so tight that layers offloaded to CPU,
    # whose inference-only hooks then broke backward).
    {"key": "nemotron-ultra-253b", "base": "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1", "suffix": "nemotron-ultra-253b-lean-lora",
     "target_modules": _ATTN_MLP, "moe": False, "trust_remote_code": True},
    # User-approved ungated mirror of the gated meta-llama repo (byte-identical BF16,
    # 191 shards), loaded with trust_remote_code=False so NO third-party code runs.
    # Seeded (--seed 1776) so a same-seed run on the official meta-llama weights, once
    # access clears, is a faithful REPLICATE (and verifies the mirror). Swap `base`
    # back to meta-llama/Llama-3.1-405B-Instruct for that replicate.
    {"key": "llama-31-405b", "base": "SillyTilly/Meta-Llama-3.1-405B-Instruct", "suffix": "llama-31-405b-lean-lora",
     "target_modules": _ATTN_MLP, "moe": False, "trust_remote_code": False},
]
_TRIO_BY_KEY = {m["key"]: m for m in TRIO}

#: Training instance role's cloud-init (payloads/train_user_data.sh): mount
#: NVMe -> REMOTE_ROOT (HF cache + checkpoints), schedule ONLY the max-lifetime
#: backstop. No watchdog, no vLLM, no secrets (HF_TOKEN arrives later over
#: SSH). ``@@MAX_LIFETIME_MIN@@`` is the sole placeholder; rendered by
#: ``_render_train_user_data`` below.


def _hf_token() -> str:
    """Return the HF token: ``.hf_token`` (override) > env > keys.env.

    ``.hf_token`` is checked FIRST so a WRITE-enabled token dropped there
    overrides the read-only token in the environment / keys.env (adapter pushes
    need write; the keys.env token is read-only). Accepts either
    ``HF_TOKEN=hf_...`` or a bare ``hf_...`` line. Never printed by this module.
    """
    def _parse(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):]
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
            if line and not line.startswith("#") and "=" not in line:
                return line  # a bare token line
        return ""

    hf_file = _REPO_ROOT / ".hf_token"
    if hf_file.exists():
        tok = _parse(hf_file.read_text())
        if tok:
            return tok
    tok = os.environ.get("HF_TOKEN", "").strip()
    if tok:
        return tok
    keys = _REPO_ROOT / "notebooks" / "periodic" / "keys.env"
    if keys.exists():
        tok = _parse(keys.read_text())
        if tok:
            return tok
    raise SystemExit(
        "HF_TOKEN not found. Put a WRITE-enabled token in .hf_token, the "
        "environment, or notebooks/periodic/keys.env."
    )


# ---------------------------------------------------------------------------
# Provisioning (reuses ec2.py's low-level AWS primitives)
# ---------------------------------------------------------------------------


def _ensure_local_keypair() -> str:
    """Generate the local SSH key pair once; return its public-key material.

    ONE local key pair is imported into every region the spot hunt touches. EC2
    key pairs are region-scoped, but a private key is not -- so importing the
    same public key everywhere makes the single ``.pem`` work no matter which
    region/AZ capacity lands in. (The earlier bug: AWS-*generated* per-region key
    pairs each returned a different private key that overwrote ``.pem``, so it
    only matched the last region created -- SSH would fail if a later instance
    type launched in an earlier region.)
    """
    pub_path = KEY_PATH.with_name(KEY_PATH.name + ".pub")
    if not KEY_PATH.exists():
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-q",
             "-C", "smolbench-lean-train", "-f", str(KEY_PATH)],
            check=True,
        )
        KEY_PATH.chmod(0o600)
        print(f"generated local key pair -> {KEY_PATH}")
    return pub_path.read_text().strip()


def _ensure_key_pair(ec2, region: str) -> None:
    """Import the local public key into ``region`` as KEY_NAME (idempotent).

    Replaces any existing key pair of that name -- which may be stale (an
    AWS-generated one from an earlier run, or a prior import) -- so the region's
    key pair ALWAYS matches the local private key. Deleting a key pair does not
    affect already-running instances that used it (the public key is already in
    their ``authorized_keys``).
    """
    from botocore.exceptions import ClientError

    pub = _ensure_local_keypair()
    client = ec2._ec2_client(region)
    try:
        client.import_key_pair(KeyName=KEY_NAME, PublicKeyMaterial=pub.encode())
    except ClientError as err:
        if ec2._error_code(err) != "InvalidKeyPair.Duplicate":
            raise
        # Already imported (our key) -- skip. (Any stale AWS-generated key pair was
        # replaced on the first provision; a delete+reimport here would race with the
        # concurrent per-model provisions that share this key name.)


def _authorize_ssh(ec2, region: str, group_id: str, ip: str) -> None:
    """Open port 22 to ip/32 on the training security group (tolerate existing)."""
    from botocore.exceptions import ClientError

    try:
        ec2._ec2_client(region).authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[{
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": f"{ip}/32", "Description": "smolbench lean-train ssh"}],
            }],
        )
    except ClientError as err:
        if ec2._error_code(err) != "InvalidPermission.Duplicate":
            raise


def _render_train_user_data(max_lifetime_min: int) -> str:
    # `--max-lifetime` defaults to None (resolved per market by the caller); a
    # None leaking through would render `shutdown -h +None`, whose `|| true`
    # silently leaves the box with NO lifetime backstop.
    assert isinstance(max_lifetime_min, int) and max_lifetime_min > 0, \
        f"max_lifetime_min must be a positive int, got {max_lifetime_min!r}"
    ud = TRAIN_USER_DATA_TEMPLATE.replace("@@MAX_LIFETIME_MIN@@", str(max_lifetime_min))
    assert "@@" not in ud, "unsubstituted placeholder in train user-data"
    assert len(ud.encode()) < 16384, f"user-data too large: {len(ud.encode())} bytes"
    return ud


# ---------------------------------------------------------------------------
# Capacity Blocks (reserved, interruption-free windows for long runs)
# ---------------------------------------------------------------------------


def _cb_load() -> List[Dict[str, Any]]:
    if not CB_STATE_PATH.exists():
        return []
    return json.loads(CB_STATE_PATH.read_text())


def _cb_save(records: List[Dict[str, Any]]) -> None:
    CB_STATE_PATH.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")


def _cb_upsert(record: Dict[str, Any]) -> None:
    """Insert-or-replace one ledger record, keyed by reservation id."""
    records = [r for r in _cb_load() if r.get("reservation_id") != record["reservation_id"]]
    records.append(record)
    _cb_save(records)


def _iso(dt: Any) -> str:
    """ISO-8601 Z string from a boto3 datetime (strings/None pass through)."""
    if hasattr(dt, "strftime"):
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)


def _cb_record(region: str, cr: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a CapacityReservation API dict into the ledger's record.

    Region is recorded because reservations are regional resources but every
    describe call needs the region supplied from outside the API response.
    """
    return {
        "reservation_id": cr["CapacityReservationId"],
        "region": region,
        "availability_zone": cr.get("AvailabilityZone"),
        "instance_type": cr.get("InstanceType"),
        "instance_count": cr.get("TotalInstanceCount"),
        "state": cr.get("State"),
        "start_date": _iso(cr.get("StartDate")),
        "end_date": _iso(cr.get("EndDate")),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _parse_when(spec: Optional[str]) -> Optional[datetime]:
    """``+Nh``/``+Nd`` offsets from now, or an ISO-8601 timestamp (naive = UTC)."""
    if not spec:
        return None
    if spec.startswith("+") and spec[-1] in "hd" and spec[1:-1].isdigit():
        unit = {"h": "hours", "d": "days"}[spec[-1]]
        return datetime.now(timezone.utc) + timedelta(**{unit: int(spec[1:-1])})
    dt = datetime.fromisoformat(spec)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def cb_search(args) -> int:
    """List purchasable capacity-block offerings across the hunt regions.

    Read-only (DescribeCapacityBlockOfferings, paginated); prints one line
    per offering, cheapest first, then the exact ``cb-purchase`` invocation
    for the top hit. Regions that reject the API (not every region sells
    blocks) are skipped with a note rather than aborting the sweep.
    """
    from smolbench.evals import ec2
    from botocore.exceptions import ClientError

    regions = tuple(r.strip() for r in args.regions.split(",") if r.strip()) \
        if args.regions else ec2.EC2_REGIONS
    params: Dict[str, Any] = {
        "InstanceType": args.instance_type,
        "InstanceCount": args.instance_count,
        "CapacityDurationHours": args.duration_hours,
    }
    start_after, end_before = _parse_when(args.start_after), _parse_when(args.end_before)
    if start_after:
        params["StartDateRange"] = start_after
    if end_before:
        params["EndDateRange"] = end_before

    found: List[Tuple[str, Dict[str, Any]]] = []
    for region in regions:
        client = ec2._ec2_client(region)
        token: Optional[str] = None
        try:
            while True:
                page = client.describe_capacity_block_offerings(
                    **params, **({"NextToken": token} if token else {}))
                found.extend((region, o) for o in page.get("CapacityBlockOfferings", []))
                token = page.get("NextToken")
                if not token:
                    break
        except ClientError as err:
            print(f"{region}: {ec2._error_code(err)} (skipped)", file=sys.stderr)

    if not found:
        print("no capacity-block offerings matched; vary --duration-hours / "
              "--start-after / --end-before / --regions.")
        return 1

    def _fee(off: Dict[str, Any]) -> float:
        try:
            return float(off.get("UpfrontFee") or "inf")
        except ValueError:
            return float("inf")

    found.sort(key=lambda ro: (_fee(ro[1]), _iso(ro[1].get("StartDate"))))
    for region, off in found:
        print(f"{region} {off.get('AvailabilityZone')}  {off.get('InstanceType')} "
              f"x{off.get('InstanceCount')}  {_iso(off.get('StartDate'))} -> "
              f"{_iso(off.get('EndDate'))}  {off.get('CapacityBlockDurationHours')}h  "
              f"${off.get('UpfrontFee')} {off.get('CurrencyCode')}  "
              f"{off['CapacityBlockOfferingId']}")
    region, best = found[0]
    print(f"\ncheapest: ${best.get('UpfrontFee')} {best.get('CurrencyCode')} total (upfront, "
          f"non-refundable). To buy it:\n  python scripts/lean_train_ec2.py cb-purchase "
          f"--region {region} --offering-id {best['CapacityBlockOfferingId']}")
    return 0


def _no_retry_ec2_client(region: str):
    """An EC2 client that never auto-retries, for the non-idempotent purchase.

    botocore's default policy transparently re-sends a request on connection
    errors and 5xx responses (up to 5 attempts), and PurchaseCapacityBlock has
    NO idempotency token (unlike RunInstances' ClientToken) -- so a replay of
    a purchase that actually committed buys a SECOND non-refundable block,
    invisibly (only the last response's reservation would be seen). One
    attempt only; on an ambiguous failure the operator reconciles via the
    console/tag filter (see cb_purchase's error path) instead of retrying
    blind. Fresh Session per call, same rotated-credentials rationale as
    ``_aws.fresh_client``.
    """
    import boto3
    from botocore.config import Config

    return boto3.session.Session().client(
        "ec2", region_name=region, config=Config(retries={"max_attempts": 1}))


def cb_purchase(args) -> int:
    """Purchase one capacity-block offering -- UPFRONT, NON-REFUNDABLE spend.

    Without ``--yes`` this only DryRun-validates the purchase (permissions,
    offering still valid) and prints the confirmation step; blocks cannot be
    cancelled after purchase, so the real call is gated on the explicit flag.
    The real call runs on a no-retry client (see ``_no_retry_ec2_client``)
    and is sequenced so no local failure can lose the reservation id: ledger
    readable BEFORE spending, id printed the moment the API returns, ledger
    write failure downgraded to a loud warning.
    """
    from smolbench.evals import ec2
    from botocore.exceptions import ClientError

    params: Dict[str, Any] = {
        "CapacityBlockOfferingId": args.offering_id,
        "InstancePlatform": CB_INSTANCE_PLATFORM,
        "TagSpecifications": [{
            "ResourceType": "capacity-reservation",
            "Tags": [
                {"Key": "smolbench:experiment", "Value": ec2.EC2_EXPERIMENT_TAG},
                {"Key": "Name", "Value": f"smolbench-{ec2.EC2_EXPERIMENT_TAG}-capacity-block"},
            ],
        }],
    }
    if not args.yes:
        try:
            ec2._ec2_client(args.region).purchase_capacity_block(DryRun=True, **params)
        except ClientError as err:
            if ec2._error_code(err) == "DryRunOperation":  # = would have succeeded
                print(f"dry-run OK: offering {args.offering_id} is purchasable in {args.region}.\n"
                      f"This is an UPFRONT, NON-REFUNDABLE purchase -- re-run with --yes to buy it.")
                return 0
            raise
        # DryRun=True must never buy; if the API ever returns success here,
        # refuse to proceed rather than guess what happened.
        print("dry-run returned success instead of DryRunOperation; NOT purchasing. "
              "Inspect the account's reservations before retrying.", file=sys.stderr)
        return 1

    # Fail fast on an unreadable ledger BEFORE spending: the record write
    # below must not be the first place a corrupt file surfaces.
    _cb_load()
    try:
        cr = _no_retry_ec2_client(args.region).purchase_capacity_block(**params)["CapacityReservation"]
        rid = cr["CapacityReservationId"]
    except Exception:
        print(f"PurchaseCapacityBlock errored, but the request may have REACHED AWS "
              f"(e.g. response lost). Do NOT re-run --yes blind: the block may already be "
              f"bought. Reconcile first:\n  aws ec2 describe-capacity-reservations --region "
              f"{args.region} --filters Name=tag:smolbench:experiment,Values={ec2.EC2_EXPERIMENT_TAG}",
              file=sys.stderr)
        raise
    # The id is the only durable local handle on the money just spent --
    # surface it before any ledger I/O gets a chance to fail.
    print(f"PURCHASED: {rid}")
    try:
        record = _cb_record(args.region, cr)
        _cb_upsert(record)
    except Exception as exc:  # noqa: BLE001 -- the purchase already happened
        print(f"WARNING: bought {rid} but could not record it in {CB_STATE_PATH} ({exc}).\n"
              f"Do NOT re-purchase. Fix the file, then re-register with:\n"
              f"  python scripts/lean_train_ec2.py cb-status --reservation-id {rid} --region {args.region}",
              file=sys.stderr)
        return 1
    print(f"purchased {record['reservation_id']} ({record['instance_type']} "
          f"x{record['instance_count']} @ {record['availability_zone']}): "
          f"{record['start_date']} -> {record['end_date']}, state={record['state']}.\n"
          f"recorded in {CB_STATE_PATH.name}. Watch with cb-status; once active:\n"
          f"  python scripts/lean_train_ec2.py provision --capacity-reservation {record['reservation_id']}")
    return 0


def _fmt_hours(delta: timedelta) -> str:
    return f"{delta.total_seconds() / 3600:.1f}h"


def cb_status(args) -> int:
    """Live states of the ledger's reservations (or one given explicitly)."""
    from smolbench.evals import ec2
    from botocore.exceptions import ClientError

    records = _cb_load()
    if args.reservation_id:
        region = args.region or next(
            (r["region"] for r in records if r["reservation_id"] == args.reservation_id), None)
        if region is None:
            raise SystemExit(f"{args.reservation_id} not in {CB_STATE_PATH.name}; pass --region.")
        targets: Dict[str, List[str]] = {region: [args.reservation_id]}
    else:
        if not records:
            print(f"no capacity blocks recorded ({CB_STATE_PATH.name}); "
                  f"run cb-search, then cb-purchase.")
            return 0
        targets = {}
        for r in records:
            targets.setdefault(r["region"], []).append(r["reservation_id"])

    now = datetime.now(timezone.utc)
    for region, ids in sorted(targets.items()):
        client = ec2._ec2_client(region)
        crs: List[Dict[str, Any]] = []
        # One describe PER id, not a batch: EC2 by-id describes are
        # all-or-nothing, so a single ledger id that aged out of the API
        # (reservations describe only ~60 days past their end) would blank
        # every LIVE block in the region. The ledger is a handful of entries;
        # N calls are nothing.
        for rid in ids:
            try:
                crs.extend(client.describe_capacity_reservations(
                    CapacityReservationIds=[rid])["CapacityReservations"])
            except ClientError as err:
                code = ec2._error_code(err)
                aged = (" (aged out of the describe API; prune it from the ledger)"
                        if code == "InvalidCapacityReservationId.NotFound" else "")
                print(f"{rid} @ {region}: {code}{aged}", file=sys.stderr)
        for cr in crs:
            record = _cb_record(region, cr)
            _cb_upsert(record)
            start, end = cr.get("StartDate"), cr.get("EndDate")
            if record["state"] == "active" and end is not None:
                when = f"ends in {_fmt_hours(end - now)}"
            elif record["state"] in ("scheduled", "payment-pending", "pending", "assessing") \
                    and start is not None:
                when = f"starts in {_fmt_hours(start - now)}"
            else:
                when = ""
            print(f"{record['reservation_id']}  {region} {record['availability_zone']}  "
                  f"{record['instance_type']} x{record['instance_count']}  "
                  f"state={record['state']}  {record['start_date']} -> {record['end_date']}  "
                  f"available={cr.get('AvailableInstanceCount')}  {when}".rstrip())
    return 0


def _resolve_capacity_reservation(args) -> Tuple[str, Dict[str, Any]]:
    """Find the reservation to launch into: an explicit cr- id or ``auto``.

    ``auto`` live-describes every ledger entry and, among the ``active`` ones
    with a free slot, picks the block with the MOST remaining window (latest
    EndDate) -- with two blocks active at once, launching a multi-day run
    into the one about to expire would hand the box to AWS's end-of-block
    reclaim mid-download. An explicit id is looked up in the ledger first
    (for its region), then probed across the hunt regions. Exits listing
    every candidate's state (with the start time for ``scheduled``) when
    nothing is launchable yet -- a scheduled block is a "come back later",
    not an error to work around.
    """
    from smolbench.evals import ec2
    from botocore.exceptions import ClientError

    wanted = args.capacity_reservation
    records = _cb_load()
    if wanted == "auto":
        candidates = [(r["region"], r["reservation_id"]) for r in records]
        if not candidates:
            raise SystemExit(f"no capacity blocks in {CB_STATE_PATH.name}; "
                             f"run cb-search, then cb-purchase.")
    else:
        region = next((r["region"] for r in records if r["reservation_id"] == wanted), None)
        if region is not None:
            candidates = [(region, wanted)]
        else:  # not in the ledger (bought elsewhere): probe the hunt regions
            regions = tuple(r.strip() for r in (args.regions or "").split(",") if r.strip()) \
                or ec2.EC2_REGIONS
            candidates = [(rg, wanted) for rg in regions]

    seen: List[str] = []
    launchable: List[Tuple[str, Dict[str, Any]]] = []
    for region, rid in candidates:
        try:
            crs = ec2._ec2_client(region).describe_capacity_reservations(
                CapacityReservationIds=[rid])["CapacityReservations"]
        except ClientError as err:
            seen.append(f"{rid} @ {region}: {ec2._error_code(err)}")
            continue
        for cr in crs:
            _cb_upsert(_cb_record(region, cr))
            if cr.get("State") == "active" and (cr.get("AvailableInstanceCount") or 0) >= 1:
                launchable.append((region, cr))
            else:
                note = f"starts {_iso(cr.get('StartDate'))}" if cr.get("State") == "scheduled" \
                    else f"available={cr.get('AvailableInstanceCount')}"
                seen.append(f"{rid} @ {region}: state={cr.get('State')} ({note})")
    if launchable:
        _floor = datetime.min.replace(tzinfo=timezone.utc)
        region, cr = max(launchable, key=lambda rc: rc[1].get("EndDate") or _floor)
        if len(launchable) > 1:
            others = ", ".join(f"{c['CapacityReservationId']} (ends {_iso(c.get('EndDate'))})"
                               for _, c in launchable if c is not cr)
            print(f"{len(launchable)} active blocks; picking {cr['CapacityReservationId']} "
                  f"(ends {_iso(cr.get('EndDate'))}, the latest). Others: {others}")
        return region, cr
    raise SystemExit("no launchable (active, free-slot) capacity reservation:\n  "
                     + "\n  ".join(seen))


def _cb_run_instances_kwargs(kwargs: Dict[str, Any], reservation_id: str) -> Dict[str, Any]:
    """Retarget one spot launch-kwargs dict at a capacity-block reservation.

    Same shape as ``ec2._run_instances_kwargs`` output except the market: the
    spot options are REPLACED by ``MarketType=capacity-block`` (SpotOptions
    are invalid there) and the launch is pinned to the reservation.
    Everything else -- ENI/SG, root volume, tags, user-data, key -- is
    untouched, so the box behaves identically once up. Pure; does not mutate
    the input.
    """
    out = dict(kwargs)
    out["InstanceMarketOptions"] = {"MarketType": "capacity-block"}
    out["CapacityReservationSpecification"] = {
        "CapacityReservationTarget": {"CapacityReservationId": reservation_id}
    }
    return out


def _provision_capacity_block(args) -> Dict[str, Any]:
    """``provision --capacity-reservation``: launch INTO a purchased block.

    No capacity hunt: the reservation fixes region, AZ and instance type
    (``--instance-types``/``--on-demand`` are ignored), so the launch either
    succeeds or the error is real (no free slot, misconfig) -- never
    retry-worthy. The OS-halt backstop defaults to the block's END +60 min
    rather than the 48h spot default: the block is prepaid, so an idle tail
    costs nothing extra, while a 48h backstop would halt a 7-day run
    mid-block. AWS reclaims the instance at the block end regardless (~30 min
    warning), which the per-stage S3 checkpoint sync already covers.
    """
    from smolbench.evals import ec2

    region, cr = _resolve_capacity_reservation(args)
    rid = cr["CapacityReservationId"]
    az, instance_type = cr["AvailabilityZone"], cr["InstanceType"]
    end = cr.get("EndDate")

    max_lifetime = args.max_lifetime
    if max_lifetime is None:
        max_lifetime = DEFAULT_MAX_LIFETIME_MIN
        if end is not None:
            max_lifetime = max(
                120, int((end - datetime.now(timezone.utc)).total_seconds() // 60) + 60)

    my_ip = ec2._my_public_ip()
    vpc_id, subnets = ec2._default_vpc_subnets(region)
    subnet_id = next((sid for sid, subnet_az in subnets if subnet_az == az), None)
    if vpc_id is None or subnet_id is None:
        raise SystemExit(f"no default-VPC subnet in {az} (reservation {rid} is pinned "
                         f"to that AZ); create one there before provisioning.")
    ami, root_device = ec2._resolve_ami(region)
    group_id = ec2._ensure_security_group(region, vpc_id, my_ip)
    _authorize_ssh(ec2, region, group_id, my_ip)
    _ensure_key_pair(ec2, region)

    kwargs = _cb_run_instances_kwargs(
        ec2._run_instances_kwargs(
            ami=ami, instance_type=instance_type, subnet_id=subnet_id,
            group_id=group_id, root_device=root_device,
            volume_gb=args.root_volume_gb,
            user_data=_render_train_user_data(max_lifetime),
            key_name=KEY_NAME, iam_profile=None,
        ),
        rid,
    )
    print(f"launching {instance_type} into {rid} ({az}, block ends {_iso(end)}) ...", flush=True)
    instance_id = ec2._try_launch(region, kwargs)
    try:
        public_ip = ec2._wait_public_ip(region, instance_id)
    except RuntimeError as err:
        # _wait_public_ip's abort message blames a spot reclaim and suggests
        # re-running the spot provisioner -- both wrong inside a reservation
        # (the slot returns to the block; a fresh SPOT box would abandon it).
        raise SystemExit(
            f"{err}\n(capacity-block launch: ignore the spot wording above -- the instance "
            f"died inside reservation {rid}, whose slot is free again. Re-run: "
            f"provision --capacity-reservation {rid})") from err
    state = {
        "instance_id": instance_id, "region": region, "availability_zone": az,
        "instance_type": instance_type, "public_ip": public_ip,
        "security_group_id": group_id, "key_name": KEY_NAME,
        "capacity_reservation_id": rid, "market": "capacity-block",
        "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ec2._save_state(state)
    print(f"launched {instance_id} ({instance_type} @ {az}, {public_ip}); "
          f"waiting for SSH ...", flush=True)
    _wait_ssh(state, timeout_s=args.ssh_timeout * 60)
    print(f"SSH up on {public_ip}. Run: setup", flush=True)
    return state


def provision(args) -> Dict[str, Any]:
    """Hunt spot capacity, launch the training box, wait for SSH, save state.

    Idempotent: reattaches to a live ``lean-train`` box recorded in the state
    file (re-authorizing SSH for the caller's current IP) instead of launching a
    second one. Mirrors ``ec2._launch_fresh``'s type x region x AZ capacity hunt,
    but with a key pair + port 22 + the training user-data.
    """
    from smolbench.evals import ec2
    from botocore.exceptions import ClientError

    # Reattach to an existing box if the state file points at a live one.
    state = ec2._load_state()
    if state is not None:
        st = ec2._instance_state(state["region"], state["instance_id"])
        if st in ("pending", "running"):
            # An EXPLICIT --capacity-reservation must never be silently
            # satisfied by a live box on a different market/block: the
            # operator would train on interruptible spot believing they
            # moved to the block, while the prepaid window burns idle.
            wanted = getattr(args, "capacity_reservation", None)
            have = state.get("capacity_reservation_id")
            if wanted and (have is None or (wanted != "auto" and wanted != have)):
                on = "the SPOT market" if have is None else f"block {have}"
                raise SystemExit(
                    f"--capacity-reservation {wanted} requested, but the state file points at "
                    f"live box {state['instance_id']} on {on} -- refusing to silently reattach. "
                    f"`teardown` that box first (or drop the flag to reattach to it).")
            my_ip = ec2._my_public_ip()
            _authorize_ssh(ec2, state["region"], state["security_group_id"], my_ip)
            if st == "running":
                state["public_ip"] = ec2._describe_instance(
                    state["region"], state["instance_id"]
                ).get("PublicIpAddress", state.get("public_ip"))
            ec2._save_state(state)
            print(f"reattached to {state['instance_id']} ({state['instance_type']} @ "
                  f"{state.get('availability_zone')}, {state.get('public_ip')}, "
                  f"market={state.get('market', 'spot')})")
            return state
        ec2._clear_state()

    # A purchased capacity block replaces the whole spot hunt: region/AZ/type
    # are fixed by the reservation. (The reattach branch above still applies.)
    if getattr(args, "capacity_reservation", None):
        return _provision_capacity_block(args)

    instance_types = tuple(args.instance_types.split(","))
    regions = tuple(r.strip() for r in (args.regions or ec2.EC2_REGIONS[0]).split(",") if r.strip()) \
        if args.regions else ec2.EC2_REGIONS
    my_ip = ec2._my_public_ip()
    user_data = _render_train_user_data(
        DEFAULT_MAX_LIFETIME_MIN if args.max_lifetime is None else args.max_lifetime)

    attempts: List[str] = []
    region_info: Dict[str, Optional[Dict[str, Any]]] = {}
    for instance_type in instance_types:
        for region in regions:
            if region not in region_info:
                vpc_id, subnets = ec2._default_vpc_subnets(region)
                if vpc_id is None or not subnets:
                    region_info[region] = None
                    attempts.append(f"{region}: no default VPC/subnets")
                    continue
                ami, root_device = ec2._resolve_ami(region)
                group_id = ec2._ensure_security_group(region, vpc_id, my_ip)
                _authorize_ssh(ec2, region, group_id, my_ip)
                _ensure_key_pair(ec2, region)
                region_info[region] = {"subnets": subnets, "ami": ami,
                                       "root_device": root_device, "group_id": group_id}
            info = region_info[region]
            if info is None:
                continue
            if not ec2._offers_instance_type(region, instance_type):
                attempts.append(f"{instance_type} @ {region}: not offered")
                continue
            for subnet_id, az in info["subnets"]:
                kwargs = ec2._run_instances_kwargs(
                    ami=info["ami"], instance_type=instance_type, subnet_id=subnet_id,
                    group_id=info["group_id"], root_device=info["root_device"],
                    volume_gb=args.root_volume_gb, user_data=user_data,
                    key_name=KEY_NAME, iam_profile=None,
                )
                # On-demand: strip the spot market options (scarce p5e has no spot
                # capacity, so the NeMo route runs on-demand). Keeps terminate-on-halt.
                if getattr(args, "on_demand", False):
                    kwargs.pop("InstanceMarketOptions", None)
                try:
                    print(f"trying {instance_type} in {az} ...", flush=True)
                    instance_id = ec2._try_launch(region, kwargs)
                except ClientError as err:
                    code = ec2._error_code(err)
                    attempts.append(f"{instance_type} @ {az}: {code}")
                    if code == "MaxSpotInstanceCountExceeded":
                        break
                    if code in ec2._CAPACITY_ERROR_CODES:
                        continue
                    raise
                public_ip = ec2._wait_public_ip(region, instance_id)
                state = {
                    "instance_id": instance_id, "region": region, "availability_zone": az,
                    "instance_type": instance_type, "public_ip": public_ip,
                    "security_group_id": info["group_id"], "key_name": KEY_NAME,
                    "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                ec2._save_state(state)
                print(f"launched {instance_id} ({instance_type} @ {az}, {public_ip}); "
                      f"waiting for SSH ...", flush=True)
                _wait_ssh(state, timeout_s=args.ssh_timeout * 60)
                print(f"SSH up on {public_ip}. Run: setup", flush=True)
                return state

    raise SystemExit("No spot capacity for any (instance type, region):\n  " + "\n  ".join(attempts))


# ---------------------------------------------------------------------------
# SSH driving
# ---------------------------------------------------------------------------

_SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
    "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30",
]


def _ssh_argv(state: Dict[str, Any], remote_cmd: str) -> List[str]:
    return ["ssh", "-i", str(KEY_PATH), *_SSH_OPTS,
            f"{SSH_USER}@{state['public_ip']}", remote_cmd]


def _ssh(state: Dict[str, Any], remote_cmd: str, *, check: bool = True,
         capture: bool = False, input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        _ssh_argv(state, remote_cmd), check=check, text=True,
        input=input_text,
        stdout=(subprocess.PIPE if capture else None),
        stderr=(subprocess.PIPE if capture else None),
    )


def _scp(state: Dict[str, Any], local: Path, remote: str) -> None:
    subprocess.run(
        ["scp", "-i", str(KEY_PATH), *_SSH_OPTS, str(local),
         f"{SSH_USER}@{state['public_ip']}:{remote}"],
        check=True,
    )


def _wait_ssh(state: Dict[str, Any], timeout_s: int) -> None:
    """Poll until the box accepts SSH and cloud-init finished (BOOTSTRAP_DONE)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = _ssh(state, "test -f /opt/train/BOOTSTRAP_DONE && echo ready",
                 check=False, capture=True)
        if r.returncode == 0 and "ready" in (r.stdout or ""):
            return
        time.sleep(10)
    raise SystemExit(
        f"SSH/bootstrap not ready after {timeout_s // 60} min on {state['public_ip']}. "
        f"Check /var/log/smolbench-train-bootstrap.log via `status`."
    )


# ---------------------------------------------------------------------------
# Setup + training
# ---------------------------------------------------------------------------


def setup(args) -> None:
    """Upload the dataset + trainer + requirements and build the training venv.

    The venv (CUDA torch + peft/trl/bitsandbytes/accelerate) is built on the box
    from ``scripts/requirements-train.txt``; nothing training-related is
    installed in the local venvs. HF_TOKEN is written to a 0600 file on the box
    (sourced by each training run) rather than passed on the command line.
    """
    from smolbench.evals import ec2

    state = ec2._require_state()
    missing = [str(p) for p in DATASETS.values() if not p.exists()]
    if missing:
        raise SystemExit(
            "SFT dataset(s) missing (run scripts/build_lean_sft.py and "
            "scripts/build_lean_synth_sft.py):\n  " + "\n  ".join(missing)
        )

    print("uploading datasets + trainer + requirements ...", flush=True)
    _ssh(state, f"mkdir -p {REMOTE_ROOT}/scripts {REMOTE_HF_CACHE} {REMOTE_OUT}")
    for name, path in DATASETS.items():
        print(f"  {name} ({path.stat().st_size // (1 << 20)} MB)", flush=True)
        _scp(state, path, f"{REMOTE_ROOT}/{name}")
    _scp(state, TRAIN_SCRIPT, f"{REMOTE_ROOT}/scripts/lean_lora_sft.py")
    _scp(state, REQUIREMENTS, f"{REMOTE_ROOT}/scripts/requirements-train.txt")
    # The resumable Qwen 4-way orchestrator (run on-box via nohup). Uploaded
    # here so a fresh box after a spot interruption has it without re-deriving.
    if ORCHESTRATOR.exists():
        _scp(state, ORCHESTRATOR, f"{REMOTE_ROOT}/{ORCHESTRATOR.name}")

    # HF token -> 0600 file on the box (transmitted over SSH stdin, not argv).
    _ssh(state, f"umask 077 && cat > {REMOTE_ROOT}/hf_env",
         input_text=f"export HF_TOKEN={_hf_token()}\nexport HF_HOME={REMOTE_HF_CACHE}\n")

    print("building the training venv (torch + peft/trl/bitsandbytes) ...", flush=True)
    # The base-OSS DL AMI is minimal (GPU drivers only): its system python3 has
    # no ensurepip/venv, so install python3-venv first (ubuntu has passwordless
    # sudo). Clear any half-created venv from a prior failed attempt.
    build = (
        f"set -e; cd {REMOTE_ROOT}; "
        f"sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv python3-pip; "
        f"rm -rf {REMOTE_VENV}; "
        f"python3 -m venv {REMOTE_VENV}; "
        f"{REMOTE_VENV}/bin/pip install -q --upgrade pip; "
        f"{REMOTE_VENV}/bin/pip install -q -r scripts/requirements-train.txt; "
        # awscli into the venv: the S3 checkpoint sync uses {venv}/bin/aws, and the
        # minimal base-OSS AMI can't be assumed to ship the CLI (it lacked venv).
        f"{REMOTE_VENV}/bin/pip install -q awscli; "
        f"{REMOTE_VENV}/bin/python -c \"import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available(),'gpus',torch.cuda.device_count())\"; "
        f"{REMOTE_VENV}/bin/aws --version"
    )
    _ssh(state, build)
    print("setup done. Run: train --model <key> [--cap N] | train-all", flush=True)


def _s3_bucket() -> str:
    """The checkpoint bucket name, parsed from ``EC2_S3_MODEL_CACHE`` (keys.env)."""
    from smolbench.evals import ec2

    uri = ec2.EC2_S3_MODEL_CACHE or ""
    if not uri.startswith("s3://"):
        raise SystemExit(
            "EC2_S3_MODEL_CACHE is unset -- `set -a; source notebooks/periodic/keys.env; "
            "set +a` before running (S3 checkpoint mode needs the cache bucket)."
        )
    return uri[len("s3://"):].split("/", 1)[0]


def _s3_region() -> str:
    from smolbench.evals import ec2

    return ec2.EC2_S3_CACHE_REGION or "us-west-2"


def _run_name(model: Dict[str, str], args) -> str:
    """This run's path segment: ``<model key>`` or ``<model key>/<--out-name>``.

    ``--out-name`` distinguishes the stages/arms of a staged run (e.g.
    ``goedel-stage1`` / ``goedel-stage2``) under one model; empty (the
    default) reproduces the original flat ``<model key>`` layout used by the
    real-only recipe.
    """
    out_name = getattr(args, "out_name", "") or ""
    return f"{model['key']}/{out_name}" if out_name else model["key"]


def _run_slug(model: Dict[str, str], args) -> str:
    """Filesystem-safe slug of `_run_name` for on-box log/marker filenames."""
    return _run_name(model, args).replace("/", "-")


def _s3_dest(run_name: str, args) -> str:
    """``s3://<bucket>/<prefix>/<run_name>/`` -- this run's checkpoint prefix."""
    return f"s3://{_s3_bucket()}/{args.s3_prefix}/{run_name}/"


def _train_cmd(model: Dict[str, str], args) -> str:
    """The remote shell command that runs one QLoRA training, detached, with a marker.

    Two durability modes (``--checkpoint-dest``):
    - ``s3`` (default): the trainer saves the adapter locally every ``--save-steps``
      and NO ``--push-to-hub`` is passed (the keys.env HF token is read-only). A
      background loop mirrors the output dir to S3 every ~90s (via the box's
      instance-profile creds -- see ``attach-s3``), and a final sync runs before the
      DONE marker is written, so the marker implies S3 is fully synced.
    - ``hub``: the original path -- push the adapter to a private HF repo (needs a
      write-enabled token in ``.hf_token``).
    """
    run_name = _run_name(model, args)
    slug = _run_slug(model, args)
    out_dir = f"{REMOTE_OUT}/{run_name}"
    dataset = f"{REMOTE_ROOT}/{args.dataset_file}"
    cap = "" if args.full else f"--max-examples {args.cap}"
    steps = f"--max-steps {args.max_steps}" if args.max_steps > 0 else ""
    det = "--full-determinism" if args.full_determinism else ""
    log = f"{REMOTE_OUT}/{slug}.log"
    done = f"{REMOTE_OUT}/{slug}.DONE"
    tm = f"--target-modules {model['target_modules']}"
    moe = "--moe-unquantized" if model.get("moe") else ""
    trc = "--trust-remote-code" if model.get("trust_remote_code") else ""
    nf = "--no-4bit" if model.get("no_4bit") else ""

    # Stage-2 (anneal) continues a stage-1 adapter pulled from S3. Sync it to a
    # local dir first, then pass --init-adapter; the trainer loads it as
    # trainable (PeftModel.from_pretrained is_trainable=True). Stage 1 always
    # writes its adapter to S3 before this runs, so a stage-2 crash re-pulls
    # the frozen stage-1 rather than redoing it.
    init_flag = ""
    init_sync = ""
    if getattr(args, "init_adapter_s3", None):
        init_dir = f"{REMOTE_OUT}/{slug}.init"
        init_sync = (
            f"{REMOTE_VENV}/bin/aws s3 sync {args.init_adapter_s3} {init_dir} "
            f"--only-show-errors --region {_s3_region()}; "
        )
        init_flag = f"--init-adapter {init_dir}"

    common_flags = (
        f"--base-model {model['base']} --dataset {dataset} "
        f"--output-dir {out_dir} {tm} {moe} {trc} {nf} {init_flag} "
        f"--save-steps {args.save_steps} {cap} {steps} "
        f"--lora-r {args.lora_r} --lora-alpha {args.lora_alpha} "
        f"--batch-size {args.batch_size} --grad-accum {args.grad_accum} "
        f"--seed {args.seed} {det}"
    )

    if args.checkpoint_dest == "s3":
        dest = _s3_dest(run_name, args)
        syncstop = f"{REMOTE_OUT}/{slug}.SYNCSTOP"
        sync = f"{REMOTE_VENV}/bin/aws s3 sync {out_dir} {dest} --only-show-errors --region {_s3_region()}"
        # HF_TOKEN (read) is still sourced -- needed to PULL gated Llama/Nemotron bases.
        inner = (
            f". {REMOTE_ROOT}/hf_env; cd {REMOTE_ROOT}; rm -f {done} {syncstop}; mkdir -p {out_dir}; "
            f"{init_sync}"
            f"( while [ ! -f {syncstop} ]; do {sync}; sleep 90; done ) & "
            f"{REMOTE_VENV}/bin/python scripts/lean_lora_sft.py {common_flags}; "
            f"rc=$?; touch {syncstop}; {sync}; echo rc=$rc > {done}"
        )
    else:  # hub
        adapter_repo = f"{args.org}/{model['suffix']}"
        inner = (
            f". {REMOTE_ROOT}/hf_env; cd {REMOTE_ROOT}; rm -f {done}; "
            f"{init_sync}"
            f"{REMOTE_VENV}/bin/python scripts/lean_lora_sft.py {common_flags} "
            f"--push-to-hub {adapter_repo} --private; "
            f"echo rc=$? > {done}"
        )
    return f"nohup bash -lc {_shq(inner)} > {log} 2>&1 & echo launched pid $!"


def _shq(s: str) -> str:
    """Single-quote a string for safe embedding in a remote bash -lc."""
    return "'" + s.replace("'", "'\\''") + "'"


def _default_train_timeout(state: Dict[str, Any]) -> int:
    """``--timeout`` default: 48h, or the block's remaining window on a CB box.

    A capacity-block box exists precisely to outlive the 48h spot horizon
    (multi-day blocks); capping the driver-side wait at 2880 min would abort
    the poll mid-stage and invite a double-launching re-run. The block's end
    date comes from the ledger record written at purchase/describe time.
    """
    if state.get("market") == "capacity-block":
        rec = next((r for r in _cb_load()
                    if r.get("reservation_id") == state.get("capacity_reservation_id")), None)
        try:
            end = datetime.strptime((rec or {}).get("end_date") or "",
                                    "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return DEFAULT_MAX_LIFETIME_MIN
        return max(60, int((end - datetime.now(timezone.utc)).total_seconds() // 60) + 120)
    return DEFAULT_MAX_LIFETIME_MIN


def train(args) -> int:
    """QLoRA one model: launch detached on the box, poll the log to completion.

    ``--attach`` skips the launch and only polls -- the recovery path after a
    driver-side timeout or disconnect. A plain re-run refuses to start while
    a trainer for the same run is alive on the box: ``_train_cmd`` begins by
    deleting the DONE/SYNCSTOP markers and nohup-launching a second trainer
    plus a second S3-sync loop against the same GPUs and S3 prefix.
    """
    from smolbench.evals import ec2

    state = ec2._require_state()
    model = _TRIO_BY_KEY.get(args.model)
    if model is None:
        raise SystemExit(f"unknown model {args.model!r}; choices: {list(_TRIO_BY_KEY)}")

    run_name = _run_name(model, args)
    slug = _run_slug(model, args)
    out_dir = f"{REMOTE_OUT}/{run_name}"
    log = f"{REMOTE_OUT}/{slug}.log"
    done = f"{REMOTE_OUT}/{slug}.DONE"
    dest = _s3_dest(run_name, args) if args.checkpoint_dest == "s3" else f"{args.org}/{model['suffix']} (HF)"
    if getattr(args, "attach", False):
        r = _ssh(state, f"test -f {log} && echo HAVE || true", check=False, capture=True)
        if "HAVE" not in (r.stdout or ""):
            raise SystemExit(f"--attach: no log at {log} on the box; nothing to attach to.")
        print(f"=== attaching to {run_name} (no relaunch) ===", flush=True)
    else:
        # The [-]- character class keeps pgrep from matching this probe's own
        # remote shell (whose cmdline also contains the pattern text).
        r = _ssh(state, f'pgrep -f "[-]-output-dir {out_dir} " >/dev/null && echo RUNNING || true',
                 check=False, capture=True)
        if "RUNNING" in (r.stdout or ""):
            raise SystemExit(
                f"a trainer for {run_name} is already running on the box; re-running would "
                f"launch a SECOND one against the same GPUs and S3 prefix. Poll it instead: "
                f"train --model {args.model} --attach (plus the same --out-name/--dataset-file).")
        print(f"=== training {run_name} ({model['base']}) on {args.dataset_file}"
              f"{' <- ' + args.init_adapter_s3 if getattr(args, 'init_adapter_s3', None) else ''} -> {dest} ===",
              flush=True)
        _ssh(state, _train_cmd(model, args))

    # Poll: stream new log lines, stop when the DONE marker appears.
    timeout_min = args.timeout if args.timeout is not None else _default_train_timeout(state)
    deadline = time.time() + timeout_min * 60
    seen = 0
    while time.time() < deadline:
        r = _ssh(state, f"cat {done} 2>/dev/null; echo ---; wc -l < {log} 2>/dev/null || echo 0",
                 check=False, capture=True)
        out = r.stdout or ""
        marker, _, nlines = out.partition("---")
        try:
            total = int(nlines.strip() or "0")
        except ValueError:
            total = 0
        if total > seen:
            tail = _ssh(state, f"tail -n +{seen + 1} {log} 2>/dev/null | tail -n 25",
                        check=False, capture=True)
            sys.stdout.write(tail.stdout or "")
            sys.stdout.flush()
            seen = total
        if marker.strip().startswith("rc="):
            rc = marker.strip()
            ok = rc == "rc=0"
            if ok:
                note = f"adapter synced to {dest}" if args.checkpoint_dest == "s3" else f"adapter pushed to {dest}"
            else:
                note = "FAILED (checkpoint not saved; see log)"
            print(f"=== {model['key']} finished: {rc} ({note}) ===", flush=True)
            return 0 if ok else 1
        time.sleep(args.poll)
    raise SystemExit(f"{model['key']} training did not finish within {timeout_min} min -- the "
                     f"trainer KEEPS RUNNING on the box. Re-poll with: train --model {args.model} "
                     f"--attach (a re-run without --attach would double-launch).")


def train_all(args) -> int:
    """Train the whole trio sequentially (Qwen -> Nemotron -> 405B)."""
    rc = 0
    for model in TRIO:
        args.model = model["key"]
        rc |= train(args)
    return rc


def gpu_smoke(args) -> int:
    """Validate the staged ``--init-adapter`` path on the box GPU, bf16 AND 4-bit.

    Runs a tiny 1B-model stage1->stage2 twice -- once bf16, once 4-bit -- to
    exercise dataset load, the ``PeftModel.from_pretrained(is_trainable=True)``
    continue-path, the device_map + fail-fast-guard load, and (crucially) the
    **4-bit** continue-path the dense/NAS trio bases use. No CPU smoke can cover
    4-bit (bnb's kernel needs a GPU), and Qwen's own run is ``--moe-unquantized``
    (bf16), so this is the only cheap on-hardware check of the quantized
    continue-path. Run BEFORE the ~470GB trio download -- pennies, ~10 min.
    """
    from smolbench.evals import ec2

    state = ec2._require_state()
    m = "Qwen/Qwen2.5-1.5B-Instruct"  # public, real weights, quantizes properly
    ds = f"{REMOTE_ROOT}/{args.dataset_file}"
    # One visible GPU -> the explicit device_map is computed for a single card
    # (the real trio path), not spread across 8. Tiny caps: 16 examples, 3 steps.
    base = (
        f"CUDA_VISIBLE_DEVICES=0 {REMOTE_VENV}/bin/python scripts/lean_lora_sft.py "
        f"--base-model {m} --dataset {ds} --max-examples 16 --grad-accum 2 "
        f"--max-steps 3 --save-steps 3 --max-seq-len 512 --no-assistant-only-loss"
    )
    steps = []
    for flag, tag in (("--no-4bit", "bf16"), ("", "4bit")):
        s1, s2 = f"{REMOTE_OUT}/smoke-{tag}-s1", f"{REMOTE_OUT}/smoke-{tag}-s2"
        steps.append(f"echo '### {tag} STAGE1 (fresh)'; {base} {flag} --output-dir {s1}")
        steps.append(f"echo '### {tag} STAGE2 (--init-adapter)'; {base} {flag} --init-adapter {s1} --output-dir {s2}")
    log, done = f"{REMOTE_OUT}/gpu-smoke.log", f"{REMOTE_OUT}/gpu-smoke.DONE"
    inner = (
        f". {REMOTE_ROOT}/hf_env; cd {REMOTE_ROOT}; rm -f {done}; "
        f"( set -e; " + "; ".join(steps) + "; echo GPU_SMOKE_OK ); echo rc=$? > " + done
    )
    print(f"=== GPU smoke: staged bf16+4bit --init-adapter on {m} ===", flush=True)
    _ssh(state, f"nohup bash -lc {_shq(inner)} > {log} 2>&1 & echo launched pid $!")

    timeout_min = args.timeout if args.timeout is not None else _default_train_timeout(state)
    deadline = time.time() + timeout_min * 60
    seen = 0
    while time.time() < deadline:
        r = _ssh(state, f"cat {done} 2>/dev/null; echo ---; wc -l < {log} 2>/dev/null || echo 0",
                 check=False, capture=True)
        marker, _, nlines = (r.stdout or "").partition("---")
        try:
            total = int(nlines.strip() or "0")
        except ValueError:
            total = 0
        if total > seen:
            tail = _ssh(state, f"tail -n +{seen + 1} {log} 2>/dev/null | tail -n 30", check=False, capture=True)
            sys.stdout.write(tail.stdout or "")
            sys.stdout.flush()
            seen = total
        if marker.strip().startswith("rc="):
            ok = marker.strip() == "rc=0"
            print(f"=== GPU smoke {'PASSED' if ok else 'FAILED'} ({marker.strip()}) ===", flush=True)
            return 0 if ok else 1
        time.sleep(args.poll)
    raise SystemExit(f"GPU smoke did not finish within {timeout_min} min (see {log} on the box).")


def status(args) -> int:
    """Describe the box and tail whatever training log is most recent."""
    from smolbench.evals import ec2

    state = ec2._load_state()
    if state is None:
        print("no lean-train state; nothing provisioned.")
        return 0
    st = ec2._instance_state(state["region"], state["instance_id"])
    print(f"instance {state['instance_id']} ({state['instance_type']} @ "
          f"{state.get('availability_zone')}): {st}  ip={state.get('public_ip')}")
    if st not in ("pending", "running"):
        return 0
    r = _ssh(state, f"for m in {' '.join(m['key'] for m in TRIO)}; do "
                    f"d={REMOTE_OUT}/$m.DONE; l={REMOTE_OUT}/$m.log; "
                    f"if [ -f $d ]; then echo \"$m: $(cat $d)\"; "
                    f"elif [ -f $l ]; then echo \"$m: running ($(wc -l < $l) log lines)\"; fi; done; "
                    f"echo '--- latest log tail ---'; "
                    f"ls -t {REMOTE_OUT}/*.log 2>/dev/null | head -1 | xargs -r tail -n 20",
             check=False, capture=True)
    sys.stdout.write(r.stdout or "")
    if r.stderr:
        sys.stderr.write(r.stderr)
    return 0


def attach_s3(args) -> int:
    """Ensure the S3-writable instance profile and associate it with the RUNNING box.

    Reuses ``ec2._ensure_instance_profile`` -> ``smolbench-ec2-role`` (read/write to
    the cache bucket via ``s3:PutObject`` on ``<bucket>/*``, + SSM core). The training
    box was launched with no profile, so we associate one with the already-running
    instance (no re-provision, keeps the cached weights) -- IMDS then hands the box
    refreshing creds and ``aws s3 sync`` works with no static/expiring keys.
    Idempotent. Run AFTER ``setup`` (the verify step uses the venv's ``aws``).
    """
    from smolbench.evals import ec2

    state = ec2._require_state()
    bucket = _s3_bucket()
    profile = ec2._ensure_instance_profile(bucket)
    client = ec2._ec2_client(state["region"])
    assocs = client.describe_iam_instance_profile_associations(
        Filters=[{"Name": "instance-id", "Values": [state["instance_id"]]}],
    )["IamInstanceProfileAssociations"]
    live = [a for a in assocs if a.get("State") in ("associating", "associated")]
    if live:
        print(f"instance profile already associated: {live[0]['IamInstanceProfile']['Arn']}")
    else:
        client.associate_iam_instance_profile(
            IamInstanceProfile={"Name": profile}, InstanceId=state["instance_id"])
        print(f"associated instance profile {profile!r} with {state['instance_id']}")

    print("verifying S3 access from the box (IMDS creds may take ~30-60s) ...", flush=True)
    check = (
        f"{REMOTE_VENV}/bin/aws sts get-caller-identity --query Arn --output text 2>/dev/null && "
        f"{REMOTE_VENV}/bin/aws s3 ls s3://{bucket}/ >/dev/null 2>&1 && echo S3_OK"
    )
    for _ in range(12):
        r = _ssh(state, check, check=False, capture=True)
        if "S3_OK" in (r.stdout or ""):
            print(f"box S3 access OK (role: {(r.stdout or '').strip().splitlines()[0]})")
            return 0
        time.sleep(10)
    print(f"WARNING: could not confirm S3 access from the box within ~2 min; "
          f"check `{REMOTE_VENV}/bin/aws sts get-caller-identity` on the box.", file=sys.stderr)
    return 1


def teardown(args) -> int:
    from smolbench.evals import ec2

    ec2.shutdown_instance(wait=not args.no_wait)
    print("teardown complete (state cleared).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("provision", help="launch the training box (spot by default; --on-demand for scarce p5e; "
                                          "--capacity-reservation for a purchased block)")
    pp.add_argument("--instance-types", default="p5e.48xlarge,p5.48xlarge")
    pp.add_argument("--regions", default=None, help="comma list; default EC2_REGIONS")
    pp.add_argument("--root-volume-gb", type=int, default=400)
    pp.add_argument("--on-demand", action="store_true", help="launch on-demand instead of spot (p5e has no spot capacity)")
    pp.add_argument("--capacity-reservation", default=None, metavar="CR_ID|auto",
                    help="launch INTO a purchased capacity block instead of hunting spot: a cr- id, or "
                         "'auto' for the ledger's active block with the most remaining window. Region/AZ/"
                         "instance type come from the reservation (--instance-types/--on-demand are ignored).")
    pp.add_argument("--max-lifetime", type=int, default=None,
                    help=f"OS-halt backstop, minutes (default {DEFAULT_MAX_LIFETIME_MIN} = 48h for spot; "
                         f"for a capacity block, the block's end +60 min)")
    pp.add_argument("--ssh-timeout", type=int, default=15, help="minutes to wait for SSH+bootstrap")
    pp.set_defaults(func=provision)

    pcbs = sub.add_parser("cb-search", help="list purchasable capacity-block offerings (read-only)")
    pcbs.add_argument("--instance-type", default="p5.48xlarge")
    pcbs.add_argument("--instance-count", type=int, default=1)
    pcbs.add_argument("--duration-hours", type=int, required=True,
                      help="desired block length in hours (e.g. 24, 72, 168); offerings come back "
                           "aligned to AWS's fixed start/end boundaries, so actual durations vary "
                           "(a live search for 24h returned 16h/24h/40h windows)")
    pcbs.add_argument("--start-after", default=None, help="earliest start: +Nh / +Nd / ISO-8601 (default: any)")
    pcbs.add_argument("--end-before", default=None, help="latest end: +Nh / +Nd / ISO-8601 (default: any)")
    pcbs.add_argument("--regions", default=None, help="comma list; default EC2_REGIONS")
    pcbs.set_defaults(func=cb_search)

    pcbp = sub.add_parser("cb-purchase", help="buy one capacity-block offering "
                                              "(DryRun validation unless --yes; UPFRONT + NON-REFUNDABLE)")
    pcbp.add_argument("--region", required=True, help="region the offering came from (cb-search prints it)")
    pcbp.add_argument("--offering-id", required=True, help="CapacityBlockOfferingId from cb-search")
    pcbp.add_argument("--yes", action="store_true",
                      help="actually purchase (without this, only a DryRun validation runs)")
    pcbp.set_defaults(func=cb_purchase)

    pcbt = sub.add_parser("cb-status", help="live states of the ledger's capacity blocks")
    pcbt.add_argument("--reservation-id", default=None, help="one reservation instead of the whole ledger")
    pcbt.add_argument("--region", default=None, help="needed with --reservation-id when it is not in the ledger")
    pcbt.set_defaults(func=cb_status)

    ps = sub.add_parser("setup", help="upload artifacts + build the training venv on the box")
    ps.set_defaults(func=setup)

    pas = sub.add_parser("attach-s3", help="associate the S3-writable instance profile with the running box (for --checkpoint-dest s3)")
    pas.set_defaults(func=attach_s3)

    def _add_train_args(sp):
        sp.add_argument("--checkpoint-dest", choices=["s3", "hub"], default="s3",
                        help="where adapter checkpoints go: s3 (default; instance-profile creds) or hub (needs a write token)")
        sp.add_argument("--s3-prefix", default="lean-train-checkpoints",
                        help="key prefix under the EC2_S3_MODEL_CACHE bucket for checkpoints")
        sp.add_argument("--org", default="rengz", help="HF namespace for the private adapter repos (hub dest only)")
        sp.add_argument("--dataset-file", default=DEFAULT_DATASET, choices=list(DATASETS),
                        help="which uploaded SFT dataset to train on (default: the decontaminated real anneal set)")
        sp.add_argument("--init-adapter-s3", default=None,
                        help="s3:// URI of a stage-1 adapter to CONTINUE (staged anneal); synced to the box and "
                             "passed as --init-adapter. Omit for a fresh (stage-1) adapter.")
        sp.add_argument("--out-name", default="",
                        help="run sub-path under the model key for markers/checkpoints (e.g. 'goedel-stage1'); "
                             "distinguishes the arms/stages of a staged run. Empty = flat <model key> (real-only).")
        sp.add_argument("--cap", type=int, default=8000, help="first-run example cap (0 with --full for all)")
        sp.add_argument("--full", action="store_true", help="train on all examples in --dataset-file (ignore --cap)")
        sp.add_argument("--max-steps", type=int, default=-1)
        sp.add_argument("--save-steps", type=int, default=200)
        sp.add_argument("--lora-r", type=int, default=16)
        sp.add_argument("--lora-alpha", type=int, default=32)
        sp.add_argument("--batch-size", type=int, default=1)
        sp.add_argument("--grad-accum", type=int, default=16)
        sp.add_argument("--seed", type=int, default=1776, help="training seed threaded to lean_lora_sft.py (reproducibility)")
        sp.add_argument("--full-determinism", action="store_true", help="bitwise-reproducible training (slower; passed through)")
        sp.add_argument("--poll", type=int, default=60, help="log-poll interval, seconds")
        sp.add_argument("--timeout", type=int, default=None,
                        help="per-model wait cap, minutes (default 2880 = 48h; on a capacity-block "
                             "box, the block's remaining window +2h)")

    pt = sub.add_parser("train", help="QLoRA one model")
    pt.add_argument("--model", required=True, choices=list(_TRIO_BY_KEY))
    pt.add_argument("--attach", action="store_true",
                    help="do not launch: poll the already-running/finished run for --model/--out-name "
                         "(the recovery path after a driver-side timeout or disconnect)")
    _add_train_args(pt)
    pt.set_defaults(func=train)

    pa = sub.add_parser("train-all", help="QLoRA the whole trio sequentially")
    _add_train_args(pa)
    pa.set_defaults(func=train_all)

    pgs = sub.add_parser("gpu-smoke", help="validate the staged --init-adapter path on GPU (bf16+4bit, tiny 1B model)")
    _add_train_args(pgs)
    pgs.set_defaults(func=gpu_smoke)

    pst = sub.add_parser("status", help="box state + training-log tail")
    pst.set_defaults(func=status)

    ptd = sub.add_parser("teardown", help="terminate the box + clear state")
    ptd.add_argument("--no-wait", action="store_true")
    ptd.set_defaults(func=teardown)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result = args.func(args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
