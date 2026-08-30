"""Offline tests for ec2.py's provisioning helpers, server_config and live probes."""

import re
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError, WaiterError

from smolbench.evals.payloads import pack_user_data
from smolbench.evals.providers import ec2

_ABSENT = object()
_SPOT = {"SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}
_BLOCK = {"MarketType": "capacity-block"}
_TARGET = {"CapacityReservationTarget": {"CapacityReservationId": "cr-0abc"}}
_IMO = "InstanceMarketOptions"


def _raiser(exc):
    def raise_it(*args, **kwargs):
        raise exc

    return raise_it


def _base_kwargs(**overrides):
    kwargs = dict(ami="ami-0123456789abcdef0", instance_type="p5e.48xlarge", volume_gb=300,
                  subnet_id="subnet-abc123", group_id="sg-def456", root_device="/dev/sda1",
                  user_data=b"#!/bin/bash\necho hi\n", key_name="", iam_profile=None)
    kwargs.update(overrides)
    return ec2._run_instances_kwargs(**kwargs)


def test_run_instances_kwargs_matches_pinned_shape(monkeypatch):
    assert _base_kwargs() == {
        "ImageId": "ami-0123456789abcdef0",
        "InstanceType": "p5e.48xlarge",
        "MinCount": 1, "MaxCount": 1,
        "InstanceMarketOptions": {"MarketType": "spot", "SpotOptions": dict(_SPOT)},
        "InstanceInitiatedShutdownBehavior": "terminate",
        "NetworkInterfaces": [{"DeviceIndex": 0, "SubnetId": "subnet-abc123",
                               "Groups": ["sg-def456"], "AssociatePublicIpAddress": True,
                               "DeleteOnTermination": True}],
        "BlockDeviceMappings": [{"DeviceName": "/dev/sda1", "Ebs": {
            "VolumeSize": 300, "VolumeType": "gp3", "DeleteOnTermination": True,
            "Throughput": ec2.EC2_ROOT_VOLUME_THROUGHPUT, "Iops": ec2.EC2_ROOT_VOLUME_IOPS}}],
        "TagSpecifications": [{"ResourceType": "instance", "Tags": [
            {"Key": "smolbench:experiment", "Value": ec2.EC2_EXPERIMENT_TAG},
            {"Key": "Name", "Value": f"smolbench-{ec2.EC2_EXPERIMENT_TAG}"}]}],
        "UserData": b"#!/bin/bash\necho hi\n",
    }
    # No MarketType="on-demand" exists: absence is how the API expresses it.
    monkeypatch.setattr(ec2, "EC2_MARKET", "spot")
    spot = _base_kwargs(max_price="12.34")
    monkeypatch.setattr(ec2, "EC2_MARKET", "on-demand")
    assert {k: v for k, v in spot.items() if k != _IMO} == _base_kwargs(max_price="12.34")


@pytest.mark.parametrize(
    "market,overrides,expected",
    [
        ("spot", {}, {"KeyName": _ABSENT, "IamInstanceProfile": _ABSENT,
                      "CapacityReservationSpecification": _ABSENT,
                      _IMO: {"MarketType": "spot", "SpotOptions": _SPOT}}),
        ("spot", {"key_name": "k", "iam_profile": "role"},
         {"KeyName": "k", "IamInstanceProfile": {"Name": "role"}}),
        ("spot", {"capacity_reservation_id": "cr-0abc"},
         {_IMO: _BLOCK, "CapacityReservationSpecification": _TARGET,
          "InstanceInitiatedShutdownBehavior": "terminate", "MinCount": 1, "MaxCount": 1}),
        ("spot", {"max_price": "25.19"},
         {_IMO: {"MarketType": "spot", "SpotOptions": dict(_SPOT, MaxPrice="25.19")}}),
        ("spot", {"capacity_reservation_id": "cr-0abc", "max_price": "25.19"}, {_IMO: _BLOCK}),
        ("on-demand", {"max_price": "12.34"},
         {_IMO: _ABSENT, "InstanceInitiatedShutdownBehavior": "terminate"}),
        ("on-demand", {"capacity_reservation_id": "cr-0abc"},
         {_IMO: _BLOCK, "CapacityReservationSpecification": _TARGET}),
    ],
)
def test_run_instances_kwargs_variants(monkeypatch, market, overrides, expected):
    monkeypatch.setattr(ec2, "EC2_MARKET", market)
    kwargs = _base_kwargs(**overrides)
    assert {k: kwargs.get(k, _ABSENT) for k in expected} == expected


def test_decode_user_data_round_trips():
    """gzip decodes; pre-determinism plain text still decodes; garbage raises."""
    rendered = "#!/bin/bash\necho hi\n"
    assert ec2._decode_user_data(pack_user_data(rendered)) == rendered
    assert ec2._decode_user_data(rendered.encode()) == rendered
    with pytest.raises(UnicodeDecodeError):
        ec2._decode_user_data(b"\xff\xfe\x00\x01not-gzip-not-utf8")


@pytest.mark.parametrize(
    "describe_return,expected",
    [(None, "absent"), ({}, "absent"), ({"State": {"Name": "running"}}, "running")],
)
def test_instance_state(monkeypatch, describe_return, expected):
    monkeypatch.setattr(ec2, "_describe_instance", lambda region, iid: describe_return)
    assert ec2._instance_state("eu-west-1", "i-abc") == expected


@pytest.mark.parametrize(
    "code,account,bucket,raises,created",
    [
        ("403", "414266451290", "smolbench-model-cache-414266451290", False, []),
        ("403", "999999999999", "smolbench-model-cache-414266451290", True, []),
        ("404", "414266451290", "some-new-bucket", False,
         [{"Bucket": "some-new-bucket",
           "CreateBucketConfiguration": {"LocationConstraint": "us-west-2"}}]),
    ],
)
def test_ensure_bucket(monkeypatch, code, account, bucket, raises, created):
    made = []
    err = ClientError({"Error": {"Code": code, "Message": ""}}, "HeadBucket")
    clients = {"s3": SimpleNamespace(head_bucket=_raiser(err),
                                     create_bucket=lambda **kw: made.append(kw)),
               "sts": SimpleNamespace(get_caller_identity=lambda: {"Account": account})}
    monkeypatch.setattr(ec2._aws, "fresh_client", lambda service, region: clients[service])
    with pytest.raises(RuntimeError) if raises else nullcontext():
        ec2._ensure_bucket(bucket, "us-west-2")
    assert made == created


_SPOT_STATE = {"instance_id": "i-spot", "region": "us-west-2"}
_BLOCK_STATE = {"instance_id": "i-block", "capacity_reservation_id": "cr-block1"}
_FRESH = {"instance_id": "i-fresh", "capacity_reservation_id": "cr-block1"}


@pytest.mark.parametrize(
    "reservation,reattach,recover,expected,calls",
    [
        (None, _SPOT_STATE, None, _SPOT_STATE, {"shutdown": 0, "launch_fresh": 0}),
        ("cr-block1", _BLOCK_STATE, None, _BLOCK_STATE, {"shutdown": 0, "launch_fresh": 0}),
        ("cr-block1", _SPOT_STATE, None, _FRESH, {"shutdown": 1, "launch_fresh": 1}),
        ("cr-block1", None, _SPOT_STATE, _FRESH, {"shutdown": 1, "launch_fresh": 1}),
    ],
)
def test_provision_reservation_authority(monkeypatch, reservation, reattach, recover, expected,
                                         calls):
    """No reservation reuses any live box; a reservation reuses only in-block boxes."""
    monkeypatch.delenv("EC2_CAPACITY_RESERVATION", raising=False)
    if reservation:
        monkeypatch.setenv("EC2_CAPACITY_RESERVATION", reservation)
    waits, launched = [], []
    monkeypatch.setattr(ec2, "_my_public_ip", lambda: "203.0.113.7")
    monkeypatch.setattr(ec2, "_reattach_existing_instance", lambda my_ip: reattach)
    monkeypatch.setattr(ec2, "_recover_tagged_instance", lambda my_ip: recover)
    monkeypatch.setattr(ec2, "shutdown_instance", lambda wait=True: waits.append(wait))
    monkeypatch.setattr(ec2, "_launch_fresh", lambda *a, **k: launched.append(1) or dict(_FRESH))
    assert ec2.provision_spot_instance() == expected
    assert {"shutdown": len(waits), "launch_fresh": len(launched)} == calls
    assert waits == [False] * calls["shutdown"]  # must not block on p5-class teardown


def test_shutdown_instance_survives_waiter_timeout(monkeypatch):
    """TerminateInstances already succeeded, so an expired waiter must not raise."""
    terminated, cleared = [], []
    expired = SimpleNamespace(wait=_raiser(WaiterError("InstanceTerminated", "expired", {})))
    fake = SimpleNamespace(terminate_instances=lambda InstanceIds: terminated.append(InstanceIds),
                           get_waiter=lambda name: expired)
    monkeypatch.setattr(ec2, "_load_state", lambda: dict(instance_id="i-slow", region="us-west-2"))
    monkeypatch.setattr(ec2, "_agent", lambda *a, **k: {})
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: fake)
    monkeypatch.setattr(ec2, "_clear_state", lambda instance_id=None: cleared.append(instance_id))
    ec2.shutdown_instance(wait=True)
    assert terminated == [["i-slow"]]
    assert cleared == ["i-slow"]  # cleared as the owner of i-slow, not blindly


