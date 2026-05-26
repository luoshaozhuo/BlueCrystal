#!/usr/bin/env bash
set -euo pipefail

# 普通用户可以运行本脚本，但在无 CAP_NET_RAW/root 时相关测试会显式 skip。
# 真正的 GOOSE/SV true PASS 需要 root 或为 runner 增加 CAP_NET_RAW。
# Docker runner 可通过 cap_add: NET_RAW 或 privileged 模式配置，不要求生产环境默认提权。

pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs
pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs
