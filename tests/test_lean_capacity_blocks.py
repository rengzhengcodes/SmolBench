"""Offline unit tests for lean_train_ec2.py's capacity-block support.

Everything here runs with no AWS credentials and no network: the EC2 client
is a recording fake monkeypatched over ``ec2._ec2_client`` (the single seam
every AWS call in the script goes through -- same convention as
tests/test_ec2_provision.py), and the reservation ledger is redirected to a
tmp path. The launch-kwargs transform and the ledger round-trip are pure;
the purchase gate and the capacity-path provision are exercised end-to-end
against the fakes. The live surface (a real DescribeCapacityBlockOfferings
sweep, an actual purchase) is exercised outside this offline suite.

The one behavior these tests treat as load-bearing enough to pin exactly:
``cb-purchase`` without ``--yes`` must NEVER issue a non-DryRun
PurchaseCapacityBlock call -- a capacity block is an upfront, non-refundable
purchase.
"""

import json
import sys
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import lean_train_ec2 as lt  # noqa: E402  (needs the sys.path insert above)
from smolbench.evals import ec2  # noqa: E402


def _client_error(code: str, op: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, op)


@pytest.fixture()
def ledger(tmp_path, monkeypatch):
    """Redirect the reservation ledger to a tmp file; returns its path."""
    path = tmp_path / "cb.json"
    monkeypatch.setattr(lt, "CB_STATE_PATH", path)
    return path


# ---------------------------------------------------------------------------
# _cb_run_instances_kwargs: the exact RunInstances retarget
# ---------------------------------------------------------------------------


def _spot_kwargs():
    return ec2._run_instances_kwargs(
        ami="ami-0123456789abcdef0",
        instance_type="p5.48xlarge",
        subnet_id="subnet-abc123",
        group_id="sg-def456",
        root_device="/dev/sda1",
        volume_gb=400,
        user_data="#!/bin/bash\necho hi\n",
        key_name="smolbench-lean-train",
        iam_profile=None,
    )


def test_cb_kwargs_swaps_market_and_targets_reservation():
    base = _spot_kwargs()
    out = lt._cb_run_instances_kwargs(base, "cr-0123456789abcdef0")
    # The market swap must be COMPLETE: SpotOptions are invalid alongside
    # MarketType=capacity-block, so no spot key may survive.
    assert out["InstanceMarketOptions"] == {"MarketType": "capacity-block"}
    assert out["CapacityReservationSpecification"] == {
        "CapacityReservationTarget": {"CapacityReservationId": "cr-0123456789abcdef0"}
    }


def test_cb_kwargs_leaves_everything_else_unchanged():
    base = _spot_kwargs()
    out = lt._cb_run_instances_kwargs(base, "cr-1")
    changed = {"InstanceMarketOptions", "CapacityReservationSpecification"}
    assert {k: v for k, v in out.items() if k not in changed} == {
        k: v for k, v in base.items() if k not in changed
    }


def test_cb_kwargs_does_not_mutate_input():
    base = _spot_kwargs()
    lt._cb_run_instances_kwargs(base, "cr-1")
    assert base["InstanceMarketOptions"]["MarketType"] == "spot"
    assert "CapacityReservationSpecification" not in base


# ---------------------------------------------------------------------------
# _parse_when: the tiny date-spec parser used by cb-search
# ---------------------------------------------------------------------------


def test_parse_when_relative_hours_and_days():
    before = datetime.now(timezone.utc)
    got_h = lt._parse_when("+6h")
    got_d = lt._parse_when("+3d")
    after = datetime.now(timezone.utc)
    assert before + timedelta(hours=6) <= got_h <= after + timedelta(hours=6)
    assert before + timedelta(days=3) <= got_d <= after + timedelta(days=3)


def test_parse_when_iso_naive_is_utc():
    got = lt._parse_when("2026-07-12T06:00:00")
    assert got == datetime(2026, 7, 12, 6, 0, 0, tzinfo=timezone.utc)


def test_parse_when_none_and_garbage():
    assert lt._parse_when(None) is None
    assert lt._parse_when("") is None
    with pytest.raises(ValueError):
        lt._parse_when("next tuesday")


