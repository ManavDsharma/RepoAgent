#!/usr/bin/env bash
# Resets target_repo/ to a clean checkout so each demo run starts from the
# same state (TECH_STACK.md: "Reset the container (or the mounted repo
# copy) between demo runs"). Discards any uncommitted agent edits.
#
# Usage: scripts/reset_target_repo.sh

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d target_repo/.git ]; then
    echo "target_repo/ is missing or not a git repo — re-clone it:"
    echo "  git clone https://github.com/testdrivenio/fastapi-crud-async.git target_repo"
    exit 1
fi

git -C target_repo reset --hard
git -C target_repo clean -fd
echo "target_repo/ reset to a clean checkout."