def test_spot_price_map(monkeypatch):
    """Newest observation per (type, AZ) wins; a client failure degrades to price-blind."""
    rows = [{"InstanceType": "p5.48xlarge", "AvailabilityZone": az, "SpotPrice": p} for az, p in
            [("us-east-1a", "20.00"), ("us-east-1a", "99.00"), ("us-east-1b", "21.50")]]
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: SimpleNamespace(
        describe_spot_price_history=lambda **kw: {"SpotPriceHistory": rows}))
    assert ec2._spot_price_map("us-east-1", ["p5.48xlarge"]) == {
        ("p5.48xlarge", "us-east-1a"): 20.00, ("p5.48xlarge", "us-east-1b"): 21.50}
    monkeypatch.setattr(ec2, "_ec2_client", _raiser(RuntimeError("no credentials")))
    assert ec2._spot_price_map("us-east-1", ["p5.48xlarge"]) == {}


# _wait_public_ip: DescribeInstances is eventually consistent, so only a sustained
# absent streak may abort; observed death states abort immediately.

_RUNNING = {"State": {"Name": "running"}, "PublicIpAddress": "1.2.3.4"}
_LIMIT = ec2._ABSENT_STREAK_LIMIT


@pytest.mark.parametrize(
    "polls,expected_ip,polls_used",
    [
        ([None] * (_LIMIT - 1) + [_RUNNING], "1.2.3.4", _LIMIT),
        ([None] * (_LIMIT + 5), None, _LIMIT),
        ([{"State": {"Name": "terminated"}}] * 5, None, 1),
    ],
)
def test_wait_public_ip(monkeypatch, polls, expected_ip, polls_used):
    monkeypatch.setattr(ec2._aws.time, "sleep", lambda s: None)
    seen, remaining = [], iter(polls)
    monkeypatch.setattr(ec2, "_describe_instance",
                        lambda region, iid: seen.append(iid) or next(remaining))
    with nullcontext() if expected_ip else pytest.raises(RuntimeError):
        assert ec2._wait_public_ip("us-east-2", "i-abc") == expected_ip
    assert len(seen) == polls_used


