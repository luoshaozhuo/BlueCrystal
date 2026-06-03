"""MQTT source 采集适配器。

实现 SourceAcquisitionPort，通过 shared/source/mqtt 生产级 client backend
执行 MQTT 消息采集（subscribe 并接收消息）。

职责边界：
- 负责采集 DTO 与 MQTT client 调用之间的转换；
- 不负责 MQTT 协议细节——由 whale.shared.source.mqtt.client 处理；
- 不负责缓存、重试、授权——由上层 decorator 链处理；
- 不负责写入（write/control）——当前 NOT_IMPLEMENTED。

订阅模式：
- MQTT 采集通过 subscribe_and_receive 实现一次性消息接收；
- 支持 topic filter 配置；
- 消息负载直接作为节点值。

Write 状态：NOT_IMPLEMENTED。仅实现 SourceAcquisitionPort，不实现 SourceWritePort。
"""
from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceReadError,
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
    SubscriptionStateHandler,
)
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.mqtt.client import MqttClientBackend, MqttMessage
from whale.shared.utils.time import ensure_utc


class MqttSourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 MqttClientBackend 采集 MQTT 消息。

    连接 MQTT broker、订阅 topic 并接收消息，将消息负载转换为
    AcquiredNodeStateBatch 供 ingest 缓存使用。

    MQTT 为订阅协议（subscribe-based），不支持传统 polling read。
    适配器通过 subscribe_and_receive 实现一次性订阅采集。
    """

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。MQTT 不支持传统 subscription 采集，
        但可通过 subscribe_and_receive 实现 one-shot 消息接收。"""
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次 MQTT subscribe 并接收消息。

        连接 MQTT broker，按 items 中指定的 topic filter 订阅，
        接收消息后断开连接并返回采集批次。

        Args:
            execution: 采集执行选项，其 protocol 字段确定 MQTT 模式。
            connection: 目标 MQTT broker 连接信息。
            items: 采集点位（每个 item 的 relative_path 作为 topic filter）。

        Returns:
            AcquiredNodeStateBatch 包含消息负载作为节点值。

        Raises:
            SourceReadError: MQTT 连接失败或订阅异常。
        """
        host = connection.host.strip()
        if not host:
            raise SourceReadError("connection.host is required for MQTT")
        if connection.port <= 0:
            raise SourceReadError("connection.port must be > 0 for MQTT")

        topic_filters = [item.relative_path.strip() or "#" for item in items]
        if not topic_filters:
            raise SourceReadError("no topic filters resolved from items")

        client_received_at = datetime.now(tz=UTC)

        try:
            client = MqttClientBackend(
                host=host,
                port=connection.port,
                client_id=f"whale-ingest-mqtt-{connection.ld_name}",
            )
            await client.connect(timeout_seconds=15.0)

            # Subscribe to the first topic filter (simplified: one topic per read)
            topic = topic_filters[0]
            result = await client.subscribe_and_receive(
                topic_filter=topic,
                qos=0,
                max_messages=len(items),
                timeout_seconds=30.0,
            )

            await client.disconnect()

            if not result.ok:
                raise SourceReadError(
                    f"MQTT subscribe failed: {result.error_reason or 'no messages'}"
                )

            client_processed_at = datetime.now(tz=UTC)
            return self._to_acquired_batch(
                connection=connection,
                items=items,
                messages=result.messages,
                client_received_at=client_received_at,
                client_processed_at=client_processed_at,
            )
        except SourceReadError:
            raise
        except ConnectionError as exc:
            raise SourceReadError(f"MQTT connection failed: {exc}") from exc
        except Exception as exc:
            raise SourceReadError(str(exc) or type(exc).__name__) from exc

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """MQTT 当前不支持持久订阅采集。"""
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "MQTT persistent subscription is not supported. Use read() for one-shot message acquisition."
        )

    @staticmethod
    def _to_acquired_batch(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        messages: tuple[MqttMessage, ...],
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """将 MQTT 消息转换为 AcquiredNodeStateBatch。

        每个 item 对应一条消息（按顺序匹配），
        若消息数少于 item 数，剩余节点标记为 UNKNOWN。
        """
        values: list[AcquiredNodeValue] = []
        for idx, item in enumerate(items):
            if idx < len(messages):
                msg = messages[idx]
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value=msg.payload,
                        quality="GOOD",
                        source_timestamp=None,
                        server_timestamp=ensure_utc(msg.received_at),
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "mqtt_topic": msg.topic,
                            "mqtt_qos": str(msg.qos),
                        },
                    )
                )
            else:
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value="",
                        quality="UNKNOWN",
                        source_timestamp=None,
                        server_timestamp=None,
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "warning": "no_message_received",
                        },
                    )
                )

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name.strip() or "mqtt_source",
            batch_observed_at=client_processed_at,
            client_received_at=ensure_utc(client_received_at),
            client_processed_at=ensure_utc(client_processed_at),
            values=values,
            availability_status="VALID",
            attributes={"acquisition_kind": "subscribe"},
        )
