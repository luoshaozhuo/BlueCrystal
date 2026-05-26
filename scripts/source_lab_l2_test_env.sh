#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
PUB_IFACE="${SOURCE_LAB_L2_PUBLISHER_INTERFACE:-sl_pub0}"
SUB_IFACE="${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE:-sl_sub0}"

usage() {
    cat <<'EOF'
Usage: source_lab_l2_test_env.sh <setup|teardown|status>

Creates or removes a disposable L2 veth pair for source_lab GOOSE/SV tests.
Run as root, inside a privileged container, or inside `unshare -Urn`.
EOF
}

ensure_ip() {
    if ! command -v ip >/dev/null 2>&1; then
        echo "ERROR: ip command not found" >&2
        exit 1
    fi
}

setup_env() {
    ensure_ip
    ip link del "${PUB_IFACE}" >/dev/null 2>&1 || true
    ip link del "${SUB_IFACE}" >/dev/null 2>&1 || true
    ip link set lo up
    ip link add "${PUB_IFACE}" type veth peer name "${SUB_IFACE}"
    ip link set "${PUB_IFACE}" up
    ip link set "${SUB_IFACE}" up
    echo "export SOURCE_LAB_L2_PUBLISHER_INTERFACE=${PUB_IFACE}"
    echo "export SOURCE_LAB_L2_SUBSCRIBER_INTERFACE=${SUB_IFACE}"
    echo "export SOURCE_LAB_L2_INTERFACE=${SUB_IFACE}"
}

teardown_env() {
    ensure_ip
    ip link del "${PUB_IFACE}" >/dev/null 2>&1 || true
    ip link del "${SUB_IFACE}" >/dev/null 2>&1 || true
}

status_env() {
    ensure_ip
    ip -brief link show "${PUB_IFACE}" 2>/dev/null || true
    ip -brief link show "${SUB_IFACE}" 2>/dev/null || true
}

case "${ACTION}" in
    setup)
        setup_env
        ;;
    teardown)
        teardown_env
        ;;
    status)
        status_env
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
