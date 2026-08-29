"""Test aws.py's SageMaker provisioning offline, against a recording fake.

``_ensure_exec_role`` and ``mint_sagemaker_token`` are stubbed; no boto3
credentials or network access are used.
"""

import os

import pytest

from smolbench.evals.providers import aws

_SPEC = {"hf_model_id": "org/model", "instance_type": "ml.p5.48xlarge", "tp": 8}
_ROLE_ARN = "arn:aws:iam::0:role/x"


@pytest.mark.parametrize(
    "spec,expected",
    [
        ({**_SPEC, "image": "custom-image:tag"}, {"Image": "custom-image:tag"}),
        ({**_SPEC, "tp": 4}, {"SM_VLLM_TENSOR_PARALLEL_SIZE": "4"}),
        (
            {"hf_model_id": "org/model", "instance_type": "ml.g5.2xlarge"},
            {"SM_VLLM_TENSOR_PARALLEL_SIZE": "1"},
        ),
        (
            {**_SPEC, "env": {"SAGEMAKER_ENABLE_LOAD_AWARE": "0", "HF_TOKEN": "hf_xyz"}},
            {
                "SAGEMAKER_ENABLE_LOAD_AWARE": "0",
                "HF_TOKEN": "hf_xyz",
                "HF_MODEL_ID": "org/model",
            },
        ),
    ],
    ids=["image-override", "tp-str-coerced", "tp-absent-defaults-1", "env-merge-spec-wins"],
)
def test_create_model_kwargs_variants(spec, expected):
    container = aws._create_model_kwargs("my-model", spec, _ROLE_ARN)["PrimaryContainer"]
    for key, value in expected.items():
        got = container["Image"] if key == "Image" else container["Environment"][key]
        assert got == value


class _FakeSagemakerClient:
    """Record every SageMaker call; describe_endpoint reports InService at once."""

    def __init__(self):
        self.calls: list = []

    def __getattr__(self, name):
        def call(**kwargs):
            self.calls.append((name, kwargs))
            return {"EndpointStatus": "InService"}

        return call


@pytest.fixture
def _sagemaker_env(monkeypatch):
    """Uses setenv, never delenv, so the minted token cannot leak into other files' tests."""
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
        assert os.environ["AWS_INFERENCE_API_KEY"] == "sagemaker-api-key-stub"

    assert [name for name, _ in fake.calls] == [
        "create_model",
        "create_endpoint_config",
        "create_endpoint",
        "describe_endpoint",
        "delete_endpoint",
        "delete_endpoint_config",
        "delete_model",
    ]
    assert fake.calls[0][1] == {
        "ModelName": "qwen2.5-1.5b-test-model",
        "ExecutionRoleArn": "arn:aws:iam::0:role/exec",
        "PrimaryContainer": {
            "Image": aws.SAGEMAKER_VLLM_DLC,
            "Environment": {
                "HF_MODEL_ID": "Qwen/Qwen2.5-1.5B-Instruct",
                "SM_VLLM_TENSOR_PARALLEL_SIZE": "1",
                "SAGEMAKER_ENABLE_LOAD_AWARE": "1",
            },
        },
    }
    assert fake.calls[1][1] == {
        "EndpointConfigName": "qwen2.5-1.5b-test-config",
        "ProductionVariants": [
            {
                "VariantName": "variant1",
                "ModelName": "qwen2.5-1.5b-test-model",
                "InitialInstanceCount": 1,
                "InstanceType": "ml.g5.2xlarge",
                "ContainerStartupHealthCheckTimeoutInSeconds": 1800,
            }
        ],
    }
    assert fake.calls[2][1] == {
        "EndpointName": "qwen2.5-1.5b-test",
        "EndpointConfigName": "qwen2.5-1.5b-test-config",
    }
    assert fake.calls[4:] == [
        ("delete_endpoint", {"EndpointName": "qwen2.5-1.5b-test"}),
        ("delete_endpoint_config", {"EndpointConfigName": "qwen2.5-1.5b-test-config"}),
        ("delete_model", {"ModelName": "qwen2.5-1.5b-test-model"}),
    ]


def test_provision_endpoint_teardown_runs_even_when_body_raises(_sagemaker_env):
    """Teardown runs from a finally block and never masks the body's exception."""
    fake = _sagemaker_env

    with pytest.raises(RuntimeError, match="boom"):
        with aws.provision_endpoint("qwen2.5-1.5b-test"):
            raise RuntimeError("boom")

    assert [name for name, _ in fake.calls][-3:] == [
        "delete_endpoint",
        "delete_endpoint_config",
        "delete_model",
    ]


def test_provision_endpoint_noop_for_non_sagemaker(monkeypatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "ec2")
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    monkeypatch.setattr(
        aws, "_sagemaker_client", lambda: pytest.fail("must not build a SageMaker client")
    )

    with aws.provision_endpoint("anything") as yielded:
        assert yielded == "anything"


def test_provision_endpoint_unknown_spec_raises_keyerror(monkeypatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    monkeypatch.setattr(
        aws, "_sagemaker_client", lambda: pytest.fail("must not build a SageMaker client")
    )

    with pytest.raises(KeyError):
        with aws.provision_endpoint("nope"):
            pass