# ---------------------------------------------------------------------------
# Ledger round-trip
# ---------------------------------------------------------------------------


def test_ledger_upsert_replaces_by_reservation_id(ledger):
    lt._cb_upsert({"reservation_id": "cr-1", "state": "scheduled"})
    lt._cb_upsert({"reservation_id": "cr-2", "state": "scheduled"})
    lt._cb_upsert({"reservation_id": "cr-1", "state": "active"})
    records = lt._cb_load()
    assert {r["reservation_id"]: r["state"] for r in records} == {
        "cr-1": "active", "cr-2": "scheduled"}
    # And the on-disk form is plain JSON (the file is the ledger of record).
    assert json.loads(ledger.read_text()) == records


def test_cb_record_normalizes_datetimes_to_iso_z():
    record = lt._cb_record("us-east-2", {
        "CapacityReservationId": "cr-1",
        "AvailabilityZone": "us-east-2c",
        "InstanceType": "p5.48xlarge",
        "TotalInstanceCount": 1,
        "State": "scheduled",
        "StartDate": datetime(2026, 7, 12, 6, 0, tzinfo=timezone.utc),
        "EndDate": datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc),
    })
    assert record["start_date"] == "2026-07-12T06:00:00Z"
    assert record["end_date"] == "2026-07-15T06:00:00Z"
    assert record["region"] == "us-east-2"


# ---------------------------------------------------------------------------
# cb-purchase: the DryRun spend gate
# ---------------------------------------------------------------------------


class _PurchaseClient:
    """Records every PurchaseCapacityBlock call; DryRun raises like AWS does."""

    def __init__(self):
        self.calls = []
        self.reservation = {
            "CapacityReservationId": "cr-bought",
            "AvailabilityZone": "us-east-2c",
            "InstanceType": "p5.48xlarge",
            "TotalInstanceCount": 1,
            "State": "payment-pending",
            "StartDate": datetime(2026, 7, 12, 6, 0, tzinfo=timezone.utc),
            "EndDate": datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc),
        }

    def purchase_capacity_block(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("DryRun"):
            raise _client_error("DryRunOperation", "PurchaseCapacityBlock")
        return {"CapacityReservation": self.reservation}


def _purchase_args(**overrides):
    args = dict(region="us-east-2", offering_id="cbo-1", yes=False)
    args.update(overrides)
    return Namespace(**args)


class _NeverPurchase:
    """A default-retry client that must never see the real purchase."""

    def purchase_capacity_block(self, **kwargs):
        if not kwargs.get("DryRun"):
            raise AssertionError("real purchase issued on the default-retry client")
        raise _client_error("DryRunOperation", "PurchaseCapacityBlock")


def test_purchase_without_yes_only_dry_runs(ledger, monkeypatch, capsys):
    client = _PurchaseClient()
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: client)
    rc = lt.cb_purchase(_purchase_args())
    assert rc == 0
    assert len(client.calls) == 1 and client.calls[0]["DryRun"] is True
    assert not ledger.exists()  # nothing bought -> nothing recorded
    assert "--yes" in capsys.readouterr().out


def test_purchase_with_yes_buys_on_no_retry_client_and_records(ledger, monkeypatch):
    """The real purchase must go through the no-retry client ONLY: botocore's
    default policy replays a lost-response purchase into duplicate
    non-refundable blocks (PurchaseCapacityBlock has no idempotency token)."""
    client = _PurchaseClient()
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _NeverPurchase())
    monkeypatch.setattr(lt, "_no_retry_ec2_client", lambda region: client)
    rc = lt.cb_purchase(_purchase_args(yes=True))
    assert rc == 0
    assert len(client.calls) == 1 and "DryRun" not in client.calls[0]
    assert client.calls[0]["CapacityBlockOfferingId"] == "cbo-1"
    assert client.calls[0]["InstancePlatform"] == "Linux/UNIX"
    (record,) = lt._cb_load()
    assert record["reservation_id"] == "cr-bought"
    assert record["region"] == "us-east-2"


