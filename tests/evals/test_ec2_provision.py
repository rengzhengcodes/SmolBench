"""Offline tests for ec2.py's provisioning helpers, server_config and live probes."""

from types import SimpleNamespace

import pytest

from smolbench.evals.providers import ec2


# _run_instances_kwargs: the exact RunInstances kwargs dict.


def _base_kwargs(**overrides):
    """Build _run_instances_kwargs with a fixed set of representative inputs."""
    kwargs = dict(
        ami="ami-0123456789abcdef0",
        instance_type="p5e.48xlarge",
        subnet_id="subnet-abc123",
        group_id="sg-def456",
        root_device="/dev/sda1",
        volume_gb=300,
        user_data=b"#!/bin/bash\necho hi\n",
        key_name="",
        iam_profile=None,
    )
    kwargs.update(overrides)
    return ec2._run_instances_kwargs(**kwargs)


def test_run_instances_kwargs_matches_pinned_shape():
    kwargs = _base_kwargs()
    assert kwargs == {
        "ImageId": "ami-0123456789abcdef0",
        "InstanceType": "p5e.48xlarge",
        "MinCount": 1,
        "MaxCount": 1,
        "InstanceMarketOptions": {
            "MarketType": "spot",
            "SpotOptions": {
                "SpotInstanceType": "one-time",
                "InstanceInterruptionBehavior": "terminate",
            },
        },
        "InstanceInitiatedShutdownBehavior": "terminate",
        "NetworkInterfaces": [
            {
                "DeviceIndex": 0,
                "SubnetId": "subnet-abc123",
                "Groups": ["sg-def456"],
                "AssociatePublicIpAddress": True,
                "DeleteOnTermination": True,
            }
        ],
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 300,
                    "VolumeType": "gp3",
                    "Throughput": ec2.EC2_ROOT_VOLUME_THROUGHPUT,
                    "Iops": ec2.EC2_ROOT_VOLUME_IOPS,
                    "DeleteOnTermination": True,
                },
            }
        ],
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "smolbench:experiment", "Value": ec2.EC2_EXPERIMENT_TAG},
                    {"Key": "Name", "Value": f"smolbench-{ec2.EC2_EXPERIMENT_TAG}"},
                ],
            }
        ],
        "UserData": b"#!/bin/bash\necho hi\n",
    }


