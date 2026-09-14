#!/bin/zsh
set -euo pipefail

project_root="$(git rev-parse --show-toplevel)"
cd "$project_root"

message="${1:-Verified research checkpoint}"

# A checkpoint is allowed only when the regression contract passes.
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check

# PDFs, LTspice raw/log/db files, local reports and temporary outputs remain
# excluded by .gitignore. Stage project changes only after validation.
git add -A

if git diff --cached --quiet; then
  echo "No verified project changes to checkpoint."
  exit 0
fi

git commit -m "$message"

# The installed post-commit hook normally pushes. Keep this fallback so the
# script remains useful on a fresh clone before hook installation.
local_head="$(git rev-parse HEAD)"
remote_head="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
if [[ "$local_head" != "$remote_head" ]]; then
  git push origin main
fi
