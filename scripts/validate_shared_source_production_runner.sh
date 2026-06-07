#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# shared_source production runner artifact 验证脚本（Task C，Round 12）
# ============================================================================
#
# 验证 shared_source native runner 在生产环境下的正确解析行为：
#   1. WHALE_SHARED_SOURCE_RUNNER_DIR 指向独立目录时优先使用
#   2. PATH 发现
#   3. dev fallback disabled 时不得使用 src/starfish/native/bin
#   4. 缺失 runner 返回 unavailable（非静默成功）
#   5. 错误消息包含 build/install hint
#
# 测试阶段：开发期验证（contract/stub）—— 验证 runner_resolution 模块的路径解析契约。
# 不要求本轮真实打包完整 artifact。
# ============================================================================

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── 失败代码分类 ──────────────────────────────────────────────────────────────

readonly RC_OK=0
readonly RC_VALIDATION_FAILED=1
readonly RC_TEST_FAILED=2

# ── Python 验证函数 ──────────────────────────────────────────────────────────

run_python_validation() {
  python3 -c '
import os, sys, shutil, tempfile
from pathlib import Path

# 添加仓库根目录到 path
repo_root = Path(os.environ.get("ROOT_DIR", ".")).resolve()
sys.path.insert(0, str(repo_root))

from whale.shared.source.runner_resolution import (
    resolve_native_runner_path,
    build_runner_unavailable_message,
    is_source_lab_dev_runner_path,
    _PRODUCTION_RUNNER_DIR_ENV,
    _ALLOW_DEV_FALLBACK_ENV,
)

errors = []

# ── 验证 1：PRODUCTION_RUNNER_DIR 指向独立目录时优先使用 ────────────────
with tempfile.TemporaryDirectory() as tmp:
    runner_dir = Path(tmp) / "prod-runners"
    runner_dir.mkdir()
    (runner_dir / "open62541_client_runner").touch(mode=0o755)

    os.environ.pop("WHALE_OPEN62541_CLIENT_RUNNER_PATH", None)
    os.environ[_PRODUCTION_RUNNER_DIR_ENV] = str(runner_dir)
    os.environ.pop(_ALLOW_DEV_FALLBACK_ENV, None)

    result = resolve_native_runner_path(
        executable_stem="open62541_client_runner",
        specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH",
    )
    assert result.source == f"env:{_PRODUCTION_RUNNER_DIR_ENV}", \
        f"FAIL v1: expected source env:WHALE_SHARED_SOURCE_RUNNER_DIR, got {result.source}"
    assert result.used_dev_fallback is False, \
        f"FAIL v1: dev fallback should be False"
    assert not is_source_lab_dev_runner_path(result.path), \
        f"FAIL v1: path should NOT point to starfish native bin"
    print("PASS v1: PRODUCTION_RUNNER_DIR priority")

# ── 验证 2：PATH 发现 ──────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    runner_path = Path(tmp) / "modbus_tcp_polling_runner"
    runner_path.touch(mode=0o755)

    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{tmp}:{old_path}"
    os.environ.pop("WHALE_MODBUS_CLIENT_RUNNER_PATH", None)
    os.environ.pop(_PRODUCTION_RUNNER_DIR_ENV, None)
    os.environ.pop(_ALLOW_DEV_FALLBACK_ENV, None)

    result = resolve_native_runner_path(
        executable_stem="modbus_tcp_polling_runner",
        specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH",
    )
    assert result.source == "PATH", \
        f"FAIL v2: expected source PATH, got {result.source}"
    assert result.used_dev_fallback is False, \
        f"FAIL v2: dev fallback should be False"
    print("PASS v2: PATH discovery")

# ── 验证 3：无 dev fallback 时不得使用 source_lab native/build ────────
os.environ.pop("WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH", None)
os.environ.pop(_PRODUCTION_RUNNER_DIR_ENV, None)
os.environ.pop(_ALLOW_DEV_FALLBACK_ENV, None)

result = resolve_native_runner_path(
    executable_stem="iec61850_mms_client_runner",
    specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
)
assert result.used_dev_fallback is False, \
    f"FAIL v3: dev fallback should not be used"
assert not is_source_lab_dev_runner_path(result.path), \
    f"FAIL v3: default path should not point to starfish native/bin"
assert "src/starfish/native/bin" not in str(result.path), \
    f"FAIL v3: path should not contain starfish native/bin, got {result.path}"
print("PASS v3: no dev fallback means no starfish path")

# ── 验证 4：缺失 runner 返回 unavailable（非静默成功） ─────────────────
msg = build_runner_unavailable_message(
    runner_label="IEC 61850 MMS client runner",
    specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
    resolution=result,
)
assert "does not exist" in msg, \
    f"FAIL v4a: message should mention missing executable"
assert "install" in msg.lower(), \
    f"FAIL v4b: message should contain install hint"
assert "WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH" in msg, \
    f"FAIL v4c: message should contain specific env var name"
assert "WHALE_SHARED_SOURCE_RUNNER_DIR" in msg, \
    f"FAIL v4d: message should contain shared runner dir env var"
print("PASS v4: unavailable runner message contains install hints")

# ── 验证 5：dev fallback 缺失时错误消息区分 production/fallback ───────
os.environ[_ALLOW_DEV_FALLBACK_ENV] = "1"
result_fb = resolve_native_runner_path(
    executable_stem="iec61850_report_runner",
    specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
)
assert result_fb.used_dev_fallback is True, \
    f"FAIL v5a: dev fallback should be enabled"

msg_fb = build_runner_unavailable_message(
    runner_label="IEC 61850 report runner",
    specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
    resolution=result_fb,
)
assert "dev/test fallback" in msg_fb, \
    f"FAIL v5b: message should mention dev/test fallback"
assert "does not count as a production runner artifact" in msg_fb, \
    f"FAIL v5c: message should state it is not production artifact"
assert "starfish native bin" in msg_fb, \
    f"FAIL v5d: message should reference starfish native bin"
print("PASS v5: dev fallback message distinguishes production vs dev/test")

# ── 验证 6：is_source_lab_dev_runner_path 识别 starfish native bin 路径 ──
assert is_source_lab_dev_runner_path(
    Path("/home/user/project/src/starfish/native/bin/open62541")
), "FAIL v6a: should identify starfish native bin path"

assert not is_source_lab_dev_runner_path(
    Path("/opt/whale/shared-source/bin/open62541")
), "FAIL v6b: production path should not be identified as dev"

print("PASS v6: is_source_lab_dev_runner_path correctly identifies paths")

# ── 收口 ──────────────────────────────────────────────────────────────
if errors:
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)

