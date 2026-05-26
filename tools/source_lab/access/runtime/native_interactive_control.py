"""Capability metadata for native runner interactive control boundaries."""

from __future__ import annotations


NATIVE_INTERACTIVE_CONTROL_CAPABILITIES: dict[str, dict[str, object]] = {
    "opcua": {
        "interactive_control": False,
        "mode": "replacement_only",
        "reason": "open62541 dynamic runtime currently uses endpoint session replacement",
    },
    "iec61850_report": {
        "interactive_control": False,
        "mode": "replacement_only",
        "reason": "report runner protocol does not expose endpoint-level pause/resume/add-points commands",
    },
    "iec61850_goose": {
        "interactive_control": False,
        "mode": "replacement_only",
        "reason": "L2 subscriber lifecycle is process scoped and permission sensitive",
    },
    "iec61850_sv": {
        "interactive_control": False,
        "mode": "replacement_only",
        "reason": "L2 subscriber lifecycle is process scoped and permission sensitive",
    },
    "mqtt": {
        "interactive_control": False,
        "mode": "replacement_only",
        "reason": "Python lightweight subscription runner recreates the topic session on change",
    },
}
