"""Test smolbench/evals/_aws.py offline: the primitives shared by aws.py and ec2.py."""

import inspect
import json
import types

import pytest
from botocore.exceptions import ClientError

from smolbench.evals import _aws
from smolbench.evals.providers import aws, ec2

ROLE = "smolbench-role"
BUCKET = "smolbench-model-cache-000000000000"
ARN = "arn:aws:iam::000000000000:role/"
MANAGED = "arn:aws:iam::aws:policy/"


def test_poll_until_success_and_failure_paths(monkeypatch):
    poll = _aws.poll_until
    monkeypatch.setattr(_aws.time, "sleep", lambda s: pytest.fail("must not sleep on success"))
    assert poll(lambda: "v", timeout_s=10.0, interval_s=1.0, on_timeout=RuntimeError) == "v"

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        poll(boom, timeout_s=10.0, interval_s=1.0, on_timeout=RuntimeError)

    times = iter([0.0, 5.0])  # deadline = 5.0; second check lands exactly on it
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", sleeps.append)
    calls = {"n": 0}

    def check():
        calls["n"] += 1
        return None if calls["n"] == 1 else "done"

    assert poll(check, timeout_s=5.0, interval_s=1.0, on_timeout=RuntimeError) == "done"
    assert sleeps == [1.0]

    times = iter([0.0, 10.1])  # deadline = 10.0; second check is past it
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))
    monkeypatch.setattr(_aws.time, "sleep", lambda s: pytest.fail("must not sleep past deadline"))
    sentinel = RuntimeError("timed out, specifically THIS instance")
    with pytest.raises(RuntimeError) as excinfo:
        poll(lambda: None, timeout_s=10.0, interval_s=1.0, on_timeout=lambda: sentinel)
    assert excinfo.value is sentinel


