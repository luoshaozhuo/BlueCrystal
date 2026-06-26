"""IEC 60870-5-101 编解码器骨架。

本子包提供 IEC 60870-5-101 协议帧编解码的基础结构，
包括：

- TypeId / CauseOfTransmission 枚举（types.py）
- ASDUHeader 数据类及其编解码（asdu.py）
- InformationObjectAddress (IOA) 编解码（3 字节，小端序）（ioa.py）
- CommonAddress (CA) 编解码（2 字节，小端序）（common_address.py）
- 质量描述符 SIQ / QDS（quality.py）
- 信息体元素 NVA / ShortFloat（information_elements.py，ShortFloat 为
  Round 17 新增；NaN/Inf 拒绝策略）
- CP56Time2a 7 字节时标 IE（time.py，Round 16 新增）
- 信息对象 M_SP_NA_1 / M_DP_NA_1 / M_ME_NA_1 / C_SC_NA_1 + 带时标
  M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1 + 带时标标度化/短浮点
  M_ME_TB_1 / M_ME_TC_1（information_object.py；后两者为 Round 17 新增）
- ASDU 信息对象列表编解码（codec.py）
- FT1.2 链路层帧编解码（frame.py）
- 链路层最小状态机 skeleton（link_layer.py，Round 16 新增，Round 17 扩展
  FCB/FCV helper / t1/t2/t3 协议计时器常量 / sequence flip / balanced
  vs unbalanced 差异化状态转移；**非 server**）

能力边界（Round 17 codec-enhanced-plus 收口阶段）：

    已实现: TypeId/COT 枚举、ASDUHeader/IOA/CA 编解码、SIQ/QDS 质量描述符、
           NVA 归一化值、ShortFloat IEEE 754 32-bit IE（4 字节 LE，
           NaN/Inf 拒绝）、CP56Time2a 7 字节时标、M_SP_NA_1/M_DP_NA_1/
           M_ME_NA_1/C_SC_NA_1 信息对象、SingleCommandQualifier 结构化 QU
           （含 select_execute / qualifier / ql / persistent 子字段）、
           带时标 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 + M_ME_TB_1/M_ME_TC_1
           信息对象、ASDU 信息对象列表（SQ=0 / SQ=1）编解码、FT1.2 固定/
           可变帧编解码、链路层最小状态机 skeleton（IDLE/WAIT_ACK/ERROR
           + FCB/FCV helper + t1/t2/t3 计时器常量 + sequence flip +
           balanced/unbalanced 模式差异化 skeleton 行为）。

    未实现: 完整 ASDU 类型矩阵（C_SE_* 等控制方向带时标命令 deferred）、
           完整 balanced/unbalanced 链路层状态机（仅 skeleton）、真实串口
           通信层。link_layer 仅 skeleton，不等同 server。Iec101Facade
           必须继续返回 supports_server=false / supports_serial_runtime=
           false；probe/profile/capacity 必须继续返回 NOT_RUN/CODEC_ONLY
           + reason。

这是编解码器骨架，不等同完整 IEC 60870-5-101 协议栈。
不负责真实串口通信、完整链路层状态机。
"""

from starfish.domain.protocols.iec101.types import CauseOfTransmission, TypeId
from starfish.domain.protocols.iec101.asdu import (
    ASDUHeader,
    decode_asdu_header,
    encode_asdu_header,
)
from starfish.domain.protocols.iec101.ioa import (
    decode_information_object_address,
    encode_information_object_address,
)
from starfish.domain.protocols.iec101.common_address import (
    decode_common_address,
    encode_common_address,
)
from starfish.domain.protocols.iec101.quality import (
    QDS,
    QDSFlags,
    SIQ,
    SIQFlags,
    decode_qds,
    decode_siq,
    encode_qds,
    encode_siq,
)
from starfish.domain.protocols.iec101.information_elements import (
    NVA_LENGTH,
    NVA_MAX,
    NVA_MIN,
    SHORT_FLOAT_FINITE_MAX,
    SHORT_FLOAT_FINITE_MIN,
    SHORT_FLOAT_LENGTH,
    SVA_INT16_MAX,
    SVA_INT16_MIN,
    SVA_LENGTH,
    NormalizedValue,
    ScaledValue,
    ShortFloat,
    decode_normalized_value,
    decode_scaled_value,
    decode_short_float,
    encode_normalized_value,
    encode_scaled_value,
    encode_short_float,
)
from starfish.domain.protocols.iec101.time import (
    CP56TIME2A_LENGTH,
    CP56Time2a,
    decode_cp56time2a,
    encode_cp56time2a,
    from_datetime,
    to_datetime,
)
from starfish.domain.protocols.iec101.information_object import (
    C_SC_NA_1_Object,
    C_SE_NA_1_Object,
    C_SE_NB_1_Object,
    C_SE_NC_1_Object,
    C_SE_TA_1_Object,
    C_SE_TB_1_Object,
    C_SE_TC_1_Object,
    CommandPulse,
    M_DP_NA_1_Object,
    M_DP_TA_1_Object,
    M_ME_NA_1_Object,
    M_ME_NB_1_Object,
    M_ME_NC_1_Object,
    M_ME_TA_1_Object,
    M_ME_TB_1_Object,
    M_ME_TC_1_Object,
    M_SP_NA_1_Object,
    M_SP_TA_1_Object,
    SetPointCommandQualifier,
    SetPointQualifier,
    SingleCommandQualifier,
)
from starfish.domain.protocols.iec101.codec import (
    Asdu,
    UnknownAsduError,
    decode_asdu,
    encode_asdu,
)
from starfish.domain.protocols.iec101.frame import (
    END_CHAR,
    FIXED_FRAME_SIZE,
    FixedFrame,
    FrameDecodeResult,
    FrameError,
    LinkControl,
    START_CHAR_FIXED,
    START_CHAR_VARIABLE,
    VARIABLE_FRAME_MAX_PAYLOAD,
    VARIABLE_FRAME_MAX_SIZE,
    VariableFrame,
    compute_checksum,
    decode_frame,
    verify_checksum,
)
from starfish.domain.protocols.iec101.link_layer import (
    T1_DEFAULT_MS,
    T2_DEFAULT_MS,
    T3_DEFAULT_MS,
    DefaultLinkLayerTimerService,
    FakeLinkLayerTimerService,
    LinkControlHelper,
    LinkEvent,
    LinkLayer,
    LinkLayerMode,
    LinkLayerTimerService,
    LinkLayerTimers,
    LinkState,
)

