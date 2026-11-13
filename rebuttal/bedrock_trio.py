"""Run the induction and Horn studies on Amazon Bedrock for three ladder models.

The notebook ``bedrock_trio.ipynb`` drives this module. Everything here reuses the
existing run code: ``providers.aws`` (bedrock-mantle, OpenAI-compatible) sends the
requests, ``ReplicateHarness`` and ``notebooks/induction/run_study.make_quizzes`` run
the induction study, and ``scripts/deduction/horn/sweep.py`` runs and scores the Horn
cells. This module adds only what Bedrock needs on top: the model roster, a per-model
endpoint switch, a results store with the released-results layout, and a check that
every response was reasoned.
"""

from __future__ import annotations

import collections
import contextlib
import importlib.util
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Iterator, Mapping, Optional, Sequence

import requests

from smolbench.evals import Marks
from smolbench.evals.results_store import ReplicateAddress, ResultsStore, format_run_ts

REPO_ROOT = Path(__file__).resolve().parents[1]
REBUTTAL_DIR = REPO_ROOT / "rebuttal"
#: Results kept in the repo: induction YAMLs and Horn rows.
RESULTS_DIR = REBUTTAL_DIR / "results"
#: Rendered Horn rungs; deterministic and digest-checked, so not committed.
RUNGS_DIR = REBUTTAL_DIR / "rungs"

MANTLE_URL = "https://bedrock-mantle.{region}.api.aws{path}"
DEFAULT_REGION = "us-east-1"
#: The three induction arms of the ICLR table (``zero`` is left out, as there).
INDUCTION_ARMS = ("intens", "noise_intens", "extens")
HORN_ARMS = ("lem", "pad", "disc", "both")
HORN_TEMPERATURE = 0.7


@dataclass(frozen=True)
class BedrockModel:
    """One model of the trio, keyed by its ICLR roster key."""

    #: Roster key in both ``iclr.json`` files and ``EC2_DEPLOY_SPECS``.
    key: str
    #: Bedrock model id; ``None`` until resolved from ``GET /models``.
    bedrock_id: Optional[str]
    #: Base path on bedrock-mantle, up to ``/chat/completions``.
    base_path: str
    #: Bedrock's output-token cap for the model (reasoning included).
    max_tokens: int
    #: Context window from the Bedrock model card.
    context_length: int
    #: Request fields that switch reasoning on, tried in order by ``pick_reasoning_args``.
    reasoning_candidates: tuple[dict, ...]
    #: Harness tag (``smolbench/evals/study_config.toml``).
    tag: str
    #: Substrings that identify the id in a ``GET /models`` listing.
    id_hints: tuple[str, ...] = field(default=())


# Output caps and context windows come from the Bedrock model cards. Gemma 4's card gives
# no output cap, so it gets Nemotron's 32K; the probe reports a lower one if Bedrock
# enforces it. DeepSeek and Nemotron take ``reasoning_effort`` (the ICLR Horn Bedrock
# rows used exactly that); for Gemma 4 the working spelling is found by the probe.
TRIO: dict[str, BedrockModel] = {
    m.key: m
    for m in (
        BedrockModel(
            key="gemma-4-31b",
            bedrock_id="google.gemma-4-31b",
            base_path="/openai/v1",
            max_tokens=32768,
            context_length=262144,
            reasoning_candidates=(
                {"reasoning_effort": "high"},
                {"chat_template_kwargs": {"enable_thinking": True}},
            ),
            tag="gemma4_31b",
        ),
        BedrockModel(
            key="nemotron-3-super-120b-a12b",
            bedrock_id="nvidia.nemotron-super-3-120b",
            base_path="/v1",
            max_tokens=32768,
            context_length=262144,
            reasoning_candidates=({"reasoning_effort": "high"},),
            tag="nemo3_120b",
        ),
        BedrockModel(
            key="deepseek-v3.1",
            bedrock_id=None,
            base_path="/v1",
            max_tokens=8192,
            context_length=131072,
            reasoning_candidates=(
                {"reasoning_effort": "high"},
                {"chat_template_kwargs": {"thinking": True}},
            ),
            tag="ds_v31",
            id_hints=("deepseek", "v3"),
        ),
    )
}


# --------------------------------------------------------------------------- auth


