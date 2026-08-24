"""Run a Bedrock-mantle live smoke test: list_models plus one seeded evaluate.

This script checks the cleanup-pass changes in smolbench/evals/aws.py:
METADATA_TIMEOUT_S on list_models, call-time formatting of
AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE, the get_model_context_length
env-or-default path after the _CONTEXT_LENGTHS removal, and the unchanged
inference round trip.
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
# Use gemma-3, not gemma-4: google.gemma-4-* returns a 401 error for this
# account ("Berm is not enabled"), even though it appears in the catalog.
preferred = [m for m in models if "qwen3-8b" in m or "mistral-small" in m.lower()
             or "gemma-3" in m.lower()]
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