def test_no_retry_client_config_disables_retries():
    """Pin the actual botocore Config the purchase client is built with --
    the whole point of the seam is max_attempts=1."""
    captured = {}

    class _Session:
        def client(self, service, region_name=None, config=None):
            captured.update(service=service, region=region_name, config=config)
            return "client-sentinel"

    import boto3

    orig = boto3.session.Session
    boto3.session.Session = _Session
    try:
        assert lt._no_retry_ec2_client("us-east-2") == "client-sentinel"
    finally:
        boto3.session.Session = orig
    assert captured["service"] == "ec2" and captured["region"] == "us-east-2"
    assert captured["config"].retries == {"max_attempts": 1}


def test_purchase_yes_fails_fast_on_corrupt_ledger_before_spending(ledger, monkeypatch):
    ledger.write_text("{not json")
    client = _PurchaseClient()
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _NeverPurchase())
    monkeypatch.setattr(lt, "_no_retry_ec2_client", lambda region: client)
    with pytest.raises(json.JSONDecodeError):
        lt.cb_purchase(_purchase_args(yes=True))
    assert client.calls == []  # the money never moved


def test_purchase_ledger_write_failure_still_prints_id(ledger, monkeypatch, capsys):
    client = _PurchaseClient()
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _NeverPurchase())
    monkeypatch.setattr(lt, "_no_retry_ec2_client", lambda region: client)
    monkeypatch.setattr(lt, "_cb_upsert", lambda record: (_ for _ in ()).throw(OSError("disk full")))
    rc = lt.cb_purchase(_purchase_args(yes=True))
    assert rc == 1
    out, err = capsys.readouterr()
    assert "PURCHASED: cr-bought" in out  # the id survives the local failure
    assert "Do NOT re-purchase" in err and "cr-bought" in err


def test_purchase_api_error_prints_reconcile_guidance(ledger, monkeypatch, capsys):
    class _Flaky:
        def purchase_capacity_block(self, **kwargs):
            raise _client_error("RequestTimeout", "PurchaseCapacityBlock")

    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _NeverPurchase())
    monkeypatch.setattr(lt, "_no_retry_ec2_client", lambda region: _Flaky())
    with pytest.raises(ClientError):
        lt.cb_purchase(_purchase_args(yes=True))
    err = capsys.readouterr().err
    assert "Do NOT re-run --yes" in err and "describe-capacity-reservations" in err


def test_purchase_dry_run_real_error_propagates(ledger, monkeypatch):
    class _Denied:
        def purchase_capacity_block(self, **kwargs):
            raise _client_error("UnauthorizedOperation", "PurchaseCapacityBlock")

    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _Denied())
    with pytest.raises(ClientError):
        lt.cb_purchase(_purchase_args())
    assert not ledger.exists()


def test_purchase_refuses_when_dry_run_succeeds(ledger, monkeypatch):
    """DryRun=True returning success (instead of DryRunOperation) is an API
    anomaly; the gate must fail closed, not fall through to a real buy."""

    class _Weird:
        def __init__(self):
            self.calls = []

        def purchase_capacity_block(self, **kwargs):
            self.calls.append(kwargs)
            return {"CapacityReservation": {}}

    client = _Weird()
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: client)
    rc = lt.cb_purchase(_purchase_args())
    assert rc == 1
    assert len(client.calls) == 1  # never retried without DryRun
    assert not ledger.exists()


# ---------------------------------------------------------------------------
# _resolve_capacity_reservation: picking what to launch into
# ---------------------------------------------------------------------------


class _DescribeClient:
    """Real EC2 by-id describe semantics: ANY unknown id fails the WHOLE call
    (all-or-nothing), returning nothing for the valid ids -- which is exactly
    why cb_status must describe per-id, never in a batch."""

    def __init__(self, by_id):
        self._by_id = by_id

    def describe_capacity_reservations(self, CapacityReservationIds):
        if any(i not in self._by_id for i in CapacityReservationIds):
            raise _client_error(
                "InvalidCapacityReservationId.NotFound", "DescribeCapacityReservations")
        return {"CapacityReservations": [self._by_id[i] for i in CapacityReservationIds]}


