#!/usr/bin/env bash
# Launch ONE CPU box that runs scripts/deduction/trace_mathlib_ec2.sh unattended
# (LeanDojo-v2 trace of mathlib4 at $COMMIT -> S3), then shuts itself down.
#
# The runbook is shipped inside the cloud-init user-data (gzip+base64, ~7 KB of
# the 16 KB cap), so the box needs no repo checkout and no SSH. Progress and the
# final log land under $S3_PREFIX$COMMIT/ next to the tarball.
#
# Usage:
#   GITHUB_ACCESS_TOKEN=... scripts/deduction/launch_trace_box.sh [--dry-run]
# Env: AWS credentials (ambient), EC2_REGION (default us-west-2),
#      TRACE_INSTANCE_TYPE (default r7i.8xlarge: 32 vCPU / 256 GiB -- RAM binds,
#      ~4 GiB per concurrent Lean process), TRACE_VOLUME_GB (default 300),
#      COMMIT (default 2ca39e62...), MAX_LIFETIME_MIN (default 720).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RUNBOOK="$HERE/trace_mathlib_ec2.sh"
REGION="${EC2_REGION:-us-west-2}"
ITYPE="${TRACE_INSTANCE_TYPE:-r7i.8xlarge}"
VOL="${TRACE_VOLUME_GB:-300}"
COMMIT="${COMMIT:-2ca39e62989124794bd8405bb2e60805f63d37bc}"
LIFETIME="${MAX_LIFETIME_MIN:-720}"
BUCKET="smolbench-results-414266451290"
S3_PREFIX="s3://$BUCKET/deduction_postcutoff/corpus/"
ROLE="${EC2_INSTANCE_ROLE_NAME:-smolbench-ec2-role}"
TAG="smolbench-trace-$COMMIT"
: "${GITHUB_ACCESS_TOKEN:?set GITHUB_ACCESS_TOKEN (lean-dojo-v2 refuses to import without it)}"

AMI=$(aws ssm get-parameter --region "$REGION" \
      --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
      --query Parameter.Value --output text)
PAYLOAD=$(gzip -9c "$RUNBOOK" | base64 -w0)
USERDATA=$(cat <<UD
#!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/smolbench-trace.log) 2>&1
shutdown -h +$LIFETIME   # hard backstop: nothing here may bill past $LIFETIME min
mkdir -p /mnt/data && chown ubuntu:ubuntu /mnt/data
echo '$PAYLOAD' | base64 -d | gunzip > /home/ubuntu/trace_mathlib_ec2.sh
chmod +x /home/ubuntu/trace_mathlib_ec2.sh
apt-get update -y && apt-get install -y awscli || snap install aws-cli --classic || true
export GITHUB_ACCESS_TOKEN='$GITHUB_ACCESS_TOKEN'
su ubuntu -c "cd /home/ubuntu && GITHUB_ACCESS_TOKEN='$GITHUB_ACCESS_TOKEN' ./trace_mathlib_ec2.sh --commit $COMMIT --s3-prefix $S3_PREFIX" \
  && echo TRACE_OK || echo TRACE_FAILED
aws s3 cp /var/log/smolbench-trace.log "$S3_PREFIX$COMMIT/trace.log" || true
shutdown -h now
UD
)
if [ "${1:-}" = "--dry-run" ]; then
  echo "region=$REGION type=$ITYPE vol=${VOL}G ami=$AMI role=$ROLE tag=$TAG lifetime=${LIFETIME}min"
  echo "user-data bytes: $(printf '%s' "$USERDATA" | wc -c) (cap 16384)"
  exit 0
fi
[ "$(printf '%s' "$USERDATA" | wc -c)" -lt 16384 ] || { echo "user-data exceeds 16 KB" >&2; exit 1; }
aws ec2 run-instances --region "$REGION" --image-id "$AMI" --instance-type "$ITYPE" \
  --iam-instance-profile "Name=$ROLE" \
  --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":$VOL,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
  --instance-initiated-shutdown-behavior terminate \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG},{Key=smolbench:experiment,Value=trace-postcutoff}]" \
  --user-data "$USERDATA" \
  --query 'Instances[0].InstanceId' --output text
