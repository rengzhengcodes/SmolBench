"""Call-time provider dispatch: env read per call, no import-order trap."""

import pytest

from smolbench.evals import provider


def test_dispatch_follows_env_after_import(monkeypatch):
    """Setting INFERENCE_PROVIDER after import must take effect -- the old
    import-time dispatch silently ignored it, forcing notebooks to mutate
    os.environ before the import."""
    from smolbench.evals import ec2, openrouter

    monkeypatch.setenv("INFERENCE_PROVIDER", "ec2")
    assert provider._provider_module() is ec2
    monkeypatch.setenv("INFERENCE_PROVIDER", "openrouter")
    assert provider._provider_module() is openrouter
    monkeypatch.delenv("INFERENCE_PROVIDER")
    assert provider._provider_module() is openrouter  # documented default


def test_unknown_provider_is_actionable(monkeypatch):
    monkeypatch.setenv("INFERENCE_PROVIDER", "nonsense")
    with pytest.raises(ValueError, match="nonsense"):
        provider._provider_module()


def test_sagemaker_requires_base_url(monkeypatch):
    """Selecting sagemaker without a base URL would silently hit Bedrock."""
    monkeypatch.setenv("INFERENCE_PROVIDER", "sagemaker")
    monkeypatch.delenv("AWS_INFERENCE_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="AWS_INFERENCE_BASE_URL"):
        provider._provider_module()
    monkeypatch.setenv(
        "AWS_INFERENCE_BASE_URL",
        "https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/{model}/openai/v1",
    )
    from smolbench.evals import aws

    assert provider._provider_module() is aws
