"""Run the induction and Horn studies on Amazon Bedrock for three ladder models.

The notebook ``bedrock_trio.ipynb`` drives this module. Everything here reuses the
existing run code: ``providers.aws`` (bedrock-mantle, OpenAI-compatible) sends the
requests, ``ReplicateHarness`` and ``notebooks/induction/run_study.make_quizzes`` run
the induction study, and ``scripts/deduction/horn/sweep.py`` runs and scores the Horn
cells. This module adds only what Bedrock needs on top: the model roster, a per-model
endpoint switch, a results store with the released-results layout, and a check that
every response was reasoned.

The private S3 bucket (``RESULTS_S3``) is the store of record for both studies and
``RESULTS_DIR`` is a local mirror of it that the report cells read. Objects in the bucket
are append-only: every writer here adds a new stamped key and none replaces one.
Pass ``s3_uri=None`` everywhere to keep the results local only.
"""

from __future__ import annotations

import collections
import contextlib
import csv
import importlib.util
import json
import logging
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, Mapping, Optional, Sequence

import requests

from smolbench.deduction.horn.render import ALL_ARMS
from smolbench.evals import Marks, _aws
from smolbench.evals.results_store import (
    ReplicateAddress,
    ResultsStore,
    S3ResultsStore,
    format_run_ts,
    parse_s3_uri,
    utcnow,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REBUTTAL_DIR = REPO_ROOT / "rebuttal"
#: Local mirror of the bucket (``RESULTS_S3``), not committed: induction YAMLs and Horn rows.
RESULTS_DIR = REBUTTAL_DIR / "results"
#: Rendered Horn rungs; deterministic and digest-checked, so not committed.
RUNGS_DIR = REBUTTAL_DIR / "rungs"
# Per-cell verdicts of the paper's Bedrock Horn cells and of the review-round ``rep`` and
# ``tjunk`` cells (Converse API, us-east-2, 131,072-token output cap).
REVIEW_CELLS = REPO_ROOT / "notebooks" / "deduction" / "review" / "bedrock_cells.csv"

MANTLE_URL = "https://bedrock-mantle.{region}.api.aws{path}"
DEFAULT_REGION = "us-east-1"
#: The three induction arms of the ICLR table (``zero`` is left out, as there).
INDUCTION_ARMS = ("intens", "noise_intens", "extens")
#: The arms the paper reports; ``horn_repro.report`` contrasts cover these only.
HORN_PAPER_ARMS = ("lem", "pad", "disc", "both")
#: The paper arms, then the four review arms (``render.ALL_ARMS``).
HORN_ARMS = tuple(ALL_ARMS)
HORN_TEMPERATURE = 0.7
#: Store of record for both studies (private, append-only); ``None`` keeps results local.
RESULTS_S3 = "s3://smolbench-rebuttals-414266451290/bedrock-trio"
#: Region of the results bucket; Bedrock inference has its own region (``DEFAULT_REGION``).
RESULTS_S3_REGION = "us-west-2"
# Sub-prefix (and local mirror folder) of smoke runs. ``smoke/`` holds the first smoke of
# 2026-11-13, whose non-ASCII text was stored mis-decoded (UTF-8 read as ISO-8859-1); the
# bucket is append-only, so that run stays where it is and is not read.
SMOKE_PREFIX = "smoke-2"
#: Opening of the listing in a released ``extens`` prompt (positions are listed from 1).
LISTING_START = "Position 1: "
#: Opening of the template text after the context (``run_study.template``); rules and
#: listing lines never contain it, as labels are lowercase letters.
QUESTION_START = "\nQuestion:"


@dataclass(frozen=True)
class BedrockModel:
    """One model of the trio, keyed by its ICLR roster key."""

    #: Roster key in both ``iclr.json`` files and ``EC2_DEPLOY_SPECS``.
    key: str
    #: Bedrock model id; ``None`` until resolved from ``GET /models``.
    bedrock_id: Optional[str]
    #: Base path on bedrock-mantle, up to ``/chat/completions``.
    base_path: str
    #: Bedrock's output-token cap for the model (reasoning included).
    max_tokens: int
    #: Context window from the Bedrock model card.
    context_length: int
    #: Request fields that switch reasoning on, tried in order by ``pick_reasoning_args``.
    reasoning_candidates: tuple[dict, ...]
    #: Harness tag (``smolbench/evals/study_config.toml``).
    tag: str
    #: Substrings that identify the id in a ``GET /models`` listing.
    id_hints: tuple[str, ...] = field(default=())


# Output caps and context windows come from the Bedrock model cards. Gemma 4's card gives
# no output cap, so it gets Nemotron's 32K; the probe reports a lower one if Bedrock
# enforces it. DeepSeek and Nemotron take ``reasoning_effort`` (the ICLR Horn Bedrock
# rows used exactly that); for Gemma 4 the working spelling is found by the probe.
TRIO: dict[str, BedrockModel] = {
    m.key: m
    for m in (
        BedrockModel(
            key="gemma-4-31b",
            bedrock_id="google.gemma-4-31b",
            base_path="/openai/v1",
            max_tokens=32768,
            context_length=262144,
            reasoning_candidates=(
                {"reasoning_effort": "high"},
                {"chat_template_kwargs": {"enable_thinking": True}},
            ),
            tag="gemma4_31b",
        ),
        BedrockModel(
            key="nemotron-3-super-120b-a12b",
            bedrock_id="nvidia.nemotron-super-3-120b",
            base_path="/v1",
            max_tokens=32768,
            context_length=262144,
            reasoning_candidates=({"reasoning_effort": "high"},),
            tag="nemo3_120b",
        ),
        BedrockModel(
            key="deepseek-v3.1",
            bedrock_id=None,
            base_path="/v1",
            max_tokens=8192,
            context_length=131072,
            reasoning_candidates=(
                {"reasoning_effort": "high"},
                {"chat_template_kwargs": {"thinking": True}},
            ),
            tag="ds_v31",
            id_hints=("deepseek", "v3"),
        ),
    )
}


# --------------------------------------------------------------------------- auth


def mint_token(region: str = DEFAULT_REGION) -> str:
    """Set ``AWS_BEARER_TOKEN_BEDROCK`` to a short-term token minted from the AWS profile.

    An already-set token is kept, so a long-term key or a token minted elsewhere wins.

    Parameters
    ----------
    region : str
        Region the token is minted for.

    Returns
    -------
    str
        The token in effect.
    """
    token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        from aws_bedrock_token_generator import (  # pylint: disable=import-outside-toplevel
            provide_token,
        )

        token = provide_token(region=region)
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
    return token


def base_url(model: BedrockModel, region: str) -> str:
    """The model's bedrock-mantle base URL (``.../v1`` or ``.../openai/v1``)."""
    return MANTLE_URL.format(region=region, path=model.base_path)


def list_mantle_models(region: str, path: str = "/v1") -> list[str]:
    """Model ids from ``GET /models`` on one bedrock-mantle path."""
    resp = requests.get(
        f"{MANTLE_URL.format(region=region, path=path)}/models",
        headers={"Authorization": f"Bearer {os.environ['AWS_BEARER_TOKEN_BEDROCK']}"},
        timeout=60,
    )
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def resolve_ids(
    listing: Sequence[str], trio: Mapping[str, BedrockModel] = TRIO
) -> dict[str, BedrockModel]:
    """Check every known id against a listing and fill the ones left ``None``.

    Parameters
    ----------
    listing : Sequence[str]
        Ids from ``GET /models`` (all paths combined).
    trio : Mapping[str, BedrockModel]
        The roster.

    Returns
    -------
    dict[str, BedrockModel]
        The roster with every ``bedrock_id`` set.

    Raises
    ------
    LookupError
        If the hints of an unresolved id match no id or more than one. A known id
        missing from the listing only logs a warning.
    """
    out = {}
    for key, model in trio.items():
        if model.bedrock_id is not None:
            if model.bedrock_id not in listing:
                # The probe is the access check: it reports the HTTP error body (such as
                # a 401 for a model not enabled on the account), which says more than
                # an absence from a listing that may not cover every path.
                logging.warning("%s: %r not in GET /models; the probe will check it", key, model.bedrock_id)
            out[key] = model
            continue
        hits = [i for i in listing if all(h in i.lower() for h in model.id_hints)]
        # DeepSeek V3.1 is spelled v3.1, v3-1 or v3-v1; V3.2 must not match.
        hits = [i for i in hits if not any(f"v3{s}2" in i.lower() for s in ".-")]
        if len(hits) != 1:
            raise LookupError(f"{key}: hints {model.id_hints} match {hits}: {sorted(listing)}")
        out[key] = replace(model, bedrock_id=hits[0])
    return out


@contextlib.contextmanager
def _env(**env: str) -> Iterator[None]:
    """Set environment variables for the duration of a block, then restore them."""
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def use_model(model: BedrockModel, region: str, stream: bool = True) -> contextlib.AbstractContextManager:
    """Route ``smolbench.evals.provider`` calls to this model on bedrock-mantle.

    ``providers.aws`` reads these variables when each request is made, so the roster key
    stays the model name everywhere else (harness tags, tokenizer, result paths) while
    the request body carries the Bedrock id. Streaming is on by default: long reasoning
    responses can outlast an idle non-streamed connection.
    """
    if model.bedrock_id is None:
        raise ValueError(f"{model.key}: resolve the Bedrock id first (resolve_ids)")
    return _env(
        INFERENCE_PROVIDER="aws",
        AWS_REGION=region,
        AWS_INFERENCE_BASE_URL=base_url(model, region),
        AWS_INFERENCE_BODY_MODEL=model.bedrock_id,
        AWS_BEDROCK_CONTEXT_LENGTH=str(model.context_length),
        AWS_BEDROCK_STREAM_COMPLETIONS="1" if stream else "0",
    )


# ---------------------------------------------------------------------- reasoning


def reasoned(reasoning: Optional[str]) -> bool:
    """Whether a response carried reasoning.

    ``ChatClient`` fills ``reasoning`` from ``reasoning_content``/``reasoning`` or, with
    no reasoning channel, from the text before ``</think>``, so this one field covers
    all three ways a server can return it.
    """
    return bool(reasoning and reasoning.strip())


def probe(model: BedrockModel, region: str, extra_args: dict, seed: int = 0) -> dict:
    """Send one short request and report whether it was reasoned.

    Parameters
    ----------
    model : BedrockModel
        Model to probe.
    region : str
        Bedrock region.
    extra_args : dict
        Reasoning fields to send.
    seed : int
        Decoding seed.

    Returns
    -------
    dict
        ``ok``, ``reasoned``, ``finish_reason``, token counts, and the error if any.
    """
    from smolbench.evals import provider  # pylint: disable=import-outside-toplevel

    with use_model(model, region):
        try:
            result = provider.complete(
                "What is 17 * 23? Answer with the integer only.",
                model.key,
                seed,
                extra_args={"max_completion_tokens": min(model.max_tokens, 4096)} | extra_args,
                request_timeout=600,
                max_retries=2,
            )
        except Exception as err:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            return {"ok": False, "reasoned": False, "error": f"{type(err).__name__}: {err}"[:600]}
    return {
        "ok": True,
        "reasoned": reasoned(result.reasoning),
        "content": result.content[:80],
        "reasoning_chars": len(result.reasoning or ""),
        "finish_reason": result.finish_reason,
        "completion_tokens": result.completion_tokens,
    }


def pick_reasoning_args(model: BedrockModel, region: str) -> tuple[dict, list[dict]]:
    """The first of the model's reasoning candidates that yields a reasoned answer.

    Returns
    -------
    tuple[dict, list[dict]]
        The chosen fields and every probe made.

    Raises
    ------
    RuntimeError
        If no candidate yields reasoning: the study must not run unreasoned.
    """
    tried = []
    for args in model.reasoning_candidates:
        result = probe(model, region, args) | {"args": args}
        tried.append(result)
        if result["reasoned"]:
            return args, tried
    raise RuntimeError(f"{model.key}: no reasoning candidate worked: {tried}")


# ---------------------------------------------------------------------- bucket


def _join_key(*parts: str) -> str:
    """Join key segments with single slashes, skipping empty ones."""
    return "/".join(p.strip("/") for p in parts if p.strip("/"))


def _s3(region: str) -> Any:
    """An uncached S3 client, as ``S3ResultsStore`` builds one: rotated credentials apply."""
    return _aws.fresh_client("s3", region)


def _list_objects(client: Any, bucket: str, prefix: str) -> list[dict]:
    """Every object under ``prefix``, in key order (paginated)."""
    out: list[dict] = []
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        out += page.get("Contents", [])
    return sorted(out, key=lambda obj: obj["Key"])


def _key_exists(client: Any, bucket: str, key: str) -> bool:
    """Whether the exact key exists; one listing, so a credential error is not read as absence."""
    # Design: an exact key sorts before every longer key that shares it as a prefix, so
    # ``MaxKeys=1`` is enough to see it.
    resp = client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
    return any(obj["Key"] == key for obj in resp.get("Contents", []))


def _put_new(client: Any, bucket: str, key: str, body: bytes) -> None:
    """Write ``body`` to ``key``, refusing to replace an existing object.

    Raises
    ------
    FileExistsError
        If the key exists.
    """
    # NOTE: check-then-put is not atomic; two writers that pick the same key within the
    # same instant can still collide. Stamps carry microseconds, which makes that remote.
    if _key_exists(client, bucket, key):
        raise FileExistsError(f"refusing to overwrite s3://{bucket}/{key}: the bucket is append-only")
    client.put_object(Bucket=bucket, Key=key, Body=body)


def check_bucket(s3_uri: str, region: str = RESULTS_S3_REGION) -> None:
    """Fail early, with a clear message, if the results bucket cannot be reached.

    Makes one listing (``MaxKeys=1``) under the URI's prefix. The notebook calls this
    before any request that bills inference.

    Parameters
    ----------
    s3_uri : str
        ``s3://bucket[/prefix]``.
    region : str
        Region of the bucket.

    Raises
    ------
    RuntimeError
        If the listing fails (no credentials, no access, wrong region, no network).
    ValueError
        If ``s3_uri`` is malformed.
    """
    from botocore.exceptions import (  # pylint: disable=import-outside-toplevel
        BotoCoreError,
        ClientError,
    )

    bucket, base = parse_s3_uri(s3_uri)
    try:
        _s3(region).list_objects_v2(Bucket=bucket, Prefix=f"{base}/" if base else "", MaxKeys=1)
    except (BotoCoreError, ClientError) as err:
        raise RuntimeError(
            f"cannot list {s3_uri} in {region}: {type(err).__name__}: {err}. "
            "Refresh the AWS credentials, or set RESULTS_S3 = None to keep results local."
        ) from err


def push_file(path: Path, s3_uri: str, rel_key: str, region: str = RESULTS_S3_REGION) -> str:
    """Upload one local file to ``<prefix>/<rel_key>``.

    Parameters
    ----------
    path : Path
        File to upload; it is read whole.
    s3_uri : str
        ``s3://bucket[/prefix]`` of the results store.
    rel_key : str
        Key below the prefix, such as ``probes/probes--<stamp>.json``.
    region : str
        Region of the bucket.

    Returns
    -------
    str
        The full key written.

    Raises
    ------
    FileExistsError
        If the key exists; nothing is uploaded.
    ValueError
        If ``rel_key`` is empty.
    """
    if not rel_key.strip("/"):
        raise ValueError("rel_key must not be empty")
    bucket, base = parse_s3_uri(s3_uri)
    key = _join_key(base, rel_key)
    _put_new(_s3(region), bucket, key, Path(path).read_bytes())
    return key


# ---------------------------------------------------------------------- induction


@dataclass
class ReproLayoutStore(ResultsStore):
    """Local results store in the released-results layout.

    Writes ``<root>/induction/<model>/seed=<seed>/<arm>--<stamp>.yaml``, which
    ``smolbench.induction.repro`` (``select_runs``, ``load_cells``, ``report``) reads.
    The built-in ``LocalResultsStore`` uses a different layout.
    """

    root: Path

    def _seed_dir(self, model: str, seed: int) -> Path:
        return self.root / "induction" / model / f"seed={seed}"

    def _runs(self, addr: ReplicateAddress) -> list[Path]:
        if addr.model is None:
            return []
        return sorted(self._seed_dir(addr.model, addr.seed).glob(f"{addr.info}--*.yaml"))

    def exists(self, addr: ReplicateAddress) -> bool:
        return bool(self._runs(addr))

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        if addr.model is None:
            raise ValueError(f"refusing to write {addr!r}: the layout is keyed by model")
        path = self._seed_dir(addr.model, addr.seed) / f"{addr.info}--{format_run_ts(run_ts)}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(marks.dumps(), encoding="utf-8")

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        runs = self._runs(addr)
        if not runs:
            raise FileNotFoundError(f"no run for {addr!r} under {self.root}")
        return Marks.loads(runs[0].read_text(encoding="utf-8"))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        if model is None:
            return []
        base = self.root / "induction" / model
        return sorted(
            int(d.name.removeprefix("seed="))
            for d in base.glob("seed=*")
            if any(d.glob(f"{info}--*.yaml"))
        )

    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        raise NotImplementedError("re-collection is not supported here; delete the files")

    def describe(self) -> str:
        return f"local {self.root}/induction"


def load_run_study() -> ModuleType:
    """Import ``notebooks/induction/run_study.py`` (not a package) for its quiz factory."""
    name = "smolbench_run_study"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "notebooks" / "induction" / "run_study.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def induction_harness(
    models: Sequence[BedrockModel],
    seeds: Sequence[int],
    results_dir: Path = RESULTS_DIR,
    s3_uri: Optional[str] = None,
    s3_region: str = RESULTS_S3_REGION,
):
    """A ``ReplicateHarness`` over the three ICLR arms, writing the released layout.

    Parameters
    ----------
    models : Sequence[BedrockModel]
        Models the harness may run.
    seeds : Sequence[int]
        Replicate seeds (ICLR: 0-29); each is also the decoding seed.
    results_dir : Path
        Local results root; with no ``s3_uri`` the YAMLs go under
        ``<results_dir>/induction/``.
    s3_uri : Optional[str]
        ``s3://bucket[/prefix]`` of the store of record. When set, replicates are written
        (and looked up, for resume) as
        ``<prefix>/induction/<model>/seed=<seed>/<arm>--<stamp>.yaml`` and nothing is
        written locally; ``pull_induction`` mirrors them afterwards. ``None`` writes to
        ``results_dir``.
    s3_region : str
        Region of the bucket.

    Returns
    -------
    ReplicateHarness
        Harness whose store is an ``S3ResultsStore`` (``s3_uri`` given) or a
        ``ReproLayoutStore``.
    """
    from smolbench.evals.replicates import (  # pylint: disable=import-outside-toplevel
        ReplicateHarness,
    )

    harness = ReplicateHarness(
        results_dir=results_dir / "induction",
        archetype_tags={m.key: m.tag for m in models},
        make_quizzes=load_run_study().make_quizzes,
        seeds=tuple(seeds),
        info_types=INDUCTION_ARMS,
    )
    # ``store`` is a cached_property; set it before first use.
    if s3_uri is None:
        harness.__dict__["store"] = ReproLayoutStore(results_dir / "induction")
    else:
        bucket, base = parse_s3_uri(s3_uri)
        harness.__dict__["store"] = S3ResultsStore(
            bucket, base_prefix=base, experiment="induction", region=s3_region
        )
    return harness


