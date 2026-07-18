"""Offline unit tests for smolbench/evals/_aws.py -- the primitives shared by
aws.py (SageMaker) and ec2.py (EC2 Spot).

Every pinned literal in this file (the two AssumeRole trust-policy dicts, the
IAM call kwargs, the deploy-spec key sets) is transcribed from the PRE-
REFACTOR source (aws.py's ``_ensure_exec_role``, ec2.py's
``_ensure_instance_profile`` / ``EC2_DEPLOY_SPECS`` / ``SAGEMAKER_DEPLOY_
SPECS``) rather than derived from ``_aws.py`` itself -- the point of this
suite is to catch the extraction silently drifting from what those two
modules did before ``_aws.py`` existed, not merely to describe whatever
``_aws.py`` happens to do today. No boto3 credentials or network access are
used anywhere here: IAM calls go through small hand-rolled recording fakes,
and real ``botocore.exceptions.ClientError``/dynamically-shaped exceptions
are constructed directly (see ``_client_error`` and ``_FakeEntityAlreadyExists``
below) so the error-code / exception-type branches under test see the same
shapes a live IAM client would raise.
"""

import inspect
import json

import pytest
from botocore.exceptions import ClientError

from smolbench.evals import _aws, aws, ec2

# ---------------------------------------------------------------------------
# poll_until: the generic wait-loop primitive every migrated ec2.py loop
# (_wait_public_ip, _wait_agent, _wait_model_ready) is rebuilt on top of.
# ---------------------------------------------------------------------------


def test_poll_until_immediate_success_returns_without_sleeping(monkeypatch):
    monkeypatch.setattr(
        _aws.time, "sleep", lambda s: pytest.fail("must not sleep on immediate success")
    )
    result = _aws.poll_until(
        lambda: "value", timeout_s=10.0, interval_s=1.0, on_timeout=lambda: RuntimeError("unreachable")
    )
    assert result == "value"


def test_poll_until_check_exception_propagates():
    """`check` raising aborts the loop immediately -- used by every migrated
    loop to fail fast on an unrecoverable condition (e.g. a terminated
    instance) instead of exhausting the whole timeout."""

    def check():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        _aws.poll_until(
            check, timeout_s=10.0, interval_s=1.0, on_timeout=lambda: RuntimeError("unreachable")
        )


def test_poll_until_timeout_raises_exactly_on_timeouts_exception(monkeypatch):
    """The raised exception must be the EXACT instance `on_timeout()`
    returned (not merely the same type) -- callers (e.g. _wait_model_ready)
    build a message from state gathered during the loop, so identity matters."""
    times = iter([0.0, 10.1])  # call 1: deadline = 0.0 + 10.0 = 10.0; call 2: past it
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))

    def _no_sleep(_seconds):
        raise AssertionError("must not sleep once the deadline has passed")

    monkeypatch.setattr(_aws.time, "sleep", _no_sleep)
    sentinel = RuntimeError("timed out, specifically THIS instance")
    with pytest.raises(RuntimeError) as excinfo:
        _aws.poll_until(lambda: None, timeout_s=10.0, interval_s=1.0, on_timeout=lambda: sentinel)
    assert excinfo.value is sentinel


def test_poll_until_deadline_checked_after_check_not_before(monkeypatch):
    """A check that succeeds exactly AT the deadline still returns normally:
    poll_until must never consult the deadline after a successful check, and
    the ``> deadline`` (not ``>=``) comparison means "equal to the deadline"
    is not yet a timeout on the failing branch either."""
    calls = {"n": 0}
    times = iter([0.0, 5.0])  # call 1: deadline = 0.0 + 5.0 = 5.0; call 2: exactly the deadline
    monkeypatch.setattr(_aws.time, "time", lambda: next(times))
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    def check():
        calls["n"] += 1
        return None if calls["n"] == 1 else "done"

    result = _aws.poll_until(
        check, timeout_s=5.0, interval_s=1.0, on_timeout=lambda: RuntimeError("should not fire")
    )
    assert result == "done"
    assert sleeps == [1.0]  # exactly one sleep, between the two check() calls


