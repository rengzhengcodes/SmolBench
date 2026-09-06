#!/usr/bin/env bash
# Launch ONE CPU box that runs scripts/deduction/trace_mathlib_ec2.sh unattended
# (LeanDojo-v2 trace of mathlib4 at $COMMIT -> S3), then shuts itself down.
#
# The runbook is shipped inside the cloud-init user-data (gzip+base64, ~7 KB of
# the 16 KB cap), so the box needs no repo checkout and no SSH. Progress and the
# final log land under $S3_PREFIX$COMMIT/ next to the tarball.
#
# Usage:
#   scripts/deduction/launch_trace_box.sh [--dry-run] [--force]
# Env: AWS credentials (ambient), EC2_REGION (default us-west-2),
#      TRACE_INSTANCE_TYPE (default r7i.8xlarge: 32 vCPU / 256 GiB -- RAM binds,
#      ~4 GiB per concurrent Lean process), TRACE_VOLUME_GB (default 300),
#      COMMIT (default 2ca39e62...), MAX_LIFETIME_MIN (default 720),
#      TRACE_GITHUB_TOKEN_SSM_PARAM (default
#      /smolbench/deduction/github_access_token) -- see SECRET MANAGEMENT below.
#
# --dry-run prints the launch plan and touches no AWS API that needs
# credentials (see the AMI note below); --force skips the idempotency check
# (see IDEMPOTENCY below) and launches unconditionally.
#
# SECRET MANAGEMENT (review finding: a prior revision of this script baked
# GITHUB_ACCESS_TOKEN's VALUE into the user-data and into a `su -c` argv --
# both are logged/inspectable, one in the EC2 console (user-data is NOT
# secret storage) and the other in process listings). This script now passes
# only the NAME of an SSM SecureString parameter through user-data; the
# instance resolves the VALUE itself, on the box, using its own IAM role, at
# the point trace_mathlib_ec2.sh actually needs it. Nothing this script emits
# -- stdout, the dry-run plan, or the user-data blob -- ever contains the
# token value.
#
#   IAM: $ROLE (EC2_INSTANCE_ROLE_NAME, default smolbench-ec2-role -- the same
#   role `smolbench/evals/_aws.py:ensure_instance_profile` provisions for the
#   general EC2 provider, but that helper does NOT currently attach an
#   ssm:GetParameter grant, so this is an extra one-time step) needs, scoped
#   to the parameter's ARN:
#     ssm:GetParameter on arn:aws:ssm:<region>:<account>:parameter$TRACE_GITHUB_TOKEN_SSM_PARAM
#     kms:Decrypt on the KMS key that encrypts it -- the account's default
#       alias/aws/ssm key, since the put-parameter command below does not
#       pass --kms-key-id
#
#   SEED THE PARAMETER (run once, from a workstation with admin credentials).
#   `--value file://...` reads the token from disk so it never appears as a
#   literal command-line argument -- not in shell history, and (unlike
#   `--value "$(cat token.txt)"`, which also avoids history but still puts
#   the decoded value briefly into this process's argv/`ps` output) not in
#   `ps` either:
#     aws ssm put-parameter --region us-west-2 --type SecureString \
#       --name /smolbench/deduction/github_access_token \
#       --value file:///path/to/token.txt --overwrite
#
# IDEMPOTENCY (review finding: run-instances had no check at all). The tag
# below is derived from $COMMIT, so re-running this script for a commit that
# already has a live box would silently double-bill a second ~$2/hr
# 32-vCPU instance racing the first one for the same S3 destination. Before
# launching, this script looks for an existing pending/running instance
# tagged $TAG and, if found, prints its id and exits without launching.
# `--force` skips that check (e.g. to intentionally relaunch after killing a
# stuck box by hand rather than waiting for it to terminate).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RUNBOOK="$HERE/trace_mathlib_ec2.sh"

# --------------------------------------------------------------------------
# Flags. Parsed before anything else touches the network, so --dry-run can
# short-circuit ahead of every AWS call it doesn't strictly need (see the AMI
# resolution below).
# --------------------------------------------------------------------------
DRY_RUN=0
FORCE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --force)   FORCE=1; shift ;;
        -h|--help) sed -n '2,60p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *)         echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