_LAST_SERVE = {
    "model": "ministral-3-14b", "hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512",
    "tp": 4, "max_model_len": 131072, "vllm_args": ["--seed", "0"],
    "image": "vllm/vllm-openai@sha256:deadbeef", "served_at": "2026-08-18T00:00:00+00:00",
}
_S5_STATE = {
    "instance_type": "g7.24xlarge", "region": "us-east-2", "availability_zone": "us-east-2c",
    "instance_id": "i-abc123", "public_ip": "203.0.113.10", "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret", "last_serve": _LAST_SERVE,
}
_VER = "0.27.2rc1.dev122+g8efa13b70"
_CACHE = ['vllm:cache_config_info{num_gpu_blocks="12345"} 1.0']
_FP = {
    "image_repo_digests": ["vllm/vllm-openai@sha256:cec2df507519abc"],
    "nvidia_smi": "H100 80GB HBM3, gpu-uuid-1, 550.90.07, 81559 MiB, Disabled",
    "hf_snapshots": ["51f9210f3cd20f3452a80d5819d15dc61cc50630"], "weights_digest": "abc123def456",
}


def _patch_s5_fetches(monkeypatch):
    calls = {"version": [], "cache": [], "agent": []}
    for name, key, value in [("_fetch_vllm_version", "version", _VER),
                             ("_fetch_vllm_cache_config", "cache", _CACHE),
                             ("_fetch_agent_fingerprint", "agent", (_FP, ["INFO backend."]))]:
        monkeypatch.setattr(ec2, name, lambda *a, k=key, v=value: calls[k].append(a) or v)
    return calls


