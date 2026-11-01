#!/bin/bash
# Installed separately so an update cannot replace its running updater.
set -euo pipefail
cd /home/ubuntu/src/ruta
exec 9>/home/ubuntu/.ruta-update.lock
flock -n 9 || exit 0
export RUTA_SECRET_KEY=deployment-check-only
export GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=15'
git fetch origin +refs/heads/deploy-ready:refs/remotes/origin/deploy-ready
old=$(git rev-parse HEAD)
next=$(git rev-parse origin/deploy-ready)
[[ "$old" != "$next" ]] || exit 0
git merge-base --is-ancestor "$old" "$next"
# Never overwrite edits to application code or unknown files.
[[ -z "$(git status --porcelain --untracked-files=all -- . ':!ruta/ruta/static')" ]] || { echo 'Local changes; update deferred'; exit 1; }
# Dependency changes require a maintenance install before automatic deployment.
git diff --quiet "$old" "$next" -- requirements.txt || { echo 'Dependencies changed; install manually'; exit 1; }
stage=$(mktemp -d)
paused=0
cleanup() {
    rm -rf "$stage"
    if [[ "$paused" == 1 ]]; then sudo -n systemctl start ruta_scheduler.timer; fi
}
trap cleanup EXIT
git archive "$next" | tar -x -C "$stage"
(cd "$stage/ruta" && python3 manage.py test irrigate --noinput)
# No automatic schema changes: preserve the live database and require maintenance.
(cd "$stage/ruta" && RUTA_DATABASE_PATH=/home/ubuntu/src/ruta/ruta/db.sqlite3 python3 manage.py migrate --check)
sudo -n systemctl stop ruta_scheduler.timer
paused=1
if systemctl is-active --quiet ruta_scheduler.service; then
    echo 'Watering job active; update deferred'
    exit 0
fi
# Save generated output before the initial transition away from tracked assets.
mkdir -p /home/ubuntu/.ruta-backups
if git ls-files ruta/ruta/static | read -r _; then
    tar -czf "/home/ubuntu/.ruta-backups/static-$old.tar.gz" ruta/ruta/static
    git restore -- ruta/ruta/static
fi
apply_static() {
    (cd ruta && python3 manage.py collectstatic --noinput --clear) || return 1
    sudo -n systemctl reload ruta.service || return 1
    for attempt in {1..15}; do
        if curl --fail --silent http://127.0.0.1:8000/login/ >/dev/null &&
           curl --fail --silent http://127.0.0.1:8000/static/irrigate/css/dashboard.css | grep -q dashboard-shell; then
            return 0
        fi
        sleep 1
    done
    return 1
}
git merge --ff-only "$next"
if ! apply_static; then
    echo 'Health check failed; restoring previous commit'
    git reset --hard "$old"
    apply_static || true
    exit 1
fi
echo "Deployed $next"