# --------------------------------------------------------------------------
# Config. REGION/ROLE/S3 knobs are re-derived here (not imported) because
# this is a standalone bash launcher meant to run on a laptop with no
# smolbench package installed and no repo checkout beyond this one file plus
# its runbook sibling -- see the file-level docstring of
# smolbench/evals/providers/ec2.py for why that constraint exists for the
# general EC2 provider too. Each default below names the Python constant it
# must stay in step with by hand.
# --------------------------------------------------------------------------
# PROVENANCE NOTE (flagged to the reviewing manager, not silently resolved):
# smolbench/evals/providers/ec2.py has no `EC2_REGION` knob at all -- its
# region env vars are `AWS_REGION` (default "us-east-1") and the multi-region
# hunt list `EC2_REGIONS`. This script's `EC2_REGION` name is this launcher's
# own invention and does not track either. The *default value* is still
# correct independently: smolbench/evals/README.md documents the results
# bucket below as living in us-west-2, which is what this box must be
# co-located with for a fast S3 upload of the trace tarball.
REGION="${EC2_REGION:-us-west-2}"
ITYPE="${TRACE_INSTANCE_TYPE:-r7i.8xlarge}"
VOL="${TRACE_VOLUME_GB:-300}"
COMMIT="${COMMIT:-2ca39e62989124794bd8405bb2e60805f63d37bc}"
LIFETIME="${MAX_LIFETIME_MIN:-720}"
# Bucket literal has no single Python owner: it is duplicated verbatim in
# scripts/deduction/lean_verify_rows.py (SPOOL_BUCKET) and
# scripts/results/audit_lean_pinning.py (BUCKET). Keep all three in sync by
# hand if it ever changes.
BUCKET="smolbench-results-414266451290"
# The "corpus/" leaf below has no Python owner either; its sibling
# "runs/" leaf (the re-collection's spool) is owned by
# smolbench/deduction/lean/runner.py:DEDUCTION_SPOOL_PREFIX
# ("deduction_postcutoff/runs"). Keep both under the same
# "deduction_postcutoff/" root if that ever changes.
S3_PREFIX="s3://$BUCKET/deduction_postcutoff/corpus/"
# Exact-name match with smolbench/evals/providers/ec2.py:EC2_INSTANCE_ROLE_NAME
# (same env var, same default) -- no mismatch here.
ROLE="${EC2_INSTANCE_ROLE_NAME:-smolbench-ec2-role}"
TAG="smolbench-trace-$COMMIT"
# Parameter NAME only -- never a value -- see SECRET MANAGEMENT above.
SSM_PARAM="${TRACE_GITHUB_TOKEN_SSM_PARAM:-/smolbench/deduction/github_access_token}"

# --------------------------------------------------------------------------
# AMI resolution. The one AWS call --dry-run cannot avoid without changing
# what gets printed for `ami=`: SSM's public alias always resolves to
# whatever Canonical shipped most recently, so there is no static fallback
# that would still describe a real launch. Skipped entirely under --dry-run
# (an unresolved placeholder is printed instead) so the plan needs no
# credentials at all.
# --------------------------------------------------------------------------
if (( DRY_RUN )); then
    AMI="<unresolved (skipped under --dry-run; see AMI resolution comment)>"
else
    AMI=$(aws ssm get-parameter --region "$REGION" \
          --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
          --query Parameter.Value --output text)
fi

PAYLOAD=$(gzip -9c "$RUNBOOK" | base64 -w0)