_HAPPY = {
    "instance_type": "g7.24xlarge", "gpu": "4x RTX PRO 4500 32GB", "instance_id": "i-abc123",
    "tp": 4,  # derived from the landed box, not the spec pin
    "availability_zone": "us-east-2c", "vllm_image": ec2.EC2_VLLM_IMAGE, "max_model_len": 131072,
    "hf_model_id": ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["hf_model_id"], "vllm_version": _VER,
    "served_at": "2026-08-18T00:00:00+00:00", "vllm_args": ["--seed", "0"], "stream": True,
    "vllm_cache_config": _CACHE, "agent_fingerprint": _FP, "max_parallel_requests": 3,
    "vllm_image_digest": "vllm/vllm-openai@sha256:cec2df507519abc",
}
# No box: box-derived fields blank, but client-side config is env-only so it survives.
_NO_BOX = dict.fromkeys("instance_type gpu vllm_args max_model_len served_at vllm_version "
                        "vllm_cache_config agent_fingerprint vllm_image_digest".split())
_NO_BOX.update(max_parallel_requests=8, stream=False)
# Serving another model: last_serve fields must not be misattributed to it, but the
# live probes describe whatever is running now, so they survive the mismatch.
_MISMATCH = {"vllm_args": None, "max_model_len": None, "served_at": None,
             "vllm_version": _VER, "agent_fingerprint": _FP}
_OTHER_STATE = dict(_S5_STATE, last_serve=dict(_LAST_SERVE, model="gemma-4-12b"))
_RAISE = object()


