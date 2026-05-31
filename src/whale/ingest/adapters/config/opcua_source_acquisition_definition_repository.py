"""配置适配器。

实现配置相关 port，从数据库加载运行时配置。
外部依赖：SQLAlchemy ORM。
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy import select
from sqlalchemy.orm import Session

from whale.ingest.framework.persistence.session import session_scope
from whale.ingest.ports.runtime.source_runtime_config_port import (
    SourceRuntimeConfigData,
)
from whale.ingest.ports.source.source_acquisition_definition_port import (
    SourceAcquisitionDefinition,
    SourceAcquisitionDefinitionPort,
)
from whale.ingest.usecases.dtos.source_acquisition_request import AcquisitionItemData
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.persistence.orm import (
    AcquisitionTask,
    CommunicationEndpoint,
    LDInstance,
    SignalProfileItem,
)


class OpcUaSourceAcquisitionDefinitionRepository(SourceAcquisitionDefinitionPort):
    """从数据库读取 OPC UA 采集定义。"""

    def __init__(
        self,
        session_factory: Callable[[], AbstractContextManager[Session]] = session_scope,
    ) -> None:
        """初始化 OPC UA 采集定义仓库。Args: session_factory: 数据库会话工厂。"""
        self._session_factory = session_factory

    def get_config(
        self,
        runtime_config: SourceRuntimeConfigData,
    ) -> SourceAcquisitionDefinition:
        """根据 runtime config 读取 source 采集定义。"""

        with self._session_factory() as session:
            task = session.get(AcquisitionTask, runtime_config.runtime_config_id)
            if task is None:
                raise LookupError(
                    f"AcquisitionTask `{runtime_config.runtime_config_id}` not found."
                )

            ld = session.get(LDInstance, task.ld_instance_id)
            if ld is None:
                raise LookupError(f"LDInstance `{task.ld_instance_id}` not found.")

            ep = session.get(CommunicationEndpoint, ld.endpoint_id)
            if ep is None:
                raise LookupError(
                    f"CommunicationEndpoint `{ld.endpoint_id}` not found."
                )

            if ld.signal_profile_id is None:
                raise LookupError(
                    f"LDInstance `{ld.ld_instance_id}` has no signal_profile_id."
                )

            items = session.scalars(
                select(SignalProfileItem)
                .where(SignalProfileItem.signal_profile_id == ld.signal_profile_id)
                .order_by(SignalProfileItem.profile_item_id)
            ).all()

        return SourceAcquisitionDefinition(
            ld_id=ld.ld_name,
            connection=SourceConnectionData(
                host=ep.host or "",
                port=ep.port or 0,
                ied_name=ep.ied.ied_name,
                ld_name=ld.ld_name,
                namespace_uri=ep.namespace_uri or "",
                security_policy=ep.security_policy,
                security_mode=ep.security_mode,
                auth_type=ep.auth_type,
                credential_ref=ep.credential_ref,
            ),
            items=[
                AcquisitionItemData(
                    key=item.do_name,
                    profile_item_id=item.profile_item_id,
                    relative_path=item.relative_path,
                )
                for item in items
            ],
            request_timeout_ms=task.request_timeout_ms,
            poll_interval_ms=task.poll_interval_ms,
            polling_max_concurrent_connections=(
                task.polling_max_concurrent_connections
            ),
            polling_connection_start_interval_ms=(
                task.polling_connection_start_interval_ms
            ),
            subscription_start_interval_ms=task.subscription_start_interval_ms,
            subscription_notification_queue_size=(
                task.subscription_notification_queue_size
            ),
            subscription_notification_max_lag_ms=(
                task.subscription_notification_max_lag_ms
            ),
        )