def _reservation(rid, state, available=1, az="us-east-2c", end=None):
    return {
        "CapacityReservationId": rid,
        "AvailabilityZone": az,
        "InstanceType": "p5.48xlarge",
        "TotalInstanceCount": 1,
        "AvailableInstanceCount": available,
        "State": state,
        "StartDate": datetime(2026, 7, 12, 6, 0, tzinfo=timezone.utc),
        "EndDate": end or datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc),
    }


def _region_clients(monkeypatch, clients):
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: clients[region])


def test_resolve_auto_skips_scheduled_takes_active(ledger, monkeypatch):
    lt._cb_save([
        {"reservation_id": "cr-sched", "region": "us-east-1"},
        {"reservation_id": "cr-live", "region": "us-east-2"},
    ])
    _region_clients(monkeypatch, {
        "us-east-1": _DescribeClient({"cr-sched": _reservation("cr-sched", "scheduled")}),
        "us-east-2": _DescribeClient({"cr-live": _reservation("cr-live", "active")}),
    })
    region, cr = lt._resolve_capacity_reservation(
        Namespace(capacity_reservation="auto", regions=None))
    assert (region, cr["CapacityReservationId"]) == ("us-east-2", "cr-live")


def test_resolve_active_but_full_block_is_not_launchable(ledger, monkeypatch):
    lt._cb_save([{"reservation_id": "cr-full", "region": "us-east-2"}])
    _region_clients(monkeypatch, {
        "us-east-2": _DescribeClient({"cr-full": _reservation("cr-full", "active", available=0)}),
    })
    with pytest.raises(SystemExit, match="available=0"):
        lt._resolve_capacity_reservation(Namespace(capacity_reservation="auto", regions=None))


def test_resolve_scheduled_only_exits_with_start_time(ledger, monkeypatch):
    lt._cb_save([{"reservation_id": "cr-sched", "region": "us-east-1"}])
    _region_clients(monkeypatch, {
        "us-east-1": _DescribeClient({"cr-sched": _reservation("cr-sched", "scheduled")}),
    })
    with pytest.raises(SystemExit, match="starts 2026-07-12T06:00:00Z"):
        lt._resolve_capacity_reservation(Namespace(capacity_reservation="auto", regions=None))


def test_resolve_empty_ledger_exits(ledger):
    with pytest.raises(SystemExit, match="cb-search"):
        lt._resolve_capacity_reservation(Namespace(capacity_reservation="auto", regions=None))


def test_resolve_explicit_id_probes_regions_when_not_in_ledger(ledger, monkeypatch):
    _region_clients(monkeypatch, {
        "us-east-1": _DescribeClient({}),
        "us-east-2": _DescribeClient({"cr-x": _reservation("cr-x", "active")}),
    })
    region, cr = lt._resolve_capacity_reservation(
        Namespace(capacity_reservation="cr-x", regions="us-east-1,us-east-2"))
    assert (region, cr["CapacityReservationId"]) == ("us-east-2", "cr-x")


def test_resolve_auto_prefers_block_with_most_remaining_window(ledger, monkeypatch):
    """Two simultaneously active blocks: auto must bind the (multi-day) run to
    the one ending LAST, not whichever the ledger happens to list first."""
    lt._cb_save([
        {"reservation_id": "cr-ending", "region": "us-east-1"},
        {"reservation_id": "cr-fresh", "region": "us-east-2"},
    ])
    _region_clients(monkeypatch, {
        "us-east-1": _DescribeClient({"cr-ending": _reservation(
            "cr-ending", "active", end=datetime(2026, 7, 11, 6, 0, tzinfo=timezone.utc))}),
        "us-east-2": _DescribeClient({"cr-fresh": _reservation(
            "cr-fresh", "active", end=datetime(2026, 7, 19, 6, 0, tzinfo=timezone.utc))}),
    })
    region, cr = lt._resolve_capacity_reservation(
        Namespace(capacity_reservation="auto", regions=None))
    assert (region, cr["CapacityReservationId"]) == ("us-east-2", "cr-fresh")