#: A replicate file or supersession marker as ``select_runs`` reads it.
_INDUCTION_KEY = re.compile(r"[^/]+/seed=\d+/[^/]+--[^/]+\.(?:yaml|superseded)")


def pull_induction(s3_uri: str, results_dir: Path = RESULTS_DIR, region: str = RESULTS_S3_REGION) -> int:
    """Mirror the bucket's induction replicates into the local released-results layout.

    Copies ``<prefix>/induction/<rest>`` to ``<results_dir>/induction/induction/<rest>``,
    the tree ``smolbench.induction.repro.load_cells(results_dir / "induction")`` reads. A
    local file of the same size is kept, so a repeat pull downloads nothing.

    Both the ``.yaml`` runs and the ``.superseded`` markers (which ``S3ResultsStore`` can
    write beside a run) are copied: ``repro.select_runs`` skips a run that has its marker
    and takes the earliest run left, as ``S3ResultsStore.load_marks`` does. Any other
    object is not copied: ``select_runs`` ignores a file with another suffix but fails on
    a ``seed=`` folder whose name is not an integer.

    Parameters
    ----------
    s3_uri : str
        ``s3://bucket[/prefix]`` of the results store.
    results_dir : Path
        Local mirror root.
    region : str
        Region of the bucket.

    Returns
    -------
    int
        Number of files written.

    Notes
    -----
    Local files that are not in the bucket are left alone. A file of a different size under
    the same name is replaced: the bucket is the store of record.
    """
    bucket, base = parse_s3_uri(s3_uri)
    root = _join_key(base, "induction") + "/"
    client = _s3(region)
    written = 0
    for obj in _list_objects(client, bucket, root):
        rest = obj["Key"][len(root) :]
        if not _INDUCTION_KEY.fullmatch(rest):
            continue
        dest = results_dir / "induction" / "induction" / rest
        if dest.is_file() and dest.stat().st_size == obj["Size"]:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Write beside, then rename, so an interrupted pull never leaves a half file under
        # a run's name (``select_runs`` ignores the ``.part`` suffix).
        part = dest.with_name(dest.name + ".part")
        part.write_bytes(client.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read())
        part.replace(dest)
        written += 1
    return written


