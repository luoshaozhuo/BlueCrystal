#!/usr/bin/env bash
set -euo pipefail
mkdir -p .agents
rm -rf .agents/skills
ln -s ../.claude/skills .agents/skills
echo ".agents/skills -> ../.claude/skills"
