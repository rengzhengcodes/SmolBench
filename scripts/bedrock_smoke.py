"""Bedrock-mantle live smoke: list_models + one small seeded evaluate.

Covers the cleanup-pass changes in smolbench/evals/aws.py: METADATA_TIMEOUT_S
on list_models, AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE call-time formatting,
_CONTEXT_LENGTHS removal (get_model_context_length env/default path), and the
untouched inference round trip.
"""
import os
import sys

sys.path.insert(0, "/workspace/SmolBench")

from aws_bedrock_token_generator import provide_token

token = provide_token(region="us-east-1")
os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
os.environ["AWS_REGION"] = "us-east-1"
os.environ["INFERENCE_PROVIDER"] = "aws"

from smolbench.evals import ToF, aws, provider

models = aws.list_models()
print(f"list_models: {len(models)} models; sample: {models[:5]}", flush=True)
assert len(models) > 10

ctx = aws.get_model_context_length("anything")
print(f"get_model_context_length default: {ctx}")
assert ctx == 200000

# Pick a small, cheap, non-reasoning chat model for the content check.
preferred = [m for m in models if "qwen3-8b" in m or "mistral-small" in m.lower()
             or "gemma" in m.lower()]
model = preferred[0] if preferred else models[0]
print(f"evaluate model: {model}")

quiz = (
    ToF(prompt="Is 7 a prime number? Answer with the single word True or False.", answer=True),
    ToF(prompt="Is 8 a prime number? Answer with the single word True or False.", answer=False),
)
marks = provider.evaluate(quiz, model, seed=1776, max_parallel=2, show_progress=False)
print(f"evaluate: correct={marks.correct} incorrect={marks.incorrect} invalid={marks.invalid}")
for m in marks.marks:
    print(f"  response={m.response!r} score={m.score} reasoning={'yes' if m.reasoning else 'no'}")
assert marks.correct + marks.incorrect + marks.invalid == 2
print("bedrock smoke: OK")
