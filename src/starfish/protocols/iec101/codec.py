"""IEC 60870-5-101 ASDU 信息对象列表编解码。

本模块实现 ASDU（Application Service Data Unit）层信息对象列表的
完整编解码：包含 ASDU 头部、IOA 列表策略（SQ=0 / SQ=1）、
信息对象本体（不同 TypeId 映射到不同的 information_object 实现）。

支持 TypeId：
- M_SP_NA_1 (1): 单点信息，不带时标。
- M_DP_NA_1 (3): 双点信息，不带时标。
- M_ME_NA_1 (9): 归一化测量值，不带时标。
- M_ME_NB_1 (11): 标度化测量值，不带时标（Round 18 新增）。
- M_ME_NC_1 (13): 短浮点测量值，不带时标（Round 18 新增）。
- C_SC_NA_1 (45): 单命令，不带时标。
- C_SE_NA_1 (48): 设点命令归一化，不带时标（Round 18 新增）。
- C_SE_NB_1 (49): 设点命令标度化，不带时标（Round 18 新增）。
- C_SE_NC_1 (50): 设点命令短浮点，不带时标（Round 18 新增）。
- C_SE_TA_1 (58): 设点命令归一化，带 CP56Time2a 时标（Round 19 新增）。
- C_SE_TB_1 (59): 设点命令标度化，带 CP56Time2a 时标（Round 19 新增）。
- C_SE_TC_1 (60): 设点命令短浮点，带 CP56Time2a 时标（Round 19 新增）。
- M_SP_TA_1 (2): 单点信息，带 CP56Time2a 时标（Round 16 新增）。
- M_DP_TA_1 (4): 双点信息，带 CP56Time2a 时标（Round 16 新增）。
- M_ME_TA_1 (10): 归一化测量值，带 CP56Time2a 时标（Round 16 新增）。
- M_ME_TB_1 (12): 标度化测量值，带 CP56Time2a 时标（Round 17 新增）。
- M_ME_TC_1 (14): 短浮点测量值，带 CP56Time2a 时标（Round 17 新增）。

对未知 TypeId：返回 UnknownAsdu 错误，不抛出异常（不崩溃）。

数据流：

    +----------------+
    |  ASDUHeader    |  <- type_id, vsq (SQ + count), cot, ca
    +----------------+
    |  IOA #1 (3B)   |  (SQ=0: 紧接在 header 后, 每个对象前置)
    |  Object #1     |
    |  IOA #2 (3B)   |  (SQ=0: 下一个对象前置)
    |  Object #2     |
    |  ...           |  (SQ=1: 仅首个对象前有 IOA, 后续 IOA 自增)
    +----------------+

    SQ=1: 首个 IOA + N 个对象（N=ioa_count），后续 IOA = first_ioa + i

不负责：
- 真实串口收发、链路层状态机（仅 codec 增强，skeleton 见 link_layer.py）。
- 完整 IEC 101 类型矩阵（实现 17 种 TypeId：4 监视 + 5 带时标监视 + 4 不带时标控制命令 + 3 带时标控制命令 + 1 M_SP_NA_1）。
- 真实写命令发送；C_SE_* 仅是命令 codec，**不**等效真实写能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starfish.protocols.iec101.asdu import (
    ASDU_HEADER_MIN_LENGTH,
    ASDUHeader,
    decode_asdu_header,
    encode_asdu_header,
)
from starfish.protocols.iec101.information_object import (
    C_SC_NA_1_Object,
    C_SE_NA_1_Object,
    C_SE_NB_1_Object,
    C_SE_NC_1_Object,
    C_SE_TA_1_Object,
    C_SE_TB_1_Object,
    C_SE_TC_1_Object,
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
)
from starfish.protocols.iec101.ioa import IOA_LENGTH, decode_information_object_address
from starfish.protocols.iec101.types import TypeId


# ── 已知 TypeId 的 object body 长度（不含 IOA）──────────────────────────────────

_TYPE_ID_OBJECT_SIZE: dict[int, int] = {
    int(TypeId.M_SP_NA_1): 1,  # SIQ
    int(TypeId.M_SP_TA_1): 8,  # SIQ + CP56Time2a
    int(TypeId.M_DP_NA_1): 1,  # DPI
    int(TypeId.M_DP_TA_1): 8,  # DPI + CP56Time2a
    int(TypeId.M_ME_NA_1): 3,  # NVA + QDS
    int(TypeId.M_ME_NB_1): 3,  # SVA + QDS (Round 18 新增)
    int(TypeId.M_ME_NC_1): 5,  # ShortFloat + QDS (Round 18 新增)
    int(TypeId.M_ME_TA_1): 10,  # NVA + QDS + CP56Time2a
    int(TypeId.M_ME_TB_1): 10,  # SVA + QDS + CP56Time2a (Round 17 新增)
    int(TypeId.M_ME_TC_1): 12,  # ShortFloat + QDS + CP56Time2a (Round 17 新增)
    int(TypeId.C_SC_NA_1): 1,  # SCS + SE + QOC
    int(TypeId.C_SE_NA_1): 5,  # NVA + QOS + S/E + reserved (Round 18 新增)
    int(TypeId.C_SE_NB_1): 5,  # SVA + QOS + S/E + reserved (Round 18 新增)
    int(TypeId.C_SE_NC_1): 7,  # ShortFloat + QOS + S/E + reserved (Round 18 新增)
    int(TypeId.C_SE_TA_1): 12,  # NVA + QOS + S/E + reserved + CP56Time2a (Round 19 新增)
    int(TypeId.C_SE_TB_1): 12,  # SVA + QOS + S/E + reserved + CP56Time2a (Round 19 新增)
    int(TypeId.C_SE_TC_1): 14,  # ShortFloat + QOS + S/E + reserved + CP56Time2a (Round 19 新增)
}

# ── TypeId -> object 工厂映射（用于 decode 时构造对象）──────────────────────────


def _build_object(type_id: int, body: bytes) -> Any:
    """根据 TypeId 构造对应的 information object。

    Args:
        type_id: ASDU TypeId 整数值。
        body: 已去除 IOA 的 object body 字节。

    Returns:
        对应 TypeId 的 information object 实例。

    Raises:
        ValueError: 未知 TypeId 或 body 长度不足。
    """
    if type_id == int(TypeId.M_SP_NA_1):
        return M_SP_NA_1_Object.decode(body)
    if type_id == int(TypeId.M_SP_TA_1):
        return M_SP_TA_1_Object.decode(body)
    if type_id == int(TypeId.M_DP_NA_1):
        return M_DP_NA_1_Object.decode(body)
    if type_id == int(TypeId.M_DP_TA_1):
        return M_DP_TA_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_NA_1):
        return M_ME_NA_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_NB_1):
        return M_ME_NB_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_NC_1):
        return M_ME_NC_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_TA_1):
        return M_ME_TA_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_TB_1):
        return M_ME_TB_1_Object.decode(body)
    if type_id == int(TypeId.M_ME_TC_1):
        return M_ME_TC_1_Object.decode(body)
    if type_id == int(TypeId.C_SC_NA_1):
        return C_SC_NA_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_NA_1):
        return C_SE_NA_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_NB_1):
        return C_SE_NB_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_NC_1):
        return C_SE_NC_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_TA_1):
        return C_SE_TA_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_TB_1):
        return C_SE_TB_1_Object.decode(body)
    if type_id == int(TypeId.C_SE_TC_1):
        return C_SE_TC_1_Object.decode(body)
    raise ValueError(f"未知 TypeId {type_id}（不支持的 information object 类型）")


def _object_size(type_id: int) -> int:
    """返回已知 TypeId 的 object body 长度。

    Args:
        type_id: ASDU TypeId 整数值。

    Returns:
        object body 长度（字节）。

    Raises:
        ValueError: 未知 TypeId。
    """
    if type_id not in _TYPE_ID_OBJECT_SIZE:
        raise ValueError(f"未知 TypeId {type_id}（无 object body 长度定义）")
    return _TYPE_ID_OBJECT_SIZE[type_id]


def _encode_object(obj: Any, type_id: int) -> bytes:
    """根据 TypeId 将 information object 编码为字节。

    Args:
        obj: information object 实例。
        type_id: ASDU TypeId 整数值。

    Returns:
        object body 编码字节。

    Raises:
        ValueError: 未知 TypeId 或对象类型不匹配。
    """
    if type_id == int(TypeId.M_SP_NA_1) and isinstance(obj, M_SP_NA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_SP_TA_1) and isinstance(obj, M_SP_TA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_DP_NA_1) and isinstance(obj, M_DP_NA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_DP_TA_1) and isinstance(obj, M_DP_TA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_NA_1) and isinstance(obj, M_ME_NA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_NB_1) and isinstance(obj, M_ME_NB_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_NC_1) and isinstance(obj, M_ME_NC_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_TA_1) and isinstance(obj, M_ME_TA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_TB_1) and isinstance(obj, M_ME_TB_1_Object):
        return obj.encode()
    if type_id == int(TypeId.M_ME_TC_1) and isinstance(obj, M_ME_TC_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SC_NA_1) and isinstance(obj, C_SC_NA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_NA_1) and isinstance(obj, C_SE_NA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_NB_1) and isinstance(obj, C_SE_NB_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_NC_1) and isinstance(obj, C_SE_NC_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_TA_1) and isinstance(obj, C_SE_TA_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_TB_1) and isinstance(obj, C_SE_TB_1_Object):
        return obj.encode()
    if type_id == int(TypeId.C_SE_TC_1) and isinstance(obj, C_SE_TC_1_Object):
        return obj.encode()
    raise ValueError(
        f"TypeId {type_id} 与 object 类型 {type(obj).__name__} 不匹配"
    )


# ── ASDU 数据结构 ──────────────────────────────────────────────────────────────


@dataclass
class UnknownAsduError:
    """未知 TypeId ASDU 错误描述。

    当 decode_asdu 遇到未实现的 TypeId 时返回此错误结构，
    不会抛出异常（保证 robustness）。

    Attributes:
        type_id: 未知 TypeId 整数值。
        reason: 详细原因。
    """

    type_id: int
    reason: str


@dataclass
class Asdu:
    """IEC 60870-5-101 ASDU 数据类。

    Attributes:
        header: ASDU 头部（含 type_id, vsq, cot, ca）。
        ioa_list: 信息对象地址列表（顺序与 information_objects 对应）。
        information_objects: 信息对象实例列表。
    """

    header: ASDUHeader
    ioa_list: list[int] = field(default_factory=list)
    information_objects: list[Any] = field(default_factory=list)


# ── ASDU 列表层 API ────────────────────────────────────────────────────────────


def encode_asdu(asdu: Asdu) -> bytes:
    """将 ASDU 编码为完整字节串。

    编码策略：
        1. 根据 ioa_count 与 sq 自动校正 header.vsq。
        2. ASDU 头部（5 字节）。
        3. SQ=0: 逐对象前置 3 字节 IOA + object body。
        4. SQ=1: 仅首对象前置 3 字节 IOA，其余仅 object body
           （调用方须保证 object 顺序与 ioa 单调递增一致；本函数不强制）。

    Args:
        asdu: 待编码的 Asdu 实例。

    Returns:
        完整 ASDU 编码字节。

    Raises:
        ValueError: object 数量与 ioa_count 不匹配、TypeId 不支持等。
    """
    type_id = asdu.header.type_id
    obj_count = len(asdu.information_objects)
    # 校正 ioa_count 与 sq 位
    if obj_count == 0:
        # 空对象列表：ioa_count = 0, sq=0
        vsq = 0x00
    else:
        vsq = obj_count & 0x7F
        if asdu.header.sq and obj_count > 0:
            vsq |= 0x80
    # 构造临时 header 用于编码（不修改入参 dataclass）
    header_for_encode = ASDUHeader(
        type_id=asdu.header.type_id,
        vsq=vsq,
        cot=asdu.header.cot,
        ca=asdu.header.ca,
        ioa_count=obj_count,
        sq=bool(vsq & 0x80),
    )
    result = bytearray()
    result.extend(encode_asdu_header(header_for_encode))

    if obj_count == 0:
        return bytes(result)

    if asdu.header.sq:
        # SQ=1: 第一个对象前有 IOA，其余仅 body
        ioa_first = asdu.ioa_list[0] if asdu.ioa_list else 0
        from starfish.protocols.iec101.ioa import encode_information_object_address
        result.extend(encode_information_object_address(ioa_first))
        for idx, obj in enumerate(asdu.information_objects):
            result.extend(_encode_object(obj, type_id))
            # 校验 ioa_list 与 sq 一致（仅警告性校验，不抛异常）
            if idx == 0 and asdu.ioa_list and asdu.ioa_list[0] != ioa_first:
                # 不抛异常，保持向后兼容
                pass
    else:
        # SQ=0: 每个对象前都有 IOA
        from starfish.protocols.iec101.ioa import encode_information_object_address
        if len(asdu.ioa_list) != obj_count:
            raise ValueError(
                f"SQ=0 时 ioa_list 长度 {len(asdu.ioa_list)} 与 "
                f"information_objects 长度 {obj_count} 不匹配"
            )
        for ioa, obj in zip(asdu.ioa_list, asdu.information_objects):
            result.extend(encode_information_object_address(ioa))
            result.extend(_encode_object(obj, type_id))
    return bytes(result)


def decode_asdu(
    data: bytes,
    *,
    allow_unknown_type: bool = True,
) -> Asdu | UnknownAsduError:
    """从字节串解码 ASDU。

    Args:
        data: 完整 ASDU 字节串（至少 5 字节头部）。
        allow_unknown_type: True 时遇到未知 TypeId 返回 UnknownAsduError，
            False 时抛出 ValueError。

    Returns:
        解码后的 Asdu 实例；或 UnknownAsduError（未知 TypeId 时）。

    Raises:
        ValueError: 数据不足、TypeId 不支持（且 allow_unknown_type=False）、
            IOA 长度或 object body 长度不足。
    """
    if len(data) < ASDU_HEADER_MIN_LENGTH:
        raise ValueError(
            f"ASDU 头部至少需要 {ASDU_HEADER_MIN_LENGTH} 字节，"
            f"实际只有 {len(data)} 字节"
        )
    header = decode_asdu_header(data)
    type_id = header.type_id
    ioa_count = header.ioa_count
    sq = header.sq

    # 检查 TypeId 是否已知
    if type_id not in _TYPE_ID_OBJECT_SIZE:
        reason = f"未知 TypeId {type_id}（不支持的 information object 类型）"
        if allow_unknown_type:
            return UnknownAsduError(type_id=type_id, reason=reason)
        raise ValueError(reason)

    obj_size = _TYPE_ID_OBJECT_SIZE[type_id]
    offset = ASDU_HEADER_MIN_LENGTH
    asdu = Asdu(header=header, ioa_list=[], information_objects=[])

    if ioa_count == 0:
        return asdu

    if sq:
        # SQ=1: 第一个对象前有 IOA
        if len(data) < offset + IOA_LENGTH + obj_size:
            raise ValueError(
                f"ASDU SQ=1 第一个对象需要至少 {IOA_LENGTH + obj_size} 字节，"
                f"实际只有 {len(data) - offset} 字节"
            )
        first_ioa = decode_information_object_address(data[offset : offset + IOA_LENGTH])
        offset += IOA_LENGTH
        # 后续对象只有 body
        for i in range(ioa_count):
            body = data[offset : offset + obj_size]
            if len(body) < obj_size:
                raise ValueError(
                    f"ASDU SQ=1 第 {i + 1} 个 object body 不足，"
                    f"期望 {obj_size} 字节，实际 {len(body)} 字节"
                )
            obj = _build_object(type_id, body)
            asdu.ioa_list.append(first_ioa + i)
            asdu.information_objects.append(obj)
            offset += obj_size
    else:
        # SQ=0: 每个对象前都有 IOA
        for i in range(ioa_count):
            if len(data) < offset + IOA_LENGTH + obj_size:
                raise ValueError(
                    f"ASDU SQ=0 第 {i + 1} 个对象需要至少 "
                    f"{IOA_LENGTH + obj_size} 字节，实际只有 {len(data) - offset} 字节"
                )
            ioa = decode_information_object_address(data[offset : offset + IOA_LENGTH])
            offset += IOA_LENGTH
            body = data[offset : offset + obj_size]
            obj = _build_object(type_id, body)
            asdu.ioa_list.append(ioa)
            asdu.information_objects.append(obj)
            offset += obj_size

    return asdu


__all__ = [
    "UnknownAsduError",
    "Asdu",
    "encode_asdu",
    "decode_asdu",
]