def run_induction(
    harness,
    model: BedrockModel,
    region: str,
    reasoning_args: dict,
    max_parallel: int = 8,
    stream: bool = True,
) -> None:
    """Collect every outstanding induction replicate of one model.

    Temperature is not sent: the ICLR induction runs used the server default.
    """
    extra_args = {"max_completion_tokens": model.max_tokens} | reasoning_args
    with use_model(model, region, stream):
        harness.run_replicates(
            model.key,
            extra_args=extra_args,
            max_parallel=max_parallel,
            request_timeout=max(600, model.max_tokens // 10),
            server_config={
                "provider": f"bedrock-mantle:{region}",
                "bedrock_id": model.bedrock_id,
                "extra_args": extra_args,
            },
        )


def released_queries(key: str, seed: int = 0) -> dict[str, list[str]]:
    """The prompts of one released ICLR replicate per arm, fetched anonymously.

    Returns
    -------
    dict[str, list[str]]
        Arm -> its 9 ``marks[i].query`` strings (empty if the field is absent).
    """
    import boto3  # pylint: disable=import-outside-toplevel
    import yaml  # pylint: disable=import-outside-toplevel
    from botocore import UNSIGNED  # pylint: disable=import-outside-toplevel
    from botocore.config import Config  # pylint: disable=import-outside-toplevel

    from smolbench.induction import repro  # pylint: disable=import-outside-toplevel

    proto = repro.load_protocol()
    s3 = boto3.client("s3", region_name=proto["region"], config=Config(signature_version=UNSIGNED))
    prefix = f"{proto['prefix']}/{key}/seed={seed}/"
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=proto["bucket"], Prefix=prefix).get("Contents", [])]
    out: dict[str, list[str]] = {}
    for arm in INDUCTION_ARMS:
        runs = sorted(k for k in keys if k.rsplit("/", 1)[1].startswith(f"{arm}--") and k.endswith(".yaml"))
        if not runs:
            continue
        body = s3.get_object(Bucket=proto["bucket"], Key=runs[0])["Body"].read()
        marks = yaml.load(body, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))["marks"]
        out[arm] = [m.get("query", "") for m in marks]
    return out