def _trust(service):
    """Copied literally from aws.py/ec2.py pre-refactor; key order is part of the contract."""
    return {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Principal": {"Service": service}, "Action": "sts:AssumeRole"}]}


@pytest.mark.parametrize("service", ["sagemaker.amazonaws.com", "ec2.amazonaws.com"])
def test_assume_role_trust_policy_pinned(service):
    assert json.dumps(_aws.assume_role_trust_policy(service)) == json.dumps(_trust(service))


#: Stands in for botocore's dynamically-generated exception class.
_FakeAlreadyExists = type("_FakeAlreadyExists", (Exception,), {})


def _client_error(code):
    return ClientError({"Error": {"Code": code, "Message": code}}, "FakeIamOperation")


class FakeIam:
    """Record every call; raise the configured exception for the named calls."""

    def __init__(self, raises=None):
        self.calls = []
        self.exceptions = types.SimpleNamespace(EntityAlreadyExistsException=_FakeAlreadyExists)
        self._raises = raises or {}

    def __getattr__(self, name):
        def call(**kwargs):
            self.calls.append((name, kwargs))
            if name in self._raises:
                raise self._raises[name]
            return {"Role": {"Arn": f"{ARN}{name}/{kwargs.get('RoleName')}"}}

        return call


def _patch_iam(monkeypatch, fake):
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", sleeps.append)
    return sleeps


@pytest.mark.parametrize("exists", [False, True], ids=["fresh", "exists"])
def test_ensure_sagemaker_execution_role(monkeypatch, exists):
    fake = FakeIam({"create_role": _FakeAlreadyExists()} if exists else None)
    sleeps = _patch_iam(monkeypatch, fake)
    arn = _aws.ensure_sagemaker_execution_role(ROLE)
    if exists:
        assert (arn, [c[0] for c in fake.calls], sleeps) == (
            f"{ARN}get_role/{ROLE}", ["create_role", "get_role"], [])
        return
    assert (arn, sleeps) == (f"{ARN}create_role/{ROLE}", [10])
    assert fake.calls == [
        ("create_role", {"RoleName": ROLE,
                         "AssumeRolePolicyDocument": json.dumps(_trust("sagemaker.amazonaws.com"))}),
        ("attach_role_policy", {"RoleName": ROLE, "PolicyArn": MANAGED + "AmazonSageMakerFullAccess"}),
    ]


_S3_STMT = {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": f"arn:aws:s3:::{BUCKET}"}
_S3_CACHE_POLICY = {"Version": "2012-10-17", "Statement": [
    _S3_STMT, {**_S3_STMT, "Action": ["s3:GetObject", "s3:PutObject"],
               "Resource": f"arn:aws:s3:::{BUCKET}/*"}]}
_PROFILE_CALLS = [
    ("create_role",
     {"RoleName": ROLE, "AssumeRolePolicyDocument": json.dumps(_trust("ec2.amazonaws.com"))}),
    ("put_role_policy", {"RoleName": ROLE, "PolicyName": "smolbench-s3-model-cache",
                         "PolicyDocument": json.dumps(_S3_CACHE_POLICY)}),
    ("attach_role_policy",
     {"RoleName": ROLE, "PolicyArn": MANAGED + "AmazonSSMManagedInstanceCore"}),
    ("create_instance_profile", {"InstanceProfileName": ROLE}),
    ("add_role_to_instance_profile", {"InstanceProfileName": ROLE, "RoleName": ROLE}),
]
_EXISTS = _client_error("EntityAlreadyExists")


@pytest.mark.parametrize(
    "raises,want_sleeps,want_calls",
    [({}, [12], _PROFILE_CALLS),
     ({"create_role": _EXISTS, "create_instance_profile": _EXISTS,
       "add_role_to_instance_profile": _client_error("LimitExceeded")}, [], _PROFILE_CALLS),
     ({"create_role": _EXISTS}, [12], _PROFILE_CALLS),
     ({"create_role": _client_error("AccessDenied")}, [], _PROFILE_CALLS[:1])],
    ids=["fresh", "all-exist", "profile-new-only", "access-denied"],
)
def test_ensure_instance_profile(monkeypatch, raises, want_sleeps, want_calls):
    """Calls are pinned; `created` ORs role/profile; AccessDenied (scoped keys) returns early."""
    fake = FakeIam(raises)
    sleeps = _patch_iam(monkeypatch, fake)
    assert _aws.ensure_instance_profile(ROLE, BUCKET, 12) == ROLE
    assert fake.calls == want_calls
    assert sleeps == want_sleeps


def test_ensure_instance_profile_propagates_untolerated_error(monkeypatch):
    fake = FakeIam({"create_role": _client_error("Throttling")})
    _patch_iam(monkeypatch, fake)
    with pytest.raises(ClientError):
        _aws.ensure_instance_profile(ROLE, BUCKET, 12)


@pytest.mark.parametrize(
    "specs,allowed_keys",
    [(aws.SAGEMAKER_DEPLOY_SPECS, _aws.SAGEMAKER_SPEC_KEYS),
     (ec2.EC2_DEPLOY_SPECS, _aws.EC2_SPEC_KEYS)],
    ids=["sagemaker", "ec2"],
)
def test_deploy_specs_match_schema(specs, allowed_keys):
    for name, spec in specs.items():
        assert "hf_model_id" in spec and not set(spec) - allowed_keys, f"{name}: bad spec keys"


def test_ec2_list_models_ignores_the_model_argument(stub_server, monkeypatch):
    """vLLM serves one model; the parameter exists only for parity with aws.list_models."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    assert [ec2.list_models(), ec2.list_models("ignored"), ec2.list_models(model="ignored")] == (
        [["stub-model"]] * 3)
    assert inspect.signature(aws.list_models).parameters["model"].default == ""


def _with_response(value):
    err = RuntimeError("boom")
    err.response = value  # botocore-free shapes: None, an HTML body, a partial dict
    return err


@pytest.mark.parametrize("err,code", [
    (ClientError({"Error": {"Code": "EntityAlreadyExists"}}, "CreateRole"), "EntityAlreadyExists"),
    (ValueError("no .response at all"), ""),
    (_with_response(None), ""),
    (_with_response("<html>429 Too Many Requests</html>"), ""),
    (_with_response({"Error": None}), ""),
])
def test_error_code_degrades_instead_of_raising(err, code):
    """Called inside except blocks: a missing/None/non-mapping response must not raise."""
    assert _aws.error_code(err) == code


def test_best_effort_teardown_runs_all_steps_even_when_one_raises():
    ran = []

    def failing_step():
        ran.append("failing")
        raise RuntimeError("cleanup blew up")

    steps = [("first", lambda: ran.append("ok")), ("second", failing_step),
             ("third", lambda: ran.append("another_ok"))]
    _aws.best_effort_teardown(steps, log_prefix="test_teardown")
    assert ran == ["ok", "failing", "another_ok"]