def mint_token(region: str = DEFAULT_REGION) -> str:
    """Set ``AWS_BEARER_TOKEN_BEDROCK`` to a short-term token minted from the AWS profile.

    An already-set token is kept, so a long-term key or a token minted elsewhere wins.

    Parameters
    ----------
    region : str
        Region the token is minted for.

    Returns
    -------
    str
        The token in effect.
    """
    token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    if not token:
        from aws_bedrock_token_generator import (  # pylint: disable=import-outside-toplevel
            provide_token,
        )

        token = provide_token(region=region)
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
    return token


def base_url(model: BedrockModel, region: str) -> str:
    """The model's bedrock-mantle base URL (``.../v1`` or ``.../openai/v1``)."""
    return MANTLE_URL.format(region=region, path=model.base_path)


def list_mantle_models(region: str, path: str = "/v1") -> list[str]:
    """Model ids from ``GET /models`` on one bedrock-mantle path."""
    resp = requests.get(
        f"{MANTLE_URL.format(region=region, path=path)}/models",
        headers={"Authorization": f"Bearer {os.environ['AWS_BEARER_TOKEN_BEDROCK']}"},
        timeout=60,
    )
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("data", [])]


def resolve_ids(
    listing: Sequence[str], trio: Mapping[str, BedrockModel] = TRIO
) -> dict[str, BedrockModel]:
    """Check every known id against a listing and fill the ones left ``None``.

    Parameters
    ----------
    listing : Sequence[str]
        Ids from ``GET /models`` (all paths combined).
    trio : Mapping[str, BedrockModel]
        The roster.

    Returns
    -------
    dict[str, BedrockModel]
        The roster with every ``bedrock_id`` set.

    Raises
    ------
    LookupError
        If a known id is not listed, or the hints match no id or more than one.
    """
    out = {}
    for key, model in trio.items():
        if model.bedrock_id is not None:
            if model.bedrock_id not in listing:
                raise LookupError(f"{key}: {model.bedrock_id!r} not listed: {sorted(listing)}")
            out[key] = model
            continue
        hits = [i for i in listing if all(h in i.lower() for h in model.id_hints)]
        # DeepSeek V3.1 is spelled v3.1, v3-1 or v3-v1; V3.2 must not match.
        hits = [i for i in hits if not any(f"v3{s}2" in i.lower() for s in ".-")]
        if len(hits) != 1:
            raise LookupError(f"{key}: hints {model.id_hints} match {hits}: {sorted(listing)}")
        out[key] = replace(model, bedrock_id=hits[0])
    return out


@contextlib.contextmanager
def use_model(model: BedrockModel, region: str) -> Iterator[None]:
    """Route ``smolbench.evals.provider`` calls to this model on bedrock-mantle.

    ``providers.aws`` reads these variables when each request is made, so the roster key
    stays the model name everywhere else (harness tags, tokenizer, result paths) while
    the request body carries the Bedrock id.
    """
    if model.bedrock_id is None:
        raise ValueError(f"{model.key}: resolve the Bedrock id first (resolve_ids)")
    env = {
        "INFERENCE_PROVIDER": "aws",
        "AWS_REGION": region,
        "AWS_INFERENCE_BASE_URL": base_url(model, region),
        "AWS_INFERENCE_BODY_MODEL": model.bedrock_id,
        "AWS_BEDROCK_CONTEXT_LENGTH": str(model.context_length),
    }
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# ---------------------------------------------------------------------- reasoning


def reasoned(reasoning: Optional[str]) -> bool:
    """Whether a response carried reasoning.

    ``ChatClient`` fills ``reasoning`` from ``reasoning_content``/``reasoning`` or, with
    no reasoning channel, from the text before ``</think>``, so this one field covers
    all three ways a server can return it.
    """
    return bool(reasoning and reasoning.strip())


