#!/bin/bash
set -uo pipefail
exec > /var/log/smolbench-train-bootstrap.log 2>&1
echo "smolbench train bootstrap starting: $(date -u)"

# Absolute backstop: an OS halt terminates a one-time spot instance even if the
# driver disconnects. Sized generously for long trainings (see --max-lifetime).
shutdown -h +@@MAX_LIFETIME_MIN@@ "smolbench train max-lifetime backstop" || true

mkdir -p /opt/train
# Model cache + checkpoints on instance-store NVMe (multi-TB, multi-GB/s). The
# DL AMI pre-assembles all NVMe into one LVM at /opt/dlami/nvme -> bind-mount it;
# otherwise mkfs the first raw instance-store device. Root gp3 is small (checkpoints
# and the 400-810 GB base downloads must NOT land there).
if mountpoint -q /opt/dlami/nvme; then
  mkdir -p /opt/dlami/nvme/train
  mount --bind /opt/dlami/nvme/train /opt/train
  echo "train dir bind-mounted on AMI-managed instance store"
else
  CACHE_DEV=$(ls /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage* 2>/dev/null | grep -v -- -part | head -1 || true)
  if [ -z "$CACHE_DEV" ]; then
    CACHE_DEV=$(lsblk -dno NAME,MODEL | tr '_' ' ' | grep -i "instance storage" | head -1 | awk '{print "/dev/"$1}' || true)
  fi
  if [ -n "$CACHE_DEV" ]; then
    echo "train dir on instance-store $CACHE_DEV"
    mkfs.ext4 -q -F "$CACHE_DEV" && mount -o noatime "$CACHE_DEV" /opt/train || echo "NVMe mount failed; train dir on root volume"
  else
    echo "no instance-store NVMe; train dir on root volume"
  fi
fi
mkdir -p /opt/train/hf-cache /opt/train/out
chown -R ubuntu:ubuntu /opt/train
chmod 755 /opt/train
touch /opt/train/BOOTSTRAP_DONE
echo "smolbench train bootstrap done: $(date -u)"
