# ADR-20260604-016-ingest-file-ingest-waveform-boundary

## Status

Accepted

## Keywords

- ingest, file_ingest, waveform, storage, speed_layer, preprocessing, boundary, decode-before-resolve, fault_record, raw_archive

## Context

Whale 需要支持故障录波、事件记录等文件数据的接入。文件接入与现有的 source 协议采集不同：数据来源为文件系统（而非网络协议采集），需要文件完成检测、二进制解码、raw_archive 归档和波形存储。

同时，波形数据（大规模浮点数组）与标准化点值（scalar value + quality_code）在存储 schema、访问模式和生命周期上差异显著，不应混入同一张 TDengine 标准表。

## Decision

1. 文件接入子系统位于 `src/whale/ingest/file_ingest/`，作为 ingest 模块的子包，不新建顶级模块。

2. 文件完成检测归属 ingest.file_ingest：
   - FileCompletionDetector 负责检测文件写入完成（inotify + 轮询 fallback）。
   - file_ingest 内部自行管理文件状态，不依赖 source_lab 的文件提供者。

3. raw_archive 复用 storage.raw_archive：
   - file_ingest 解码前先将原始文件写入 raw_archive（LocalCompressedArchiveSink 或 S3RawArchiveSink）。
   - 归档格式为 gzip + JSONL，与 speed_layer raw_archive 一致。

4. 解码输出 DecodedSignal，不直接 resolve 点值：
   - FaultRecordBinaryDecoder 解析二进制格式（magic 4B + version 2B + channel_count 2B + sample_rate 4B + timestamp 8B + sample_count 4B + values float32 LE, header 24 bytes）。
   - 解码产物为 DecodedSignal + StandardizedWaveformValue，符合 preprocessing pipeline 的 decode-before-resolve 约束。
   - file_ingest 解码不直接写 standardized 点值表（TdengineStandardizedSink）。

5. 波形独立 sink：
   - `src/whale/storage/waveform.py` 定义 StandardizedWaveformSinkPort。
   - InMemoryStandardizedWaveformSink 用于 P1/P3 开发验证。
   - TdengineStandardizedWaveformSink 为真实 REST API adapter（Round C: 已从 contract-only 升级为真实 TDengine REST API write()/readback()），当前环境 taosAdapter 不可用（P5 集成测试 3 FAIL, MISSING_ENVIRONMENT）。正确行为：连接失败时不抛异常，write() 返回 False，readback() 返回 []。
   - 波形 sink 与 TdengineStandardizedSink（点值）物理分离，避免 schema 混淆和高频浮点数组写入对点值索引的冲击。

6. fault_event 为运行期元数据：
   - FileIngestService 编排闭环记录 fault_event（文件路径、时间范围、故障类型等）。
   - 本轮 fault_event 为 Python 运行期对象；ORM 持久化模型留到后续实现。

7. 端到端编排：
   - FileIngestService 闭环: detect completion -> raw_archive original file -> decode (FaultRecordBinaryDecoder) -> waveform sink (StandardizedWaveformSinkPort) -> fault_event recording。
   - speed_layer preprocessing pipeline 阶段 9（write standardized）在文件接入场景中由 StandardizedWaveformSinkPort 承载；阶段 10（update state view）的 StateViewRecord 来源于 ResolvedSignal（点值），与波形路径分离。

## Consequences

- 文件接入与协议采集在 ingest 层共用 port-adapter 架构，但数据路径物理分离（文件 -> raw_archive + waveform sink，协议 -> cache -> message -> speed_layer -> storage）。
- waveform.py 定义独立 sink 端口，允许未来替换 TDengine 为 Parquet/HDF5 等大规模时间序列格式。
- TdengineStandardizedWaveformSink 已实现为真实 REST API adapter（Round C），当前环境 taosAdapter 不可用导致 P5 集成测试 FAIL（MISSING_ENVIRONMENT，非代码缺陷）。
- fault_event ORM 模型缺失，仅记录运行期日志/字典，不参与 scheduler/lease/job 生命周期。
- decode-before-resolve 约束保持：ingest/file_ingest 不解码即 resolve；StandardizedWaveformValue 包含原始解码值 + 质量元数据；ResolvedSignal（点值映射）由 preprocessing pipeline 承担。

## Rejected Options

- 将波形数据存入 TdengineStandardizedSink 同一张表：波形数组字段与 scalar value 语义不匹配，大数据量写入将影响点值查询性能。
- 在 speed_layer 中集成文件检测逻辑：文件检测属于采集边界（ingest），speed_layer 只消费消息管道中的标准化数据。
- 在 file_ingest 中直接 resolve 点值：违反 decode-before-resolve 约束，且 file_ingest 只关注故障录波原始波形，业务映射应在 speed_layer/preprocessing 完成。

## Related Files

- `src/whale/ingest/file_ingest/__init__.py`
- `src/whale/ingest/file_ingest/models.py`
- `src/whale/ingest/file_ingest/detector.py`
- `src/whale/ingest/file_ingest/decoder.py`
- `src/whale/ingest/file_ingest/repository.py`
- `src/whale/ingest/file_ingest/service.py`
- `src/whale/storage/waveform.py`
- `src/whale/speed_layer/preprocessing/models.py` (StandardizedWaveformValue)
- `src/whale/speed_layer/preprocessing/pipeline.py` (阶段 9: write standardized)
- `tests/unit/test_ingest_file_ingest_*.py`
- `tests/integration/test_ingest_file_ingest_integration.py`
- `tests/unit/test_storage_waveform.py`
- `tests/integration/test_storage_waveform_tdengine_integration.py` (Round C: 4 tests, 3 FAIL MISSING_ENVIRONMENT)

## Supersedes / Superseded By

无。本 ADR 为新增边界决策，不替代已有 ADR。