# ---------------------------------------------------------------------------
# cb-status: per-id describes survive aged-out ledger entries
# ---------------------------------------------------------------------------


def test_cb_status_shows_live_block_despite_aged_out_id(ledger, monkeypatch, capsys):
    """One stale id must not blank the region: EC2 batch describes are
    all-or-nothing, so cb_status describes per id."""
    lt._cb_save([
        {"reservation_id": "cr-old", "region": "us-east-2"},
        {"reservation_id": "cr-live", "region": "us-east-2"},
    ])
    _region_clients(monkeypatch, {
        "us-east-2": _DescribeClient({"cr-live": _reservation("cr-live", "active")}),
    })
    rc = lt.cb_status(Namespace(reservation_id=None, region=None))
    assert rc == 0
    out, err = capsys.readouterr()
    assert "cr-live" in out and "state=active" in out
    assert "cr-old" in err and "aged out" in err


# ---------------------------------------------------------------------------
# _provision_capacity_block: offline end-to-end (fakes for every AWS touch)
# ---------------------------------------------------------------------------


def _provision_args(**overrides):
    args = dict(capacity_reservation="auto", regions=None, root_volume_gb=400,
                max_lifetime=None, ssh_timeout=15)
    args.update(overrides)
    return Namespace(**args)


@pytest.fixture()
def launch_env(ledger, monkeypatch):
    """Monkeypatches every AWS/SSH touch of _provision_capacity_block and
    returns the dict the fakes record into."""
    seen = {}
    end = datetime.now(timezone.utc) + timedelta(hours=72)
    cr = _reservation("cr-live", "active")
    cr["EndDate"] = end
    seen["end"] = end
    monkeypatch.setattr(lt, "_resolve_capacity_reservation", lambda args: ("us-east-2", cr))
    monkeypatch.setattr(ec2, "_my_public_ip", lambda: "1.2.3.4")
    monkeypatch.setattr(ec2, "_default_vpc_subnets",
                        lambda region: ("vpc-1", [("subnet-a", "us-east-2a"),
                                                  ("subnet-c", "us-east-2c")]))
    monkeypatch.setattr(ec2, "_resolve_ami", lambda region: ("ami-1", "/dev/sda1"))
    monkeypatch.setattr(ec2, "_ensure_security_group", lambda region, vpc, ip: "sg-1")
    monkeypatch.setattr(lt, "_authorize_ssh", lambda *a, **k: None)
    monkeypatch.setattr(lt, "_ensure_key_pair", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "_try_launch",
                        lambda region, kwargs: seen.update(launch=(region, kwargs)) or "i-cb1")
    monkeypatch.setattr(ec2, "_wait_public_ip", lambda region, iid: "5.6.7.8")
    monkeypatch.setattr(ec2, "_save_state", lambda state: seen.update(state=state))
    monkeypatch.setattr(lt, "_wait_ssh", lambda state, timeout_s: None)
    return seen


def test_provision_cb_launch_kwargs_and_state(launch_env):
    lt._provision_capacity_block(_provision_args())
    region, kwargs = launch_env["launch"]
    assert region == "us-east-2"
    assert kwargs["InstanceMarketOptions"] == {"MarketType": "capacity-block"}
    assert kwargs["CapacityReservationSpecification"] == {
        "CapacityReservationTarget": {"CapacityReservationId": "cr-live"}}
    # Subnet must be the one in the reservation's AZ, not the first subnet.
    assert kwargs["NetworkInterfaces"][0]["SubnetId"] == "subnet-c"
    assert kwargs["InstanceType"] == "p5.48xlarge"
    state = launch_env["state"]
    assert state["capacity_reservation_id"] == "cr-live"
    assert state["market"] == "capacity-block"
    assert state["instance_id"] == "i-cb1"


