"""Test call-time provider dispatch: env read per call, no import-order trap."""

import pytest

from smolbench.evals import provider


def test_dispatch_follows_env_after_import(monkeypatch):
    """If you set INFERENCE_PROVIDER after import, it must take effect.

    Dispatch reads the env var per call, so notebooks need not mutate
    os.environ before the import.
    """
    from smolbench.evals.providers import ec2, openrouter

    monkeypatch.setenv("INFERENCE_PROVIDER", "ec2")
    assert provider.provider_module() is ec2
    monkeypatch.setenv("INFERENCE_PROVIDER", "openrouter")
    assert provider.provider_module() is openrouter
    monkeypatch.delenv("INFERENCE_PROVIDER")
    assert provider.provider_module() is openrouter  # documented default


def test_unknown_provider_is_actionable(monkeypatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "nonsense")
    with pytest.raises(ValueError, match="nonsense"):
        provider.provider_module()


def test_sagemaker_requires_base_url(monkeypatch):
    """Selecting sagemaker without a base URL would silently hit Bedrock."""
    monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="AWS_INFERENCE_BASE_URL"):
        provider.provider_module()
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    from smolbench.evals.providers import aws

    assert provider.provider_module() is aws


def test_provider_module_explicit_name_bypasses_env(monkeypatch):
    """provider_module(name) resolves that provider directly.

    It ignores whatever INFERENCE_PROVIDER happens to be set to. This
    is the mixed-provider sweep use case described in the module
    docstring.
    """
    from smolbench.evals.providers import ec2, openrouter

    monkeypatch.setenv("INFERENCE_PROVIDER", "ec2")
    # Explicit name wins over the env var, in both directions.
    assert provider.provider_module("openrouter") is openrouter
    assert provider.provider_module("ec2") is ec2


def test_provider_module_explicit_unknown_is_actionable():
    with pytest.raises(ValueError, match="nope"):
        provider.provider_module("nope")


def test_provider_module_explicit_sagemaker_requires_base_url(monkeypatch):
    """The sagemaker/no-base-URL guard applies to an explicitly passed name too.

    It is not limited to the env-dispatch path.
    """
    monkeypatch.delenv("INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="AWS_INFERENCE_BASE_URL"):
        provider.provider_module("sagemaker")
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    from smolbench.evals.providers import aws

    assert provider.provider_module("sagemaker") is aws