# ---------------------------------------------------------------------------
# assume_role_trust_policy: pinned against the two pre-refactor inline dicts
# ---------------------------------------------------------------------------
# Transcribed literally from aws.py:294-303 (_ensure_exec_role) and
# ec2.py:1259-1268 (_ensure_instance_profile) -- identical shape, differing
# only in the Principal.Service value.

_SAGEMAKER_TRUST_POLICY_PRE_REFACTOR = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "sagemaker.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}

_EC2_TRUST_POLICY_PRE_REFACTOR = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}


def test_assume_role_trust_policy_matches_sagemaker_pre_refactor_literal():
    got = _aws.assume_role_trust_policy("sagemaker.amazonaws.com")
    assert json.dumps(got) == json.dumps(_SAGEMAKER_TRUST_POLICY_PRE_REFACTOR)


def test_assume_role_trust_policy_matches_ec2_pre_refactor_literal():
    got = _aws.assume_role_trust_policy("ec2.amazonaws.com")
    assert json.dumps(got) == json.dumps(_EC2_TRUST_POLICY_PRE_REFACTOR)


# ---------------------------------------------------------------------------
# ensure_sagemaker_execution_role: fake IAM client, both branches
# ---------------------------------------------------------------------------
# aws.py's original _ensure_exec_role catches the SPECIFIC
# iam.exceptions.EntityAlreadyExistsException (not a ClientError-with-code
# check, unlike the EC2 instance-profile helper below) -- so the fake client
# must expose a real, catchable `.exceptions.EntityAlreadyExistsException`.


class _FakeEntityAlreadyExists(Exception):
    """Stands in for botocore's dynamically-generated exception class."""


class _FakeIamExceptions:
    EntityAlreadyExistsException = _FakeEntityAlreadyExists


class FakeSagemakerIam:
    """Records every call; `create_role` either succeeds or raises the fake
    already-exists exception, per `role_exists`."""

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


def test_ensure_sagemaker_execution_role_fresh_create(monkeypatch):
    fake = FakeSagemakerIam(role_exists=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    arn = _aws.ensure_sagemaker_execution_role("smolbench-sm-exec-role")

    assert arn == "arn:aws:iam::000000000000:role/smolbench-sm-exec-role"
    assert fake.calls == [
        (
            "create_role",
            {
                "RoleName": "smolbench-sm-exec-role",
                "AssumeRolePolicyDocument": json.dumps(_SAGEMAKER_TRUST_POLICY_PRE_REFACTOR),
            },
        ),
        (
            "attach_role_policy",
            {
                "RoleName": "smolbench-sm-exec-role",
                "PolicyArn": "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
            },
        ),
    ]
    assert sleeps == [10]  # the fresh-create path's fixed 10s propagation sleep


def test_ensure_sagemaker_execution_role_already_exists_no_sleep(monkeypatch):
    fake = FakeSagemakerIam(role_exists=True)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    monkeypatch.setattr(
        _aws.time, "sleep", lambda s: pytest.fail("already-exists path must not sleep")
    )

    arn = _aws.ensure_sagemaker_execution_role("smolbench-sm-exec-role")

    assert arn == "arn:aws:iam::000000000000:role/existing-smolbench-sm-exec-role"
    assert [c[0] for c in fake.calls] == ["create_role", "get_role"]


# ---------------------------------------------------------------------------
# ensure_instance_profile: fake IAM client covering all four tolerated
# ClientError branches plus the `created`-flag OR semantics.
# ---------------------------------------------------------------------------


def _client_error(code: str) -> ClientError:
    """A real botocore ClientError carrying `code`, matching what a live IAM
    call raises -- `error_code()`'s parsing must work against the genuine
    exception shape, not a hand-rolled stand-in."""
    return ClientError({"Error": {"Code": code, "Message": code}}, "FakeIamOperation")


class FakeEc2ProfileIam:
    """Records every call; each already-exists/limit-exceeded branch is
    independently toggleable so both the fresh-create and already-exists
    paths (and the `created` flag's OR-across-two-resources semantics) are
    covered without four near-duplicate fake classes."""

    def __init__(self, *, role_exists: bool, profile_exists: bool, role_already_attached: bool):
        self.calls: list = []
        self._role_exists = role_exists
        self._profile_exists = profile_exists
        self._role_already_attached = role_already_attached

    def create_role(self, **kwargs):
        self.calls.append(("create_role", kwargs))
        if self._role_exists:
            raise _client_error("EntityAlreadyExists")

    def put_role_policy(self, **kwargs):
        self.calls.append(("put_role_policy", kwargs))

    def attach_role_policy(self, **kwargs):
        self.calls.append(("attach_role_policy", kwargs))

    def create_instance_profile(self, **kwargs):
        self.calls.append(("create_instance_profile", kwargs))
        if self._profile_exists:
            raise _client_error("EntityAlreadyExists")

    def add_role_to_instance_profile(self, **kwargs):
        self.calls.append(("add_role_to_instance_profile", kwargs))
        if self._role_already_attached:
            raise _client_error("LimitExceeded")


_EXPECTED_S3_CACHE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::smolbench-model-cache-000000000000",
        },
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": "arn:aws:s3:::smolbench-model-cache-000000000000/*",
        },
    ],
}


def test_ensure_instance_profile_fresh_create_sleeps_and_pins_calls(monkeypatch):
    fake = FakeEc2ProfileIam(role_exists=False, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    name = _aws.ensure_instance_profile(
        "smolbench-ec2-role", "smolbench-model-cache-000000000000", 12
    )

    assert name == "smolbench-ec2-role"
    assert fake.calls == [
        (
            "create_role",
            {
                "RoleName": "smolbench-ec2-role",
                "AssumeRolePolicyDocument": json.dumps(_EC2_TRUST_POLICY_PRE_REFACTOR),
            },
        ),
        (
            "put_role_policy",
            {
                "RoleName": "smolbench-ec2-role",
                "PolicyName": "smolbench-s3-model-cache",
                "PolicyDocument": json.dumps(_EXPECTED_S3_CACHE_POLICY),
            },
        ),
        (
            "attach_role_policy",
            {
                "RoleName": "smolbench-ec2-role",
                "PolicyArn": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
            },
        ),
        ("create_instance_profile", {"InstanceProfileName": "smolbench-ec2-role"}),
        (
            "add_role_to_instance_profile",
            {"InstanceProfileName": "smolbench-ec2-role", "RoleName": "smolbench-ec2-role"},
        ),
    ]
    assert sleeps == [12]  # propagation_sleep_s, because something was freshly created


def test_ensure_instance_profile_already_exists_created_flag_false_no_sleep(monkeypatch):
    """Role, profile, AND the role-to-profile attachment all already exist
    (the three ClientError branches all fire) -> `created` stays False ->
    no sleep at all, even though propagation_sleep_s is nonzero."""
    fake = FakeEc2ProfileIam(role_exists=True, profile_exists=True, role_already_attached=True)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    monkeypatch.setattr(
        _aws.time, "sleep", lambda s: pytest.fail("nothing was freshly created; must not sleep")
    )

    name = _aws.ensure_instance_profile(
        "smolbench-ec2-role", "smolbench-model-cache-000000000000", 12
    )
    assert name == "smolbench-ec2-role"


def test_ensure_instance_profile_created_flag_true_when_only_profile_is_new(monkeypatch):
    """The role already existed but the instance profile is new -> `created`
    is set via the profile alone (an OR, not an AND, across the two
    resources) -> the propagation sleep still fires."""
    fake = FakeEc2ProfileIam(role_exists=True, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    _aws.ensure_instance_profile("smolbench-ec2-role", "smolbench-model-cache-000000000000", 12)
    assert sleeps == [12]


def test_ensure_instance_profile_reraises_unexpected_client_error(monkeypatch):
    """A ClientError code OTHER than the tolerated ones must propagate, not
    be silently swallowed. (AccessDenied is no longer in this bucket -- it
    gets the scoped-credentials early return, pinned by its own test below.)"""

    class _ThrottledIam(FakeEc2ProfileIam):
        def create_role(self, **kwargs):
            self.calls.append(("create_role", kwargs))
            raise _client_error("Throttling")

    fake = _ThrottledIam(role_exists=False, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)

    with pytest.raises(ClientError):
        _aws.ensure_instance_profile(
            "smolbench-ec2-role", "smolbench-model-cache-000000000000", 12
        )


# ---------------------------------------------------------------------------
# Deploy-spec schema: every real spec entry fits the documented key sets
# ---------------------------------------------------------------------------


def test_sagemaker_deploy_specs_match_schema():
    for name, spec in aws.SAGEMAKER_DEPLOY_SPECS.items():
        assert "hf_model_id" in spec, f"{name}: missing required hf_model_id"
        extra = set(spec.keys()) - _aws.SAGEMAKER_SPEC_KEYS
        assert not extra, f"{name}: keys {extra} not in SAGEMAKER_SPEC_KEYS"


def test_ec2_deploy_specs_match_schema():
    for name, spec in ec2.EC2_DEPLOY_SPECS.items():
        assert "hf_model_id" in spec, f"{name}: missing required hf_model_id"
        extra = set(spec.keys()) - _aws.EC2_SPEC_KEYS
        assert not extra, f"{name}: keys {extra} not in EC2_SPEC_KEYS"


# ---------------------------------------------------------------------------
# list_models parity: aws.list_models and ec2.list_models both accept a
# `model` parameter defaulting to "" -- part of the provider-dispatch
# surface (smolbench.evals.provider treats every provider module the same
# way), even though EC2's vLLM instance serves exactly one model and ignores
# the argument entirely.
# ---------------------------------------------------------------------------


def test_list_models_signature_parity():
    for module in (aws, ec2):
        sig = inspect.signature(module.list_models)
        assert "model" in sig.parameters, f"{module.__name__}.list_models missing a model param"
        assert sig.parameters["model"].default == "", (
            f"{module.__name__}.list_models model default != ''"
        )


def test_ec2_list_models_ignores_the_model_argument(stub_server, monkeypatch):
    """ec2.list_models(model=...) returns the same thing regardless of what
    (if anything) is passed -- vLLM serves exactly one model, so the
    parameter exists purely for call-site parity with aws.list_models, not
    because the stub (or a real instance) routes on it."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")

    assert ec2.list_models() == ["stub-model"]
    assert ec2.list_models("some-ignored-argument") == ["stub-model"]
    assert ec2.list_models(model="another-ignored-argument") == ["stub-model"]


# ---------------------------------------------------------------------------
# best_effort_teardown: every step runs; failures are logged, never raised
# ---------------------------------------------------------------------------


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

    # Every step ran, in order, despite the middle one raising.
    assert ran == ["ok", "failing", "another_ok"]
    messages = [r.message for r in caplog.records]
    assert any("torn down first" in m for m in messages)
    assert any("teardown skip second" in m and "RuntimeError" in m for m in messages)
    assert any("torn down third" in m for m in messages)


def test_best_effort_teardown_does_not_raise():
    def always_fails():
        raise ValueError("nope")

    _aws.best_effort_teardown([("only", always_fails)], log_prefix="test_teardown")  # must not raise


def test_ensure_instance_profile_access_denied_returns_early_no_sleep(monkeypatch):
    """Scoped credentials (EC2-only operator key) get AccessDenied on the
    very first IAM call even when the role/profile already exist from prior
    admin runs -> return the fixed name optimistically, touch nothing else,
    never sleep (RunInstances is the arbiter of whether the profile exists)."""

    class AccessDeniedIam(FakeEc2ProfileIam):
        def create_role(self, **kwargs):
            self.calls.append(("create_role", kwargs))
            raise _client_error("AccessDenied")

    fake = AccessDeniedIam(role_exists=False, profile_exists=False, role_already_attached=False)
    monkeypatch.setattr(_aws, "fresh_client", lambda service, region=None: fake)
    sleeps = []
    monkeypatch.setattr(_aws.time, "sleep", lambda s: sleeps.append(s))

    name = _aws.ensure_instance_profile(
        "smolbench-ec2-role", "smolbench-model-cache-000000000000", 12
    )

    assert name == "smolbench-ec2-role"
    assert [c[0] for c in fake.calls] == ["create_role"]  # stopped at the denial
    assert sleeps == []