_ABSENT = object()
_SPOT = {"SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}
_BLOCK = {"MarketType": "capacity-block"}
_TARGET = {"CapacityReservationTarget": {"CapacityReservationId": "cr-0abc"}}
_IMO = "InstanceMarketOptions"


def _at(kwargs, path):
    cur = kwargs
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return _ABSENT
        cur = cur[part]
    return cur


@pytest.mark.parametrize(
    "market,overrides,expected",
    [
        ("spot", {}, {"KeyName": _ABSENT, "IamInstanceProfile": _ABSENT}),
        ("spot", {"iam_profile": ""}, {"IamInstanceProfile": _ABSENT}),
        ("spot", {"key_name": "k", "iam_profile": "role"},
         {"KeyName": "k", "IamInstanceProfile": {"Name": "role"}}),
        ("spot", {}, {_IMO + ".MarketType": "spot", "CapacityReservationSpecification": _ABSENT,
                      _IMO + ".SpotOptions.MaxPrice": _ABSENT}),
        ("spot", {"capacity_reservation_id": "cr-0abc"},
         {_IMO: _BLOCK, "CapacityReservationSpecification": _TARGET,
          "InstanceInitiatedShutdownBehavior": "terminate", "MinCount": 1, "MaxCount": 1}),
        ("spot", {"max_price": "25.19"}, {_IMO + ".SpotOptions": dict(_SPOT, MaxPrice="25.19")}),
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
    assert {path: _at(kwargs, path) for path in expected} == expected


def test_on_demand_differs_from_spot_only_in_the_market(monkeypatch):
    """No MarketType="on-demand" exists: absence is how the API expresses it."""
    monkeypatch.setattr(ec2, "EC2_MARKET", "spot")
    spot = _base_kwargs(max_price="12.34")
    monkeypatch.setattr(ec2, "EC2_MARKET", "on-demand")
    assert {k: v for k, v in spot.items() if k != _IMO} == _base_kwargs(max_price="12.34")


# _decode_user_data: gzip-or-plain-text decode, the read side of pack_user_data.


def test_decode_user_data_round_trips():
    """gzip decodes; pre-determinism plain text still decodes; garbage raises."""
    from smolbench.evals.payloads import pack_user_data

    rendered = "#!/bin/bash\necho hi\n"
    assert ec2._decode_user_data(pack_user_data(rendered)) == rendered
    assert ec2._decode_user_data(rendered.encode()) == rendered
    with pytest.raises(UnicodeDecodeError):
        ec2._decode_user_data(b"\xff\xfe\x00\x01not-gzip-not-utf8")


# _instance_state: "absent" normalization over _describe_instance's Optional.


@pytest.mark.parametrize(
    "describe_return,expected",
    [(None, "absent"), ({}, "absent"), ({"State": {"Name": "running"}}, "running")],
)
def test_instance_state(monkeypatch, describe_return, expected):
    captured = {}

    def fake_describe(region, instance_id):
        captured.update(region=region, instance_id=instance_id)
        return describe_return

    monkeypatch.setattr(ec2, "_describe_instance", fake_describe)
    assert ec2._instance_state("eu-west-1", "i-abc") == expected
    assert captured == {"region": "eu-west-1", "instance_id": "i-abc"}


# _ensure_bucket: a 403 HEAD is ambiguous, so the account-id suffix breaks the tie.


def _client_error(code):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": ""}}, "HeadBucket")


class _FakeS3:
    def __init__(self, head_error=None):
        self.head_error = head_error
        self.created = []

    def head_bucket(self, Bucket):
        if self.head_error is not None:
            raise self.head_error

    def create_bucket(self, **kwargs):
        self.created.append(kwargs)


class _FakeSts:
    def __init__(self, account):
        self.account = account

    def get_caller_identity(self):
        return {"Account": self.account}


def _patch_clients(monkeypatch, s3, sts):
    def fake_fresh_client(service, region):
        return {"s3": s3, "sts": sts}[service]

    monkeypatch.setattr(ec2._aws, "fresh_client", fake_fresh_client)


def test_ensure_bucket(monkeypatch):
    """403 on our own account proceeds, 403 on a foreign name raises, 404 creates."""
    s3 = _FakeS3(head_error=_client_error("403"))
    _patch_clients(monkeypatch, s3, _FakeSts("414266451290"))
    ec2._ensure_bucket("smolbench-model-cache-414266451290", "us-west-2")
    assert s3.created == []

    s3 = _FakeS3(head_error=_client_error("403"))
    _patch_clients(monkeypatch, s3, _FakeSts("999999999999"))
    with pytest.raises(RuntimeError, match="not accessible"):
        ec2._ensure_bucket("smolbench-model-cache-414266451290", "us-west-2")

    s3 = _FakeS3(head_error=_client_error("404"))
    _patch_clients(monkeypatch, s3, _FakeSts("414266451290"))
    ec2._ensure_bucket("some-new-bucket", "us-west-2")
    assert s3.created == [
        {
            "Bucket": "some-new-bucket",
            "CreateBucketConfiguration": {"LocationConstraint": "us-west-2"},
        }
    ]


# provision_spot_instance: a purchased block outranks any live off-block box.


def _patch_provision(monkeypatch, reattach=None, recover=None):
    calls = {"shutdown": 0, "launch_fresh": 0}
    monkeypatch.setattr(ec2, "_my_public_ip", lambda: "203.0.113.7")
    monkeypatch.setattr(ec2, "_reattach_existing_instance", lambda my_ip: reattach)
    monkeypatch.setattr(ec2, "_recover_tagged_instance", lambda my_ip: recover)

    def fake_shutdown(wait=True):
        calls["shutdown"] += 1
        assert wait is False  # must not block on p5-class teardown

    def fake_launch_fresh(*args, **kwargs):
        calls["launch_fresh"] += 1
        return {"instance_id": "i-fresh", "capacity_reservation_id": "cr-block1"}

    monkeypatch.setattr(ec2, "shutdown_instance", fake_shutdown)
    monkeypatch.setattr(ec2, "_launch_fresh", fake_launch_fresh)
    return calls


_SPOT_STATE = {"instance_id": "i-spot", "region": "us-west-2"}
_BLOCK_STATE = {"instance_id": "i-block", "capacity_reservation_id": "cr-block1"}


def test_provision_reservation_authority(monkeypatch):
    """No reservation reuses any live box; a reservation reuses only in-block boxes."""
    monkeypatch.delenv("EC2_CAPACITY_RESERVATION", raising=False)
    calls = _patch_provision(monkeypatch, reattach=_SPOT_STATE)
    assert ec2.provision_spot_instance() is _SPOT_STATE
    assert calls == {"shutdown": 0, "launch_fresh": 0}

    monkeypatch.setenv("EC2_CAPACITY_RESERVATION", "cr-block1")
    calls = _patch_provision(monkeypatch, reattach=_BLOCK_STATE)
    assert ec2.provision_spot_instance() is _BLOCK_STATE
    assert calls == {"shutdown": 0, "launch_fresh": 0}

    calls = _patch_provision(monkeypatch, reattach=_SPOT_STATE)
    state = ec2.provision_spot_instance()
    assert calls == {"shutdown": 1, "launch_fresh": 1}
    assert state["capacity_reservation_id"] == "cr-block1"

    calls = _patch_provision(monkeypatch, reattach=None, recover=_SPOT_STATE)
    state = ec2.provision_spot_instance()
    assert calls == {"shutdown": 1, "launch_fresh": 1}
    assert state["instance_id"] == "i-fresh"


def test_shutdown_instance_survives_waiter_timeout(monkeypatch):
    """TerminateInstances already succeeded, so an expired waiter must not raise."""
    from botocore.exceptions import WaiterError

    def timeout(**kwargs):
        raise WaiterError("InstanceTerminated", "Max attempts exceeded", {})

    terminated, cleared = [], []
    fake = SimpleNamespace(
        terminate_instances=lambda InstanceIds: terminated.append(InstanceIds),
        get_waiter=lambda name: SimpleNamespace(wait=timeout),
    )
    monkeypatch.setattr(
        ec2, "_load_state", lambda: {"instance_id": "i-slow", "region": "us-west-2"}
    )
    monkeypatch.setattr(ec2, "_agent", lambda *a, **k: {})
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: fake)
    monkeypatch.setattr(ec2, "_clear_state", lambda instance_id=None: cleared.append(instance_id))

    ec2.shutdown_instance(wait=True)

    assert terminated == [["i-slow"]]
    assert cleared == ["i-slow"]  # cleared as the owner of i-slow, not blindly


def test_spot_price_map(monkeypatch):
    """Newest observation per (type, AZ) wins; a client failure degrades to price-blind."""
    rows = [
        {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1a", "SpotPrice": "20.00"},
        {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1a", "SpotPrice": "99.00"},
        {"InstanceType": "p5.48xlarge", "AvailabilityZone": "us-east-1b", "SpotPrice": "21.50"},
    ]
    monkeypatch.setattr(ec2, "_ec2_client", lambda region: SimpleNamespace(
        describe_spot_price_history=lambda **kw: {"SpotPriceHistory": rows}))
    assert ec2._spot_price_map("us-east-1", ["p5.48xlarge"]) == {
        ("p5.48xlarge", "us-east-1a"): 20.00,
        ("p5.48xlarge", "us-east-1b"): 21.50,
    }

    def boom(region):
        raise RuntimeError("no credentials")

    monkeypatch.setattr(ec2, "_ec2_client", boom)
    assert ec2._spot_price_map("us-east-1", ["p5.48xlarge"]) == {}


# _wait_public_ip: DescribeInstances is eventually consistent, so only a sustained
# absent streak may abort; observed death states abort immediately.

def _no_sleep_ip(monkeypatch):
    monkeypatch.setattr(ec2._aws.time, "sleep", lambda s: None)


_RUNNING = {"State": {"Name": "running"}, "PublicIpAddress": "1.2.3.4"}
_LIMIT = ec2._ABSENT_STREAK_LIMIT


@pytest.mark.parametrize(
    "polls,expected_ip,error",
    [
        ([None] * (_LIMIT - 1) + [_RUNNING], "1.2.3.4", None),
        ([None] * (_LIMIT + 5), None, "went absent right after launch"),
        ([{"State": {"Name": "terminated"}}] * 5, None, "went terminated right after launch"),
    ],
)
def test_wait_public_ip(monkeypatch, polls, expected_ip, error):
    _no_sleep_ip(monkeypatch)
    calls = {"n": 0}

    def describe(region, iid):
        calls["n"] += 1
        return polls[calls["n"] - 1]

    monkeypatch.setattr(ec2, "_describe_instance", describe)
    if error is None:
        assert ec2._wait_public_ip("us-east-2", "i-abc") == expected_ip
        return
    with pytest.raises(RuntimeError, match=error):
        ec2._wait_public_ip("us-east-2", "i-abc")
    if "absent" in error:
        assert calls["n"] == _LIMIT


# ec2.server_config: the provenance snapshot stamped onto stored results.

_S5_STATE = {
    "instance_type": "g7.24xlarge",
    "region": "us-east-2",
    "availability_zone": "us-east-2c",
    "instance_id": "i-abc123",
    "public_ip": "203.0.113.10",
    "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret",
    "last_serve": {
        "model": "ministral-3-14b",
        "hf_model_id": "mistralai/Ministral-3-14B-Reasoning-2512",
        "tp": 4,
        "max_model_len": 131072,
        "vllm_args": ["--seed", "0"],
        "image": "vllm/vllm-openai@sha256:deadbeef",
        "served_at": "2026-08-18T00:00:00+00:00",
    },
}


def _patch_s5_fetches(monkeypatch, *, vllm_version="0.27.2rc1.dev122+g8efa13b70",
                       vllm_cache_config=None, agent_fp=None):
    """Stand in for the three live-probe helpers server_config() calls, recording args."""
    calls = {"version": [], "cache": [], "agent": []}
    if vllm_cache_config is None:
        vllm_cache_config = ["vllm:cache_config_info{num_gpu_blocks=\"12345\"} 1.0"]
    if agent_fp is None:
        agent_fp = {
            "image_repo_digests": ["vllm/vllm-openai@sha256:cec2df507519abc"],
            "nvidia_smi": "H100 80GB HBM3, gpu-uuid-1, 550.90.07, 81559 MiB, Disabled",
            "hf_snapshots": ["51f9210f3cd20f3452a80d5819d15dc61cc50630"],
            "weights_digest": "abc123def456",
        }

    def fake_version(ip, key):
        calls["version"].append((ip, key))
        return vllm_version

    def fake_cache(ip, key):
        calls["cache"].append((ip, key))
        return vllm_cache_config

    def fake_agent_fp(state):
        calls["agent"].append(state)
        return agent_fp, ["INFO Using Flash Attention backend."]

    monkeypatch.setattr(ec2, "_fetch_vllm_version", fake_version)
    monkeypatch.setattr(ec2, "_fetch_vllm_cache_config", fake_cache)
    monkeypatch.setattr(ec2, "_fetch_agent_fingerprint", fake_agent_fp)
    return calls


def test_server_config_happy_path(monkeypatch):
    """Box up, last_serve names the queried model, all probes succeed."""
    monkeypatch.setattr(ec2, "_load_state", lambda: dict(_S5_STATE))
    calls = _patch_s5_fetches(monkeypatch)
    monkeypatch.setenv("EC2_MAX_PARALLEL_REQUESTS", "3")
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")

    cfg = ec2.server_config("ministral-3-14b")

    assert cfg["instance_type"] == "g7.24xlarge"
    assert cfg["gpu"] == "4x RTX PRO 4500 32GB"
    assert cfg["tp"] == 4  # derived from the landed box, not the spec pin
    assert cfg["availability_zone"] == "us-east-2c"
    assert cfg["instance_id"] == "i-abc123"
    assert cfg["vllm_image"] == ec2.EC2_VLLM_IMAGE
    assert cfg["hf_model_id"] == ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["hf_model_id"]
    assert cfg["vllm_args"] == ["--seed", "0"]
    assert cfg["max_model_len"] == 131072
    assert cfg["served_at"] == "2026-08-18T00:00:00+00:00"
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"
    assert cfg["vllm_cache_config"] == ["vllm:cache_config_info{num_gpu_blocks=\"12345\"} 1.0"]
    assert cfg["agent_fingerprint"]["nvidia_smi"].startswith("H100")
    assert cfg["vllm_image_digest"] == "vllm/vllm-openai@sha256:cec2df507519abc"
    assert cfg["max_parallel_requests"] == 3
    assert cfg["stream"] is True
    assert calls["version"] == [("203.0.113.10", "vk-stub-secret")]
    assert calls["cache"] == [("203.0.113.10", "vk-stub-secret")]
    assert len(calls["agent"]) == 1


def test_server_config_degradations(monkeypatch):
    """A raising state load, an absent box, a model mismatch and a malformed env var."""
    def boom():
        raise RuntimeError("corrupt state")

    monkeypatch.setattr(ec2, "_load_state", boom)
    assert ec2.server_config("ministral-3-14b") is None

    monkeypatch.setattr(ec2, "_load_state", lambda: None)
    calls = _patch_s5_fetches(monkeypatch)
    cfg = ec2.server_config("gemma-4-12b")
    assert cfg is not None
    assert cfg["instance_type"] is None and cfg["gpu"] is None
    for field in ("vllm_args", "max_model_len", "served_at", "vllm_version",
                  "vllm_cache_config", "agent_fingerprint", "vllm_image_digest"):
        assert cfg[field] is None
    assert calls == {"version": [], "cache": [], "agent": []}
    # Client-side config is env-only, so no box must not blank it.
    assert cfg["max_parallel_requests"] == 8
    assert cfg["stream"] is False

    state = dict(_S5_STATE, last_serve=dict(_S5_STATE["last_serve"], model="gemma-4-12b"))
    monkeypatch.setattr(ec2, "_load_state", lambda: state)
    _patch_s5_fetches(monkeypatch)
    cfg = ec2.server_config("ministral-3-14b")
    assert cfg["vllm_args"] is None
    assert cfg["max_model_len"] is None
    assert cfg["served_at"] is None
    # Live probes describe whatever is running now, so they survive the mismatch.
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"
    assert cfg["agent_fingerprint"] is not None

    monkeypatch.setattr(ec2, "_load_state", lambda: dict(_S5_STATE))
    _patch_s5_fetches(monkeypatch)
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "true")
    cfg = ec2.server_config("ministral-3-14b")
    assert cfg is not None
    assert cfg["stream"] is None
    assert cfg["vllm_args"] == ["--seed", "0"]
    assert cfg["vllm_version"] == "0.27.2rc1.dev122+g8efa13b70"


class _FakeResponse:
    """Minimal requests.Response stand-in with only the attributes the code reads."""

    def __init__(self, *, ok=True, json_body=None, text="", status_code=200):
        self.ok = ok
        self._json_body = json_body
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._json_body


def test_fetch_vllm_version_and_cache_config(monkeypatch):
    """Both probes return their payload, and both degrade to None, never raising."""
    monkeypatch.setattr(
        ec2.requests, "get",
        lambda url, headers, timeout: _FakeResponse(json_body={"version": "0.27.2rc1.dev122+g8efa13b70"}),
    )
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") == "0.27.2rc1.dev122+g8efa13b70"

    monkeypatch.setattr(ec2.requests, "get", lambda url, headers, timeout: _FakeResponse(ok=False))
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") is None

    def dead_box(url, headers, timeout):
        raise ec2.requests.exceptions.ConnectionError("dead box")

    monkeypatch.setattr(ec2.requests, "get", dead_box)
    assert ec2._fetch_vllm_version("203.0.113.10", "vk") is None

    body = (
        "# HELP vllm:cache_config_info info\n"
        "# TYPE vllm:cache_config_info gauge\n"
        'vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0\n'
        'vllm:num_requests_running{} 0.0\n'
    )
    monkeypatch.setattr(
        ec2.requests, "get", lambda url, headers, timeout: _FakeResponse(text=body)
    )
    assert ec2._fetch_vllm_cache_config("203.0.113.10", "vk") == [
        'vllm:cache_config_info{num_gpu_blocks="12345",block_size="16"} 1.0'
    ]

    monkeypatch.setattr(
        ec2.requests, "get",
        lambda url, headers, timeout: _FakeResponse(text="vllm:num_requests_running{} 0.0\n"),
    )
    assert ec2._fetch_vllm_cache_config("203.0.113.10", "vk") is None


def test_fetch_agent_fingerprint(monkeypatch):
    """Extracts the fingerprint key, mines backend lines from the log tail, else None."""
    monkeypatch.setattr(
        ec2, "_agent",
        lambda state, method, path, timeout=None, connect_retries=None: {
            "healthy": True, "fingerprint": {"nvidia_smi": "stub"},
        },
    )
    fp, backend = ec2._fetch_agent_fingerprint(_S5_STATE)
    assert fp == {"nvidia_smi": "stub"}
    assert backend is None  # no log_tail in the fake status

    monkeypatch.setattr(
        ec2, "_agent",
        lambda state, method, path, timeout=None, connect_retries=None: {
            "fingerprint": {"nvidia_smi": "stub"},
            "log_tail": "INFO boot\nINFO Using Flash Attention backend on V1 engine.\nINFO ready",
        },
    )
    fp, backend = ec2._fetch_agent_fingerprint(_S5_STATE)
    assert backend == ["INFO Using Flash Attention backend on V1 engine."]

    def unreachable(state, method, path, timeout=None, connect_retries=None):
        raise RuntimeError("agent unreachable")

    monkeypatch.setattr(ec2, "_agent", unreachable)
    assert ec2._fetch_agent_fingerprint(_S5_STATE) == (None, None)


def test_serve_model_stashes_last_serve_with_the_actual_launched_argv(monkeypatch):
    state = {k: v for k, v in _S5_STATE.items() if k != "last_serve"}
    monkeypatch.delenv("EC2_REQUIRE_GPU", raising=False)
    monkeypatch.setattr(ec2, "_require_state", lambda: state)

    agent_calls = []

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        agent_calls.append((method, path, payload))
        if method == "GET" and path == "/status":
            return {"healthy": False}  # not already serving -> take the real-swap path
        if method == "POST" and path == "/serve":
            return {"ok": True, "launching": payload["served_model_name"]}
        raise AssertionError(f"unexpected agent call: {method} {path}")

    saved = {}
    monkeypatch.setattr(ec2, "_agent", fake_agent)
    monkeypatch.setattr(ec2, "_wait_model_ready", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "list_models", lambda: ["ministral-3-14b"])
    monkeypatch.setattr(ec2, "_save_state", lambda s: saved.update(s))

    with ec2.serve_model("ministral-3-14b") as served:
        assert served == "ministral-3-14b"

    assert saved["last_serve"]["model"] == "ministral-3-14b"
    assert saved["last_serve"]["hf_model_id"] == "mistralai/Ministral-3-14B-Reasoning-2512"
    assert saved["last_serve"]["tp"] == 4  # derived from g7.24xlarge, not the spec's static pin
    assert saved["last_serve"]["max_model_len"] == 131072
    assert saved["last_serve"]["vllm_args"] == ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"]
    assert saved["last_serve"]["image"] == ec2.EC2_VLLM_IMAGE

    from datetime import datetime as _dt

    _dt.fromisoformat(saved["last_serve"]["served_at"])
    assert saved["serving"]["served_model_name"] == "ministral-3-14b"
    assert "served_model_name" not in saved["last_serve"]
    assert ("POST", "/serve") in [(m, p) for m, p, _ in agent_calls]


def test_launch_fresh_wraps_user_data_in_pack_user_data():
    """Source pin: the raw render exceeds EC2's 16 KB cap, so gzip is load-bearing."""
    import re
    from pathlib import Path

    src = Path(ec2.__file__.replace(".pyc", ".py")).read_text()
    assert re.search(r"pack_user_data\(\s*render_user_data\(", src)