print()
print("=== ALL VALIDATIONS PASSED ===")
print("测试阶段：开发期验证（contract/stub）")
print("Production runner path resolution works correctly under:")
print("  - PRODUCTION_RUNNER_DIR env var priority")
print("  - PATH discovery")
print("  - No dev fallback without explicit opt-in")
print("  - Clear unavailable messages with install hints")
print("  - Dev fallback marked as non-production")
'
}

# ── 执行 ──────────────────────────────────────────────────────────────────────

echo "=== shared_source production runner artifact validation ==="
echo "测试阶段：开发期验证（contract/stub）—— validates runner_resolution module contracts."
echo "This script does NOT verify actual compiled native binaries — it validates"
echo "the path resolution logic, which is the prerequisite for artifact delivery."
echo ""

export ROOT_DIR="${ROOT_DIR}"

if run_python_validation; then
  echo ""
  echo "=== validation-entry-ready ==="
  echo "The runner_resolution module correctly:"
  echo "  1. Prioritizes WHALE_SHARED_SOURCE_RUNNER_DIR"
  echo "  2. Discovers runners via PATH"
  echo "  3. Does NOT fall back to starfish native/bin without opt-in"
  echo "  4. Returns clear unavailable messages with build/install hints"
  echo "  5. Marks dev fallback as non-production"
  exit ${RC_OK}
else
  echo ""
  echo "=== VALIDATION FAILED ==="
  exit ${RC_VALIDATION_FAILED}
fi
