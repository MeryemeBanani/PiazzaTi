#!/bin/bash
set -euo pipefail

echo "=== lsblk ==="
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT || true
echo

echo "=== blkid ==="
blkid || true
echo

echo "=== file -s /dev/sdb ==="
file -s /dev/sdb || true
echo

echo "=== df -h / ==="
df -h / || true
echo

echo "=== df -i / ==="
df -i / || true
echo

echo "=== du summary ==="
for d in /var/lib/docker/overlay2 /var/lib/docker /root/.ollama /var/log /usr /opt /home; do
  if [ -d \"$d\" ]; then du -s -BM \"$d\" 2>/dev/null || true; fi
done
echo

echo "=== docker info (truncated) ==="
docker info 2>/dev/null | sed -n '1,120p' || true
