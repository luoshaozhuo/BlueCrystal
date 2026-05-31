"""Bundle 脱敏辅助函数。对 bundle 中的敏感字段按可配置规则做脱敏处理。"""

from __future__ import annotations

from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.domain.audit_event import redact_value


def redact_bundle(bundle: IngestBundle) -> IngestBundle:
    """返回 bundle 的一份脱敏副本。按配置的脱敏规则替换或删除敏感字段。"""

    tasks = [
        AcquisitionTaskBundleItem(
            **{
                **item.model_dump(),
                "protocol_params": redact_value(item.protocol_params),
            }
        )
        for item in bundle.acquisition_tasks
    ]
    return IngestBundle(
        **{
            **bundle.model_dump(),
            "redacted": True,
            "acquisition_tasks": tasks,
        }
    )
