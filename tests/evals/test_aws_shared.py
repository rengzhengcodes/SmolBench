"""Test smolbench/evals/_aws.py offline: the primitives shared by aws.py and ec2.py."""

import inspect
import json

import pytest
from botocore.exceptions import ClientError

from smolbench.evals import _aws
from smolbench.evals.providers import aws, ec2

ROLE = "smolbench-role"


def test_poll_until_success_paths(monkeypatch):
    monkeypatch.setattr(
        _aws.time, "sleep", lambda s: pytest.fail("must not sleep on immediate success")
    )
    value = _aws.poll_until(lambda: "value", timeout_s=10.0, interval_s=1.0, on_timeout=RuntimeError)
    assert value == "value"

    times = iter([0.0, 5.0])  # deadline = 5.0; second check lands exactly on it
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))
    calls = {"n": 0}

    def check():
        calls["n"] += 1
        return None if calls["n"] == 1 else "done"

    result = _aws.poll_until(
        check, timeout_s=5.0, interval_s=1.0, on_timeout=RuntimeError
    )
    assert result == "done"
    assert sleeps == [1.0]


def test_poll_until_failure_paths(monkeypatch):
    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        _aws.poll_until(boom, timeout_s=10.0, interval_s=1.0, on_timeout=RuntimeError)

    times = iter([0.0, 10.1])  # deadline = 10.0; second check is past it
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))
    monkeypatch.setattr(
        _aws.time, "sleep", lambda s: pytest.fail("must not sleep once the deadline has passed")
    )
    sentinel = RuntimeError("timed out, specifically THIS instance")
    with pytest.raises(RuntimeError) as excinfo:
        _aws.poll_until(lambda: None, timeout_s=10.0, interval_s=1.0, on_timeout=lambda: sentinel)
    assert excinfo.value is sentinel


# Copied literally from aws.py's _ensure_exec_role and ec2.py's
# _ensure_instance_profile; key order is part of the contract.
def _pinned_trust_policy(service):
    return {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": service}, "Action": "sts:AssumeRole"}
        ],
    }


_SAGEMAKER_TRUST_POLICY_PRE_REFACTOR = _pinned_trust_policy("sagemaker.amazonaws.com")
_EC2_TRUST_POLICY_PRE_REFACTOR = _pinned_trust_policy("ec2.amazonaws.com")


@pytest.mark.parametrize(
    "service,expected",
    [
        ("sagemaker.amazonaws.com", _SAGEMAKER_TRUST_POLICY_PRE_REFACTOR),
        ("ec2.amazonaws.com", _EC2_TRUST_POLICY_PRE_REFACTOR),
    ],
)
def test_assume_role_trust_policy_pinned(service, expected):
    assert json.dumps(_aws.assume_role_trust_policy(service)) == json.dumps(expected)


class _FakeEntityAlreadyExists(Exception):
    """Stands in for botocore's dynamically-generated exception class."""


class _FakeIamExceptions:
    EntityAlreadyExistsException = _FakeEntityAlreadyExists


class FakeSagemakerIam:
    """Record every call; create_role raises the fake already-exists per role_exists."""

    def __init__(self, *, role_exists: bool):
        self.calls: list = []
        self.exceptions = _FakeIamExceptions()
        self._role_exists = role_exists

    def create_role(self, **kwargs):
        self.calls.append(("create_role", kwargs))
        if self._role_exists:
            raise self.exceptions.EntityAlreadyExistsException()
        return {"Role": {"Arn": "arn:aws:iam::000000000000:role/" + kwargs["RoleName"]}}

    def attach_role_policy(self, **kwargs):
        self.calls.append(("attach_role_policy", kwargs))

    def get_role(self, **kwargs):
        self.calls.append(("get_role", kwargs))
        return {"Role": {"Arn": "arn:aws:iam::000000000000:role/existing-" + kwargs["RoleName"]}}


def test_ensure_sagemaker_execution_role(monkeypatch):
    fresh = FakeSagemakerIam(role_exists=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fresh)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    arn = _aws.ensure_sagemaker_execution_role(ROLE)

    assert arn == "arn:aws:iam::000000000000:role/" + ROLE
    sm_trust = json.dumps(_SAGEMAKER_TRUST_POLICY_PRE_REFACTOR)
    assert fresh.calls == [
        ("create_role", {"RoleName": ROLE, "AssumeRolePolicyDocument": sm_trust}),
        (
            "attach_role_policy",
            {"RoleName": ROLE, "PolicyArn": "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"},
        ),
    ]
    assert sleeps == [10]

    existing = FakeSagemakerIam(role_exists=True)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: existing)
    sleeps.clear()

    arn = _aws.ensure_sagemaker_execution_role(ROLE)
    assert sleeps == []
    assert arn == "arn:aws:iam::000000000000:role/existing-" + ROLE
    assert [c[0] for c in existing.calls] == ["create_role", "get_role"]


def _client_error(code: str) -> ClientError:
    """Build a real botocore ClientError carrying `code`."""
    return ClientError({"Error": {"Code": code, "Message": code}}, "FakeIamOperation")


