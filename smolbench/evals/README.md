# Evaluations

Evaluation infrastructure for OpenAI-compatible inference providers:
OpenRouter, Prime Intellect, AWS Bedrock/SageMaker, and a self-provisioned
EC2 spot instance running vLLM.

The retry loop, response parsing (content/reasoning channels, `<think>`
splitting, token guard), and parallel quiz evaluation live once in
`openai_compat.py`; each provider module is a thin configuration over it.
Select a provider with `INFERENCE_PROVIDER` (read at call time) and import
`query`/`evaluate` from `provider.py`. Result files round-trip through
`Marks.dump`/`Marks.load` (plain-mapping YAML; the loader also reads the
legacy `!!python/object`-tagged files).
