"""Offline unit tests for smolbench/evals/aws.py's SageMaker provisioning --
the pure kwargs-builders (``_create_model_kwargs`` / ``_create_endpoint_config_
kwargs`` / ``_create_endpoint_kwargs`` / ``_teardown_steps``) and
``provision_endpoint``'s control flow (the no-op fast path for non-SageMaker
providers, the unknown-spec ``KeyError``, and -- in the happy-path tests below
-- the full deploy/poll/yield/teardown sequence).

Every pinned literal in the builder tests is transcribed from the PRE-
REFACTOR inline code this module's ``provision_endpoint`` used to contain
(the ``create_model``/``create_endpoint_config``/``create_endpoint`` calls and
the teardown loop, formerly inline at roughly aws.py:350-412) rather than
derived from the builders themselves -- like ``tests/test_aws_shared.py`` and
``tests/test_ec2_provision.py``, the point is to catch the extraction
silently drifting from what the inline code did, not merely to describe
whatever the builders happen to return today.

No boto3 credentials or network access are used anywhere in this file:
``provision_endpoint`` is exercised against small hand-rolled recording fakes
standing in for the SageMaker client (see ``_FakeSagemakerClient`` below), and
``aws._ensure_exec_role`` / ``aws.mint_sagemaker_token`` are monkeypatched out
entirely rather than exercised (their own behavior is covered elsewhere --
``_ensure_exec_role``'s underlying primitive by ``tests/test_aws_shared.py``'s
``ensure_sagemaker_execution_role`` tests).
"""

import os

import pytest

from smolbench.evals import aws

# ---------------------------------------------------------------------------
# _create_model_kwargs: pinned against the pre-refactor create_model() call
# ---------------------------------------------------------------------------
# Original (pre-refactor):
#     _sagemaker_client().create_model(
#         ModelName=mdl,
#         ExecutionRoleArn=role,
#         PrimaryContainer={
#             "Image": spec.get("image", SAGEMAKER_VLLM_DLC),
#             "Environment": {
#                 "HF_MODEL_ID": spec["hf_model_id"],
#                 "SM_VLLM_TENSOR_PARALLEL_SIZE": str(spec.get("tp", 1)),
#                 "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
#             }
#             | spec.get("env", {}),
#         },
#     )

_SPEC = {"hf_model_id": "org/model", "instance_type": "ml.p5.48xlarge", "tp": 8}
_ROLE_ARN = "arn:aws:iam::0:role/x"


def test_create_model_kwargs_pinned_default_image():
    """Default image (no spec override) -- the base image constant, verbatim."""
    kwargs = aws._create_model_kwargs("my-model", _SPEC, _ROLE_ARN)
    assert kwargs == {
        "ModelName": "my-model-model",
        "ExecutionRoleArn": _ROLE_ARN,
        "PrimaryContainer": {
            "Image": aws.SAGEMAKER_VLLM_DLC,
            "Environment": {
                "HF_MODEL_ID": "org/model",
                "SM_VLLM_TENSOR_PARALLEL_SIZE": "8",
                "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
            },
        },
    }


def test_create_model_kwargs_image_override():
    """spec["image"] wins over SAGEMAKER_VLLM_DLC when present."""
    spec = {**_SPEC, "image": "custom-image:tag"}
    kwargs = aws._create_model_kwargs("my-model", spec, _ROLE_ARN)
    assert kwargs["PrimaryContainer"]["Image"] == "custom-image:tag"


def test_create_model_kwargs_tp_present_is_str_coerced():
    kwargs = aws._create_model_kwargs("my-model", {**_SPEC, "tp": 4}, _ROLE_ARN)
    assert kwargs["PrimaryContainer"]["Environment"]["SM_VLLM_TENSOR_PARALLEL_SIZE"] == "4"


def test_create_model_kwargs_tp_absent_defaults_to_str_one():
    spec = {"hf_model_id": "org/model", "instance_type": "ml.g5.2xlarge"}  # no "tp" key
    kwargs = aws._create_model_kwargs("my-model", spec, _ROLE_ARN)
    assert kwargs["PrimaryContainer"]["Environment"]["SM_VLLM_TENSOR_PARALLEL_SIZE"] == "1"


def test_create_model_kwargs_env_merge_spec_key_overrides_base_key():
    """The ``|`` merge is base-dict-then-spec-env, so a spec env key with the
    SAME name as a base key (e.g. SAGEMAKER_ENABLE_LOAD_AWARE) wins -- and an
    unrelated spec env key (HF_TOKEN) is simply added alongside the base
    keys."""
    spec = {**_SPEC, "env": {"SAGEMAKER_ENABLE_LOAD_AWARE": "0", "HF_TOKEN": "hf_xyz"}}
    kwargs = aws._create_model_kwargs("my-model", spec, _ROLE_ARN)
    env = kwargs["PrimaryContainer"]["Environment"]
    assert env["SAGEMAKER_ENABLE_LOAD_AWARE"] == "0"  # spec env overrides the base "1"
    assert env["HF_TOKEN"] == "hf_xyz"
    assert env["HF_MODEL_ID"] == "org/model"  # base keys untouched by an unrelated override


