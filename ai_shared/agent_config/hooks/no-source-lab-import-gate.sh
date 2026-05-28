#!/usr/bin/env bash
set -euo pipefail

paths=()
[ -d "src/whale/ingest" ] && paths+=("src/whale/ingest")
[ -d "src/whale/shared/source" ] && paths+=("src/whale/shared/source")

if [ "${#paths[@]}" -eq 0 ]; then
  exit 0
fi

if grep -R --include='*.py' -nE '(^|[[:space:]])(import|from)[[:space:]]+tools\.source_lab' "${paths[@]}" >/tmp/source_lab_import_gate.txt 2>/dev/null; then
  echo "BLOCKED: production path imports tools.source_lab:" >&2
  cat /tmp/source_lab_import_gate.txt >&2
  exit 2
fi
