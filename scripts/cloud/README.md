# scripts/cloud/

Configuration for running SmolBench development in Claude Code cloud sessions
(claude.ai/code, `claude --cloud`, routines).

| File | Where it runs | Job |
| :- | :- | :- |
| `setup.sh` | Pasted into the environment dialog; runs once as root, then cached for about seven days | Make sure Python 3.12 exists; warm the wheel and tiktoken caches |
| `session_start.sh` | `SessionStart` hook in `.claude/settings.json`; runs on every cloud session start and resume | `uv sync --all-extras --frozen` into `.venv` in the fresh clone |

`session_start.sh` does nothing unless `CLAUDE_CODE_REMOTE=true`, so local
sessions are unaffected.

## Create the environment (one time)

An environment can only be created in the dialog; there is no CLI or API for
it, and `/remote-env` only selects an existing one.

1. Open [claude.ai/code](https://claude.ai/code) and select the cloud icon in
   the row above the message box.
2. Select **Add cloud environment** and fill in the four fields below.
3. Select **Create environment**.

### Name

```text
SmolBench
```

### Network access

Select **Custom**, check **Also include default list of common package
managers**, and enter these domains:

```text
huggingface.co
*.huggingface.co
hf.co
*.hf.co
openaipublic.blob.core.windows.net
```

The Trusted list already covers PyPI, GitHub and `*.amazonaws.com`. It does
not cover the Hugging Face hub, which `smolbench.evals.tokenization.HFTokenizer`
downloads each model's `tokenizer.json` from, or the tiktoken encoding host.

### Environment variables

```text
UV_CACHE_DIR=/opt/smolbench-cache/uv
TIKTOKEN_CACHE_DIR=/opt/smolbench-cache/tiktoken
UV_PYTHON_DOWNLOADS=never
```

The first two point every command in the session at the caches `setup.sh`
filled; without `TIKTOKEN_CACHE_DIR` the tests download the encodings again.
The third stops uv from trying to download an interpreter (see
[Limits and troubleshooting](#limits-and-troubleshooting)).

Live runs (EC2 provisioning, the S3 results store, gated Hugging Face models)
also need credentials. `notebooks/induction/keys.env` is untracked, so a cloud
clone does not have it; the driver reads the same names from the environment.
Add only the ones you need:

```text
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-west-2
SMOLBENCH_RESULTS_S3=s3://smolbench-results-414266451290
HF_TOKEN=
```

Anyone who can use the environment can read these values, so keep the
environment personal and use a narrowly scoped key. AWS SSO and other
browser logins do not work in a cloud session. The dialog's API credentials
cannot replace the AWS keys: they attach a header, and AWS requests are
signed in the client.

### Setup script

Paste the whole of [`setup.sh`](setup.sh). When you change that file, paste it
again; the dialog does not read the repository.

## Use the environment

- Browser, mobile, Desktop app: pick **SmolBench** in the environment selector.
- Terminal: run `/remote-env` once and pick **SmolBench**, then
  `claude --cloud "<task>"`. The session clones the GitHub remote at your
  current branch, so push first.

The hook loads from the branch the session clones. A branch without
`.claude/settings.json` and `scripts/cloud/` gets no `.venv`; ask Claude to run
`uv sync --all-extras --frozen` there.

## Check that it works

Start a session in the environment with this prompt:

```text
Run `bash scripts/cloud/session_start.sh`, then `.venv/bin/python -m pytest tests/ -q -rs`, then `id -u; which uv; uv python find 3.12; du -sh /opt/smolbench-cache/*; ls $TIKTOKEN_CACHE_DIR`. Report every output.
```

A good result has these properties:

- The hook prints `.venv ready (Python 3.12.x, ...)`.
- pytest reports every test passed and none skipped. Skips that say `tiktoken ... unavailable offline` mean
  the encoding host is missing from the allowed domains.
- `/opt/smolbench-cache/uv` holds several hundred MB and `$TIKTOKEN_CACHE_DIR`
  holds two files. A missing or near-empty directory means `setup.sh` failed
  without stopping the session (it always exits 0); the session still works,
  but each new one downloads every wheel again.

Dry run on a development machine (no root, caches in a scratch directory):

```bash
export SMOLBENCH_CLOUD_CACHE=/tmp/smolbench-cloud-dryrun
bash scripts/cloud/setup.sh
UV_CACHE_DIR=$SMOLBENCH_CLOUD_CACHE/uv TIKTOKEN_CACHE_DIR=$SMOLBENCH_CLOUD_CACHE/tiktoken \
    CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=$PWD bash scripts/cloud/session_start.sh
```

## Limits and troubleshooting

**`uv sync` finds no interpreter.** `requires-python` is `>=3.12,<3.13`.
`setup.sh` installs `python3.12` from apt when the image has none. uv's own
download is a GitHub release asset from a repository that is not attached to
the session, and the GitHub proxy rejects it with a 403; `UV_PYTHON_DOWNLOADS=never`
turns that into an immediate, readable error.

**The Lean toolchain is not installed.** The `lean` extra installs from PyPI,
but `elan`, Lean releases and the Mathlib cache come from hosts outside the
allowed list, and partly from GitHub release assets that the proxy rejects.
Deduction verification needs those added to `setup.sh` and to the allowed
domains, then a test on the VM.

**`GH_TOKEN` and `GITHUB_TOKEN` read `proxy-injected`.** `gh` and `git` work
through the GitHub proxy. A script that reads the variable gets the
placeholder, not a token. `git push` works only on the session's own branch.

**The setup script is not cached.** It must finish in about five minutes. A
dry run with a cold cache took 6.5 s on a development machine; allow a minute
or two behind the session proxy.

**Sessions with several repositories.** They do not read any repository's
`.claude/settings.json`, so the hook does not run; ask Claude to run
`session_start.sh`.

**Resources.** A session VM has about 4 vCPUs, 16 GB of RAM and 30 GB of
disk. It suits code, tests and analysis. GPU work stays on the EC2 fleet.

**Existing checkouts.** `.claude/settings.json` is tracked from the commit
that added this directory. A checkout that has its own untracked copy must
move those rules to `.claude/settings.local.json` before it can check out a
branch that tracks the file.