def test_create_model_kwargs_no_env_key_is_base_dict_unchanged():
    """No spec["env"] at all -- merging with {} must not alter the base dict's
    keys or values (guards the `| spec.get("env", {})` default)."""
    kwargs = aws._create_model_kwargs("my-model", _SPEC, _ROLE_ARN)
    assert kwargs["PrimaryContainer"]["Environment"] == {
        "HF_MODEL_ID": "org/model",
        "SM_VLLM_TENSOR_PARALLEL_SIZE": "8",
        "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
    }


# ---------------------------------------------------------------------------
# _create_endpoint_config_kwargs: pinned against the pre-refactor
# create_endpoint_config() call
# ---------------------------------------------------------------------------


def test_create_endpoint_config_kwargs_pinned():
    kwargs = aws._create_endpoint_config_kwargs("my-model", _SPEC)
    assert kwargs == {
        "EndpointConfigName": "my-model-config",
        "ProductionVariants": [
            {
                "VariantName": "variant1",
                "ModelName": "my-model-model",
                "InitialInstanceCount": 1,
                "InstanceType": "ml.p5.48xlarge",
                "ContainerStartupHealthCheckTimeoutInSeconds": 1800,
            }
        ],
    }


def test_create_endpoint_config_kwargs_instance_type_passthrough():
    kwargs = aws._create_endpoint_config_kwargs("my-model", {**_SPEC, "instance_type": "ml.g5.2xlarge"})
    assert kwargs["ProductionVariants"][0]["InstanceType"] == "ml.g5.2xlarge"


# ---------------------------------------------------------------------------
# _create_endpoint_kwargs: pinned against the pre-refactor create_endpoint()
# call
# ---------------------------------------------------------------------------


def test_create_endpoint_kwargs_pinned():
    assert aws._create_endpoint_kwargs("my-model") == {
        "EndpointName": "my-model",
        "EndpointConfigName": "my-model-config",
    }


# ---------------------------------------------------------------------------
# _teardown_steps: pinned against the pre-refactor `finally` block's 3-tuple
# ---------------------------------------------------------------------------
# Original (pre-refactor):
#     sm = _sagemaker_client()
#     for label, call in (
#         ("endpoint", lambda: sm.delete_endpoint(EndpointName=model)),
#         ("endpoint-config", lambda: sm.delete_endpoint_config(EndpointConfigName=cfg)),
#         ("model", lambda: sm.delete_model(ModelName=mdl)),
#     ):


class _RecordingSagemakerClient:
    """Records every delete_* call's kwargs; no real boto3 involved."""

    def __init__(self):
        self.calls: list = []

    def delete_endpoint(self, **kwargs):
        self.calls.append(("delete_endpoint", kwargs))

    def delete_endpoint_config(self, **kwargs):
        self.calls.append(("delete_endpoint_config", kwargs))

    def delete_model(self, **kwargs):
        self.calls.append(("delete_model", kwargs))


def test_teardown_steps_order_and_calls():
    sm = _RecordingSagemakerClient()
    steps = aws._teardown_steps(sm, "my-model")

    # Order matters: endpoint before endpoint-config before model -- deleting
    # an endpoint before its config/model is the dependency-safe direction.
    assert [label for label, _ in steps] == ["endpoint", "endpoint-config", "model"]

    for _, call in steps:
        call()
    assert sm.calls == [
        ("delete_endpoint", {"EndpointName": "my-model"}),
        ("delete_endpoint_config", {"EndpointConfigName": "my-model-config"}),
        ("delete_model", {"ModelName": "my-model-model"}),
    ]


# ---------------------------------------------------------------------------
# provision_endpoint: no-op fast path for a non-SageMaker provider
# ---------------------------------------------------------------------------


def _assert_never_calls_sagemaker_client(monkeypatch):
    def _boom():
        raise AssertionError("must not construct a SageMaker client for a non-SageMaker provider")

    monkeypatch.setattr(aws, "_sagemaker_client", _boom)


@pytest.mark.parametrize("provider_env", [None, "openrouter"])
def test_provision_endpoint_noop_for_non_sagemaker(monkeypatch, provider_env):
    if provider_env is None:
        monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("INFERENCE_PROVIDER", provider_env)
    # AWS_INFERENCE_BASE_URL absent must NOT accidentally make
    # _is_sagemaker_provider() true via a stray "{model}"/"sagemaker" default.
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    _assert_never_calls_sagemaker_client(monkeypatch)

    with aws.provision_endpoint("anything") as yielded:
        assert yielded == "anything"  # yields immediately, no deploy attempted


# ---------------------------------------------------------------------------
# provision_endpoint: unknown spec raises KeyError with the exact message
# ---------------------------------------------------------------------------


