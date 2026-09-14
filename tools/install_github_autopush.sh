#!/bin/zsh
set -euo pipefail

project_root="$(git rev-parse --show-toplevel)"
hook="$project_root/.git/hooks/post-commit"

mkdir -p "${hook:h}"
cp "$project_root/tools/post-commit.autopush" "$hook"
chmod +x "$hook"
echo "Installed verified-checkpoint auto-push hook at $hook"
