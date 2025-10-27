#!/usr/bin/env bash
set -euo pipefail

# fix_layerdb.sh
# Safe helper to back up /var/lib/docker/image/overlay2/layerdb/tmp
# and move specified sha256 directories into a timestamped backup, then
# restart containerd/docker so Docker can re-create clean layerdb entries.
#
# Usage:
#   sudo ./scripts/fix_layerdb.sh HASH1 [HASH2 ...]
#   sudo ./scripts/fix_layerdb.sh --move-tmp-only
#   sudo ./scripts/fix_layerdb.sh --help
#
# Notes:
# - This script MOVES files to /root/docker-layerdb-backup-<TS>. It's non-destructive
#   because moved files can be restored by moving them back.
# - Provide the sha256 hashes that Docker reported as "file exists" to move
#   those target directories into the backup.

LB_DIR=/var/lib/docker/image/overlay2/layerdb
TMP_DIR="$LB_DIR/tmp"
SHA256_DIR="$LB_DIR/sha256"

if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root (sudo)"
  exit 2
fi

usage(){
  sed -n '1,120p' "$0" | sed -n '1,80p'
}

if [ "${1-}" = "--help" ]; then
  usage
  exit 0
fi

# timestamped backup dir
ts=$(date -u +%Y%m%dT%H%M%SZ)
backup="/root/docker-layerdb-backup-$ts"
mkdir -p "$backup"

echo "Backup directory: $backup"

# Stop services
echo "Stopping docker and containerd (if running)..."
systemctl stop docker || true
systemctl stop docker.socket || true
systemctl stop containerd || true

# Show what we'll move
echo

echo "Contents of layerdb/tmp:" 
ls -la "$TMP_DIR" || echo "(no tmp directory or empty)"

echo
# Move tmp contents into backup
if [ -d "$TMP_DIR" ] && [ "$(ls -A "$TMP_DIR" 2>/dev/null || true)" != "" ]; then
  echo "Moving tmp files to backup..."
  mkdir -p "$backup/tmp"
  mv "$TMP_DIR"/* "$backup/tmp/" || true
  echo "Moved tmp -> $backup/tmp"
else
  echo "No tmp files to move."
fi

# If args provided and not --move-tmp-only, treat them as hashes to move
if [ "${1-}" != "" ] && [ "${1-}" != "--move-tmp-only" ]; then
  echo
  echo "Moving specified sha256 directories into backup:"
  mkdir -p "$backup/sha256"
  for h in "$@"; do
    # skip options
    if [[ "$h" == --* ]]; then
      continue
    fi
    src="$SHA256_DIR/$h"
    if [ -d "$src" ]; then
      echo "  moving $src -> $backup/sha256/"
      mv "$src" "$backup/sha256/" || echo "  failed to move $src"
    else
      echo "  sha256/$h not found -> skipping"
    fi
  done
fi

# show backup summary
echo

echo "Backup summary (top-level):"
ls -la "$backup" || true

echo
# start services again
echo "Starting containerd and docker..."
systemctl start containerd
systemctl start docker
systemctl start docker.socket || true

echo

echo "Done. Check $backup for moved files."

echo "Next: pull images one-at-a-time. Example:" 
echo "  cd /opt/piazzati && docker compose pull node-exporter && docker compose pull prometheus && ..."

exit 0
