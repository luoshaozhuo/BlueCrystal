#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Root-only artifacts that should never be kept in repository root.
declare -a ROOT_ARTIFACTS=(
  "all_test_output.txt"
  "compile_output.txt"
  "fail_fast_output.txt"
  "mypy_output.txt"
  "profile_test_output.txt"
  "pytest_out.txt"
  "test_output.txt"
  "output.log"
  "pytest_output.log"
  "pytest_output_v2.log"
  "test_out.log"
  "test_output.log"
)

removed=0
for name in "${ROOT_ARTIFACTS[@]}"; do
  path="${ROOT_DIR}/${name}"
  if [[ -f "${path}" ]]; then
    rm -f -- "${path}"
    removed=$((removed + 1))
    echo "[cleanup] removed ${name}"
  fi
done

if [[ ${removed} -eq 0 ]]; then
  echo "[cleanup] no root log artifacts found"
fi