def _expected_extens(intens: str, released: str) -> str:
    """The ``extens`` prompt of this branch, rebuilt from an ``intens`` and a released prompt.

    This branch's ``extens`` context is the intensional rules followed by the listing; the
    released ``extens`` context is the listing only. The prompts of one question share the
    template text:

    - ``intens``   = template head + rules + template tail
    - ``released`` = template head + listing + template tail
    - ``extens``   = template head + rules + listing + template tail

    So the rules are the text of ``intens`` from the end of the template head (where the
    released listing starts) to the start of the template tail, and ``extens`` is those
    rules inserted before the released listing. Both ends are located by the template's
    own text, not by comparing the prompts' common prefix and suffix: rules and listing
    both end in a period and a newline, so a common-suffix match can place the cut one
    line off.

    Raises
    ------
    ValueError
        If the released prompt has no listing, ``intens`` has no template tail after it,
        or the rules block is empty.
    """
    cut = released.find(LISTING_START)
    if cut < 0:
        raise ValueError(f"no listing ({LISTING_START!r}) in the released prompt")
    end = intens.find(QUESTION_START, cut)
    if end < 0:
        raise ValueError(f"no {QUESTION_START!r} after the template head in the intens prompt")
    if end == cut:
        raise ValueError("the intens prompt has no rules block")
    return released[:cut] + intens[cut:end] + released[cut:]


def check_induction_prompts(
    mine: Mapping[str, Sequence[Any]], released: Mapping[str, Sequence[str]], tokenizer: Any
) -> None:
    """Check this branch's induction prompts against the released ICLR prompts.

    Per arm:

    - ``intens``: byte-identical to the released prompts.
    - ``extens``: this branch's context is the intensional rules and then the listing,
      the released one the listing only. A prompt must equal the released one with the
      rules block of the question's ``intens`` prompt inserted before the listing (that
      is, with the rules block removed it equals the released one), byte for byte.
    - ``noise_intens``: it is padded to the token count of the matching ``extens`` prompt of
      this branch, so it differs from the released text; its token count under
      ``tokenizer`` must equal that ``extens`` prompt's.

    Parameters
    ----------
    mine : Mapping[str, Sequence[Any]]
        Arm -> questions with a ``.prompt`` (``make_quizzes(seed, key)``), in question order.
        Needs ``intens``, ``extens`` and ``noise_intens``.
    released : Mapping[str, Sequence[str]]
        Arm -> released prompt strings (``released_queries``). Needs ``intens`` and
        ``extens``; ``noise_intens`` is not compared.
    tokenizer : Any
        The model's own tokenizer, with ``count(text) -> int``.

    Raises
    ------
    AssertionError
        On the first mismatch, naming the arm and the question index; also if an arm is
        missing or has a different number of questions.
    """
    for arm in INDUCTION_ARMS:
        if not mine.get(arm):
            raise AssertionError(f"{arm}: no prompts of this branch to check")
        if arm != "noise_intens":
            if not released.get(arm):
                raise AssertionError(f"{arm}: the released file has no prompts")
            if len(released[arm]) != len(mine[arm]):
                raise AssertionError(f"{arm}: {len(mine[arm])} prompts, released {len(released[arm])}")
    for i, (intens, extens, noise) in enumerate(
        zip(mine["intens"], mine["extens"], mine["noise_intens"], strict=True)
    ):
        if intens.prompt != released["intens"][i]:
            raise AssertionError(f"intens[{i}]: differs from the released prompt")
        try:
            expected = _expected_extens(intens.prompt, released["extens"][i])
        except ValueError as err:
            raise AssertionError(f"extens[{i}]: {err}") from err
        if extens.prompt != expected:
            raise AssertionError(
                f"extens[{i}]: not the released prompt with the intens prompt's rules "
                "block inserted before the listing"
            )
        if tokenizer.count(noise.prompt) != tokenizer.count(extens.prompt):
            raise AssertionError(f"noise_intens[{i}]: token count differs from the extens prompt's")


def induction_reasoning_report(results_dir: Path = RESULTS_DIR) -> dict[tuple[str, str], dict]:
    """Per (model, arm): replicates, marks, unreasoned marks and ungradable (null) marks."""
    import yaml  # pylint: disable=import-outside-toplevel

    from smolbench.induction import repro  # pylint: disable=import-outside-toplevel

    out: dict[tuple[str, str], dict] = collections.defaultdict(collections.Counter)
    runs = repro.select_runs(results_dir / "induction", INDUCTION_ARMS)
    for (model, _seed, arm), path in sorted(runs.items()):
        marks = yaml.safe_load(path.read_text(encoding="utf-8"))["marks"]
        c = out[(model, arm)]
        c["replicates"] += 1
        c["marks"] += len(marks)
        c["unreasoned"] += sum(not reasoned(m.get("reasoning")) for m in marks)
        c["null_score"] += sum(m.get("score") is None for m in marks)
        for m in marks:
            c[f"compliance:{m.get('compliance')}"] += 1
    return {k: dict(v) for k, v in out.items()}


# --------------------------------------------------------------------------- horn


def load_sweep() -> ModuleType:
    """Import ``scripts/deduction/horn/sweep.py`` (not a package) for its cell runner."""
    name = "smolbench_horn_sweep"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "scripts" / "deduction" / "horn" / "sweep.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def horn_m(key: str) -> int:
    """The model's ICLR chain length."""
    from smolbench.deduction.horn import repro  # pylint: disable=import-outside-toplevel

    return int(repro.model_entry(key)["m"])


def render_horn_rung(
    m: int, seeds: Sequence[int], rungs_dir: Path = RUNGS_DIR, arms: Sequence[str] = HORN_ARMS
) -> Path:
    """Render rung ``m<m>`` for ``seeds`` and ``arms`` and check it against the ICLR digests.

    ``<rung>/s<seed>/<arm>/prompt.md`` exists for every requested arm afterwards. An arm
    already rendered is kept; one that is missing (say, a review arm added to a rung that
    holds only the paper arms) is rendered into the existing seed folder. The theory is
    rebuilt from the protocol's parameters, so the paper arms stay byte-identical to the
    ICLR rung. ``repro.render_rung`` renders the four paper arms only, so this calls the
    renderer it uses (``cli.write_seed``) with the requested arms.

    Parameters
    ----------
    m : int
        Chain length.
    seeds : Sequence[int]
        Theory seeds.
    rungs_dir : Path
        Folder that holds ``m<m>``.
    arms : Sequence[str]
        Arms to render; any of ``render.ALL_ARMS``.

    Returns
    -------
    Path
        The rung folder.

    Raises
    ------
    ValueError
        If an arm is not one of ``render.ALL_ARMS``.
    RuntimeError
        If a seed differs from the ICLR rung (checked on the paper arms; an ``m`` the
        protocol does not pin fails here, as in ``repro.verify_rung``).
    """
    from smolbench.deduction.horn import render as horn_render  # pylint: disable=import-outside-toplevel
    from smolbench.deduction.horn import repro  # pylint: disable=import-outside-toplevel
    from smolbench.deduction.horn.cli import (  # pylint: disable=import-outside-toplevel
        build_theory,
        write_seed,
    )

    for arm in arms:
        horn_render.check_arm(arm)
    rung = rungs_dir / f"m{m}"
    proto = repro.load_protocol()
    tok = None
    for seed in seeds:
        sd = rung / f"s{seed:04d}"
        todo = [
            arm
            for arm in arms
            if not all((sd / arm / name).exists() for name in repro.ARM_FILES)
        ]
        if not todo:
            continue
        tok = tok or horn_render.Tokenizer()
        write_seed(rung, build_theory(seed, m, proto["height"], proto["alt_per_lemma"]), todo, tok)
    problems = repro.verify_rung(rung, m, list(seeds))
    if problems:
        raise RuntimeError(f"rung m{m} differs from the ICLR rung: {problems[:5]}")
    return rung


def horn_rows_path(key: str, results_dir: Path = RESULTS_DIR) -> Path:
    """Rows file for one model."""
    return results_dir / "horn" / f"{key}.jsonl"


def _row_lines(text: str) -> list[str]:
    """Non-blank lines of a rows file, split on ``\\n`` only.

    ``str.splitlines`` would also split on U+2028 and U+0085, which ``json.dumps``
    (``ensure_ascii=False``) leaves unescaped inside a row's text.
    """
    return [line for line in text.split("\n") if line.strip()]


def _dump_row(row: dict) -> str:
    """One row as a single JSON line that ``str.splitlines`` readers cannot split.

    ``json.dumps`` (``ensure_ascii=False``) leaves U+0085, U+2028 and U+2029 raw inside
    strings. ``sweep.done_keys`` and ``stats.load_rows`` split on them, so a row holding
    one would never count as done and would be billed again on every run.
    """
    line = json.dumps(row, ensure_ascii=False)
    for ch in ("\x85", "\u2028", "\u2029"):
        line = line.replace(ch, f"\\u{ord(ch):04x}")
    return line


def _horn_parts(client: Any, bucket: str, prefix: str) -> list[str]:
    """Keys of the row parts under ``prefix``, in key (that is, stamp) order."""
    return [
        obj["Key"]
        for obj in _list_objects(client, bucket, prefix)
        if "/" not in obj["Key"][len(prefix) :]
        and obj["Key"][len(prefix) :].startswith("rows--")
        and obj["Key"].endswith(".jsonl")
    ]


