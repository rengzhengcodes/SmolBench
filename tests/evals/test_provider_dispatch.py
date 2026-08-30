"""Test provider_module() name resolution (env vs explicit)."""

import importlib

import pytest

from smolbench.evals import provider

_SM_URL = "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1"


@pytest.mark.parametrize(
    "env_value,name,expected",
    [("ec2", None, "ec2"), ("openrouter", None, "openrouter"), (None, None, "openrouter"),
     ("ec2", "openrouter", "openrouter"), ("openrouter", "ec2", "ec2"),
     ("nonsense", None, ValueError), (None, "nope", ValueError)],
)
def test_provider_module_resolution(monkeypatch, env_value, name, expected):
    """Explicit name beats env, unset env defaults to openrouter, unknown raises."""
    if env_value is None:
        monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("INFERENCE_PROVIDER", env_value)
    if expected is ValueError:
        with pytest.raises(ValueError) as excinfo:
            provider.provider_module(name)
        assert (name or env_value) in str(excinfo.value)
    else:
        assert provider.provider_module(name) is importlib.import_module(
            f"smolbench.evals.providers.{expected}")


@pytest.mark.parametrize("name", [None, "sagemaker"])
def test_sagemaker_requires_base_url(monkeypatch, name):
    """Selecting sagemaker without a base URL would silently hit Bedrock."""
    if name is None:
        monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    else:
        monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="AWS_INFERENCE_BASE_URL"):
        provider.provider_module(name)
    monkeypatch.setenv("AWS_INFERENCE_BASE_URL", _SM_URL)
    from smolbench.evals.providers import aws

    assert provider.provider_module(name) is aws