class FakeEc2ProfileIam:
    """Record every call; raise the tolerated ClientError codes per the flags."""

    def __init__(self, *, role_exists: bool, profile_exists: bool, role_already_attached: bool):
        self.calls: list = []
        self._raises = {
            "create_role": "EntityAlreadyExists" if role_exists else None,
            "create_instance_profile": "EntityAlreadyExists" if profile_exists else None,
            "add_role_to_instance_profile": "LimitExceeded" if role_already_attached else None,
        }

    def __getattr__(self, name):
        def call(**kwargs):
            self.calls.append((name, kwargs))
            if self._raises.get(name):
                raise _client_error(self._raises[name])

        return call


_BUCKET = "smolbench-model-cache-000000000000"
_EXPECTED_S3_CACHE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": f"arn:aws:s3:::{_BUCKET}"},
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": f"arn:aws:s3:::{_BUCKET}/*",
        },
    ],
}


def test_ensure_instance_profile_fresh_create_sleeps_and_pins_calls(monkeypatch):
    fake = FakeEc2ProfileIam(role_exists=False, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    name = _aws.ensure_instance_profile(ROLE, _BUCKET, 12)

    assert name == ROLE
    assert fake.calls == [
        (
            "create_role",
            {"RoleName": ROLE, "AssumeRolePolicyDocument": json.dumps(_EC2_TRUST_POLICY_PRE_REFACTOR)},
        ),
        (
            "put_role_policy",
            {
                "RoleName": ROLE,
                "PolicyName": "smolbench-s3-model-cache",
                "PolicyDocument": json.dumps(_EXPECTED_S3_CACHE_POLICY),
            },
        ),
        (
            "attach_role_policy",
            {"RoleName": ROLE, "PolicyArn": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"},
        ),
        ("create_instance_profile", {"InstanceProfileName": ROLE}),
        ("add_role_to_instance_profile", {"InstanceProfileName": ROLE, "RoleName": ROLE}),
    ]
    assert sleeps == [12]


@pytest.mark.parametrize(
    "flags,expected_sleeps",
    [
        ((True, True, True), []),
        ((True, False, False), [12]),
    ],
    ids=["all-exist", "profile-new-only"],
)
def test_ensure_instance_profile_created_flag(monkeypatch, flags, expected_sleeps):
    """`created` ORs across role and profile, so either fresh resource triggers the sleep."""
    role_exists, profile_exists, attached = flags
    fake = FakeEc2ProfileIam(
        role_exists=role_exists, profile_exists=profile_exists, role_already_attached=attached
    )
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    name = _aws.ensure_instance_profile(ROLE, _BUCKET, 12)
    assert name == ROLE
    assert sleeps == expected_sleeps


@pytest.mark.parametrize("code", ["Throttling", "AccessDenied"])
def test_ensure_instance_profile_error_codes(monkeypatch, code):
    """Untolerated codes propagate; AccessDenied (scoped operator keys) returns early."""

    class _FailingIam(FakeEc2ProfileIam):
        def create_role(self, **kwargs):
            self.calls.append(("create_role", kwargs))
            raise _client_error(code)

    fake = _FailingIam(role_exists=False, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    if code == "Throttling":
        with pytest.raises(ClientError):
            _aws.ensure_instance_profile(ROLE, _BUCKET, 12)
    else:
        name = _aws.ensure_instance_profile(ROLE, _BUCKET, 12)
        assert name == ROLE
        assert [c[0] for c in fake.calls] == ["create_role"]
        assert sleeps == []


@pytest.mark.parametrize(
    "specs,allowed_keys",
    [
        (aws.SAGEMAKER_DEPLOY_SPECS, _aws.SAGEMAKER_SPEC_KEYS),
        (ec2.EC2_DEPLOY_SPECS, _aws.EC2_SPEC_KEYS),
    ],
    ids=["sagemaker", "ec2"],
)
def test_deploy_specs_match_schema(specs, allowed_keys):
    for name, spec in specs.items():
        assert "hf_model_id" in spec, f"{name}: missing required hf_model_id"
        extra = set(spec.keys()) - allowed_keys
        assert not extra, f"{name}: keys {extra} not in the allowed spec keys"


def test_ec2_list_models_ignores_the_model_argument(stub_server, monkeypatch):
    """vLLM serves one model; the parameter exists only for parity with aws.list_models."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")

    assert ec2.list_models() == ["stub-model"]
    assert ec2.list_models("some-ignored-argument") == ["stub-model"]
    assert ec2.list_models(model="another-ignored-argument") == ["stub-model"]
    assert inspect.signature(aws.list_models).parameters["model"].default == ""


def test_best_effort_teardown_runs_all_steps_even_when_one_raises(caplog):
    ran = []

    def ok_step():
        ran.append("ok")

    def failing_step():
        ran.append("failing")
        raise RuntimeError("cleanup blew up")

    def another_ok_step():
        ran.append("another_ok")

    with caplog.at_level("INFO"):
        _aws.best_effort_teardown(
            [("first", ok_step), ("second", failing_step), ("third", another_ok_step)],
            log_prefix="test_teardown",
        )

    assert ran == ["ok", "failing", "another_ok"]
    assert any(
        "teardown skip second" in r.message and "RuntimeError" in r.message for r in caplog.records
    )