# --------------------------------------------------------------------------
# User-data. DELIBERATELY UNQUOTED heredoc (<<UD, not <<'UD'): this launcher
# must interpolate its own shell variables into the script that runs on the
# instance. The only things that heredoc interpolation may ever substitute
# are: $PAYLOAD (the gzipped+base64 runbook, not a secret), $COMMIT,
# $S3_PREFIX, $LIFETIME, $REGION and $SSM_PARAM (an SSM parameter NAME, which
# is not sensitive -- only the VALUE it names is). NEVER add a variable here
# that holds a secret VALUE (e.g. a token, a password); that is exactly the
# hole this revision closes -- see SECRET MANAGEMENT above. Anywhere the
# heredoc body needs a shell variable to be resolved ON THE INSTANCE instead
# (e.g. \$TOKEN below), the `$` is backslash-escaped so it survives this
# heredoc literally and only expands later, in the instance's own shell.
# --------------------------------------------------------------------------
USERDATA=$(cat <<UD
#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/smolbench-trace.log) 2>&1
shutdown -h +$LIFETIME   # hard backstop: nothing here may bill past $LIFETIME min
mkdir -p /mnt/data && chown ubuntu:ubuntu /mnt/data
echo '$PAYLOAD' | base64 -d | gunzip > /home/ubuntu/trace_mathlib_ec2.sh
chmod +x /home/ubuntu/trace_mathlib_ec2.sh
apt-get update -y && apt-get install -y awscli || snap install aws-cli --classic || true

# Resolve the GitHub token VALUE here, on the box, via this instance's own
# IAM role -- only the parameter NAME ($SSM_PARAM, baked in above) ever
# travels through user-data. This whole script runs under the tee -a to
# smolbench-trace.log above (uploaded to S3 at the bottom), so the token is
# NEVER echoed and NEVER covered by set -x past this point -- either would
# ship it to the results bucket in plaintext.
# NOTE: no backticks anywhere below this point, including in comments -- this
# heredoc is unquoted, so a markdown-style code-span backtick pair is
# evaluated as a REAL command substitution by the launcher while building
# this very string. Caught by testing --dry-run: an earlier draft's own
# comments literally executed "su ubuntu -c" and "|| true" as commands, in
# THIS launcher's shell, at build time -- not on the instance at all.
TOKEN=\$(aws ssm get-parameter --region $REGION --name '$SSM_PARAM' \\
  --with-decryption --query Parameter.Value --output text) || TOKEN=""
if [ -z "\$TOKEN" ] || [ "\$TOKEN" = "None" ]; then
  # Fail loud, not silent-fallback-to-unauthenticated: an unauthenticated
  # trace_mathlib_ec2.sh run would rate-limit itself into failure hours into
  # the trace instead of seconds into boot. awscli may itself be absent if
  # both install attempts above failed (silently, via their trailing
  # "|| true"), in which case the upload below is best-effort too.
  echo "ERROR: SSM parameter '$SSM_PARAM' is missing, empty, or unreadable." >&2
  echo "  Check that $ROLE has ssm:GetParameter + kms:Decrypt on it, and" >&2
  echo "  that it was seeded -- see launch_trace_box.sh's header comment." >&2
  aws s3 cp /var/log/smolbench-trace.log "$S3_PREFIX$COMMIT/trace.log" || true
  shutdown -h now
  exit 1
fi
# Deliberately \$TOKEN, not \$GITHUB_ACCESS_TOKEN interpolated by the
# launcher: this line must resolve ON THE INSTANCE, from the SSM fetch
# above, never at heredoc-build time in the launcher's own shell.
export GITHUB_ACCESS_TOKEN=\$TOKEN
# Plain "su ubuntu -c" (no --preserve-environment / no runuser): this DOES
# reset HOME to /home/ubuntu, which the runbook's own PATH export (it does
# "export PATH=\$HOME/.elan/bin:\$PATH") depends on for elan's toolchain
# shims -- --preserve-environment would instead leak HOME=/root from this
# root shell and break every resumed run. It does NOT reset arbitrary
# exported vars, so GITHUB_ACCESS_TOKEN reaches the child via the export
# above without being repeated -- and thus never appearing -- in the -c
# argv string itself.
su ubuntu -c "cd /home/ubuntu && ./trace_mathlib_ec2.sh --commit $COMMIT --s3-prefix $S3_PREFIX" \
  && echo TRACE_OK || echo TRACE_FAILED
aws s3 cp /var/log/smolbench-trace.log "$S3_PREFIX$COMMIT/trace.log" || true
shutdown -h now
UD
)
if (( DRY_RUN )); then
  echo "region=$REGION type=$ITYPE vol=${VOL}G ami=$AMI role=$ROLE tag=$TAG lifetime=${LIFETIME}min force=$FORCE ssm_param=$SSM_PARAM"
  echo "user-data bytes: $(printf '%s' "$USERDATA" | wc -c) (cap 16384)"
  exit 0
fi
[ "$(printf '%s' "$USERDATA" | wc -c)" -lt 16384 ] || { echo "user-data exceeds 16 KB" >&2; exit 1; }

# --------------------------------------------------------------------------
# Idempotency check (review finding: run-instances had none). $TAG is
# derived from $COMMIT, so a re-run for a commit that already has a live box
# would otherwise launch a second ~$2/hr 32-vCPU instance racing the first
# for the same S3 destination. The state filter matters: a long-terminated
# box from a PRIOR trace of this commit must not block a legitimate relaunch
# -- only pending/running instances count as "already in flight". --force
# bypasses this (e.g. after manually killing a stuck box, before it has
# finished terminating).
# --------------------------------------------------------------------------
if (( ! FORCE )); then
  EXISTING=$(aws ec2 describe-instances --region "$REGION" \
    --filters "Name=tag:Name,Values=$TAG" "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[0].Instances[0].InstanceId' --output text)
  if [ -n "$EXISTING" ] && [ "$EXISTING" != "None" ]; then
    echo "already in flight: $EXISTING (tag Name=$TAG); pass --force to launch anyway" >&2
    echo "$EXISTING"
    exit 0
  fi
fi

aws ec2 run-instances --region "$REGION" --image-id "$AMI" --instance-type "$ITYPE" \
  --iam-instance-profile "Name=$ROLE" \
  --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$VOL,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
  --instance-initiated-shutdown-behavior terminate \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG},{Key=smolbench:experiment,Value=trace-postcutoff}]" \
  --user-data "$USERDATA" \
  --query 'Instances[0].InstanceId' --output text