def probe(model: BedrockModel, region: str, extra_args: dict, seed: int = 0) -> dict:
    """Send one short request and report whether it was reasoned.

    Parameters
    ----------
    model : BedrockModel
        Model to probe.
    region : str
        Bedrock region.
    extra_args : dict
        Reasoning fields to send.
    seed : int
        Decoding seed.

    Returns
    -------
    dict
        ``ok``, ``reasoned``, ``finish_reason``, token counts, and the error if any.
    """
    from smolbench.evals import provider  # pylint: disable=import-outside-toplevel

    with use_model(model, region):
        try:
            result = provider.complete(
                "What is 17 * 23? Answer with the integer only.",
                model.key,
                seed,
                extra_args={"max_completion_tokens": min(model.max_tokens, 4096)} | extra_args,
                request_timeout=600,
                max_retries=2,
            )
        except Exception as err:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            return {"ok": False, "reasoned": False, "error": f"{type(err).__name__}: {err}"[:600]}
    return {
        "ok": True,
        "reasoned": reasoned(result.reasoning),
        "content": result.content[:80],
        "reasoning_chars": len(result.reasoning or ""),
        "finish_reason": result.finish_reason,
        "completion_tokens": result.completion_tokens,
    }


def pick_reasoning_args(model: BedrockModel, region: str) -> tuple[dict, list[dict]]:
    """The first of the model's reasoning candidates that yields a reasoned answer.

    Returns
    -------
    tuple[dict, list[dict]]
        The chosen fields and every probe made.

    Raises
    ------
    RuntimeError
        If no candidate yields reasoning: the study must not run unreasoned.
    """
    tried = []
    for args in model.reasoning_candidates:
        result = probe(model, region, args) | {"args": args}
        tried.append(result)
        if result["reasoned"]:
            return args, tried
    raise RuntimeError(f"{model.key}: no reasoning candidate worked: {tried}")


# ---------------------------------------------------------------------- induction


@dataclass
class ReproLayoutStore(ResultsStore):
    """Local results store in the released-results layout.

    Writes ``<root>/induction/<model>/seed=<seed>/<arm>--<stamp>.yaml``, which
    ``smolbench.induction.repro`` (``select_runs``, ``load_cells``, ``report``) reads.
    The built-in ``LocalResultsStore`` uses a different layout.
    """

    root: Path

    def _seed_dir(self, model: str, seed: int) -> Path:
        return self.root / "induction" / model / f"seed={seed}"

    def _runs(self, addr: ReplicateAddress) -> list[Path]:
        if addr.model is None:
            return []
        return sorted(self._seed_dir(addr.model, addr.seed).glob(f"{addr.info}--*.yaml"))

    def exists(self, addr: ReplicateAddress) -> bool:
        return bool(self._runs(addr))

    def dump_marks(self, marks: Marks, addr: ReplicateAddress, run_ts: datetime) -> None:
        if addr.model is None:
            raise ValueError(f"refusing to write {addr!r}: the layout is keyed by model")
        path = self._seed_dir(addr.model, addr.seed) / f"{addr.info}--{format_run_ts(run_ts)}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(marks.dumps(), encoding="utf-8")

    def load_marks(self, addr: ReplicateAddress) -> Marks:
        runs = self._runs(addr)
        if not runs:
            raise FileNotFoundError(f"no run for {addr!r} under {self.root}")
        return Marks.loads(runs[0].read_text(encoding="utf-8"))

    def list_seeds(self, model: Optional[str], tag: str, info: str) -> list[int]:
        if model is None:
            return []
        base = self.root / "induction" / model
        return sorted(
            int(d.name.removeprefix("seed="))
            for d in base.glob("seed=*")
            if any(d.glob(f"{info}--*.yaml"))
        )

    def supersede_all(self, addr: ReplicateAddress, reason: str) -> int:
        raise NotImplementedError("re-collection is not supported here; delete the files")

    def describe(self) -> str:
        return f"local {self.root}/induction"