@pytest.mark.parametrize(
    "state,model,env,expected",
    [
        (_S5_STATE, "ministral-3-14b",
         {"EC2_MAX_PARALLEL_REQUESTS": "3", "EC2_STREAM_COMPLETIONS": "1"}, _HAPPY),
        (_RAISE, "ministral-3-14b", {}, None),
        (None, "gemma-4-12b", {}, _NO_BOX),
        (_OTHER_STATE, "ministral-3-14b", {}, _MISMATCH),
        (_S5_STATE, "ministral-3-14b", {"EC2_STREAM_COMPLETIONS": "true"},
         {"stream": None, "vllm_args": ["--seed", "0"], "vllm_version": _VER}),
    ],
)
def test_server_config(monkeypatch, state, model, env, expected):
    """Happy path, then a raising state load, an absent box, a mismatch, a malformed env var."""
    for name in ("EC2_MAX_PARALLEL_REQUESTS", "EC2_STREAM_COMPLETIONS"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    load = _raiser(RuntimeError("corrupt state")) if state is _RAISE else lambda: state
    monkeypatch.setattr(ec2, "_load_state", load)
    calls = _patch_s5_fetches(monkeypatch)
    cfg = ec2.server_config(model)
    if expected is None:  # no snapshot could be built at all
        assert cfg is None
        return
    assert {k: cfg[k] for k in expected} == expected
    probed = [] if state is None else [("203.0.113.10", "vk-stub-secret")]
    assert (calls["version"], calls["cache"], len(calls["agent"])) == (probed, probed, len(probed))


@pytest.mark.parametrize(
    "probe,resp,expected",
    [
        ("_fetch_vllm_version", SimpleNamespace(ok=True, json=lambda: {"version": _VER}), _VER),
        ("_fetch_vllm_version", SimpleNamespace(ok=False), None),
        ("_fetch_vllm_version", ec2.requests.exceptions.ConnectionError("dead box"), None),
        ("_fetch_vllm_cache_config", SimpleNamespace(ok=True, text=(
            "# HELP vllm:cache_config_info info\n# TYPE vllm:cache_config_info gauge\n"
            'vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0\n'
            "vllm:num_requests_running{} 0.0\n")),
         ['vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0']),
        ("_fetch_vllm_cache_config",
         SimpleNamespace(ok=True, text="vllm:num_requests_running{} 0.0\n"), None),
    ],
)
def test_fetch_vllm_probes(monkeypatch, probe, resp, expected):
    """Both probes return their payload, and both degrade to None, never raising."""
    get = _raiser(resp) if isinstance(resp, Exception) else lambda url, headers, timeout: resp
    monkeypatch.setattr(ec2.requests, "get", get)
    assert getattr(ec2, probe)("203.0.113.10", "vk") == expected


@pytest.mark.parametrize(
    "status,expected",
    [
        ({"healthy": True, "fingerprint": {"nvidia_smi": "stub"}},
         ({"nvidia_smi": "stub"}, None)),  # no log_tail in the fake status
        ({"fingerprint": {"nvidia_smi": "stub"},
          "log_tail": "INFO boot\nINFO Using Flash Attention backend on V1 engine.\nINFO ready"},
         ({"nvidia_smi": "stub"}, ["INFO Using Flash Attention backend on V1 engine."])),
        (RuntimeError("agent unreachable"), (None, None)),
    ],
)
def test_fetch_agent_fingerprint(monkeypatch, status, expected):
    """Extracts the fingerprint key, mines backend lines from the log tail, else None."""
    agent = _raiser(status) if isinstance(status, Exception) else lambda *a, **kw: status
    monkeypatch.setattr(ec2, "_agent", agent)
    assert ec2._fetch_agent_fingerprint(_S5_STATE) == expected


def test_serve_model_stashes_last_serve_with_the_actual_launched_argv(monkeypatch):
    state = {k: v for k, v in _S5_STATE.items() if k != "last_serve"}
    monkeypatch.delenv("EC2_REQUIRE_GPU", raising=False)
    monkeypatch.setattr(ec2, "_require_state", lambda: state)
    saved, agent_calls = {}, []

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        agent_calls.append((method, path, payload))
        # An unhealthy status means "not already serving" -> take the real-swap path.
        return {"healthy": False} if path == "/status" else {"ok": True}

    monkeypatch.setattr(ec2, "_agent", fake_agent)
    monkeypatch.setattr(ec2, "_wait_model_ready", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "list_models", lambda: ["ministral-3-14b"])
    monkeypatch.setattr(ec2, "_save_state", lambda s: saved.update(s))
    with ec2.serve_model("ministral-3-14b") as served:
        assert served == "ministral-3-14b"
    last = dict(saved["last_serve"])
    datetime.fromisoformat(last.pop("served_at"))
    assert last == {
        "model": "ministral-3-14b", "max_model_len": 131072, "image": ec2.EC2_VLLM_IMAGE,
        "hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512",
        "tp": 4,  # derived from g7.24xlarge, not the spec's static pin
        "vllm_args": ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"],
    }
    assert saved["serving"]["served_model_name"] == "ministral-3-14b"
    assert ("POST", "/serve") in [(m, p) for m, p, _ in agent_calls]


def test_launch_fresh_wraps_user_data_in_pack_user_data():
    """Source pin: the raw render exceeds EC2's 16 KB cap, so gzip is load-bearing."""
    src = Path(ec2.__file__.replace(".pyc", ".py")).read_text()
    assert re.search(r"pack_user_data\(\s*render_user_data\(", src)