def _part_lines(client: Any, bucket: str, key: str) -> list[str]:
    """The rows of one part."""
    return _row_lines(client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8"))


def _local_text(out: Path) -> str:
    """A local rows file as text, ``""`` when it does not exist (bytes, so no newline translation)."""
    return out.read_bytes().decode("utf-8") if out.exists() else ""


def pull_horn_rows(
    key: str,
    s3_uri: str,
    results_dir: Path = RESULTS_DIR,
    region: str = RESULTS_S3_REGION,
    out: Optional[Path] = None,
) -> int:
    """Append the bucket's rows of one model to the local rows file.

    Reads every part under ``<prefix>/deduction/horn/<key>/`` in key order and appends
    each line that the local file does not already contain (exact match, so a line that
    two parts share is appended once).

    Parameters
    ----------
    key : str
        Roster key of the model.
    s3_uri : str
        ``s3://bucket[/prefix]`` of the results store.
    results_dir : Path
        Local mirror root; sets the default ``out``.
    region : str
        Region of the bucket.
    out : Optional[Path]
        Rows file; default ``horn_rows_path(key, results_dir)``.

    Returns
    -------
    int
        Number of lines appended.

    Notes
    -----
    Every part is downloaded on every call, so the cost grows with the bucket. The file is
    only ever appended to. If its last line is unterminated (a crash mid-write), a newline
    is written first so the first new row is not glued to the fragment.
    """
    bucket, base = parse_s3_uri(s3_uri)
    out = out or horn_rows_path(key, results_dir)
    client = _s3(region)
    text = _local_text(out)
    have = set(_row_lines(text))
    new: list[str] = []
    for part in _horn_parts(client, bucket, _join_key(base, "deduction", "horn", key) + "/"):
        for line in _part_lines(client, bucket, part):
            if line not in have:
                have.add(line)
                new.append(line)
    if new:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("ab") as fh:
            fh.write((("\n" if text and not text.endswith("\n") else "") + "".join(f"{x}\n" for x in new)).encode())
    return len(new)


def push_horn_rows(
    key: str,
    s3_uri: str,
    results_dir: Path = RESULTS_DIR,
    region: str = RESULTS_S3_REGION,
    out: Optional[Path] = None,
) -> Optional[str]:
    """Upload the local rows of one model that the bucket does not have, as one new part.

    The part is ``<prefix>/deduction/horn/<key>/rows--<stamp>.jsonl`` with the stamp from
    ``format_run_ts(utcnow())``. If that key exists (another machine pushed in the same
    instant), the stamp moves on one second at a time to the first free one; nothing in the
    bucket is overwritten.

    Parameters
    ----------
    key : str
        Roster key of the model.
    s3_uri : str
        ``s3://bucket[/prefix]`` of the results store.
    results_dir : Path
        Local mirror root; sets the default ``out``.
    region : str
        Region of the bucket.
    out : Optional[Path]
        Rows file; default ``horn_rows_path(key, results_dir)``.

    Returns
    -------
    Optional[str]
        The key written, or ``None`` (and no upload) when every local line is already in
        some part, or the file is missing or empty.

    Notes
    -----
    Every part is downloaded to find which lines it holds. An unterminated last line (a
    crash mid-write) is left out: the bucket is append-only, so a fragment would stay.
    """
    bucket, base = parse_s3_uri(s3_uri)
    out = out or horn_rows_path(key, results_dir)
    client = _s3(region)
    prefix = _join_key(base, "deduction", "horn", key) + "/"
    remote = {line for part in _horn_parts(client, bucket, prefix) for line in _part_lines(client, bucket, part)}
    # dict.fromkeys: each missing line once, in file order.
    text = _local_text(out)
    whole = text if text.endswith("\n") else text[: text.rfind("\n") + 1]
    new = [line for line in dict.fromkeys(_row_lines(whole)) if line not in remote]
    if not new:
        return None
    when = utcnow()
    while _key_exists(client, bucket, f"{prefix}rows--{format_run_ts(when)}.jsonl"):
        when += timedelta(seconds=1)
    part = f"{prefix}rows--{format_run_ts(when)}.jsonl"
    _put_new(client, bucket, part, "".join(f"{line}\n" for line in new).encode("utf-8"))
    return part


def run_horn(  # pylint: disable=too-many-arguments,too-many-locals
    model: BedrockModel,
    region: str,
    reasoning_args: dict,
    rung: Path,
    seeds: Sequence[int],
    reps: int,
    concurrency: int = 8,
    out: Optional[Path] = None,
    stream: bool = True,
    arms: Sequence[str] = HORN_ARMS,
    s3_uri: Optional[str] = None,
    s3_region: str = RESULTS_S3_REGION,
    push_every: int = 200,
) -> list[dict]:
    """Run and score every outstanding Horn cell of one model with ``sweep.run_cell``.

    The decoding seed is the replicate index and the temperature is 0.7, as in the ICLR
    protocol. Rows already in ``out`` (other than ``exception`` rows) are skipped.

    With ``s3_uri``, the bucket is the store of record. Once the rows lock is held, the
    bucket's rows are pulled into ``out`` so that resume sees rows collected on any
    machine. New rows are pushed as one part after every ``push_every`` of them, and
    again in a ``finally``, so an interrupted run keeps what it collected.

    Parameters
    ----------
    model : BedrockModel
        Model to run; ``bedrock_id`` must be resolved.
    region : str
        Bedrock region.
    reasoning_args : dict
        Reasoning fields to send.
    rung : Path
        Rendered rung (``render_horn_rung``) holding a prompt for every arm in ``arms``.
    seeds : Sequence[int]
        Theory seeds.
    reps : int
        Replicates per (arm, seed).
    concurrency : int
        Parallel requests.
    out : Optional[Path]
        Local rows file; default ``horn_rows_path(model.key)``.
    stream : bool
        Stream responses.
    arms : Sequence[str]
        Arms to run; cells of an arm with no rendered prompt are not run.
    s3_uri : Optional[str]
        ``s3://bucket[/prefix]`` of the store of record; ``None`` keeps rows local only.
    s3_region : str
        Region of the bucket.
    push_every : int
        New rows per push; at least 1.

    Returns
    -------
    list[dict]
        The rows written by this call.

    Raises
    ------
    ValueError
        If the Bedrock id is unresolved or ``push_every`` is below 1.
    RuntimeError
        If another sweep holds the rows lock.
    """
    from botocore.exceptions import (  # pylint: disable=import-outside-toplevel
        BotoCoreError,
        ClientError,
    )

    from smolbench.evals.openai_compat import (  # pylint: disable=import-outside-toplevel
        ChatClient,
    )

    if model.bedrock_id is None:
        raise ValueError(f"{model.key}: resolve the Bedrock id first (resolve_ids)")
    if push_every < 1:
        raise ValueError(f"push_every must be >= 1, got {push_every}")
    sweep = load_sweep()
    out = out or horn_rows_path(model.key)
    out.parent.mkdir(parents=True, exist_ok=True)
    st = sweep.Settings(
        model=model.bedrock_id,
        spec_key=model.key,
        extra_args={"max_tokens": model.max_tokens, "temperature": HORN_TEMPERATURE}
        | reasoning_args,
        context_length=model.context_length,
        timeout=max(900, model.max_tokens // 10),
        max_retries=8,
        system_prompt=None,
    )
    url = f"{base_url(model, region)}/chat/completions"
    client = ChatClient(
        name="horn-bedrock",
        env_prefix="HORN",
        connection=lambda _: (url, os.environ["AWS_BEARER_TOKEN_BEDROCK"]),
        context_length=lambda _: model.context_length,
        retry_backoff_s=30,
        read_timeout_s=st.timeout,
    )
    fh = sweep.lock_rows(out)
    if fh is None:
        raise RuntimeError(f"{out} is locked by another sweep")
    rows: list[dict] = []
    with fh:
        # Pull under the lock and before ``done_keys``: another process cannot append
        # meanwhile, and the cells another machine finished are not run again.
        if s3_uri is not None:
            pull_horn_rows(model.key, s3_uri, region=s3_region, out=out)
        done = sweep.done_keys(out)
        cells = sweep.cells_in(rung, list(arms), list(seeds), reps)
        todo = [c for c in cells if (st.model,) + c.key not in done]
        with _env(HORN_STREAM_COMPLETIONS="1" if stream else "0"), ThreadPoolExecutor(concurrency) as pool:
            futs = [pool.submit(sweep.run_cell, client, c, st) for c in todo]
            kept: set = set()
            unpushed = 0

            def keep(fut) -> None:
                row = fut.result() | {"provider": f"bedrock-mantle:{region}"}
                fh.write(_dump_row(row) + "\n")
                fh.flush()
                rows.append(row)
                kept.add(fut)

            try:
                for fut in as_completed(futs):
                    keep(fut)
                    unpushed += 1
                    if s3_uri is not None and unpushed >= push_every:
                        # The rows are safe on disk; the push after the loop retries.
                        try:
                            push_horn_rows(model.key, s3_uri, region=s3_region, out=out)
                            unpushed = 0
                        except (BotoCoreError, ClientError) as err:
                            print(f"{model.key}: periodic push failed, continuing: {err}")
            finally:
                # Cells that have not started are dropped, so an interrupt does not bill
                # the rest of the queue. Cells already running are billed either way, so
                # their rows are kept before the final push.
                for fut in futs:
                    fut.cancel()
                for fut in futs:
                    if fut in kept or fut.cancelled():
                        continue
                    try:
                        keep(fut)
                    except Exception as err:  # pylint: disable=broad-exception-caught
                        print(f"{model.key}: a running cell left no row: {err!r}")
                if s3_uri is not None:
                    push_horn_rows(model.key, s3_uri, region=s3_region, out=out)
    return rows


def horn_breakdown(paths: Sequence[Path]) -> dict[tuple[str, str], dict]:
    """Per (model, arm): rows, verdicts, finish reasons and unreasoned rows (exceptions apart)."""
    out: dict[tuple[str, str], dict] = collections.defaultdict(collections.Counter)
    for path in paths:
        for line in _row_lines(Path(path).read_text(encoding="utf-8")):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            c = out[(r.get("spec_key") or r["model"], r["arm"])]
            c["rows"] += 1
            c[f"verdict:{r['verdict']}"] += 1
            if r["verdict"] != "exception":
                c[f"finish:{r.get('finish_reason')}"] += 1
                c["unreasoned"] += not reasoned(r.get("reasoning"))
    return {k: dict(v) for k, v in out.items()}


def horn_reference(
    keys: Sequence[str], path: Path = REVIEW_CELLS
) -> dict[tuple[str, str], dict]:
    """Per (model, arm): the published Bedrock Horn cells, as run and under the caps here.

    The cells in `path` ran through the Converse API with a 131,072-token output cap.
    This notebook sends each model's ``max_tokens``, which is lower, so the published
    rate is not what the same generations would score here.

    Parameters
    ----------
    keys : Sequence[str]
        Roster keys. A model with no cell in `path` (Gemma 4 ran on vLLM) is left out.
    path : Path, optional
        The per-cell CSV (columns ``model``, ``m``, ``arm``, ``verdict``,
        ``completion_tokens``).

    Returns
    -------
    dict[tuple[str, str], dict]
        ``cells``; ``m``; ``pass``, the published pass rate in percent; ``pass_capped``,
        the rate when a success counts only if its completion fits ``max_tokens``; and
        ``over_cap``, the percentage of cells whose completion is longer than that.
    """
    wanted = set(keys)
    cells: dict[tuple[str, str], list[tuple[bool, int, int]]] = collections.defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["model"] in wanted:
                cells[(r["model"], r["arm"])].append(
                    (r["verdict"] == "success", int(r["completion_tokens"]), int(r["m"]))
                )
    out = {}
    for (key, arm), rows in cells.items():
        cap, n = TRIO[key].max_tokens, len(rows)
        out[(key, arm)] = {
            "cells": n,
            "m": rows[0][2],
            "pass": 100 * sum(ok for ok, _, _ in rows) / n,
            "pass_capped": 100 * sum(ok and toks <= cap for ok, toks, _ in rows) / n,
            "over_cap": 100 * sum(toks > cap for _, toks, _ in rows) / n,
        }
    return out
