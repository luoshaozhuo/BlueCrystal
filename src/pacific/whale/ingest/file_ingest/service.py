"""文件接入服务。

编排文件接入最小闭环的完整流程：
1. 检测文件落地完成（manifest/size stable/done flag）。
2. 写入 raw_archive（记录文件元数据和载荷摘要）。
3. 解码文件内容（JSON / 二进制）。
4. 写入标准化波形存储。
5. 记录故障事件元数据。
6. 返回结构化 FileIngestResult。

若 raw_archive 成功但 decode 失败，返回 accepted=False 或 partial 状态，
并记录 error；不静默吞错。

本文件包含：
- FileIngestService: 文件接入服务（依赖注入 wiring）。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from pacific.whale.ingest.file_ingest.decoder import (
    FaultRecordBinaryDecoder,
    PlcHighRateJsonDecoder,
)
from pacific.whale.ingest.file_ingest.detector import FileCompletionDetector
from pacific.whale.ingest.file_ingest.models import (
    FaultEventMetadata,
    FileIngestManifest,
    FileIngestRequest,
    FileIngestResult,
)
from pacific.whale.ingest.file_ingest.repository import FaultEventRepositoryPort
from pacific.whale.storage.raw_archive import (
    FileArchiveSinkPort,
    InMemoryManifestRepository,
    ManifestRepositoryPort,
)
from pacific.whale.storage.waveform import StandardizedWaveformSinkPort

logger = logging.getLogger(__name__)


class FileIngestService:
    """文件接入服务。

    编排文件接入的完整流程，将所有组件（检测器、解码器、存储、仓储）
    串联为最小闭环。

    依赖注入：
    - detector: 文件完成检测器。
    - raw_archive: 原始归档写入端口。
    - manifest_repo: raw_archive manifest 记录端口。
    - waveform_sink: 标准化波形写入端口。
    - fault_event_repo: 故障事件仓储端口。

    Attributes:
        _detector: 文件完成检测器。
        _raw_archive: 原始归档写入端口。
        _manifest_repo: manifest 记录端口。
        _waveform_sink: 波形写入端口。
        _fault_event_repo: 故障事件仓储。
    """

    def __init__(
        self,
        detector: FileCompletionDetector,
        raw_archive: FileArchiveSinkPort,
        manifest_repo: ManifestRepositoryPort | None = None,
        waveform_sink: StandardizedWaveformSinkPort | None = None,
        fault_event_repo: FaultEventRepositoryPort | None = None,
    ) -> None:
        """初始化文件接入服务。

        所有外部依赖通过构造函数注入，遵循 composition root 模式。

        Args:
            detector: 文件完成检测器。
            raw_archive: 原始归档写入端口。
            manifest_repo: manifest 记录端口，默认使用 InMemoryManifestRepository。
            waveform_sink: 波形写入端口。
            fault_event_repo: 故障事件仓储。
        """
        self._detector = detector
        self._raw_archive = raw_archive
        self._manifest_repo: ManifestRepositoryPort = (
            manifest_repo or InMemoryManifestRepository()
        )
        self._waveform_sink = waveform_sink
        self._fault_event_repo = fault_event_repo

    async def ingest(self, request: FileIngestRequest) -> FileIngestResult:
        """执行文件接入。

        完整流程：
        1. 检测文件完成状态。
        2. 构建 manifest 并计算校验和。
        3. 写入 raw_archive（元数据和载荷摘要）。
        4. 解码文件内容。
        5. 写入标准化波形。
        6. 记录故障事件。
        7. 返回结构化结果。

        raw_archive 成功后即使后续步骤失败，也会在 result 中记录 partial
        状态和错误信息，不静默吞错。

        Args:
            request: 文件接入请求。

        Returns:
            FileIngestResult，包含 accepted、统计信息和错误列表。
        """
        result = FileIngestResult()

        # ── 1. 确定数据文件路径和检测文件完成状态 ──
        manifest: FileIngestManifest | None = None
        data_path = request.data_path

        if request.manifest_path:
            # 通过 manifest JSON 检测
            probe = self._detector.detect_by_manifest(request.manifest_path)
            if not probe.stable:
                result.reason = f"manifest 检测失败: {probe.reason}"
                result.add_error(probe.reason)
                return result
            data_path = probe.path
            manifest = self._detector.build_manifest_from_file(
                data_path, request.file_type
            )
        elif data_path:
            # 直接路径，先做 size stable，再构建 manifest
            probe = self._detector.detect_by_size_stable(data_path)
            if not probe.stable:
                # 尝试 done flag（作为 size stable 的补充）
                probe_done = self._detector.detect_by_done_flag(data_path)
                if not probe_done.stable:
                    result.reason = f"文件稳定性检测失败: {probe.reason}"
                    result.add_error(probe.reason)
                    return result
            manifest = self._detector.build_manifest_from_file(
                data_path, request.file_type
            )
        else:
            result.reason = "未指定 manifest_path 或 data_path"
            result.add_error(result.reason)
            return result

        if manifest is None:
            result.reason = f"无法构建 manifest: data_path={data_path}"
            result.add_error(result.reason)
            return result

        # ── 2. 写入 raw_archive ──
        batch_id = f"file-{uuid.uuid4().hex[:12]}"
        result.raw_batch_id = batch_id

        try:
            # 写入的是文件元数据和载荷摘要，不将大文件内容读入长期内存
            raw_envelope = {
                "batch_id": batch_id,
                "file_id": manifest.file_id,
                "file_type": manifest.file_type,
                "path": manifest.path,
                "size_bytes": manifest.size_bytes,
                "checksum": manifest.checksum,
                "checksum_algorithm": manifest.checksum_algorithm,
                "source_id": request.source_id,
                "asset_id": request.asset_id or request.device_id,
                "trace_id": request.trace_id,
                "ingest_at": datetime.now(tz=timezone.utc).isoformat(),
                "summary": f"file={manifest.file_id} type={manifest.file_type} "
                f"size={manifest.size_bytes} checksum={manifest.checksum[:16]}",
            }
            await self._raw_archive.write(batch_id, [raw_envelope])
            await self._raw_archive.commit(batch_id)
            await self._manifest_repo.record_manifest(
                batch_id=batch_id,
                file_path=manifest.path,
                message_count=1,
                start_time=datetime.fromisoformat(
                    manifest.created_at.rstrip("Z")
                ) if manifest.created_at.endswith("Z") else datetime.fromisoformat(
                    manifest.created_at
                ),
                end_time=datetime.now(tz=timezone.utc),
            )
            result.reason = "raw_archive 写入成功"
        except Exception as exc:
            result.reason = f"raw_archive 写入失败: {exc}"
            result.add_error(str(exc))
            return result

        # ── 3. 解码文件内容 ──
        try:
            decoded_signals, waveforms = self._decode_file(
                data_path=data_path,
                file_type=manifest.file_type,
                source_id=request.source_id,
            )
            result.decoded_signal_count = len(decoded_signals)
        except Exception as exc:
            # raw_archive 已成功，但 decode 失败 -> accepted=False
            result.accepted = False
            result.reason = f"raw_archive 成功但解码失败: {exc}"
            result.add_error(str(exc))
            return result

        # ── 4. 写入标准化波形 ──
        waveform_count = 0
        if self._waveform_sink is not None and waveforms:
            event_id = f"evt-{uuid.uuid4().hex[:8]}"
            for wf in waveforms:
                try:
                    ok = await self._waveform_sink.write_waveform(
                        event_id=event_id,
                        source_id=request.source_id,
                        channel_key=wf.variable_key,
                        timestamps=wf.timestamps,
                        values=wf.values,
                        sample_rate_hz=wf.sample_rate_hz,
                        quality_code=wf.quality_code,
                        channel_id=wf.channel_id,
                    )
                    if ok:
                        waveform_count += 1
                except Exception as exc:
                    logger.warning(
                        "波形写入失败 event=%s channel=%s: %s",
                        event_id, wf.variable_key, exc,
                    )
                    result.add_error(f"波形写入失败: {exc}")
            result.waveform_count = waveform_count

        # ── 5. 记录故障事件 ──
        fault_event_count = 0
        if self._fault_event_repo is not None:
            event_id = f"flt-{uuid.uuid4().hex[:8]}"
            # 从文件类型推导事件类型
            event_type = self._infer_event_type(manifest.file_type)
            fault_event = FaultEventMetadata(
                event_id=event_id,
                source_id=request.source_id,
                asset_id=request.asset_id,
                device_id=request.device_id,
                event_type=event_type,
                started_at=datetime.now(tz=timezone.utc).isoformat(),
                ended_at=datetime.now(tz=timezone.utc).isoformat(),
                sample_rate_hz=(
                    waveforms[0].sample_rate_hz if waveforms else 0.0
                ),
                channel_count=len(waveforms),
                raw_batch_id=batch_id,
                severity="WARNING",
                metadata={
                    "file_type": manifest.file_type,
                    "file_id": manifest.file_id,
                    "checksum": manifest.checksum,
                },
            )
            try:
                await self._fault_event_repo.save(fault_event)
                fault_event_count = 1
            except Exception as exc:
                logger.warning("故障事件记录失败: %s", exc)
                result.add_error(f"故障事件记录失败: {exc}")
            result.fault_event_count = fault_event_count

        # ── 6. 汇总结果 ──
        result.accepted = True
        if result.errors:
            result.reason += " (有部分错误)"
        else:
            result.reason = f"接入完成: {result.decoded_signal_count} signals, "
            result.reason += f"{result.waveform_count} waveforms, "
            result.reason += f"{result.fault_event_count} fault_events"
        return result

    def _decode_file(
        self,
        data_path: str,
        file_type: str,
        source_id: str,
    ) -> tuple[list, list]:
        """根据文件类型选择解码器并解码。

        读取文件内容后调用对应解码器。

        Args:
            data_path: 数据文件路径。
            file_type: 文件类型（plc_high_rate_json / fault_record_binary）。
            source_id: 数据源标识。

        Returns:
            (decoded_signals, waveforms) 元组。
        """
        if file_type == "plc_high_rate_json":
            json_decoder = PlcHighRateJsonDecoder()
            with open(data_path, "r", encoding="utf-8") as f:
                json_content: str = f.read()
            return json_decoder.decode(json_content, source_id=source_id)

        if file_type == "fault_record_binary":
            binary_decoder = FaultRecordBinaryDecoder()
            with open(data_path, "rb") as f:
                binary_content: bytes = f.read()
            return binary_decoder.decode(binary_content, source_id=source_id)

        raise ValueError(f"不支持的文件类型: {file_type}")

    @staticmethod
    def _infer_event_type(file_type: str) -> str:
        """从文件类型推导故障事件类型。

        Args:
            file_type: 文件类型字符串。

        Returns:
            故障事件类型标签。
        """
        if "json" in file_type:
            return "PLC_HIGH_RATE_RECORD"
        if "binary" in file_type:
            return "FAULT_RECORD"
        return "UNKNOWN_FILE_TYPE"