__all__ = [
    # types
    "TypeId",
    "CauseOfTransmission",
    # asdu header
    "ASDUHeader",
    "encode_asdu_header",
    "decode_asdu_header",
    # ioa
    "encode_information_object_address",
    "decode_information_object_address",
    # ca
    "encode_common_address",
    "decode_common_address",
    # quality
    "SIQ",
    "QDS",
    "SIQFlags",
    "QDSFlags",
    "encode_siq",
    "decode_siq",
    "encode_qds",
    "decode_qds",
    # information elements
    "NVA_LENGTH",
    "NVA_MIN",
    "NVA_MAX",
    "SVA_LENGTH",
    "SVA_INT16_MIN",
    "SVA_INT16_MAX",
    "SHORT_FLOAT_LENGTH",
    "SHORT_FLOAT_FINITE_MAX",
    "SHORT_FLOAT_FINITE_MIN",
    "NormalizedValue",
    "ScaledValue",
    "ShortFloat",
    "encode_normalized_value",
    "decode_normalized_value",
    "encode_scaled_value",
    "decode_scaled_value",
    "encode_short_float",
    "decode_short_float",
    # CP56Time2a
    "CP56TIME2A_LENGTH",
    "CP56Time2a",
    "encode_cp56time2a",
    "decode_cp56time2a",
    "from_datetime",
    "to_datetime",
    # information objects
    "M_SP_NA_1_Object",
    "M_DP_NA_1_Object",
    "M_ME_NA_1_Object",
    "M_ME_NB_1_Object",
    "M_ME_NC_1_Object",
    "C_SC_NA_1_Object",
    "C_SE_NA_1_Object",
    "C_SE_NB_1_Object",
    "C_SE_NC_1_Object",
    "C_SE_TA_1_Object",
    "C_SE_TB_1_Object",
    "C_SE_TC_1_Object",
    "M_SP_TA_1_Object",
    "M_DP_TA_1_Object",
    "M_ME_TA_1_Object",
    "M_ME_TB_1_Object",
    "M_ME_TC_1_Object",
    "CommandPulse",
    "SetPointQualifier",
    "SingleCommandQualifier",
    "SetPointCommandQualifier",
    # asdu list codec
    "Asdu",
    "UnknownAsduError",
    "encode_asdu",
    "decode_asdu",
    # frame
    "START_CHAR_FIXED",
    "START_CHAR_VARIABLE",
    "END_CHAR",
    "LinkControl",
    "FIXED_FRAME_SIZE",
    "VARIABLE_FRAME_MAX_PAYLOAD",
    "VARIABLE_FRAME_MAX_SIZE",
    "FixedFrame",
    "VariableFrame",
    "FrameDecodeResult",
    "FrameError",
    "compute_checksum",
    "verify_checksum",
    "decode_frame",
    # link layer skeleton
    "LinkLayerMode",
    "LinkState",
    "LinkEvent",
    "LinkControlHelper",
    "LinkLayerTimers",
    "LinkLayerTimerService",
    "DefaultLinkLayerTimerService",
    "FakeLinkLayerTimerService",
    "T1_DEFAULT_MS",
    "T2_DEFAULT_MS",
    "T3_DEFAULT_MS",
    "LinkLayer",
]