def test_provision_cb_backstop_sized_to_block_end(launch_env):
    lt._provision_capacity_block(_provision_args())
    _, kwargs = launch_env["launch"]
    minutes = int(kwargs["UserData"].split("shutdown -h +")[1].split()[0])
    expected = int((launch_env["end"] - datetime.now(timezone.utc)).total_seconds() // 60) + 60
    # The block ends in ~72h -> backstop ~4380 min, never the 2880 spot default.
    assert abs(minutes - expected) <= 2
    assert minutes > lt.DEFAULT_MAX_LIFETIME_MIN


def test_provision_cb_explicit_max_lifetime_wins(launch_env):
    lt._provision_capacity_block(_provision_args(max_lifetime=777))
    _, kwargs = launch_env["launch"]
    assert "shutdown -h +777 " in kwargs["UserData"]


def test_provision_cb_no_subnet_in_reservation_az(launch_env, monkeypatch):
    monkeypatch.setattr(ec2, "_default_vpc_subnets",
                        lambda region: ("vpc-1", [("subnet-a", "us-east-2a")]))
    with pytest.raises(SystemExit, match="us-east-2c"):
        lt._provision_capacity_block(_provision_args())


def test_provision_cb_dead_instance_gets_block_guidance(launch_env, monkeypatch):
    """_wait_public_ip's abort message blames a spot reclaim and suggests the
    spot provisioner -- both wrong inside a reservation; the CB path must
    override with retry-the-block guidance."""
    def _dead(region, iid):
        raise RuntimeError("instance i-cb1 went terminated right after launch "
                           "(spot reclaimed?); re-run provision_spot_instance().")

    monkeypatch.setattr(ec2, "_wait_public_ip", _dead)
    with pytest.raises(SystemExit, match="provision --capacity-reservation cr-live"):
        lt._provision_capacity_block(_provision_args())


def test_provision_dispatches_to_capacity_path(monkeypatch):
    monkeypatch.setattr(ec2, "_load_state", lambda: None)
    sentinel = object()
    monkeypatch.setattr(lt, "_provision_capacity_block", lambda args: sentinel)
    assert lt.provision(_provision_args()) is sentinel


# ---------------------------------------------------------------------------
# provision reattach x --capacity-reservation precedence
# ---------------------------------------------------------------------------


def _live_state(**overrides):
    state = {"instance_id": "i-live", "region": "us-east-2", "availability_zone": "us-east-2c",
             "instance_type": "p5.48xlarge", "public_ip": "3.3.3.3",
             "security_group_id": "sg-1", "key_name": "smolbench-lean-train"}
    state.update(overrides)
    return state


def test_provision_refuses_reservation_flag_on_live_spot_box(monkeypatch):
    """An explicit --capacity-reservation must never be silently satisfied by
    reattaching to a live SPOT box -- the exact double-spend the block was
    bought to end."""
    monkeypatch.setattr(ec2, "_load_state", _live_state)
    monkeypatch.setattr(ec2, "_instance_state", lambda region, iid: "running")
    with pytest.raises(SystemExit, match="refusing to silently reattach"):
        lt.provision(_provision_args(capacity_reservation="auto"))


def test_provision_refuses_reservation_flag_on_other_block_box(monkeypatch):
    monkeypatch.setattr(ec2, "_load_state",
                        lambda: _live_state(capacity_reservation_id="cr-other",
                                            market="capacity-block"))
    monkeypatch.setattr(ec2, "_instance_state", lambda region, iid: "running")
    with pytest.raises(SystemExit, match="cr-other"):
        lt.provision(_provision_args(capacity_reservation="cr-wanted"))


def test_provision_reattaches_to_matching_block_box(monkeypatch, capsys):
    """Reattach (after IP churn etc.) to the box already on the requested
    block -- both by explicit id and via auto."""
    monkeypatch.setattr(ec2, "_load_state",
                        lambda: _live_state(capacity_reservation_id="cr-live",
                                            market="capacity-block"))
    monkeypatch.setattr(ec2, "_instance_state", lambda region, iid: "running")
    monkeypatch.setattr(ec2, "_my_public_ip", lambda: "1.2.3.4")
    monkeypatch.setattr(lt, "_authorize_ssh", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "_describe_instance", lambda region, iid: {"PublicIpAddress": "9.9.9.9"})
    monkeypatch.setattr(ec2, "_save_state", lambda state: None)
    for wanted in ("cr-live", "auto"):
        state = lt.provision(_provision_args(capacity_reservation=wanted))
        assert state["instance_id"] == "i-live"
    assert "market=capacity-block" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Backstop rendering + train-timeout defaults
# ---------------------------------------------------------------------------


def test_render_user_data_rejects_none_lifetime():
    """None leaking into the template would render `shutdown -h +None`, whose
    `|| true` silently leaves the box with NO lifetime backstop."""
    with pytest.raises(AssertionError):
        lt._render_train_user_data(None)


def test_render_user_data_spot_default_backstop():
    assert f"shutdown -h +{lt.DEFAULT_MAX_LIFETIME_MIN} " in \
        lt._render_train_user_data(lt.DEFAULT_MAX_LIFETIME_MIN)


def test_default_train_timeout_spot_is_48h():
    assert lt._default_train_timeout({"market": "spot"}) == lt.DEFAULT_MAX_LIFETIME_MIN
    assert lt._default_train_timeout({}) == lt.DEFAULT_MAX_LIFETIME_MIN


def test_default_train_timeout_cb_covers_block_window(ledger):
    end = datetime.now(timezone.utc) + timedelta(days=6)
    lt._cb_save([{"reservation_id": "cr-live", "region": "us-east-2",
                  "end_date": end.strftime("%Y-%m-%dT%H:%M:%SZ")}])
    got = lt._default_train_timeout(
        {"market": "capacity-block", "capacity_reservation_id": "cr-live"})
    expected = int((end - datetime.now(timezone.utc)).total_seconds() // 60) + 120
    assert abs(got - expected) <= 2
    assert got > lt.DEFAULT_MAX_LIFETIME_MIN  # the 48h cap must not apply


def test_default_train_timeout_cb_without_ledger_record_falls_back(ledger):
    assert lt._default_train_timeout(
        {"market": "capacity-block", "capacity_reservation_id": "cr-gone"}
    ) == lt.DEFAULT_MAX_LIFETIME_MIN


# ---------------------------------------------------------------------------
# cb-search: sort, pagination, region skip, purchase hint
# ---------------------------------------------------------------------------


def _offering(oid, fee, az="us-east-2c"):
    return {
        "CapacityBlockOfferingId": oid,
        "AvailabilityZone": az,
        "InstanceType": "p5.48xlarge",
        "InstanceCount": 1,
        "StartDate": datetime(2026, 7, 12, 6, 0, tzinfo=timezone.utc),
        "EndDate": datetime(2026, 7, 15, 6, 0, tzinfo=timezone.utc),
        "CapacityBlockDurationHours": 72,
        "UpfrontFee": fee,
        "CurrencyCode": "USD",
    }


class _OfferingsClient:
    """Pages of DescribeCapacityBlockOfferings, chained via NextToken."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def describe_capacity_block_offerings(self, **kwargs):
        self.calls.append(kwargs)
        idx = int(kwargs.get("NextToken", "0"))
        page = {"CapacityBlockOfferings": list(self.pages[idx])}
        if idx + 1 < len(self.pages):
            page["NextToken"] = str(idx + 1)
        return page


def _search_args(**overrides):
    args = dict(instance_type="p5.48xlarge", instance_count=1, duration_hours=72,
                start_after=None, end_before=None, regions="us-east-2")
    args.update(overrides)
    return Namespace(**args)


def test_cb_search_sorts_numerically_and_hints_cheapest(monkeypatch, capsys):
    """'9.00' must sort before '100.00' (numeric, not lexicographic), a
    missing fee must sort last, and the copy-paste hint must name the
    CHEAPEST offering with the cb-purchase flags."""
    client = _OfferingsClient([[
        _offering("cbo-pricey", "100.00"),
        _offering("cbo-cheap", "9.00"),
        _offering("cbo-nofee", None),
    ]])
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: client)
    assert lt.cb_search(_search_args()) == 0
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.startswith("us-east-2 ")]
    assert [ln.split()[-1] for ln in lines] == ["cbo-cheap", "cbo-pricey", "cbo-nofee"]
    assert "cb-purchase --region us-east-2 --offering-id cbo-cheap" in out


def test_cb_search_paginates_and_passes_date_range(monkeypatch, capsys):
    client = _OfferingsClient([[_offering("cbo-a", "10")], [_offering("cbo-b", "20")]])
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: client)
    assert lt.cb_search(_search_args(start_after="+6h")) == 0
    out = capsys.readouterr().out
    assert "cbo-a" in out and "cbo-b" in out
    assert len(client.calls) == 2 and client.calls[1]["NextToken"] == "1"
    assert isinstance(client.calls[0]["StartDateRange"], datetime)


def test_cb_search_skips_broken_region_keeps_going(monkeypatch, capsys):
    class _Denied:
        def describe_capacity_block_offerings(self, **kwargs):
            raise _client_error("UnsupportedOperation", "DescribeCapacityBlockOfferings")

    clients = {"us-east-1": _Denied(),
               "us-east-2": _OfferingsClient([[_offering("cbo-ok", "10")]])}
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: clients[region])
    assert lt.cb_search(_search_args(regions="us-east-1,us-east-2")) == 0
    out, err = capsys.readouterr()
    assert "cbo-ok" in out
    assert "us-east-1: UnsupportedOperation" in err


def test_cb_search_no_offerings_is_rc1(monkeypatch, capsys):
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: _OfferingsClient([[]]))
    assert lt.cb_search(_search_args()) == 1
    assert "no capacity-block offerings" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# train: double-launch guard + --attach
# ---------------------------------------------------------------------------


def _train_args(**overrides):
    args = dict(model="qwen3-235b-a22b", attach=False, checkpoint_dest="s3",
                s3_prefix="lean-train-checkpoints", org="rengz",
                dataset_file=lt.DEFAULT_DATASET, init_adapter_s3=None, out_name="",
                cap=8000, full=False, max_steps=-1, save_steps=200, lora_r=16,
                lora_alpha=32, batch_size=1, grad_accum=16, seed=1776,
                full_determinism=False, poll=1, timeout=1)
    args.update(overrides)
    return Namespace(**args)


class _SshRecorder:
    def __init__(self, replies):
        self.replies = replies  # substring -> stdout
        self.cmds = []

    def __call__(self, state, cmd, check=True, capture=False, input_text=None):
        self.cmds.append(cmd)
        stdout = ""
        for needle, reply in self.replies.items():
            if needle in cmd:
                stdout = reply
                break
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


@pytest.fixture()
def train_env(monkeypatch):
    monkeypatch.setattr(ec2, "_require_state", lambda: {"public_ip": "1.2.3.4"})
    monkeypatch.setattr(ec2, "EC2_S3_MODEL_CACHE", "s3://test-bucket/models")


def test_train_refuses_to_double_launch(train_env, monkeypatch):
    """_train_cmd starts by deleting the DONE marker and nohup-launching a
    second trainer + S3-sync loop; a plain re-run while one is alive must
    refuse and point at --attach."""
    ssh = _SshRecorder({"pgrep": "RUNNING\n"})
    monkeypatch.setattr(lt, "_ssh", ssh)
    with pytest.raises(SystemExit, match="--attach"):
        lt.train(_train_args())
    assert all("nohup" not in c for c in ssh.cmds)  # never launched


def test_train_attach_requires_existing_log(train_env, monkeypatch):
    ssh = _SshRecorder({})  # test -f log -> no HAVE
    monkeypatch.setattr(lt, "_ssh", ssh)
    with pytest.raises(SystemExit, match="nothing to attach to"):
        lt.train(_train_args(attach=True))
    assert all("nohup" not in c for c in ssh.cmds)


def test_train_attach_polls_existing_run_to_done(train_env, monkeypatch):
    ssh = _SshRecorder({"test -f": "HAVE\n", "cat": "rc=0\n---\n0\n"})
    monkeypatch.setattr(lt, "_ssh", ssh)
    assert lt.train(_train_args(attach=True)) == 0
    assert all("nohup" not in c for c in ssh.cmds)  # attach never relaunches
