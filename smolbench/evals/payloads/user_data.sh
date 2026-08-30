#!/bin/bash
set -euo pipefail
exec > /var/log/smolbench-bootstrap.log 2>&1
echo "smolbench bootstrap starting: $(date -u)"

# Absolute backstop before anything fallible: an OS halt terminates a
# one-time spot instance.
shutdown -h +@@MAX_LIFETIME_MIN@@ "smolbench max-lifetime backstop" || true

mkdir -p /opt/smolbench /opt/hf-cache /var/run/smolbench /etc/smolbench

# Model cache on instance-store NVMe (multi-GB/s; no instance store -> root
# volume, so size EC2_ROOT_VOLUME_GB for the checkpoints then). The DL AMI
# pre-assembles ALL NVMe into one LVM at /opt/dlami/nvme -- mkfs on a raw
# device then fails "in use" (bit a live p5): bind-mount it instead. The
# raw-device path is for AMIs that leave devices alone; by-id detection
# because lsblk MODEL renders underscores on some kernels (also bit a p5).
if mountpoint -q /opt/dlami/nvme; then
  mkdir -p /opt/dlami/nvme/smolbench-hf-cache
  mount --bind /opt/dlami/nvme/smolbench-hf-cache /opt/hf-cache
  echo "model cache bind-mounted on the AMI-managed instance store (/opt/dlami/nvme)"
else
  CACHE_DEV=$(ls /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage* 2>/dev/null | grep -v -- -part | head -1 || true)
  if [ -z "$CACHE_DEV" ]; then
    CACHE_DEV=$(lsblk -dno NAME,MODEL | tr '_' ' ' | grep -i "instance storage" | head -1 | awk '{print "/dev/"$1}' || true)
  fi
  if [ -n "$CACHE_DEV" ]; then
    echo "model cache on instance-store $CACHE_DEV"
    mkfs.ext4 -q -F "$CACHE_DEV" && mount -o noatime "$CACHE_DEV" /opt/hf-cache || echo "NVMe mount failed; cache stays on the root volume"
  else
    echo "no instance-store NVMe; model cache on the root volume"
  fi
fi
mkdir -p /opt/hf-cache/hub

# Parallelism for the S3 cache pulls/pushes (aws s3 sync).
aws configure set default.s3.max_concurrent_requests 64 || true

cat > /etc/smolbench/env <<'ENV_EOF'
CONTROL_TOKEN=@@CONTROL_TOKEN@@
VLLM_API_KEY=@@VLLM_API_KEY@@
HF_TOKEN=@@HF_TOKEN@@
VLLM_IMAGE=@@VLLM_IMAGE@@
S3_CACHE_URI=@@S3_CACHE_URI@@
IDLE_TIMEOUT_MIN=@@IDLE_TIMEOUT_MIN@@
STARTUP_GRACE_MIN=@@STARTUP_GRACE_MIN@@
SMOLBENCH_VLLM_PORT=@@VLLM_PORT@@
ENV_EOF
chmod 600 /etc/smolbench/env

cat > /opt/smolbench/agent.py <<'AGENT_EOF'
@@AGENT_PY@@
AGENT_EOF

cat > /opt/smolbench/watchdog.py <<'WATCHDOG_EOF'
@@WATCHDOG_PY@@
WATCHDOG_EOF

# Looping service, NOT a timer (see WATCHDOG_PY in payloads/__init__.py).
cat > /etc/systemd/system/smolbench-watchdog.service <<'UNIT_EOF'
[Unit]
Description=smolbench idle watchdog
After=docker.service

[Service]
EnvironmentFile=/etc/smolbench/env
ExecStart=/usr/bin/python3 /opt/smolbench/watchdog.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT_EOF

cat > /etc/systemd/system/smolbench-agent.service <<'UNIT_EOF'
[Unit]
Description=smolbench model-switcher agent
After=network-online.target docker.service
Wants=network-online.target

[Service]
EnvironmentFile=/etc/smolbench/env
ExecStart=/usr/bin/python3 /opt/smolbench/agent.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
# Watchdog first: even if the agent fails, idle termination still works.
systemctl enable --now smolbench-watchdog.service
systemctl enable --now smolbench-agent.service

# Pre-pull the (multi-GB) vLLM image so the first /serve does not block on it.
. /etc/smolbench/env
docker pull "$VLLM_IMAGE" > /var/log/smolbench-pull.log 2>&1 &

echo "smolbench bootstrap done: $(date -u)"
