"""Run a staged live smoke test of the smolbench EC2 provider.

Run this script as `ec2_lifecycle_smoke.py <step>`. Set these environment
variables before you start the script: EC2_EXPERIMENT_TAG, EC2_STATE_FILE,
EC2_INSTANCE_TYPES, EC2_REGIONS, EC2_ROOT_VOLUME_GB, EC2_IDLE_TIMEOUT_MIN.
The provisioning code reads these variables at import time, so you must
set them before the script starts.
"""
import json
import os
import sys
import time

sys.path.insert(0, "/workspace/SmolBench")

STEP = sys.argv[1]
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


from smolbench.evals import ec2  # noqa: E402  (the shell already set env vars)

log(f"tag={ec2.EC2_EXPERIMENT_TAG} types={ec2.EC2_INSTANCE_TYPES} "
    f"regions={ec2.EC2_REGIONS} state_file={ec2._state_path()}")

if STEP == "provision":
    state = ec2.provision_spot_instance()
    log(f"provisioned: id={state['instance_id']} type={state['instance_type']} "
        f"region={state['region']} ip={state['public_ip']}")
elif STEP == "serve_eval":
    os.environ["INFERENCE_PROVIDER"] = "ec2"
    from smolbench.evals import provider
    from smolbench.evals import ToF
    quiz = (
        ToF(prompt="Is 7 a prime number? Answer True or False only.", answer=True),
        ToF(prompt="Is 8 a prime number? Answer True or False only.", answer=False),
        ToF(prompt="Is 11 a prime number? Answer True or False only.", answer=True),
        ToF(prompt="Is 15 a prime number? Answer True or False only.", answer=False),
    )
    with ec2.serve_model("qwen2.5-1.5b"):
        log("model healthy; running 4-question seeded evaluate")
        marks = provider.evaluate(quiz, "qwen2.5-1.5b", seed=1776,
                                  max_parallel=2, show_progress=False)
    log(f"evaluate done: correct={marks.correct} incorrect={marks.incorrect} "
        f"invalid={marks.invalid} (model={marks.model})")
    assert marks.correct + marks.incorrect + marks.invalid == 4
elif STEP == "reattach":
    t = time.time()
    state = ec2.provision_spot_instance()
    dt = time.time() - t
    log(f"reattach returned in {dt:.1f}s: id={state['instance_id']}")
    assert dt < 60, f"reattach took {dt:.1f}s -- state-file branch not hit?"
elif STEP == "recover":
    sf = ec2._state_path()
    saved = json.loads(sf.read_text())
    sf.unlink()
    log(f"state file {sf} deleted; re-provisioning (tag-recovery branch)")
    state = ec2.provision_spot_instance()
    log(f"recovered: id={state['instance_id']} (expected {saved['instance_id']})")
    assert state["instance_id"] == saved["instance_id"], "recovered a different instance!"
elif STEP == "shutdown":
    ec2.shutdown_instance()
    log("shutdown_instance() returned")
else:
    raise SystemExit(f"unknown step {STEP}")
log(f"step {STEP}: OK")