def load_run_study() -> ModuleType:
    """Import ``notebooks/induction/run_study.py`` (not a package) for its quiz factory."""
    name = "smolbench_run_study"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "notebooks" / "induction" / "run_study.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def induction_harness(
    models: Sequence[BedrockModel], seeds: Sequence[int], results_dir: Path = RESULTS_DIR
):
    """A ``ReplicateHarness`` over the three ICLR arms, writing the released layout.

    Parameters
    ----------
    models : Sequence[BedrockModel]
        Models the harness may run.
    seeds : Sequence[int]
        Replicate seeds (ICLR: 0-29); each is also the decoding seed.
    results_dir : Path
        Results root; the YAMLs go under ``<results_dir>/induction/``.

    Returns
    -------
    ReplicateHarness
        Harness whose store is a ``ReproLayoutStore``.
    """
    from smolbench.evals.replicates import (  # pylint: disable=import-outside-toplevel
        ReplicateHarness,
    )

    harness = ReplicateHarness(
        results_dir=results_dir / "induction",
        archetype_tags={m.key: m.tag for m in models},
        make_quizzes=load_run_study().make_quizzes,
        seeds=tuple(seeds),
        info_types=INDUCTION_ARMS,
    )
    # ``store`` is a cached_property; set it before first use.
    harness.__dict__["store"] = ReproLayoutStore(results_dir / "induction")
    return harness


def run_induction(
    harness,
    model: BedrockModel,
    region: str,
    reasoning_args: dict,
    max_parallel: int = 8,
) -> None:
    """Collect every outstanding induction replicate of one model.

    Temperature is not sent: the ICLR induction runs used the server default.
    """
    extra_args = {"max_completion_tokens": model.max_tokens} | reasoning_args
    with use_model(model, region):
        harness.run_replicates(
            model.key,
            extra_args=extra_args,
            max_parallel=max_parallel,
            request_timeout=max(600, model.max_tokens // 10),
            server_config={
                "provider": f"bedrock-mantle:{region}",
                "bedrock_id": model.bedrock_id,
                "extra_args": extra_args,
            },
        )


def released_queries(key: str, seed: int = 0) -> dict[str, list[str]]:
    """The prompts of one released ICLR replicate per arm, fetched anonymously.

    Returns
    -------
    dict[str, list[str]]
        Arm -> its 9 ``marks[i].query`` strings (empty if the field is absent).
    """
    import boto3  # pylint: disable=import-outside-toplevel
    import yaml  # pylint: disable=import-outside-toplevel
    from botocore import UNSIGNED  # pylint: disable=import-outside-toplevel
    from botocore.config import Config  # pylint: disable=import-outside-toplevel

    from smolbench.induction import repro  # pylint: disable=import-outside-toplevel

    proto = repro.load_protocol()
    s3 = boto3.client("s3", region_name=proto["region"], config=Config(signature_version=UNSIGNED))
    prefix = f"{proto['prefix']}/{key}/seed={seed}/"
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=proto["bucket"], Prefix=prefix).get("Contents", [])]
    out: dict[str, list[str]] = {}
    for arm in INDUCTION_ARMS:
        runs = sorted(k for k in keys if k.rsplit("/", 1)[1].startswith(f"{arm}--") and k.endswith(".yaml"))
        if not runs:
            continue
        body = s3.get_object(Bucket=proto["bucket"], Key=runs[0])["Body"].read()
        marks = yaml.load(body, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))["marks"]
        out[arm] = [m.get("query", "") for m in marks]
    return out


def induction_reasoning_report(results_dir: Path = RESULTS_DIR) -> dict[tuple[str, str], dict]:
    """Per (model, arm): replicates, marks, unreasoned marks and ungradable (null) marks."""
    import yaml  # pylint: disable=import-outside-toplevel

    from smolbench.induction import repro  # pylint: disable=import-outside-toplevel

    out: dict[tuple[str, str], dict] = collections.defaultdict(collections.Counter)
    runs = repro.select_runs(results_dir / "induction", INDUCTION_ARMS)
    for (model, _seed, arm), path in sorted(runs.items()):
        marks = yaml.safe_load(path.read_text(encoding="utf-8"))["marks"]
        c = out[(model, arm)]
        c["replicates"] += 1
        c["marks"] += len(marks)
        c["unreasoned"] += sum(not reasoned(m.get("reasoning")) for m in marks)
        c["null_score"] += sum(m.get("score") is None for m in marks)
        for m in marks:
            c[f"compliance:{m.get('compliance')}"] += 1
    return {k: dict(v) for k, v in out.items()}


# --------------------------------------------------------------------------- horn


def load_sweep() -> ModuleType:
    """Import ``scripts/deduction/horn/sweep.py`` (not a package) for its cell runner."""
    name = "smolbench_horn_sweep"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "scripts" / "deduction" / "horn" / "sweep.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def horn_m(key: str) -> int:
    """The model's ICLR chain length."""
    from smolbench.deduction.horn import repro  # pylint: disable=import-outside-toplevel

    return int(repro.model_entry(key)["m"])


