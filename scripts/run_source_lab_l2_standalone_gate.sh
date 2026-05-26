#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_SCRIPT="${ROOT_DIR}/scripts/source_lab_l2_test_env.sh"
LOG_DIR="${ROOT_DIR}/ai_shared/reports"

GOOSE_APP_ID="${SOURCE_LAB_GOOSE_APP_ID:-1000}"
SV_APP_ID="${SOURCE_LAB_SV_APP_ID:-4000}"
GOOSE_INTERVAL_MS="${SOURCE_LAB_GOOSE_INTERVAL_MS:-500}"
SV_SAMPLE_RATE_HZ="${SOURCE_LAB_SV_SAMPLE_RATE_HZ:-1}"
SUB_DURATION_S="${SOURCE_LAB_L2_SUB_DURATION_S:-3}"

run_pair() {
    local label="$1"
    local publisher="$2"
    local subscriber="$3"
    local publisher_iface="$4"
    local subscriber_iface="$5"
    local app_id="$6"
    local publisher_rate="$7"

    local sub_log="${LOG_DIR}/${label}_subscriber.log"
    local pub_log="${LOG_DIR}/${label}_publisher.log"

    rm -f "${sub_log}" "${pub_log}"

    "${subscriber}" "${subscriber_iface}" "${app_id}" "${SUB_DURATION_S}" >"${sub_log}" 2>&1 &
    local sub_pid=$!

    local ready=0
    for _ in $(seq 1 30); do
        if grep -q '^READY$' "${sub_log}" 2>/dev/null; then
            ready=1
            break
        fi
        if ! kill -0 "${sub_pid}" 2>/dev/null; then
            break
        fi
        sleep 0.1
    done

    if [[ "${ready}" != "1" ]]; then
        wait "${sub_pid}" || true
        echo "${label}_STANDALONE_FAIL subscriber_not_ready app_id=${app_id} publisher_iface=${publisher_iface} subscriber_iface=${subscriber_iface}"
        cat "${sub_log}" >&2 || true
        return 1
    fi

    "${publisher}" "${publisher_iface}" "${app_id}" "${publisher_rate}" >"${pub_log}" 2>&1 &
    local pub_pid=$!

    wait "${sub_pid}"
    local sub_rc=$?
    kill "${pub_pid}" >/dev/null 2>&1 || true
    wait "${pub_pid}" >/dev/null 2>&1 || true

    local count
    count="$(awk -F'\t' '/^STREAM_SUMMARY\t/ {print $2; found=1} END {if (!found) print 0}' "${sub_log}")"

    if [[ "${sub_rc}" -eq 0 && "${count}" -gt 0 ]]; then
        echo "${label}_STANDALONE_PASS app_id=${app_id} publisher_iface=${publisher_iface} subscriber_iface=${subscriber_iface} count=${count}"
        return 0
    fi

    echo "${label}_STANDALONE_FAIL app_id=${app_id} publisher_iface=${publisher_iface} subscriber_iface=${subscriber_iface} count=${count} subscriber_rc=${sub_rc}"
    echo "--- ${label} subscriber log ---" >&2
    cat "${sub_log}" >&2 || true
    echo "--- ${label} publisher log ---" >&2
    cat "${pub_log}" >&2 || true
    return 1
}

inner_main() {
    # shellcheck disable=SC1090
    source <("${ENV_SCRIPT}" setup)
    trap '"${ENV_SCRIPT}" teardown >/dev/null 2>&1 || true' EXIT

    run_pair \
        "GOOSE" \
        "${ROOT_DIR}/tools/source_lab/native/build/iec61850_goose_publisher_simulator" \
        "${ROOT_DIR}/tools/source_lab/native/build/iec61850_goose_subscriber_runner" \
        "${SOURCE_LAB_L2_PUBLISHER_INTERFACE}" \
        "${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE}" \
        "${GOOSE_APP_ID}" \
        "${GOOSE_INTERVAL_MS}"

    run_pair \
        "SV" \
        "${ROOT_DIR}/tools/source_lab/native/build/iec61850_sv_publisher_simulator" \
        "${ROOT_DIR}/tools/source_lab/native/build/iec61850_sv_subscriber_runner" \
        "${SOURCE_LAB_L2_PUBLISHER_INTERFACE}" \
        "${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE}" \
        "${SV_APP_ID}" \
        "${SV_SAMPLE_RATE_HZ}"
}

if [[ "${1:-}" == "--inner" ]]; then
    cd "${ROOT_DIR}"
    inner_main
    exit 0
fi

cd "${ROOT_DIR}"
if [[ -n "${SOURCE_LAB_L2_PUBLISHER_INTERFACE:-}" && -n "${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE:-}" ]]; then
    inner_main
else
    exec unshare -Urn bash -lc "cd '${ROOT_DIR}' && bash scripts/run_source_lab_l2_standalone_gate.sh --inner"
fi