def test_provision_endpoint_unknown_spec_raises_keyerror(monkeypatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    _assert_never_calls_sagemaker_client(monkeypatch)  # spec lookup fails before any client is built

    with pytest.raises(
        KeyError,
        match=r"No SAGEMAKER_DEPLOY_SPECS entry for endpoint 'nope'; add one with hf_model_id / instance_type / tp\.",
    ):
        with aws.provision_endpoint("nope"):
            pass  # pragma: no cover -- KeyError fires on __enter__, before the body ever runs


# ---------------------------------------------------------------------------
# provision_endpoint: full happy-path lifecycle against a recording fake
# ---------------------------------------------------------------------------


class _FakeSagemakerClient:
    """Records every SageMaker call. ``describe_endpoint`` reports InService
    on its very first call, so the poll loop inside ``provision_endpoint``
    exits after exactly one iteration without any real sleeping."""

    def __init__(self):
        self.calls: list = []

    def create_model(self, **kwargs):
        self.calls.append(("create_model", kwargs))

    def create_endpoint_config(self, **kwargs):
        self.calls.append(("create_endpoint_config", kwargs))

    def create_endpoint(self, **kwargs):
        self.calls.append(("create_endpoint", kwargs))

    def describe_endpoint(self, **kwargs):
        self.calls.append(("describe_endpoint", kwargs))
        return {"EndpointStatus": "InService"}

    def delete_endpoint(self, **kwargs):
        self.calls.append(("delete_endpoint", kwargs))

    def delete_endpoint_config(self, **kwargs):
        self.calls.append(("delete_endpoint_config", kwargs))

    def delete_model(self, **kwargs):
        self.calls.append(("delete_model", kwargs))


@pytest.fixture
def _sagemaker_env(monkeypatch):
    """Common env/monkeypatch setup for the full-lifecycle tests below: makes
    _is_sagemaker_provider() true, stubs _ensure_exec_role/mint_sagemaker_token
    (their own behavior is covered elsewhere -- see module docstring), and
    seeds AWS_INFERENCE_API_KEY via setenv (never delenv/raw-assignment) so
    monkeypatch's built-in teardown restores the ORIGINAL env var state
    afterwards even though provision_endpoint mutates os.environ directly
    inside the `with` body -- a delenv(raising=False) on an already-absent
    var registers no undo and would leak the minted token into later tests
    (e.g. tests/test_openai_compat.py, tests/test_provider_dispatch.py, which
    also read AWS_INFERENCE_API_KEY through aws._api_key())."""
    monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    monkeypatch.setenv("AWS_INFERENCE_API_KEY", "placeholder-pre-provision-token")
    monkeypatch.setitem(
        aws.SAGEMAKER_DEPLOY_SPECS,
        "qwen2.5-1.5b-test",
        {"hf_model_id": "Qwen/Qwen2.5-1.5B-Instruct", "instance_type": "ml.g5.2xlarge", "tp": 1},
    )
    monkeypatch.setattr(aws, "_ensure_exec_role", lambda: "arn:aws:iam::0:role/exec")
    monkeypatch.setattr(aws, "mint_sagemaker_token", lambda: "sagemaker-api-key-stub")
    fake = _FakeSagemakerClient()
    monkeypatch.setattr(aws, "_sagemaker_client", lambda: fake)
    return fake


def test_provision_endpoint_happy_path_full_lifecycle(_sagemaker_env):
    fake = _sagemaker_env

    with aws.provision_endpoint("qwen2.5-1.5b-test") as yielded:
        assert yielded == "qwen2.5-1.5b-test"
        # Token refresh happens before yield -- the inference path reads this
        # env var at call time, so it must already be set once the body runs.
        assert os.environ["AWS_INFERENCE_API_KEY"] == "sagemaker-api-key-stub"

    call_names = [name for name, _ in fake.calls]
    assert call_names == [
        "create_model",
        "create_endpoint_config",
        "create_endpoint",
        "describe_endpoint",
        "delete_endpoint",
        "delete_endpoint_config",
        "delete_model",
    ]

    # Spot-check the payloads the fake actually received end-to-end.
    create_model_kwargs = fake.calls[0][1]
    assert create_model_kwargs["ModelName"] == "qwen2.5-1.5b-test-model"
    assert create_model_kwargs["ExecutionRoleArn"] == "arn:aws:iam::0:role/exec"
    assert create_model_kwargs["PrimaryContainer"]["Environment"]["HF_MODEL_ID"] == (
        "Qwen/Qwen2.5-1.5B-Instruct"
    )
    assert fake.calls[4][1] == {"EndpointName": "qwen2.5-1.5b-test"}
    assert fake.calls[5][1] == {"EndpointConfigName": "qwen2.5-1.5b-test-config"}
    assert fake.calls[6][1] == {"ModelName": "qwen2.5-1.5b-test-model"}


def test_provision_endpoint_teardown_runs_even_when_body_raises(_sagemaker_env):
    """Teardown is in a `finally` -- it must run (all three deletes) even
    when the `with` body raises, and the body's own exception must still
    propagate (teardown must never mask it)."""
    fake = _sagemaker_env

    with pytest.raises(RuntimeError, match="boom"):
        with aws.provision_endpoint("qwen2.5-1.5b-test"):
            raise RuntimeError("boom")

    call_names = [name for name, _ in fake.calls]
    assert call_names[-3:] == ["delete_endpoint", "delete_endpoint_config", "delete_model"]