def render_horn_rung(m: int, seeds: Sequence[int], rungs_dir: Path = RUNGS_DIR) -> Path:
    """Render rung ``m<m>`` for ``seeds`` (skipping seeds already there) and check it
    against the ICLR digests.

    Raises
    ------
    RuntimeError
        If a seed differs from the ICLR rung.
    """
    from smolbench.deduction.horn import repro  # pylint: disable=import-outside-toplevel

    rung = rungs_dir / f"m{m}"
    todo = [s for s in seeds if not (rung / f"s{s:04d}" / "theory.json").exists()]
    if todo:
        repro.render_rung(rung, m, todo)
    problems = repro.verify_rung(rung, m, list(seeds))
    if problems:
        raise RuntimeError(f"rung m{m} differs from the ICLR rung: {problems[:5]}")
    return rung


def horn_rows_path(key: str, results_dir: Path = RESULTS_DIR) -> Path:
    """Rows file for one model."""
    return results_dir / "horn" / f"{key}.jsonl"


def run_horn(  # pylint: disable=too-many-arguments,too-many-locals
    model: BedrockModel,
    region: str,
    reasoning_args: dict,
    rung: Path,
    seeds: Sequence[int],
    reps: int,
    concurrency: int = 8,
    out: Optional[Path] = None,
) -> list[dict]:
    """Run and score every outstanding Horn cell of one model with ``sweep.run_cell``.

    The decoding seed is the replicate index and the temperature is 0.7, as in the ICLR
    protocol. Rows already in ``out`` (other than ``exception`` rows) are skipped.

    Returns
    -------
    list[dict]
        The rows written by this call.
    """
    from smolbench.evals.openai_compat import (  # pylint: disable=import-outside-toplevel
        ChatClient,
    )

    if model.bedrock_id is None:
        raise ValueError(f"{model.key}: resolve the Bedrock id first (resolve_ids)")
    sweep = load_sweep()
    out = out or horn_rows_path(model.key)
    out.parent.mkdir(parents=True, exist_ok=True)
    st = sweep.Settings(
        model=model.bedrock_id,
        spec_key=model.key,
        extra_args={"max_tokens": model.max_tokens, "temperature": HORN_TEMPERATURE}
        | reasoning_args,
        context_length=model.context_length,
        timeout=max(900, model.max_tokens // 10),
        max_retries=8,
        system_prompt=None,
    )
    url = f"{base_url(model, region)}/chat/completions"
    client = ChatClient(
        name="horn-bedrock",
        env_prefix="HORN",
        connection=lambda _: (url, os.environ["AWS_BEARER_TOKEN_BEDROCK"]),
        context_length=lambda _: model.context_length,
        retry_backoff_s=30,
        read_timeout_s=st.timeout,
    )
    fh = sweep.lock_rows(out)
    if fh is None:
        raise RuntimeError(f"{out} is locked by another sweep")
    done = sweep.done_keys(out)
    cells = sweep.cells_in(rung, list(HORN_ARMS), list(seeds), reps)
    todo = [c for c in cells if (st.model,) + c.key not in done]
    rows: list[dict] = []
    with fh, ThreadPoolExecutor(concurrency) as pool:
        futs = [pool.submit(sweep.run_cell, client, c, st) for c in todo]
        for fut in as_completed(futs):
            row = fut.result() | {"provider": f"bedrock-mantle:{region}"}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            rows.append(row)
    return rows


def horn_breakdown(paths: Sequence[Path]) -> dict[tuple[str, str], dict]:
    """Per (model, arm): rows, verdicts, finish reasons and unreasoned rows (exceptions apart)."""
    out: dict[tuple[str, str], dict] = collections.defaultdict(collections.Counter)
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            c = out[(r.get("spec_key") or r["model"], r["arm"])]
            c["rows"] += 1
            c[f"verdict:{r['verdict']}"] += 1
            if r["verdict"] != "exception":
                c[f"finish:{r.get('finish_reason')}"] += 1
                c["unreasoned"] += not reasoned(r.get("reasoning"))
    return {k: dict(v) for k, v in out.items()}
