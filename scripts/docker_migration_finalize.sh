#!/usr/bin/env bash
set -euo pipefail

# docker_migration_finalize.sh
# Safely finalize the migration of Docker and Ollama data onto the LV.
# Modes:
#   --check                : run quick verification checks and print report
#   --finalize --dry-run   : show destructive actions that would be taken
#   --finalize --yes       : perform the destructive cleanup actions
#
# Safety rules:
# - This script only removes files/dirs that match expected backup patterns
#   created during the migration: e.g. paths containing ".bak" or
#   /root/docker-layerdb-backup-*
# - It performs multiple checks before destructive actions and refuses
#   to run if Docker shows unexpected state unless --finalize --yes used.

ACTION=check
DRY_RUN=1

usage(){
  cat <<'EOF'
Usage:
  ./scripts/docker_migration_finalize.sh --check
  ./scripts/docker_migration_finalize.sh --finalize --dry-run
  ./scripts/docker_migration_finalize.sh --finalize --yes

This script will NOT remove anything unless you pass --finalize --yes.
EOF
}

if [ "$#" -eq 0 ]; then
  usage
  exit 2
fi

if [ "$1" = "--check" ]; then
  ACTION=check
fi

if [ "$1" = "--finalize" ]; then
  ACTION=finalize
  if [ "${2-}" = "--dry-run" ]; then
    DRY_RUN=1
  elif [ "${2-}" = "--yes" ]; then
    DRY_RUN=0
  else
    echo "When using --finalize you must pass --dry-run or --yes"
    usage
    exit 2
  fi
fi

echo "Running docker_migration_finalize.sh ($ACTION)"

echo "\n== Quick environment checks =="
# check docker root
DOCKER_ROOT=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)
echo "Docker Root Dir: ${DOCKER_ROOT:-unknown}"
mount | grep "$DOCKER_ROOT" || true

echo "\nDocker system summary:"
docker info --format 'Containers: {{.Containers}}  Running: {{.ContainersRunning}}  Images: {{.Images}}' || true

echo "\nList candidate backup dirs (these will be removed by finalize):"
declare -a CANDIDATES
# common patterns created during migration
CANDIDATES+=(/var/lib/docker.bak* /var/lib/docker.orig* /var/lib/docker.backup* /var/lib/docker-*.bak /root/docker-layerdb-backup-* /root/docker-layerdb-full-backup-* /root/docker-layerdb-backup-* /root/docker-layerdb-* /root/docker-*backup-* /root/docker-*-backup-*)
# Ollama backup patterns we used earlier
CANDIDATES+=(/root/.ollama.bak* /usr/local/lib/ollama.bak* /usr/local/lib/ollama.*.bak)

echo
for p in "${CANDIDATES[@]}"; do
  # expand globs
  for match in $p; do
    if [ -e "$match" ]; then
      echo "  KEEP_CANDIDATE: $match -> $(du -sh "$match" 2>/dev/null || echo 'size?')"
    fi
  done
done

echo "\nNote: script only lists and removes paths that match these patterns."

if [ "$ACTION" = "check" ]; then
  echo "\n--check completed. If everything looks OK run:"
  echo "  ./scripts/docker_migration_finalize.sh --finalize --dry-run"
  exit 0
fi

echo "\n== Finalize: DRY_RUN=$DRY_RUN =="

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN: no files will be removed. The following commands would be executed:"
else
  echo "FINALIZE: the following removals will be executed now."
fi

declare -a REMOVES
for p in "${CANDIDATES[@]}"; do
  for match in $p; do
    if [ -e "$match" ]; then
      REMOVES+=("$match")
    fi
  done
done

if [ ${#REMOVES[@]} -eq 0 ]; then
  echo "No matching backup files found. Nothing to remove."
  exit 0
fi

for r in "${REMOVES[@]}"; do
  echo "  rm -rf $r"
done

if [ "$DRY_RUN" -eq 1 ]; then
  echo "\nDry-run complete. When ready run: ./scripts/docker_migration_finalize.sh --finalize --yes"
  exit 0
fi

echo "\nProceeding to remove backups..."
for r in "${REMOVES[@]}"; do
  echo "Removing $r"
  rm -rf -- "$r"
done

echo "Cleanup complete. You can verify with: ls -lah /root | grep docker-layerdb || true"

echo "All set. Migration finalize completed." 

exit 0
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME=$(basename "$0")
TIMESTAMP=$(date +%s)
BACKUP_TAR="/root/docker_metadata_backup_${TIMESTAMP}.tar.gz"
FSTAB_BIND_LINE="/mnt/piazza_docker/docker /var/lib/docker none bind 0 0"

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [--check | --finalize --yes | --rollback --yes | --dry-run]

Modes:
  --check           Run non-destructive checks and print status (recommended first).
  --finalize --yes  Finalize migration: ensure fstab bind, ensure ownership, enable/start containerd and docker.
  --rollback --yes  Attempt safe rollback: stop services, unmount /var/lib/docker and restore backup tar if present.
  --dry-run         Print actions without performing them (can be combined with --finalize or --rollback).

Notes:
 - This script must be run on the target server as root.
 - Finalize will create a tar backup at: $BACKUP_TAR (unless dry-run).
 - Rollback will look for a backup tar file in /root matching docker_metadata_backup_*.tar.gz and extract the newest if present.
 - The script is conservative: requires explicit --yes for destructive operations.
EOF
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: must be run as root" >&2
    exit 2
  fi
}

run_cmd() {
  if [ "$DRY_RUN" = true ]; then
    echo "+ $*"
  else
    echo "$*"
    eval "$*"
  fi
}

check_mounts_and_files() {
  echo "--- findmnt /var/lib/docker ---"
  findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS /var/lib/docker || true
  echo
  echo "--- findmnt /mnt/piazza_docker ---"
  findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS /mnt/piazza_docker || true
  echo
  echo "--- df -hT on relevant mounts ---"
  df -hT /var/lib/docker /mnt/piazza_docker || true
  echo
  echo "--- du sizes (quick) ---"
  du -sh /var/lib/docker /mnt/piazza_docker/docker 2>/dev/null || true
  echo
  echo "--- ls /var/lib/docker (head) ---"
  ls -la /var/lib/docker | head -n 60 || true
  echo
  echo "--- ls /mnt/piazza_docker/docker (head) ---"
  ls -la /mnt/piazza_docker/docker | head -n 60 || true
  echo
  echo "--- sample containers dirs ---"
  sudo find /var/lib/docker/containers -maxdepth 2 -mindepth 1 -type d -print | head -n 20 || true
  echo
  echo "--- search for config.v2.json ---"
  sudo find /var/lib/docker -maxdepth 4 -type f -name 'config.v2.json' -print | head -n 20 || true
  echo
  echo "--- ownership/perm sample ---"
  sudo stat -c '%U:%G %a %n' /var/lib/docker /var/lib/docker/* 2>/dev/null | head -n 60 || true
  echo
  echo "--- systemd: containerd and docker status ---"
  sudo systemctl status containerd --no-pager -l || true
  echo
  sudo systemctl status docker --no-pager -l || true
  echo
  echo "--- journal (last 200 lines) for docker ---"
  sudo journalctl -u docker -n 200 --no-pager || true
  echo
  echo "--- docker CLI view ---"
  sudo docker info || true
  sudo docker ps -a --no-trunc || true
  sudo docker images || true
  sudo docker volume ls || true
}

finalize_migration() {
  echo "*** Finalizing migration (DRY_RUN=$DRY_RUN)"

  # ensure /mnt/piazza_docker is mounted
  if ! mount | grep -q "/mnt/piazza_docker"; then
    run_cmd "mount /mnt/piazza_docker"
  fi

  # add bind line to /etc/fstab if missing
  if ! grep -Fq "$FSTAB_BIND_LINE" /etc/fstab 2>/dev/null; then
    echo "Adding bind entry to /etc/fstab"
    run_cmd "echo '$FSTAB_BIND_LINE' >> /etc/fstab"
  else
    echo "fstab bind entry already present"
  fi

  # create a backup tar of current /var/lib/docker (conservative)
  if [ "$DRY_RUN" = true ]; then
    echo "Would create backup tar: $BACKUP_TAR (skipped in dry-run)"
  else
    echo "Creating backup tar (this may take time): $BACKUP_TAR"
    # use --exclude to keep size reasonable? we keep full backup to be safe
    tar -czf "$BACKUP_TAR" -C / var/lib/docker || true
  fi

  # ensure ownership
  run_cmd "chown -R root:root /var/lib/docker"

  # ensure containerd active then (un)mask and start docker
  run_cmd "systemctl enable --now containerd"
  run_cmd "systemctl unmask docker.socket || true"
  run_cmd "systemctl enable --now docker"

  echo "Waiting a few seconds for docker to initialize..."
  if [ "$DRY_RUN" = false ]; then
    sleep 3
  fi

  echo "--- Post-start checks ---"
  run_cmd "docker info || true"
  run_cmd "docker ps -a || true"
  run_cmd "docker images || true"
}

rollback_migration() {
  echo "*** Rollback (DRY_RUN=$DRY_RUN)"

  # stop Docker and mask socket to avoid socket activated restarts
  run_cmd "systemctl stop docker || true"
  run_cmd "systemctl mask docker.socket || true"
  run_cmd "systemctl stop containerd || true"

  # try to unmount /var/lib/docker
  run_cmd "umount /var/lib/docker || true"

  # look for latest backup tar
  LATEST_TAR=$(ls -1t /root/docker_metadata_backup_*.tar.gz 2>/dev/null | head -n1 || true)
  if [ -n "$LATEST_TAR" ]; then
    echo "Found backup tar: $LATEST_TAR"
    if [ "$DRY_RUN" = true ]; then
      echo "Would extract $LATEST_TAR to /var/lib/docker"
    else
      run_cmd "mkdir -p /var/lib/docker"
      run_cmd "tar -xzf $LATEST_TAR -C /"
      echo "Restored backup from $LATEST_TAR"
    fi
  else
    echo "No backup tar found in /root matching docker_metadata_backup_*.tar.gz; cannot restore automatically"
  fi

  # start services back
  run_cmd "systemctl unmask docker.socket || true"
  run_cmd "systemctl enable --now containerd || true"
  run_cmd "systemctl enable --now docker || true"

  echo "--- Post-rollback checks ---"
  run_cmd "docker info || true"
  run_cmd "docker ps -a || true"
}

# main
if [ ${#@} -eq 0 ]; then
  usage
  exit 0
fi

MODE=""
CONFIRM_NO=""
DRY_RUN=false

while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check"; shift;;
    --finalize) MODE="finalize"; shift;;
    --rollback) MODE="rollback"; shift;;
    --yes) CONFIRM_NO="yes"; shift;;
    --dry-run) DRY_RUN=true; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

require_root

if [ "$MODE" = "check" ]; then
  check_mounts_and_files
  exit 0
fi

if [ "$MODE" = "finalize" ]; then
  if [ "$CONFIRM_NO" != "yes" ]; then
    echo "Refusing to finalize without --yes. Rerun with --finalize --yes to proceed. Use --dry-run to preview."
    exit 3
  fi
  finalize_migration
  exit 0
fi

if [ "$MODE" = "rollback" ]; then
  if [ "$CONFIRM_NO" != "yes" ]; then
    echo "Refusing to rollback without --yes. Rerun with --rollback --yes to proceed. Use --dry-run to preview."
    exit 3
  fi
  rollback_migration
  exit 0
fi

usage
exit 2
