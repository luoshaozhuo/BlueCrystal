"""Starfish IEC 60870-5-101 信息对象（Information Object）测试。

验证：
1. M_SP_NA_1 / M_DP_NA_1 / M_ME_NA_1 / C_SC_NA_1 信息对象 roundtrip。
2. ASDU 列表 SQ=0 多个对象 roundtrip。
3. ASDU 列表 SQ=1 连续信息对象 roundtrip。
4. 未知 TypeId 解码返回 UnknownAsduError，不崩溃。
5. ASDU 列表与 IOA 一致性。
6. M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1 带时标信息对象（Round 16 新增）。
7. SingleCommandQualifier 结构化 QU 字段（Round 16 新增，Round 17 扩展
   select_execute / qualifier / ql / persistent / CommandPulse）。
8. M_ME_TB_1 / M_ME_TC_1 带时标标度化/短浮点信息对象
   （Round 17 新增）。
9. ASDU 列表支持 M_ME_TB_1 / M_ME_TC_1 编解码。
10. M_ME_NB_1 / M_ME_NC_1 不带时标标度化/短浮点信息对象
    （Round 18 新增）。
11. C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1 不带时标设定值命令
    （Round 18 新增）。
12. SetPointCommandQualifier QOS 字段（Round 18 新增）。
13. ASDU 列表支持 M_ME_NB_1 / M_ME_NC_1 / C_SE_* 编解码
    （Round 18 新增）。
14. C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 带时标设定值命令
    （Round 19 新增）。
15. ASDU SQ=0 / SQ=1 包含 3 个带时标命令（Round 19 新增）。
16. SetPointCommandQualifier QOS 与 select_execute 联合测试
    （Round 19 强化）。

测试阶段：开发期验证 (P1)。
使用的替身：无（纯编解码器测试）。
不能证明：真实 IEC101 server 帧正确性、链路层能力、串口通信。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

import pytest

from starfish.domain.protocols.iec101 import (
    Asdu,
    C_SC_NA_1_Object,
    C_SE_NA_1_Object,
    C_SE_NB_1_Object,
    C_SE_NC_1_Object,
    C_SE_TA_1_Object,
    C_SE_TB_1_Object,
    C_SE_TC_1_Object,
    CP56Time2a,
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
    QDS,
    SIQ,
    SetPointCommandQualifier,
    SetPointQualifier,
    SingleCommandQualifier,
    UnknownAsduError,
    decode_asdu,
    encode_asdu,
)
from starfish.domain.protocols.iec101.types import TypeId
from starfish.domain.protocols.iec101.asdu import ASDUHeader


# ── M_SP_NA_1 信息对象测试 ────────────────────────────────────────────────────


class TestMSPNA1Object:
    """M_SP_NA_1 信息对象编解码测试。"""

    def test_m_sp_na_1_encode(self) -> None:
        """M_SP_NA_1 编码为 1 字节（SIQ）。"""
        siq = SIQ(value=True)
        obj = M_SP_NA_1_Object(siq=siq)
        assert obj.encode() == b"\x01"

    def test_m_sp_na_1_decode(self) -> None:
        """M_SP_NA_1 解码 1 字节。"""
        obj = M_SP_NA_1_Object.decode(b"\x01")
        assert obj.siq.value is True

    def test_m_sp_na_1_roundtrip(self) -> None:
        """M_SP_NA_1 多种 SIQ 组合 roundtrip。"""
        siqs = [
            SIQ(value=False),
            SIQ(value=True),
            SIQ(value=True, blocked=True),
            SIQ(value=False, substituted=True, not_topical=True),
            SIQ(value=True, blocked=True, substituted=True, not_topical=True, invalid=True),
        ]
        for siq in siqs:
            obj = M_SP_NA_1_Object(siq=siq)
            decoded = M_SP_NA_1_Object.decode(obj.encode())
            assert decoded.siq.value == siq.value
            assert decoded.siq.blocked == siq.blocked
            assert decoded.siq.substituted == siq.substituted
            assert decoded.siq.not_topical == siq.not_topical
            assert decoded.siq.invalid == siq.invalid

    def test_m_sp_na_1_decode_too_short(self) -> None:
        """M_SP_NA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_SP_NA_1_Object.decode(b"")


# ── M_DP_NA_1 信息对象测试 ────────────────────────────────────────────────────


class TestMDPNA1Object:
    """M_DP_NA_1 信息对象编解码测试。"""

    def test_m_dp_na_1_encode_off(self) -> None:
        """M_DP_NA_1 DPI=OFF (1) 编码为 0x01。"""
        obj = M_DP_NA_1_Object(dpi=1)
        assert obj.encode() == b"\x01"

    def test_m_dp_na_1_encode_on(self) -> None:
        """M_DP_NA_1 DPI=ON (2) 编码为 0x02。"""
        obj = M_DP_NA_1_Object(dpi=2)
        assert obj.encode() == b"\x02"

    def test_m_dp_na_1_encode_intermediate(self) -> None:
        """M_DP_NA_1 DPI=INTERMEDIATE (0) 编码为 0x00。"""
        obj = M_DP_NA_1_Object(dpi=0)
        assert obj.encode() == b"\x00"

    def test_m_dp_na_1_encode_indeterminate(self) -> None:
        """M_DP_NA_1 DPI=INDETERMINATE (3) 编码为 0x03。"""
        obj = M_DP_NA_1_Object(dpi=3)
        assert obj.encode() == b"\x03"

    def test_m_dp_na_1_decode(self) -> None:
        """M_DP_NA_1 解码。"""
        for dpi_val in (0, 1, 2, 3):
            obj = M_DP_NA_1_Object.decode(bytes([dpi_val]))
            assert obj.dpi == dpi_val

    def test_m_dp_na_1_invalid_dpi(self) -> None:
        """M_DP_NA_1 越界 DPI 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_DP_NA_1_Object(dpi=4)
        with pytest.raises(ValueError):
            M_DP_NA_1_Object(dpi=-1)

    def test_m_dp_na_1_roundtrip(self) -> None:
        """M_DP_NA_1 多种 DPI roundtrip。"""
        for dpi_val in (0, 1, 2, 3):
            obj = M_DP_NA_1_Object(dpi=dpi_val)
            decoded = M_DP_NA_1_Object.decode(obj.encode())
            assert decoded.dpi == dpi_val

    def test_m_dp_na_1_decode_too_short(self) -> None:
        """M_DP_NA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_DP_NA_1_Object.decode(b"")


# ── M_ME_NA_1 信息对象测试 ────────────────────────────────────────────────────


class TestMMENA1Object:
    """M_ME_NA_1 信息对象编解码测试。"""

    def test_m_me_na_1_encode(self) -> None:
        """M_ME_NA_1 编码为 3 字节（NVA + QDS）。"""
        obj = M_ME_NA_1_Object(nva=0.5, qds=QDS())
        encoded = obj.encode()
        assert len(encoded) == 3

    def test_m_me_na_1_decode(self) -> None:
        """M_ME_NA_1 解码 3 字节。"""
        obj = M_ME_NA_1_Object(nva=0.25, qds=QDS(invalid=True))
        encoded = obj.encode()
        decoded = M_ME_NA_1_Object.decode(encoded)
        assert abs(decoded.nva - 0.25) < 1e-6
        assert decoded.qds.invalid is True

    def test_m_me_na_1_roundtrip(self) -> None:
        """M_ME_NA_1 多种组合 roundtrip。

        NVA 为 16-bit 量化值（量化步长 1/32768），
        因此 roundtrip 误差应 < 1/32768 ≈ 3.05e-5。
        """
        cases = [
            (0.0, QDS()),
            (0.5, QDS(overflow=True)),
            (-0.5, QDS(invalid=True)),
            (0.99, QDS(substituted=True)),
            (-1.0, QDS(blocked=True, not_topical=True, invalid=True)),
        ]
        for nva, qds in cases:
            obj = M_ME_NA_1_Object(nva=nva, qds=qds)
            decoded = M_ME_NA_1_Object.decode(obj.encode())
            assert abs(decoded.nva - nva) < 1.0 / 32768.0
            assert decoded.qds.overflow == qds.overflow
            assert decoded.qds.blocked == qds.blocked
            assert decoded.qds.substituted == qds.substituted
            assert decoded.qds.not_topical == qds.not_topical
            assert decoded.qds.invalid == qds.invalid

    def test_m_me_na_1_decode_too_short(self) -> None:
        """M_ME_NA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_NA_1_Object.decode(b"\x01\x02")


# ── C_SC_NA_1 信息对象测试 ─────────────────────────────────────────────────────


class TestCSCNA1Object:
    """C_SC_NA_1 信息对象编解码测试。"""

    def test_c_sc_na_1_encode_off(self) -> None:
        """C_SC_NA_1 SCS=0 编码为 0x00。"""
        obj = C_SC_NA_1_Object(scs=0, select_execute=0, qualifier=0)
        assert obj.encode() == b"\x00"

    def test_c_sc_na_1_encode_on(self) -> None:
        """C_SC_NA_1 SCS=1 编码为 0x01。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0)
        assert obj.encode() == b"\x01"

    def test_c_sc_na_1_encode_select(self) -> None:
        """C_SC_NA_1 select=1, scs=1 编码为 0x03。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0)
        assert obj.encode() == b"\x03"

    def test_c_sc_na_1_decode(self) -> None:
        """C_SC_NA_1 解码。"""
        obj = C_SC_NA_1_Object.decode(b"\x01")
        assert obj.scs == 1
        assert obj.select_execute == 0

        obj2 = C_SC_NA_1_Object.decode(b"\x03")
        assert obj2.scs == 1
        assert obj2.select_execute == 1

    def test_c_sc_na_1_invalid_scs(self) -> None:
        """C_SC_NA_1 越界 SCS 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            C_SC_NA_1_Object(scs=2)
        with pytest.raises(ValueError):
            C_SC_NA_1_Object(scs=-1)

    def test_c_sc_na_1_invalid_select(self) -> None:
        """C_SC_NA_1 越界 select_execute 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            C_SC_NA_1_Object(scs=0, select_execute=2)

    def test_c_sc_na_1_invalid_qualifier(self) -> None:
        """C_SC_NA_1 越界 qualifier 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            C_SC_NA_1_Object(scs=0, qualifier=0x40)

    def test_c_sc_na_1_roundtrip(self) -> None:
        """C_SC_NA_1 多种组合 roundtrip。"""
        cases = [
            C_SC_NA_1_Object(scs=0, select_execute=0, qualifier=0),
            C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0),
            C_SC_NA_1_Object(scs=0, select_execute=1, qualifier=0),
            C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0x3F),
        ]
        for obj in cases:
            decoded = C_SC_NA_1_Object.decode(obj.encode())
            assert decoded.scs == obj.scs
            assert decoded.select_execute == obj.select_execute
            assert decoded.qualifier == obj.qualifier

    def test_c_sc_na_1_decode_too_short(self) -> None:
        """C_SC_NA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            C_SC_NA_1_Object.decode(b"")


# ── ASDU 列表 SQ=0 测试 ───────────────────────────────────────────────────────


class TestAsduSQFZero:
    """ASDU 列表 SQ=0 多个对象 roundtrip 测试。"""

    def test_asdu_sq0_m_sp_na_1_single(self) -> None:
        """ASDU SQ=0 单个 M_SP_NA_1 对象 roundtrip。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[M_SP_NA_1_Object(siq=SIQ(value=True))],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.header.type_id == 1
        assert decoded.header.ioa_count == 1
        assert decoded.header.sq is False
        assert decoded.ioa_list == [100]
        assert isinstance(decoded.information_objects[0], M_SP_NA_1_Object)
        assert decoded.information_objects[0].siq.value is True

    def test_asdu_sq0_m_sp_na_1_multiple(self) -> None:
        """ASDU SQ=0 多个 M_SP_NA_1 对象 roundtrip。"""
        siqs = [SIQ(value=True), SIQ(value=False), SIQ(value=True, blocked=True)]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x03, cot=3, ca=1, ioa_count=3, sq=False,
            ),
            ioa_list=[100, 101, 102],
            information_objects=[M_SP_NA_1_Object(siq=s) for s in siqs],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [100, 101, 102]
        assert len(decoded.information_objects) == 3
        for i, siq in enumerate(siqs):
            obj = decoded.information_objects[i]
            assert isinstance(obj, M_SP_NA_1_Object)
            assert obj.siq.value == siq.value
            assert obj.siq.blocked == siq.blocked

    def test_asdu_sq0_m_me_na_1(self) -> None:
        """ASDU SQ=0 M_ME_NA_1 roundtrip。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=9, vsq=0x02, cot=2, ca=2, ioa_count=2, sq=False,
            ),
            ioa_list=[200, 201],
            information_objects=[
                M_ME_NA_1_Object(nva=0.5, qds=QDS()),
                M_ME_NA_1_Object(nva=-0.25, qds=QDS(invalid=True)),
            ],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [200, 201]
        assert abs(decoded.information_objects[0].nva - 0.5) < 1e-6
        assert abs(decoded.information_objects[1].nva - (-0.25)) < 1e-6
        assert decoded.information_objects[1].qds.invalid is True

    def test_asdu_sq0_c_sc_na_1(self) -> None:
        """ASDU SQ=0 C_SC_NA_1 roundtrip。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=45, vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[300],
            information_objects=[
                C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0),
            ],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [300]
        obj = decoded.information_objects[0]
        assert isinstance(obj, C_SC_NA_1_Object)
        assert obj.scs == 1

    def test_asdu_sq0_mixed_type_ids(self) -> None:
        """ASDU SQ=0 同 TypeId 多个对象 roundtrip。"""
        objs = [M_DP_NA_1_Object(dpi=i) for i in (0, 1, 2, 3)]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=3, vsq=0x04, cot=2, ca=1, ioa_count=4, sq=False,
            ),
            ioa_list=[400, 401, 402, 403],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert len(decoded.information_objects) == 4
        for i, obj in enumerate(decoded.information_objects):
            assert isinstance(obj, M_DP_NA_1_Object)
            assert obj.dpi == i


# ── ASDU 列表 SQ=1 测试 ───────────────────────────────────────────────────────


class TestAsduSQFOne:
    """ASDU 列表 SQ=1 顺序寻址 roundtrip 测试。"""

    def test_asdu_sq1_m_sp_na_1_sequence(self) -> None:
        """ASDU SQ=1 M_SP_NA_1 顺序寻址 roundtrip。"""
        siqs = [SIQ(value=True), SIQ(value=False), SIQ(value=True)]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x83, cot=3, ca=1, ioa_count=3, sq=True,
            ),
            ioa_list=[500, 501, 502],
            information_objects=[M_SP_NA_1_Object(siq=s) for s in siqs],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.header.sq is True
        assert decoded.ioa_list == [500, 501, 502]
        assert len(decoded.information_objects) == 3
        for i, siq in enumerate(siqs):
            obj = decoded.information_objects[i]
            assert isinstance(obj, M_SP_NA_1_Object)
            assert obj.siq.value == siq.value

    def test_asdu_sq1_m_me_na_1_sequence(self) -> None:
        """ASDU SQ=1 M_ME_NA_1 顺序寻址 roundtrip。

        NVA 16-bit 量化，roundtrip 误差容差为 1/32768。
        """
        nvas = [0.1, 0.2, 0.3, 0.4, 0.5]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=9, vsq=0x85, cot=1, ca=1, ioa_count=5, sq=True,
            ),
            ioa_list=[600, 601, 602, 603, 604],
            information_objects=[M_ME_NA_1_Object(nva=v, qds=QDS()) for v in nvas],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [600, 601, 602, 603, 604]
        for i, nva in enumerate(nvas):
            assert abs(decoded.information_objects[i].nva - nva) < 1.0 / 32768.0

    def test_asdu_sq1_single_object(self) -> None:
        """ASDU SQ=1 单个对象 roundtrip。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x81, cot=3, ca=1, ioa_count=1, sq=True,
            ),
            ioa_list=[700],
            information_objects=[M_SP_NA_1_Object(siq=SIQ(value=True))],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [700]


# ── 未知 TypeId 测试 ──────────────────────────────────────────────────────────


class TestUnknownTypeId:
    """未知 TypeId 解码测试。"""

    def test_unknown_type_id_returns_error(self) -> None:
        """未知 TypeId 解码应返回 UnknownAsduError，不崩溃。"""
        # 构造一个未实现的 TypeId ASDU 字节串 (type_id=200)
        # header(5 字节) + ioa(3 字节) = 至少 8 字节
        data = bytes([200, 0x01, 0x03, 0x01, 0x00]) + b"\x00\x00\x00"
        result = decode_asdu(data, allow_unknown_type=True)
        assert isinstance(result, UnknownAsduError)
        assert result.type_id == 200
        assert "未知" in result.reason or "TypeId" in result.reason

    def test_unknown_type_id_raises_when_not_allowed(self) -> None:
        """未知 TypeId 且 allow_unknown_type=False 时应抛出 ValueError。"""
        data = bytes([200, 0x01, 0x03, 0x01, 0x00]) + b"\x00\x00\x00"
        with pytest.raises(ValueError):
            decode_asdu(data, allow_unknown_type=False)


# ── ASDU 边界测试 ─────────────────────────────────────────────────────────────


class TestAsduEdgeCases:
    """ASDU 边界测试。"""

    def test_asdu_empty_objects(self) -> None:
        """空信息对象列表应能正常编解码。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x00, cot=3, ca=1, ioa_count=0, sq=False,
            ),
            ioa_list=[],
            information_objects=[],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == []
        assert decoded.information_objects == []

    def test_asdu_decode_too_short(self) -> None:
        """ASDU 解码数据不足头部时抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_asdu(b"\x01\x02\x03")

    def test_asdu_encode_sq0_ioa_count_mismatch_raises(self) -> None:
        """ASDU SQ=0 ioa_list 与 objects 数量不匹配时抛出 ValueError。"""
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x02, cot=3, ca=1, ioa_count=2, sq=False,
            ),
            ioa_list=[100],  # 只有一个 IOA
            information_objects=[
                M_SP_NA_1_Object(siq=SIQ(value=True)),
                M_SP_NA_1_Object(siq=SIQ(value=False)),
            ],
        )
        with pytest.raises(ValueError):
            encode_asdu(asdu)


# ── SingleCommandQualifier 测试（Round 16 新增）────────────────────────────────


class TestSingleCommandQualifier:
    """C_SC_NA_1 QU 字段结构化（SingleCommandQualifier）测试。

    注意：S/E 位不在 QU 字段中，本类只建模 ql_value 与 persistent。
    """

    def test_default_values(self) -> None:
        """默认 ql_value=0 / persistent=False。"""
        qu = SingleCommandQualifier()
        assert qu.ql_value == 0
        assert qu.persistent is False

    def test_to_byte_default(self) -> None:
        """默认 SingleCommandQualifier.to_byte() == 0。"""
        assert SingleCommandQualifier().to_byte() == 0

    def test_to_byte_ql_value_2(self) -> None:
        """ql_value=2 -> bit 1-2 = 0b10 -> 0x04。"""
        qu = SingleCommandQualifier(ql_value=2)
        assert qu.to_byte() & 0x06 == 0x04

    def test_to_byte_ql_value_3(self) -> None:
        """ql_value=3 -> bit 1-2 = 0b11 -> 0x06。"""
        qu = SingleCommandQualifier(ql_value=3)
        assert qu.to_byte() & 0x06 == 0x06

    def test_to_byte_persistent(self) -> None:
        """persistent=True -> bit 3 = 1。"""
        qu = SingleCommandQualifier(persistent=True)
        assert qu.to_byte() & 0x08 == 0x08

    def test_to_byte_combined(self) -> None:
        """ql_value=2 + persistent=True -> 0x04 | 0x08 = 0x0C。"""
        qu = SingleCommandQualifier(ql_value=2, persistent=True)
        assert qu.to_byte() == 0x0C

    def test_from_byte_zero(self) -> None:
        """from_byte(0) -> ql_value=0 / persistent=False。"""
        qu = SingleCommandQualifier.from_byte(0)
        assert qu.ql_value == 0
        assert qu.persistent is False

    def test_from_byte_long_pulse(self) -> None:
        """from_byte(0x04) -> ql_value=2 (long pulse) / persistent=False。"""
        qu = SingleCommandQualifier.from_byte(0x04)
        assert qu.ql_value == 2
        assert qu.persistent is False

    def test_from_byte_persistent(self) -> None:
        """from_byte(0x08) -> ql_value=0 / persistent=True。"""
        qu = SingleCommandQualifier.from_byte(0x08)
        assert qu.ql_value == 0
        assert qu.persistent is True

    def test_from_byte_combined(self) -> None:
        """from_byte(0x0C) -> ql_value=2 + persistent=True。"""
        qu = SingleCommandQualifier.from_byte(0x0C)
        assert qu.ql_value == 2
        assert qu.persistent is True

    def test_from_byte_out_of_range(self) -> None:
        """from_byte(0x40) -> 越界抛出 ValueError。"""
        with pytest.raises(ValueError):
            SingleCommandQualifier.from_byte(0x40)

    def test_from_byte_negative(self) -> None:
        """from_byte(-1) -> 越界抛出 ValueError。"""
        with pytest.raises(ValueError):
            SingleCommandQualifier.from_byte(-1)

    def test_invalid_ql_value(self) -> None:
        """ql_value 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            SingleCommandQualifier(ql_value=4)
        with pytest.raises(ValueError):
            SingleCommandQualifier(ql_value=-1)

    def test_to_from_byte_roundtrip(self) -> None:
        """to_byte / from_byte roundtrip（仅限前 4 位：ql_value + persistent）。"""
        # 仅使用前 4 位有效位（0x00..0x0F）
        cases = [0, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E]
        for value in cases:
            qu = SingleCommandQualifier.from_byte(value)
            assert qu.to_byte() == value, f"roundtrip 失败: {value} -> {qu.to_byte()}"


class TestCSCNA1ObjectStructuredQU:
    """C_SC_NA_1 升级到 SingleCommandQualifier 的兼容性与新语义测试。"""

    def test_old_qualifier_zero_roundtrip(self) -> None:
        """旧用法 qualifier=0 应保持 SCS 编码 0x00/0x01 不变。"""
        for scs in (0, 1):
            obj = C_SC_NA_1_Object(scs=scs, select_execute=0, qualifier=0)
            expected = bytes([scs & 0x01])
            assert obj.encode() == expected

    def test_old_select_execute_roundtrip(self) -> None:
        """旧用法 select_execute=1 + qualifier=0 仍编码为 0x03。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0)
        assert obj.encode() == b"\x03"

    def test_old_qualifier_max_roundtrip(self) -> None:
        """旧用法 qualifier=0x3F 仍编码 0xFC 区间。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0x3F)
        # 0x01 | (0x01 << 1) | (0x3F << 2) = 0x01 | 0x02 | 0xFC = 0xFF
        assert obj.encode() == b"\xFF"

    def test_decode_preserves_qu_bit(self) -> None:
        """decode 应同时填充 qu_bit 结构化字段。"""
        obj = C_SC_NA_1_Object.decode(b"\x11")  # scs=1, s/e=0, qu=0b000100 (ql=2)
        assert obj.qu_bit.ql_value == 2
        assert obj.qu_bit.persistent is False

    def test_structured_long_pulse(self) -> None:
        """结构化 qu_bit ql_value=2 (long pulse) 经 sync_qu_bit 后编码为 0x11。"""
        qu = SingleCommandQualifier(ql_value=2)
        obj = C_SC_NA_1_Object(scs=1, qu_bit=qu)
        obj.sync_qu_bit()
        # scs=1, s/e=0, qu=0b000100 -> 0x01 | 0x10 = 0x11
        assert obj.encode() == b"\x11"

    def test_structured_select_execute_via_bit_field(self) -> None:
        """S/E 由 self.select_execute 维护，与 QU 字段正交。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0)
        # 显式构造的 qu_bit 来自 __post_init__ 自动填充
        assert obj.qu_bit.ql_value == 0
        assert obj.qu_bit.persistent is False
        # 编码：scs=1, s/e=1, qu=0 -> 0x01 | 0x02 = 0x03
        assert obj.encode() == b"\x03"

    def test_structured_persistent(self) -> None:
        """结构化 qu_bit persistent=True 经 sync_qu_bit 后编码为 0x20。"""
        qu = SingleCommandQualifier(persistent=True)
        obj = C_SC_NA_1_Object(scs=0, qu_bit=qu)
        obj.sync_qu_bit()
        # scs=0, s/e=0, qu=0b001000 -> 0x20
        assert obj.encode() == b"\x20"

    def test_qu_bit_explicit_preserved(self) -> None:
        """显式提供 qu_bit 时不应被 __post_init__ 覆盖。"""
        qu = SingleCommandQualifier(ql_value=1, persistent=False)
        obj = C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0, qu_bit=qu)
        # __post_init__ 应保留调用方提供的 qu_bit，不与位级字段同步
        assert obj.qu_bit.ql_value == 1
        assert obj.qu_bit.persistent is False
        # 位级字段保持调用方初始值（select_execute=0, qualifier=0）
        assert obj.select_execute == 0
        assert obj.qualifier == 0

    def test_sync_qu_bit_method(self) -> None:
        """sync_qu_bit 方法将 qu_bit 同步到 qualifier 位级字段。"""
        qu = SingleCommandQualifier(ql_value=2, persistent=True)
        obj = C_SC_NA_1_Object(scs=0, select_execute=0, qualifier=0, qu_bit=qu)
        obj.sync_qu_bit()
        # qu_bit.to_byte() = 0x04 | 0x08 = 0x0C
        assert obj.qualifier == 0x0C
        # select_execute 保持调用方初始值（S/E 不由 qu_bit 维护）
        assert obj.select_execute == 0


# ── M_SP_TA_1 带时标信息对象测试（Round 16 新增）────────────────────────────────


class TestMSPTA1Object:
    """M_SP_TA_1 信息对象（单点信息带 CP56Time2a）编解码测试。"""

    def test_m_sp_ta_1_size(self) -> None:
        """M_SP_TA_1 编码为 8 字节（SIQ + CP56Time2a）。"""
        obj = M_SP_TA_1_Object(
            siq=SIQ(value=True),
            time=CP56Time2a(),
        )
        encoded = obj.encode()
        assert len(encoded) == 8

    def test_m_sp_ta_1_roundtrip(self) -> None:
        """M_SP_TA_1 多种组合 roundtrip。"""
        cases = [
            M_SP_TA_1_Object(
                siq=SIQ(value=False),
                time=CP56Time2a(milliseconds=0, minute=0, hour=0, year=0),
            ),
            M_SP_TA_1_Object(
                siq=SIQ(value=True, blocked=True),
                time=CP56Time2a(
                    milliseconds=12345, minute=30, hour=15, day_of_month=15,
                    month=6, year=26, invalid=True, summer_time=True,
                ),
            ),
            M_SP_TA_1_Object(
                siq=SIQ(value=True, invalid=True, substituted=True),
                time=CP56Time2a(
                    milliseconds=59999, minute=59, hour=23, day_of_month=31,
                    month=12, year=99, invalid=True, summer_time=True,
                    substituted=True,
                ),
            ),
        ]
        for obj in cases:
            decoded = M_SP_TA_1_Object.decode(obj.encode())
            assert decoded.siq.value == obj.siq.value
            assert decoded.siq.blocked == obj.siq.blocked
            assert decoded.siq.invalid == obj.siq.invalid
            assert decoded.time.milliseconds == obj.time.milliseconds
            assert decoded.time.minute == obj.time.minute
            assert decoded.time.hour == obj.time.hour
            assert decoded.time.day_of_month == obj.time.day_of_month
            assert decoded.time.month == obj.time.month
            assert decoded.time.year == obj.time.year
            assert decoded.time.invalid == obj.time.invalid
            assert decoded.time.summer_time == obj.time.summer_time
            assert decoded.time.substituted == obj.time.substituted

    def test_m_sp_ta_1_decode_too_short(self) -> None:
        """M_SP_TA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_SP_TA_1_Object.decode(b"\x01\x02\x03")

    def test_m_sp_ta_1_asdu_roundtrip(self) -> None:
        """M_SP_TA_1 通过 ASDU 列表 roundtrip。"""
        obj = M_SP_TA_1_Object(
            siq=SIQ(value=True, invalid=True),
            time=CP56Time2a(
                milliseconds=1000, minute=30, hour=12, day_of_month=15,
                month=6, year=26,
            ),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=2, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_SP_TA_1_Object)
        assert decoded.information_objects[0].siq.value is True
        assert decoded.information_objects[0].time.minute == 30


# ── M_DP_TA_1 带时标信息对象测试（Round 16 新增）────────────────────────────────


class TestMDPTA1Object:
    """M_DP_TA_1 信息对象（双点信息带 CP56Time2a）编解码测试。"""

    def test_m_dp_ta_1_size(self) -> None:
        """M_DP_TA_1 编码为 8 字节（DPI + CP56Time2a）。"""
        obj = M_DP_TA_1_Object(
            dpi=2, time=CP56Time2a(),
        )
        encoded = obj.encode()
        assert len(encoded) == 8

    def test_m_dp_ta_1_roundtrip(self) -> None:
        """M_DP_TA_1 多种 DPI roundtrip。"""
        for dpi in (0, 1, 2, 3):
            obj = M_DP_TA_1_Object(
                dpi=dpi,
                time=CP56Time2a(
                    milliseconds=500, minute=15, hour=10, day_of_month=5,
                    month=3, year=24,
                ),
            )
            decoded = M_DP_TA_1_Object.decode(obj.encode())
            assert decoded.dpi == dpi
            assert decoded.time.minute == 15
            assert decoded.time.hour == 10

    def test_m_dp_ta_1_decode_too_short(self) -> None:
        """M_DP_TA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_DP_TA_1_Object.decode(b"\x01\x02")

    def test_m_dp_ta_1_invalid_dpi(self) -> None:
        """M_DP_TA_1 越界 DPI 应抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_DP_TA_1_Object(dpi=4, time=CP56Time2a())

    def test_m_dp_ta_1_asdu_roundtrip(self) -> None:
        """M_DP_TA_1 通过 ASDU 列表 roundtrip。"""
        obj = M_DP_TA_1_Object(
            dpi=2,
            time=CP56Time2a(minute=30, hour=12, year=26),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=4, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[200],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_DP_TA_1_Object)
        assert decoded.information_objects[0].dpi == 2
        assert decoded.information_objects[0].time.year == 26


# ── M_ME_TA_1 带时标信息对象测试（Round 16 新增）────────────────────────────────


class TestMMETA1Object:
    """M_ME_TA_1 信息对象（归一化测量值带 CP56Time2a）编解码测试。"""

    def test_m_me_ta_1_size(self) -> None:
        """M_ME_TA_1 编码为 10 字节（NVA + QDS + CP56Time2a）。"""
        obj = M_ME_TA_1_Object(
            nva=0.5, qds=QDS(), time=CP56Time2a(),
        )
        encoded = obj.encode()
        assert len(encoded) == 10

    def test_m_me_ta_1_roundtrip(self) -> None:
        """M_ME_TA_1 多种 NVA + QDS + time 组合 roundtrip。"""
        cases = [
            M_ME_TA_1_Object(
                nva=0.0, qds=QDS(),
                time=CP56Time2a(milliseconds=0, minute=0, hour=0, year=0),
            ),
            M_ME_TA_1_Object(
                nva=0.5, qds=QDS(overflow=True),
                time=CP56Time2a(
                    milliseconds=1234, minute=30, hour=12, day_of_month=15,
                    month=6, year=26, invalid=True,
                ),
            ),
            M_ME_TA_1_Object(
                nva=-0.75, qds=QDS(invalid=True, blocked=True, not_topical=True),
                time=CP56Time2a(
                    milliseconds=59999, minute=59, hour=23, day_of_month=31,
                    month=12, year=99,
                ),
            ),
        ]
        for obj in cases:
            decoded = M_ME_TA_1_Object.decode(obj.encode())
            assert abs(decoded.nva - obj.nva) < 1.0 / 32768.0
            assert decoded.qds.overflow == obj.qds.overflow
            assert decoded.qds.blocked == obj.qds.blocked
            assert decoded.qds.invalid == obj.qds.invalid
            assert decoded.time.milliseconds == obj.time.milliseconds
            assert decoded.time.minute == obj.time.minute
            assert decoded.time.year == obj.time.year

    def test_m_me_ta_1_decode_too_short(self) -> None:
        """M_ME_TA_1 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_TA_1_Object.decode(b"\x01\x02\x03\x04")

    def test_m_me_ta_1_asdu_roundtrip(self) -> None:
        """M_ME_TA_1 通过 ASDU 列表 roundtrip。"""
        obj = M_ME_TA_1_Object(
            nva=0.5,
            qds=QDS(overflow=True),
            time=CP56Time2a(minute=30, hour=12, year=26),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=10, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[300],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_ME_TA_1_Object)
        assert abs(decoded.information_objects[0].nva - 0.5) < 1e-6
        assert decoded.information_objects[0].qds.overflow is True
        assert decoded.information_objects[0].time.year == 26

    def test_m_me_ta_1_default_qds_time(self) -> None:
        """M_ME_TA_1 不传 qds/time 时应使用默认空 QDS + 零值 CP56Time2a。"""
        obj = M_ME_TA_1_Object(nva=0.0)
        assert isinstance(obj.qds, QDS)
        assert isinstance(obj.time, CP56Time2a)
        assert obj.time.milliseconds == 0


# ── M_ME_TB_1 带时标标度化测量值测试（Round 17 新增）────────────────────────────


class TestMMeTb1Object:
    """M_ME_TB_1 信息对象（标度化测量值带 CP56Time2a）编解码测试。"""

    def test_m_me_tb_1_size(self) -> None:
        """M_ME_TB_1 编码为 10 字节（SVA + QDS + CP56Time2a）。"""
        obj = M_ME_TB_1_Object(sva=100, qds=QDS(), time=CP56Time2a())
        encoded = obj.encode()
        assert len(encoded) == 10

    def test_m_me_tb_1_encode_sva_bytes(self) -> None:
        """M_ME_TB_1 sva 应编码为小端序 int16。"""
        obj = M_ME_TB_1_Object(sva=0x1234, qds=QDS(), time=CP56Time2a())
        encoded = obj.encode()
        # byte 0-1 = SVA, byte 2 = QDS, byte 3-9 = CP56Time2a
        assert encoded[0] == 0x34
        assert encoded[1] == 0x12

    def test_m_me_tb_1_negative_sva(self) -> None:
        """M_ME_TB_1 负 sva 应编码为 int16 LE。"""
        obj = M_ME_TB_1_Object(sva=-1, qds=QDS(), time=CP56Time2a())
        encoded = obj.encode()
        # -1 = 0xFFFF, LE = b"\xFF\xFF"
        assert encoded[0] == 0xFF
        assert encoded[1] == 0xFF

    def test_m_me_tb_1_roundtrip(self) -> None:
        """M_ME_TB_1 多种组合 roundtrip。"""
        cases = [
            M_ME_TB_1_Object(sva=0, qds=QDS(), time=CP56Time2a()),
            M_ME_TB_1_Object(
                sva=12345, qds=QDS(overflow=True),
                time=CP56Time2a(
                    milliseconds=1000, minute=30, hour=12,
                    day_of_month=15, month=6, year=26,
                ),
            ),
            M_ME_TB_1_Object(
                sva=-32768, qds=QDS(invalid=True, blocked=True),
                time=CP56Time2a(
                    milliseconds=59999, minute=59, hour=23,
                    day_of_month=31, month=12, year=99,
                ),
            ),
            M_ME_TB_1_Object(
                sva=32767, qds=QDS(substituted=True, not_topical=True),
                time=CP56Time2a(year=0),
            ),
        ]
        for obj in cases:
            decoded = M_ME_TB_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            assert decoded.qds.overflow == obj.qds.overflow
            assert decoded.qds.blocked == obj.qds.blocked
            assert decoded.qds.invalid == obj.qds.invalid
            assert decoded.time.milliseconds == obj.time.milliseconds
            assert decoded.time.minute == obj.time.minute
            assert decoded.time.year == obj.time.year

    def test_m_me_tb_1_invalid_sva(self) -> None:
        """M_ME_TB_1 sva 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_TB_1_Object(sva=32768, qds=QDS(), time=CP56Time2a())
        with pytest.raises(ValueError):
            M_ME_TB_1_Object(sva=-32769, qds=QDS(), time=CP56Time2a())

    def test_m_me_tb_1_decode_too_short(self) -> None:
        """M_ME_TB_1 解码数据不足 10 字节时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_TB_1_Object.decode(b"\x00" * 9)

    def test_m_me_tb_1_asdu_roundtrip(self) -> None:
        """M_ME_TB_1 通过 ASDU 列表 roundtrip。"""
        obj = M_ME_TB_1_Object(
            sva=12345, qds=QDS(overflow=True),
            time=CP56Time2a(minute=30, hour=12, year=26),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=12, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_ME_TB_1_Object)
        assert decoded.information_objects[0].sva == 12345
        assert decoded.information_objects[0].qds.overflow is True
        assert decoded.information_objects[0].time.year == 26

    def test_m_me_tb_1_default_qds_time(self) -> None:
        """M_ME_TB_1 不传 qds/time 时使用默认值。"""
        obj = M_ME_TB_1_Object(sva=100)
        assert isinstance(obj.qds, QDS)
        assert isinstance(obj.time, CP56Time2a)


# ── M_ME_TC_1 带时标短浮点测量值测试（Round 17 新增）────────────────────────────


class TestMMeTc1Object:
    """M_ME_TC_1 信息对象（短浮点测量值带 CP56Time2a）编解码测试。"""

    def test_m_me_tc_1_size(self) -> None:
        """M_ME_TC_1 编码为 12 字节（ShortFloat + QDS + CP56Time2a）。"""
        obj = M_ME_TC_1_Object(sva=3.14, qds=QDS(), time=CP56Time2a())
        encoded = obj.encode()
        assert len(encoded) == 12

    def test_m_me_tc_1_encode_short_float_bytes(self) -> None:
        """M_ME_TC_1 sva 应编码为 4 字节 IEEE 754 LE ShortFloat。"""
        obj = M_ME_TC_1_Object(sva=1.0, qds=QDS(), time=CP56Time2a())
        encoded = obj.encode()
        # 1.0 = 0x3F800000, LE = b"\x00\x00\x80\x3F"
        assert encoded[0] == 0x00
        assert encoded[1] == 0x00
        assert encoded[2] == 0x80
        assert encoded[3] == 0x3F

    def test_m_me_tc_1_roundtrip(self) -> None:
        """M_ME_TC_1 多种 ShortFloat 组合 roundtrip。

        仅使用 IEEE 754 single-precision 精确可表示的值
        （如 0.5、1.0、1.5、2.0 等二进制浮点）；3.14 此类
        十进制小数会引入精度误差，不在本测试范围内。
        """
        cases = [
            M_ME_TC_1_Object(sva=0.0, qds=QDS(), time=CP56Time2a()),
            M_ME_TC_1_Object(
                sva=2.5, qds=QDS(overflow=True),
                time=CP56Time2a(
                    milliseconds=1000, minute=30, hour=12,
                    day_of_month=15, month=6, year=26,
                ),
            ),
            M_ME_TC_1_Object(
                sva=-1.5, qds=QDS(invalid=True),
                time=CP56Time2a(
                    milliseconds=59999, minute=59, hour=23,
                    day_of_month=31, month=12, year=99,
                ),
            ),
            M_ME_TC_1_Object(
                sva=0.0625, qds=QDS(substituted=True),
                time=CP56Time2a(year=0),
            ),
        ]
        for obj in cases:
            decoded = M_ME_TC_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, (
                f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            )
            assert decoded.qds.overflow == obj.qds.overflow
            assert decoded.qds.invalid == obj.qds.invalid
            assert decoded.time.milliseconds == obj.time.milliseconds
            assert decoded.time.year == obj.time.year

    def test_m_me_tc_1_nan_rejected(self) -> None:
        """M_ME_TC_1 sva=NaN 应在 __post_init__ 通过 encode 路径抛出。"""
        obj = M_ME_TC_1_Object(sva=0.0, qds=QDS(), time=CP56Time2a())
        obj.sva = float("nan")
        with pytest.raises(ValueError, match="NaN"):
            obj.encode()

    def test_m_me_tc_1_inf_rejected(self) -> None:
        """M_ME_TC_1 sva=Inf 应在 encode 路径抛出。"""
        obj = M_ME_TC_1_Object(sva=0.0, qds=QDS(), time=CP56Time2a())
        obj.sva = float("inf")
        with pytest.raises(ValueError, match="Inf"):
            obj.encode()

    def test_m_me_tc_1_non_float_rejected(self) -> None:
        """M_ME_TC_1 sva 非 float 在 __post_init__ 抛出。"""
        with pytest.raises(TypeError, match="float"):
            M_ME_TC_1_Object(sva=1, qds=QDS(), time=CP56Time2a())  # type: ignore[arg-type]

    def test_m_me_tc_1_decode_too_short(self) -> None:
        """M_ME_TC_1 解码数据不足 12 字节时抛出 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_TC_1_Object.decode(b"\x00" * 11)

    def test_m_me_tc_1_asdu_roundtrip(self) -> None:
        """M_ME_TC_1 通过 ASDU 列表 roundtrip。"""
        obj = M_ME_TC_1_Object(
            sva=2.5, qds=QDS(overflow=True),
            time=CP56Time2a(minute=30, hour=12, year=26),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=14, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_ME_TC_1_Object)
        assert decoded.information_objects[0].sva == 2.5
        assert decoded.information_objects[0].qds.overflow is True
        assert decoded.information_objects[0].time.year == 26

    def test_m_me_tc_1_default_qds_time(self) -> None:
        """M_ME_TC_1 不传 qds/time 时使用默认值。"""
        obj = M_ME_TC_1_Object(sva=1.0)
        assert isinstance(obj.qds, QDS)
        assert isinstance(obj.time, CP56Time2a)


# ── CommandPulse 枚举 + SingleCommandQualifier 扩展字段测试（Round 17 新增）───


class TestCommandPulse:
    """CommandPulse 枚举测试。"""

    def test_enum_values(self) -> None:
        """CommandPulse 四个取值正确。"""
        assert CommandPulse.NO_QUALIFIER.value == "no_qualifier"
        assert CommandPulse.SHORT_PULSE.value == "short_pulse"
        assert CommandPulse.LONG_PULSE.value == "long_pulse"
        assert CommandPulse.PERSISTENT.value == "persistent"


class TestSingleCommandQualifierExtended:
    """SingleCommandQualifier 扩展字段（Round 17）测试。

    权威源策略：``ql_value`` 是协议位级字段权威源；``ql`` / ``pulse`` /
    ``qualifier`` 均为 ``ql_value`` 同步视图。``sync_from_qualifier()``
    提供"以 qualifier 位级反推结构化字段"的回写路径。
    """

    def test_select_execute_field(self) -> None:
        """select_execute 字段默认 0，可设为 1。"""
        qu = SingleCommandQualifier()
        assert qu.select_execute == 0
        qu2 = SingleCommandQualifier(select_execute=1)
        assert qu2.select_execute == 1

    def test_select_execute_invalid(self) -> None:
        """select_execute 越界抛出 ValueError。"""
        with pytest.raises(ValueError, match="select_execute"):
            SingleCommandQualifier(select_execute=2)

    def test_qualifier_field_default(self) -> None:
        """qualifier 字段默认与 to_byte() 一致（auto-sync）。"""
        qu = SingleCommandQualifier()
        assert qu.qualifier == qu.to_byte()

    def test_qualifier_field_out_of_range(self) -> None:
        """qualifier 越界抛出 ValueError。"""
        with pytest.raises(ValueError, match="qualifier"):
            SingleCommandQualifier(qualifier=0x40)

    def test_ql_alias(self) -> None:
        """ql 与 ql_value 互相同步（ql 跟随 ql_value）。"""
        qu = SingleCommandQualifier(ql_value=2)
        assert qu.ql == 2
        # ql_value 是权威源：ql=3 会被 ql_value=0 覆写
        qu2 = SingleCommandQualifier(ql_value=0, ql=3)
        assert qu2.ql == 0
        assert qu2.ql_value == 0  # 权威源不变

    def test_pulse_field_default(self) -> None:
        """pulse 字段默认 NO_QUALIFIER（ql_value 默认 0）。"""
        qu = SingleCommandQualifier()
        assert qu.pulse == CommandPulse.NO_QUALIFIER

    def test_pulse_field_short_pulse(self) -> None:
        """ql_value=1 时 pulse=SHORT_PULSE（auto-sync）。"""
        qu = SingleCommandQualifier(ql_value=1)
        assert qu.ql_value == 1
        assert qu.ql == 1
        assert qu.pulse == CommandPulse.SHORT_PULSE

    def test_pulse_field_long_pulse(self) -> None:
        """ql_value=2 时 pulse=LONG_PULSE（auto-sync）。"""
        qu = SingleCommandQualifier(ql_value=2)
        assert qu.ql_value == 2
        assert qu.pulse == CommandPulse.LONG_PULSE

    def test_pulse_field_persistent(self) -> None:
        """ql_value=3 时 pulse=PERSISTENT（auto-sync）。"""
        qu = SingleCommandQualifier(ql_value=3)
        assert qu.ql_value == 3
        assert qu.pulse == CommandPulse.PERSISTENT

    def test_ql_value_conflict_with_pulse(self) -> None:
        """ql_value 与 pulse 不一致时以 ql_value 为准（auto-sync）。"""
        qu = SingleCommandQualifier(ql_value=2, pulse=CommandPulse.NO_QUALIFIER)
        assert qu.pulse == CommandPulse.LONG_PULSE  # auto-sync

    def test_pulse_invalid_type(self) -> None:
        """pulse 非 CommandPulse 抛出 ValueError。"""
        with pytest.raises(ValueError, match="pulse"):
            SingleCommandQualifier(pulse="short_pulse")  # type: ignore[arg-type]

    def test_ql_out_of_range(self) -> None:
        """ql 越界抛出 ValueError。"""
        with pytest.raises(ValueError, match="ql"):
            SingleCommandQualifier(ql_value=4, ql=4)

    def test_sync_from_qualifier(self) -> None:
        """sync_from_qualifier 把 qualifier 同步到 ql_value / persistent / pulse。"""
        qu = SingleCommandQualifier(qualifier=0x0C)  # ql=2, persistent=True
        qu.sync_from_qualifier()
        assert qu.ql_value == 2
        assert qu.persistent is True
        assert qu.pulse == CommandPulse.LONG_PULSE

    def test_from_byte_pulse_populated(self) -> None:
        """from_byte 同时填充 pulse 字段（位级反推）。"""
        qu = SingleCommandQualifier.from_byte(0x04)  # ql=2
        assert qu.ql_value == 2
        assert qu.pulse == CommandPulse.LONG_PULSE
        qu2 = SingleCommandQualifier.from_byte(0x02)  # ql=1
        assert qu2.pulse == CommandPulse.SHORT_PULSE
        qu3 = SingleCommandQualifier.from_byte(0x08)  # persistent=True, ql=0
        assert qu3.pulse == CommandPulse.NO_QUALIFIER  # pulse 跟随 ql
        assert qu3.persistent is True
        qu4 = SingleCommandQualifier.from_byte(0x00)
        assert qu4.pulse == CommandPulse.NO_QUALIFIER


class TestCSCNA1SelectExecute:
    """C_SC_NA_1 S/E 位与 QU 字段正交性测试（Round 17）。"""

    def test_s_e_zero_qualifier_zero(self) -> None:
        """S/E=0, QU=0 应编码为 0x00。"""
        obj = C_SC_NA_1_Object(scs=0, select_execute=0, qualifier=0)
        assert obj.encode() == b"\x00"

    def test_s_e_one_qualifier_zero(self) -> None:
        """S/E=1, QU=0 应编码为 0x02。"""
        obj = C_SC_NA_1_Object(scs=0, select_execute=1, qualifier=0)
        assert obj.encode() == b"\x02"

    def test_s_e_one_with_short_pulse(self) -> None:
        """S/E=1, QU=SHORT_PULSE 应编码为 0x0A。

        字节布局：scs(1b) | s/e(1b) | qu(6b, 左移 2) = 0 | 0x02 | 0x08 = 0x0A。
        """
        obj = C_SC_NA_1_Object(
            scs=0, select_execute=1, qualifier=0,
        )
        obj.qu_bit = SingleCommandQualifier(ql_value=1)  # SHORT_PULSE
        obj.sync_qu_bit()
        # qualifier = (ql=1 << 1) | 0 = 2
        # encoded = scs(0) | s/e(1)<<1=0x02 | qualifier(2)<<2=0x08 = 0x0A
        assert obj.encode() == b"\x0A"

    def test_s_e_zero_with_long_pulse(self) -> None:
        """S/E=0, QU=LONG_PULSE 应编码为 0x10。

        字节布局：scs(1b) | s/e(1b) | qu(6b, 左移 2) = 0 | 0 | 0x10 = 0x10。
        qualifier = (ql=2 << 1) | 0 = 4; (4 << 2) = 16 = 0x10。
        """
        obj = C_SC_NA_1_Object(
            scs=0, select_execute=0, qualifier=0,
        )
        obj.qu_bit = SingleCommandQualifier(ql_value=2)  # LONG_PULSE
        obj.sync_qu_bit()
        assert obj.encode() == b"\x10"

    def test_decode_propagates_select_execute(self) -> None:
        """decode 应把 S/E 同步到 qu_bit.select_execute。"""
        # 字节 0x0A = 0b00001010: scs=0, s/e=1, qu=0b000010 (ql=1, persistent=False)
        obj = C_SC_NA_1_Object.decode(b"\x0A")
        assert obj.select_execute == 1
        assert obj.qu_bit.select_execute == 1
        assert obj.qu_bit.ql_value == 1
        assert obj.qu_bit.pulse == CommandPulse.SHORT_PULSE

    def test_pulse_short_long_persistent_constants(self) -> None:
        """CommandPulse 枚举的 ql_value 映射常量正确。"""
        from starfish.domain.protocols.iec101.information_object import (
            _COMMAND_PULSE_TO_QL,
            _QL_TO_COMMAND_PULSE,
        )
        assert _COMMAND_PULSE_TO_QL[CommandPulse.NO_QUALIFIER] == 0
        assert _COMMAND_PULSE_TO_QL[CommandPulse.SHORT_PULSE] == 1
        assert _COMMAND_PULSE_TO_QL[CommandPulse.LONG_PULSE] == 2
        assert _COMMAND_PULSE_TO_QL[CommandPulse.PERSISTENT] == 3
        assert _QL_TO_COMMAND_PULSE[0] == CommandPulse.NO_QUALIFIER
        assert _QL_TO_COMMAND_PULSE[1] == CommandPulse.SHORT_PULSE
        assert _QL_TO_COMMAND_PULSE[2] == CommandPulse.LONG_PULSE
        assert _QL_TO_COMMAND_PULSE[3] == CommandPulse.PERSISTENT

    def test_legacy_qualifier_zero_still_rounds_trip(self) -> None:
        """旧 roundtrip 兼容：qu_bit=None 走 __post_init__ 默认填充路径。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0)
        decoded = C_SC_NA_1_Object.decode(obj.encode())
        assert decoded.scs == 1
        assert decoded.select_execute == 0
        assert decoded.qualifier == 0

    def test_legacy_qualifier_max_still_rounds_trip(self) -> None:
        """旧 roundtrip 兼容：qualifier=0x3F 仍能编解码。"""
        obj = C_SC_NA_1_Object(scs=1, select_execute=1, qualifier=0x3F)
        decoded = C_SC_NA_1_Object.decode(obj.encode())
        assert decoded.scs == 1
        assert decoded.select_execute == 1
        assert decoded.qualifier == 0x3F


# ── M_ME_NB_1 不带时标标度化测量值测试（Round 18 新增）────────────────────────


class TestMMeNb1Object:
    """M_ME_NB_1 信息对象（标度化测量值不带时标）编解码测试。"""

    def test_m_me_nb_1_size(self) -> None:
        """M_ME_NB_1 编码为 3 字节（SVA + QDS）。"""
        obj = M_ME_NB_1_Object(sva=100, qds=QDS())
        encoded = obj.encode()
        assert len(encoded) == 3

    def test_m_me_nb_1_encode_sva_bytes(self) -> None:
        """M_ME_NB_1 sva 应编码为小端序 int16。"""
        obj = M_ME_NB_1_Object(sva=0x1234, qds=QDS())
        encoded = obj.encode()
        assert encoded[0] == 0x34
        assert encoded[1] == 0x12

    def test_m_me_nb_1_roundtrip(self) -> None:
        """M_ME_NB_1 多种组合 roundtrip。"""
        cases = [
            M_ME_NB_1_Object(sva=0, qds=QDS()),
            M_ME_NB_1_Object(sva=12345, qds=QDS(overflow=True)),
            M_ME_NB_1_Object(sva=-32768, qds=QDS(invalid=True)),
            M_ME_NB_1_Object(sva=32767, qds=QDS(substituted=True)),
        ]
        for obj in cases:
            decoded = M_ME_NB_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, (
                f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            )
            assert decoded.qds.overflow == obj.qds.overflow
            assert decoded.qds.invalid == obj.qds.invalid

    def test_m_me_nb_1_invalid_sva(self) -> None:
        """M_ME_NB_1 sva 越界应抛 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_NB_1_Object(sva=32768)
        with pytest.raises(ValueError):
            M_ME_NB_1_Object(sva=-32769)

    def test_m_me_nb_1_decode_too_short(self) -> None:
        """M_ME_NB_1 解码数据不足 3 字节时抛 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_NB_1_Object.decode(b"\x00\x00")

    def test_m_me_nb_1_default_qds(self) -> None:
        """M_ME_NB_1 不传 qds 时使用默认 QDS。"""
        obj = M_ME_NB_1_Object(sva=100)
        assert isinstance(obj.qds, QDS)

    def test_m_me_nb_1_asdu_roundtrip(self) -> None:
        """M_ME_NB_1 通过 ASDU 列表 roundtrip（SQ=0）。"""
        obj = M_ME_NB_1_Object(
            sva=12345, qds=QDS(overflow=True),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=11, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_ME_NB_1_Object)
        assert decoded.information_objects[0].sva == 12345
        assert decoded.information_objects[0].qds.overflow is True

    def test_m_me_nb_1_asdu_sq1_roundtrip(self) -> None:
        """M_ME_NB_1 通过 ASDU 列表 SQ=1 roundtrip。"""
        objs = [
            M_ME_NB_1_Object(sva=10, qds=QDS()),
            M_ME_NB_1_Object(sva=20, qds=QDS(overflow=True)),
            M_ME_NB_1_Object(sva=30, qds=QDS(invalid=True)),
        ]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=11, vsq=0x83, cot=2, ca=1, ioa_count=3, sq=True,
            ),
            ioa_list=[100, 101, 102],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.header.sq is True
        assert decoded.ioa_list == [100, 101, 102]
        for i, obj in enumerate(objs):
            d_obj = decoded.information_objects[i]
            assert isinstance(d_obj, M_ME_NB_1_Object)
            assert d_obj.sva == obj.sva


# ── M_ME_NC_1 不带时标短浮点测量值测试（Round 18 新增）────────────────────────


class TestMMeNc1Object:
    """M_ME_NC_1 信息对象（短浮点测量值不带时标）编解码测试。"""

    def test_m_me_nc_1_size(self) -> None:
        """M_ME_NC_1 编码为 5 字节（ShortFloat + QDS）。"""
        obj = M_ME_NC_1_Object(sva=2.5, qds=QDS())
        encoded = obj.encode()
        assert len(encoded) == 5

    def test_m_me_nc_1_encode_short_float_bytes(self) -> None:
        """M_ME_NC_1 sva 应编码为 4 字节 IEEE 754 LE。"""
        obj = M_ME_NC_1_Object(sva=1.0, qds=QDS())
        encoded = obj.encode()
        assert encoded[0] == 0x00
        assert encoded[1] == 0x00
        assert encoded[2] == 0x80
        assert encoded[3] == 0x3F

    def test_m_me_nc_1_roundtrip(self) -> None:
        """M_ME_NC_1 多种 ShortFloat 组合 roundtrip。"""
        cases = [
            M_ME_NC_1_Object(sva=0.0, qds=QDS()),
            M_ME_NC_1_Object(sva=2.5, qds=QDS(overflow=True)),
            M_ME_NC_1_Object(sva=-1.5, qds=QDS(invalid=True)),
            M_ME_NC_1_Object(sva=1024.0, qds=QDS(substituted=True)),
        ]
        for obj in cases:
            decoded = M_ME_NC_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, (
                f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            )
            assert decoded.qds.overflow == obj.qds.overflow

    def test_m_me_nc_1_nan_rejected(self) -> None:
        """M_ME_NC_1 sva=NaN 应在 encode 路径抛 ValueError。"""
        obj = M_ME_NC_1_Object(sva=0.0, qds=QDS())
        obj.sva = float("nan")
        with pytest.raises(ValueError, match="NaN"):
            obj.encode()

    def test_m_me_nc_1_inf_rejected(self) -> None:
        """M_ME_NC_1 sva=Inf 应在 encode 路径抛 ValueError。"""
        obj = M_ME_NC_1_Object(sva=0.0, qds=QDS())
        obj.sva = float("inf")
        with pytest.raises(ValueError, match="Inf"):
            obj.encode()

    def test_m_me_nc_1_non_float_rejected(self) -> None:
        """M_ME_NC_1 sva 非 float 在 __post_init__ 抛 TypeError。"""
        with pytest.raises(TypeError, match="float"):
            M_ME_NC_1_Object(sva=1, qds=QDS())  # type: ignore[arg-type]

    def test_m_me_nc_1_decode_too_short(self) -> None:
        """M_ME_NC_1 解码数据不足 5 字节时抛 ValueError。"""
        with pytest.raises(ValueError):
            M_ME_NC_1_Object.decode(b"\x00\x00\x00\x00")

    def test_m_me_nc_1_default_qds(self) -> None:
        """M_ME_NC_1 不传 qds 时使用默认 QDS。"""
        obj = M_ME_NC_1_Object(sva=1.0)
        assert isinstance(obj.qds, QDS)

    def test_m_me_nc_1_asdu_roundtrip(self) -> None:
        """M_ME_NC_1 通过 ASDU 列表 roundtrip（SQ=0）。"""
        obj = M_ME_NC_1_Object(
            sva=2.5, qds=QDS(overflow=True),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=13, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], M_ME_NC_1_Object)
        assert decoded.information_objects[0].sva == 2.5
        assert decoded.information_objects[0].qds.overflow is True

    def test_m_me_nc_1_asdu_sq1_roundtrip(self) -> None:
        """M_ME_NC_1 通过 ASDU 列表 SQ=1 roundtrip。"""
        objs = [
            M_ME_NC_1_Object(sva=0.5, qds=QDS()),
            M_ME_NC_1_Object(sva=1.5, qds=QDS(invalid=True)),
        ]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=13, vsq=0x82, cot=2, ca=1, ioa_count=2, sq=True,
            ),
            ioa_list=[200, 201],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert decoded.ioa_list == [200, 201]
        for i, obj in enumerate(objs):
            d_obj = decoded.information_objects[i]
            assert isinstance(d_obj, M_ME_NC_1_Object)
            assert d_obj.sva == obj.sva


# ── SetPointQualifier 枚举 + SetPointCommandQualifier QOS 测试（Round 18 新增）


class TestSetPointQualifier:
    """SetPointQualifier 枚举测试。"""

    def test_enum_values(self) -> None:
        """SetPointQualifier 四个取值正确。"""
        assert SetPointQualifier.NOT_PERMITTED.value == "not_permitted"
        assert SetPointQualifier.SHORT_PULSE.value == "short_pulse"
        assert SetPointQualifier.LONG_PULSE.value == "long_pulse"
        assert SetPointQualifier.PERSISTENT_OUTPUT.value == "persistent_output"


class TestSetPointCommandQualifier:
    """SetPointCommandQualifier QOS 结构化字段测试。"""

    def test_default_values(self) -> None:
        """默认 ql=0 / qualifier=NOT_PERMITTED / select_execute=0 / qos=0。"""
        qos = SetPointCommandQualifier()
        assert qos.ql == 0
        assert qos.qualifier == SetPointQualifier.NOT_PERMITTED
        assert qos.select_execute == 0
        assert qos.qos == 0

    def test_to_byte_default(self) -> None:
        """默认 SetPointCommandQualifier.to_byte() == 0。"""
        assert SetPointCommandQualifier().to_byte() == 0

    def test_to_byte_ql_1(self) -> None:
        """ql=1 -> bit 1-2 = 0b01 -> 0x02。"""
        qos = SetPointCommandQualifier(ql=1)
        assert qos.to_byte() & 0x06 == 0x02

    def test_to_byte_ql_2(self) -> None:
        """ql=2 -> bit 1-2 = 0b10 -> 0x04。"""
        qos = SetPointCommandQualifier(ql=2)
        assert qos.to_byte() & 0x06 == 0x04

    def test_to_byte_ql_3(self) -> None:
        """ql=3 -> bit 1-2 = 0b11 -> 0x06。"""
        qos = SetPointCommandQualifier(ql=3)
        assert qos.to_byte() & 0x06 == 0x06

    def test_from_byte_zero(self) -> None:
        """from_byte(0) -> ql=0 / qualifier=NOT_PERMITTED。"""
        qos = SetPointCommandQualifier.from_byte(0)
        assert qos.ql == 0
        assert qos.qualifier == SetPointQualifier.NOT_PERMITTED

    def test_from_byte_long_pulse(self) -> None:
        """from_byte(0x04) -> ql=2 (LONG_PULSE)。"""
        qos = SetPointCommandQualifier.from_byte(0x04)
        assert qos.ql == 2
        assert qos.qualifier == SetPointQualifier.LONG_PULSE

    def test_from_byte_persistent(self) -> None:
        """from_byte(0x06) -> ql=3 (PERSISTENT_OUTPUT)。"""
        qos = SetPointCommandQualifier.from_byte(0x06)
        assert qos.ql == 3
        assert qos.qualifier == SetPointQualifier.PERSISTENT_OUTPUT

    def test_from_byte_out_of_range(self) -> None:
        """from_byte(0x40) 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            SetPointCommandQualifier.from_byte(0x40)

    def test_from_byte_negative(self) -> None:
        """from_byte(-1) 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            SetPointCommandQualifier.from_byte(-1)

    def test_invalid_ql_value(self) -> None:
        """ql 越界应抛 ValueError。"""
        with pytest.raises(ValueError):
            SetPointCommandQualifier(ql=4)
        with pytest.raises(ValueError):
            SetPointCommandQualifier(ql=-1)

    def test_invalid_select_execute(self) -> None:
        """select_execute 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            SetPointCommandQualifier(select_execute=2)

    def test_qualifier_ql_sync(self) -> None:
        """qualifier 与 ql 不一致时以 ql 为准（auto-sync）。"""
        qos = SetPointCommandQualifier(ql=2, qualifier=SetPointQualifier.NOT_PERMITTED)
        assert qos.qualifier == SetPointQualifier.LONG_PULSE

    def test_qos_field_default(self) -> None:
        """qos 字段默认与 to_byte() 一致。"""
        qos = SetPointCommandQualifier()
        assert qos.qos == qos.to_byte()

    def test_to_from_byte_roundtrip(self) -> None:
        """to_byte / from_byte roundtrip（仅 bit 1-2 ql 有效位 0..0x06）。"""
        for value in (0, 0x02, 0x04, 0x06):
            qos = SetPointCommandQualifier.from_byte(value)
            assert qos.to_byte() == value, (
                f"roundtrip 失败: {value} -> {qos.to_byte()}"
            )


# ── C_SE_NA_1 设点命令测试（Round 18 新增）────────────────────────────────────


class TestCSeNa1Object:
    """C_SE_NA_1 信息对象（归一化设点命令）编解码测试。"""

    def test_c_se_na_1_size(self) -> None:
        """C_SE_NA_1 编码为 5 字节（NVA + QOS + S/E + reserved）。"""
        obj = C_SE_NA_1_Object(nva=0.5, select_execute=0)
        encoded = obj.encode()
        assert len(encoded) == 5

    def test_c_se_na_1_default_qos(self) -> None:
        """C_SE_NA_1 默认 QOS 为 SetPointCommandQualifier()（ql=0）。"""
        obj = C_SE_NA_1_Object(nva=0.0)
        assert isinstance(obj.qos, SetPointCommandQualifier)
        assert obj.qos.ql == 0

    def test_c_se_na_1_roundtrip(self) -> None:
        """C_SE_NA_1 多种组合 roundtrip。"""
        cases = [
            C_SE_NA_1_Object(nva=0.0, select_execute=0),
            C_SE_NA_1_Object(nva=0.5, select_execute=1),
            C_SE_NA_1_Object(
                nva=-0.5, select_execute=0,
                qos=SetPointCommandQualifier(ql=2),
            ),
            C_SE_NA_1_Object(
                nva=32767.0 / 32768.0, select_execute=1,
                qos=SetPointCommandQualifier(ql=3),
            ),
        ]
        for obj in cases:
            decoded = C_SE_NA_1_Object.decode(obj.encode())
            assert abs(decoded.nva - obj.nva) < 1.0 / 32768.0
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql

    def test_c_se_na_1_invalid_nva(self) -> None:
        """C_SE_NA_1 nva 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NA_1_Object(nva=1.5)
        with pytest.raises(ValueError):
            C_SE_NA_1_Object(nva=-1.5)

    def test_c_se_na_1_invalid_select(self) -> None:
        """C_SE_NA_1 select_execute 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NA_1_Object(nva=0.0, select_execute=2)

    def test_c_se_na_1_decode_too_short(self) -> None:
        """C_SE_NA_1 解码数据不足 5 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NA_1_Object.decode(b"\x00\x00\x00\x00")

    def test_c_se_na_1_asdu_roundtrip(self) -> None:
        """C_SE_NA_1 通过 ASDU 列表 roundtrip。"""
        obj = C_SE_NA_1_Object(
            nva=0.5, select_execute=1,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=48, vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_NA_1_Object)
        assert abs(decoded.information_objects[0].nva - 0.5) < 1.0 / 32768.0
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2


# ── C_SE_NB_1 设点命令测试（Round 18 新增）────────────────────────────────────


class TestCSeNb1Object:
    """C_SE_NB_1 信息对象（标度化设点命令）编解码测试。"""

    def test_c_se_nb_1_size(self) -> None:
        """C_SE_NB_1 编码为 5 字节（SVA + QOS + S/E + reserved）。"""
        obj = C_SE_NB_1_Object(sva=12345, select_execute=0)
        encoded = obj.encode()
        assert len(encoded) == 5

    def test_c_se_nb_1_encode_sva_bytes(self) -> None:
        """C_SE_NB_1 sva 应编码为小端序 int16。"""
        obj = C_SE_NB_1_Object(sva=0x1234, select_execute=0)
        encoded = obj.encode()
        assert encoded[0] == 0x34
        assert encoded[1] == 0x12

    def test_c_se_nb_1_roundtrip(self) -> None:
        """C_SE_NB_1 多种组合 roundtrip。"""
        cases = [
            C_SE_NB_1_Object(sva=0, select_execute=0),
            C_SE_NB_1_Object(sva=12345, select_execute=1),
            C_SE_NB_1_Object(
                sva=-32768, select_execute=0,
                qos=SetPointCommandQualifier(ql=3),
            ),
            C_SE_NB_1_Object(
                sva=32767, select_execute=1,
                qos=SetPointCommandQualifier(ql=1),
            ),
        ]
        for obj in cases:
            decoded = C_SE_NB_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, (
                f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            )
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql

    def test_c_se_nb_1_invalid_sva(self) -> None:
        """C_SE_NB_1 sva 越界抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NB_1_Object(sva=32768)
        with pytest.raises(ValueError):
            C_SE_NB_1_Object(sva=-32769)

    def test_c_se_nb_1_decode_too_short(self) -> None:
        """C_SE_NB_1 解码数据不足 5 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NB_1_Object.decode(b"\x00\x00\x00\x00")

    def test_c_se_nb_1_asdu_roundtrip(self) -> None:
        """C_SE_NB_1 通过 ASDU 列表 roundtrip。"""
        obj = C_SE_NB_1_Object(
            sva=12345, select_execute=1,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=49, vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[200],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_NB_1_Object)
        assert decoded.information_objects[0].sva == 12345
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2


# ── C_SE_NC_1 设点命令测试（Round 18 新增）────────────────────────────────────


class TestCSeNc1Object:
    """C_SE_NC_1 信息对象（短浮点设点命令）编解码测试。"""

    def test_c_se_nc_1_size(self) -> None:
        """C_SE_NC_1 编码为 7 字节（ShortFloat + QOS + S/E + reserved）。"""
        obj = C_SE_NC_1_Object(sva=2.5, select_execute=0)
        encoded = obj.encode()
        assert len(encoded) == 7

    def test_c_se_nc_1_encode_short_float_bytes(self) -> None:
        """C_SE_NC_1 sva 应编码为 4 字节 IEEE 754 LE。"""
        obj = C_SE_NC_1_Object(sva=1.0, select_execute=0)
        encoded = obj.encode()
        assert encoded[0] == 0x00
        assert encoded[1] == 0x00
        assert encoded[2] == 0x80
        assert encoded[3] == 0x3F

    def test_c_se_nc_1_roundtrip(self) -> None:
        """C_SE_NC_1 多种 ShortFloat 组合 roundtrip。"""
        cases = [
            C_SE_NC_1_Object(sva=0.0, select_execute=0),
            C_SE_NC_1_Object(sva=2.5, select_execute=1),
            C_SE_NC_1_Object(
                sva=-1.5, select_execute=0,
                qos=SetPointCommandQualifier(ql=3),
            ),
            C_SE_NC_1_Object(
                sva=1024.0, select_execute=1,
                qos=SetPointCommandQualifier(ql=1),
            ),
        ]
        for obj in cases:
            decoded = C_SE_NC_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva, (
                f"sva roundtrip 失败: {obj.sva} -> {decoded.sva}"
            )
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql

    def test_c_se_nc_1_nan_rejected(self) -> None:
        """C_SE_NC_1 sva=NaN 应在 encode 路径抛 ValueError。"""
        obj = C_SE_NC_1_Object(sva=0.0, select_execute=0)
        obj.sva = float("nan")
        with pytest.raises(ValueError, match="NaN"):
            obj.encode()

    def test_c_se_nc_1_inf_rejected(self) -> None:
        """C_SE_NC_1 sva=Inf 应在 encode 路径抛 ValueError。"""
        obj = C_SE_NC_1_Object(sva=0.0, select_execute=0)
        obj.sva = float("inf")
        with pytest.raises(ValueError, match="Inf"):
            obj.encode()

    def test_c_se_nc_1_non_float_rejected(self) -> None:
        """C_SE_NC_1 sva 非 float 在 __post_init__ 抛 TypeError。"""
        with pytest.raises(TypeError, match="float"):
            C_SE_NC_1_Object(sva=1, select_execute=0)  # type: ignore[arg-type]

    def test_c_se_nc_1_decode_too_short(self) -> None:
        """C_SE_NC_1 解码数据不足 7 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_NC_1_Object.decode(b"\x00\x00\x00\x00\x00\x00")

    def test_c_se_nc_1_asdu_roundtrip(self) -> None:
        """C_SE_NC_1 通过 ASDU 列表 roundtrip。"""
        obj = C_SE_NC_1_Object(
            sva=2.5, select_execute=1,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=50, vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[300],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_NC_1_Object)
        assert decoded.information_objects[0].sva == 2.5
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2


# ── C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 带时标设定值命令测试（Round 19 新增）─


def _build_test_time() -> CP56Time2a:
    """构造测试用 CP56Time2a（year=99 边界）。"""
    return CP56Time2a(
        milliseconds=12345,
        minute=59,
        hour=23,
        day_of_month=31,
        day_of_week=3,
        month=12,
        year=99,
        invalid=False,
        summer_time=False,
        substituted=False,
    )


class TestCSeTa1Object:
    """C_SE_TA_1 信息对象（归一化设点命令，带 CP56Time2a 时标，Round 19）。"""

    def test_c_se_ta_1_size(self) -> None:
        """C_SE_TA_1 编码为 12 字节（NVA + QOS + S/E + reserved + CP56Time2a）。"""
        t = _build_test_time()
        obj = C_SE_TA_1_Object(nva=0.5, select_execute=0, time=t)
        encoded = obj.encode()
        assert len(encoded) == 12

    def test_c_se_ta_1_default_qos_and_time(self) -> None:
        """C_SE_TA_1 默认 QOS 为 SetPointCommandQualifier()（ql=0），
        默认 time 为 CP56Time2a()。"""
        obj = C_SE_TA_1_Object(nva=0.0)
        assert isinstance(obj.qos, SetPointCommandQualifier)
        assert obj.qos.ql == 0
        assert isinstance(obj.time, CP56Time2a)

    def test_c_se_ta_1_roundtrip(self) -> None:
        """C_SE_TA_1 多种组合 roundtrip（含 select_execute=0/1、
        qos ql=0/1/2/3、time 年/月/日/时/分/毫秒）。"""
        t = _build_test_time()
        cases = [
            C_SE_TA_1_Object(nva=0.0, select_execute=0, time=t),
            C_SE_TA_1_Object(nva=0.5, select_execute=1, time=t),
            C_SE_TA_1_Object(
                nva=-0.5, select_execute=0, time=t,
                qos=SetPointCommandQualifier(ql=1),
            ),
            C_SE_TA_1_Object(
                nva=32767.0 / 32768.0, select_execute=1, time=t,
                qos=SetPointCommandQualifier(ql=3),
            ),
        ]
        for obj in cases:
            decoded = C_SE_TA_1_Object.decode(obj.encode())
            assert abs(decoded.nva - obj.nva) < 1.0 / 32768.0
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql
            assert decoded.time.year == 99
            assert decoded.time.month == 12
            assert decoded.time.day_of_month == 31
            assert decoded.time.hour == 23
            assert decoded.time.minute == 59
            assert decoded.time.milliseconds == 12345

    def test_c_se_ta_1_invalid_nva(self) -> None:
        """C_SE_TA_1 nva 越界抛 ValueError。"""
        t = _build_test_time()
        with pytest.raises(ValueError):
            C_SE_TA_1_Object(nva=1.5, time=t)
        with pytest.raises(ValueError):
            C_SE_TA_1_Object(nva=-1.5, time=t)

    def test_c_se_ta_1_invalid_select(self) -> None:
        """C_SE_TA_1 select_execute 越界抛 ValueError。"""
        t = _build_test_time()
        with pytest.raises(ValueError):
            C_SE_TA_1_Object(nva=0.0, select_execute=2, time=t)

    def test_c_se_ta_1_decode_too_short(self) -> None:
        """C_SE_TA_1 解码数据不足 12 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_TA_1_Object.decode(b"\x00" * 11)

    def test_c_se_ta_1_qos_select_sync(self) -> None:
        """C_SE_TA_1 qos.select_execute 镜像应与 select_execute 同步。"""
        t = _build_test_time()
        obj = C_SE_TA_1_Object(nva=0.0, select_execute=1, time=t)
        assert obj.qos.select_execute == 1

    def test_c_se_ta_1_asdu_roundtrip(self) -> None:
        """C_SE_TA_1 通过 ASDU 列表 roundtrip（TypeId=58）。"""
        t = _build_test_time()
        obj = C_SE_TA_1_Object(
            nva=0.5, select_execute=1, time=t,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TA_1),
                vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[400],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_TA_1_Object)
        assert abs(decoded.information_objects[0].nva - 0.5) < 1.0 / 32768.0
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2
        assert decoded.information_objects[0].time.year == 99


class TestCSeTb1Object:
    """C_SE_TB_1 信息对象（标度化设点命令，带 CP56Time2a 时标，Round 19）。"""

    def test_c_se_tb_1_size(self) -> None:
        """C_SE_TB_1 编码为 12 字节（SVA + QOS + S/E + reserved + CP56Time2a）。"""
        t = _build_test_time()
        obj = C_SE_TB_1_Object(sva=12345, select_execute=0, time=t)
        encoded = obj.encode()
        assert len(encoded) == 12

    def test_c_se_tb_1_encode_sva_bytes(self) -> None:
        """C_SE_TB_1 sva 应编码为小端序 int16。"""
        t = _build_test_time()
        obj = C_SE_TB_1_Object(sva=0x1234, select_execute=0, time=t)
        encoded = obj.encode()
        assert encoded[0] == 0x34
        assert encoded[1] == 0x12

    def test_c_se_tb_1_roundtrip(self) -> None:
        """C_SE_TB_1 多种组合 roundtrip。"""
        t = _build_test_time()
        cases = [
            C_SE_TB_1_Object(sva=0, select_execute=0, time=t),
            C_SE_TB_1_Object(sva=12345, select_execute=1, time=t),
            C_SE_TB_1_Object(
                sva=-32768, select_execute=0, time=t,
                qos=SetPointCommandQualifier(ql=2),
            ),
            C_SE_TB_1_Object(
                sva=32767, select_execute=1, time=t,
                qos=SetPointCommandQualifier(ql=3),
            ),
        ]
        for obj in cases:
            decoded = C_SE_TB_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql
            assert decoded.time.year == 99
            assert decoded.time.month == 12

    def test_c_se_tb_1_invalid_sva(self) -> None:
        """C_SE_TB_1 sva 越界抛 ValueError。"""
        t = _build_test_time()
        with pytest.raises(ValueError):
            C_SE_TB_1_Object(sva=32768, time=t)
        with pytest.raises(ValueError):
            C_SE_TB_1_Object(sva=-32769, time=t)

    def test_c_se_tb_1_decode_too_short(self) -> None:
        """C_SE_TB_1 解码数据不足 12 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_TB_1_Object.decode(b"\x00" * 11)

    def test_c_se_tb_1_asdu_roundtrip(self) -> None:
        """C_SE_TB_1 通过 ASDU 列表 roundtrip（TypeId=59）。"""
        t = _build_test_time()
        obj = C_SE_TB_1_Object(
            sva=12345, select_execute=1, time=t,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TB_1),
                vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[500],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_TB_1_Object)
        assert decoded.information_objects[0].sva == 12345
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2
        assert decoded.information_objects[0].time.year == 99


class TestCSeTc1Object:
    """C_SE_TC_1 信息对象（短浮点设点命令，带 CP56Time2a 时标，Round 19）。"""

    def test_c_se_tc_1_size(self) -> None:
        """C_SE_TC_1 编码为 14 字节（ShortFloat + QOS + S/E + reserved + CP56Time2a）。"""
        t = _build_test_time()
        obj = C_SE_TC_1_Object(sva=2.5, select_execute=0, time=t)
        encoded = obj.encode()
        assert len(encoded) == 14

    def test_c_se_tc_1_encode_short_float_bytes(self) -> None:
        """C_SE_TC_1 sva 应编码为 4 字节 IEEE 754 LE。"""
        t = _build_test_time()
        obj = C_SE_TC_1_Object(sva=1.0, select_execute=0, time=t)
        encoded = obj.encode()
        assert encoded[0] == 0x00
        assert encoded[1] == 0x00
        assert encoded[2] == 0x80
        assert encoded[3] == 0x3F

    def test_c_se_tc_1_roundtrip(self) -> None:
        """C_SE_TC_1 多种 ShortFloat 组合 roundtrip。"""
        t = _build_test_time()
        cases = [
            C_SE_TC_1_Object(sva=0.0, select_execute=0, time=t),
            C_SE_TC_1_Object(sva=2.5, select_execute=1, time=t),
            C_SE_TC_1_Object(
                sva=-1.5, select_execute=0, time=t,
                qos=SetPointCommandQualifier(ql=3),
            ),
            C_SE_TC_1_Object(
                sva=1024.0, select_execute=1, time=t,
                qos=SetPointCommandQualifier(ql=1),
            ),
        ]
        for obj in cases:
            decoded = C_SE_TC_1_Object.decode(obj.encode())
            assert decoded.sva == obj.sva
            assert decoded.select_execute == obj.select_execute
            assert decoded.qos.ql == obj.qos.ql
            assert decoded.time.year == 99

    def test_c_se_tc_1_nan_rejected(self) -> None:
        """C_SE_TC_1 sva=NaN 应在 encode 路径抛 ValueError。"""
        t = _build_test_time()
        obj = C_SE_TC_1_Object(sva=0.0, select_execute=0, time=t)
        obj.sva = float("nan")
        with pytest.raises(ValueError, match="NaN"):
            obj.encode()

    def test_c_se_tc_1_inf_rejected(self) -> None:
        """C_SE_TC_1 sva=Inf 应在 encode 路径抛 ValueError。"""
        t = _build_test_time()
        obj = C_SE_TC_1_Object(sva=0.0, select_execute=0, time=t)
        obj.sva = float("inf")
        with pytest.raises(ValueError, match="Inf"):
            obj.encode()

    def test_c_se_tc_1_non_float_rejected(self) -> None:
        """C_SE_TC_1 sva 非 float 在 __post_init__ 抛 TypeError。"""
        t = _build_test_time()
        with pytest.raises(TypeError, match="float"):
            C_SE_TC_1_Object(sva=1, select_execute=0, time=t)  # type: ignore[arg-type]

    def test_c_se_tc_1_decode_too_short(self) -> None:
        """C_SE_TC_1 解码数据不足 14 字节抛 ValueError。"""
        with pytest.raises(ValueError):
            C_SE_TC_1_Object.decode(b"\x00" * 13)

    def test_c_se_tc_1_asdu_roundtrip(self) -> None:
        """C_SE_TC_1 通过 ASDU 列表 roundtrip（TypeId=60）。"""
        t = _build_test_time()
        obj = C_SE_TC_1_Object(
            sva=2.5, select_execute=1, time=t,
            qos=SetPointCommandQualifier(ql=2),
        )
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TC_1),
                vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[600],
            information_objects=[obj],
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert isinstance(decoded.information_objects[0], C_SE_TC_1_Object)
        assert decoded.information_objects[0].sva == 2.5
        assert decoded.information_objects[0].select_execute == 1
        assert decoded.information_objects[0].qos.ql == 2
        assert decoded.information_objects[0].time.year == 99


# ── C_SE_T* ASDU SQ=0 / SQ=1 联合测试（Round 19 新增）─────────────────────────


class TestCSeTimeTaggedSq0MultiType:
    """C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 ASDU SQ=0 多种类型 roundtrip。"""

    def test_sq0_c_se_ta1_tb1_tc1_individual(self) -> None:
        """SQ=0 模式下 3 个不同 TypeId 各自 roundtrip。"""
        t = _build_test_time()
        cases = [
            (TypeId.C_SE_TA_1, C_SE_TA_1_Object(
                nva=0.5, select_execute=0, time=t,
                qos=SetPointCommandQualifier(ql=1),
            )),
            (TypeId.C_SE_TB_1, C_SE_TB_1_Object(
                sva=12345, select_execute=1, time=t,
                qos=SetPointCommandQualifier(ql=2),
            )),
            (TypeId.C_SE_TC_1, C_SE_TC_1_Object(
                sva=2.5, select_execute=0, time=t,
                qos=SetPointCommandQualifier(ql=3),
            )),
        ]
        for tid, obj in cases:
            asdu = Asdu(
                header=ASDUHeader(
                    type_id=int(tid), vsq=0x01, cot=6, ca=1, ioa_count=1, sq=False,
                ),
                ioa_list=[700],
                information_objects=[obj],
            )
            encoded = encode_asdu(asdu)
            decoded = decode_asdu(encoded)
            assert isinstance(decoded, Asdu)
            assert len(decoded.information_objects) == 1
            assert type(decoded.information_objects[0]) is type(obj)
            assert decoded.ioa_list == [700]


class TestCSeTimeTaggedSq1:
    """C_SE_T* ASDU SQ=1 多个相同 TypeId 连续对象 roundtrip。"""

    def test_sq1_c_se_ta_1_sequence(self) -> None:
        """SQ=1 模式下 3 个 C_SE_TA_1 连续对象 roundtrip（IOA 自增）。"""
        t = _build_test_time()
        objs = [
            C_SE_TA_1_Object(nva=0.0, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=0)),
            C_SE_TA_1_Object(nva=0.5, select_execute=1, time=t,
                             qos=SetPointCommandQualifier(ql=1)),
            C_SE_TA_1_Object(nva=-0.5, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=2)),
        ]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TA_1),
                vsq=0x83, cot=6, ca=1, ioa_count=3, sq=True,
            ),
            ioa_list=[1000],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert len(decoded.information_objects) == 3
        for i, expected in enumerate(objs):
            actual = decoded.information_objects[i]
            assert isinstance(actual, C_SE_TA_1_Object)
            assert abs(actual.nva - expected.nva) < 1.0 / 32768.0
            assert actual.select_execute == expected.select_execute
            assert actual.qos.ql == expected.qos.ql
            assert actual.time.year == 99
        assert decoded.ioa_list == [1000, 1001, 1002]

    def test_sq1_c_se_tb_1_sequence(self) -> None:
        """SQ=1 模式下 3 个 C_SE_TB_1 连续对象 roundtrip。"""
        t = _build_test_time()
        objs = [
            C_SE_TB_1_Object(sva=0, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=0)),
            C_SE_TB_1_Object(sva=12345, select_execute=1, time=t,
                             qos=SetPointCommandQualifier(ql=1)),
            C_SE_TB_1_Object(sva=-32768, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=2)),
        ]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TB_1),
                vsq=0x83, cot=6, ca=1, ioa_count=3, sq=True,
            ),
            ioa_list=[2000],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert len(decoded.information_objects) == 3
        for i, expected in enumerate(objs):
            actual = decoded.information_objects[i]
            assert isinstance(actual, C_SE_TB_1_Object)
            assert actual.sva == expected.sva
            assert actual.select_execute == expected.select_execute
            assert actual.qos.ql == expected.qos.ql
        assert decoded.ioa_list == [2000, 2001, 2002]

    def test_sq1_c_se_tc_1_sequence(self) -> None:
        """SQ=1 模式下 3 个 C_SE_TC_1 连续对象 roundtrip。"""
        t = _build_test_time()
        objs = [
            C_SE_TC_1_Object(sva=0.0, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=0)),
            C_SE_TC_1_Object(sva=1.0, select_execute=1, time=t,
                             qos=SetPointCommandQualifier(ql=1)),
            C_SE_TC_1_Object(sva=-1.5, select_execute=0, time=t,
                             qos=SetPointCommandQualifier(ql=2)),
        ]
        asdu = Asdu(
            header=ASDUHeader(
                type_id=int(TypeId.C_SE_TC_1),
                vsq=0x83, cot=6, ca=1, ioa_count=3, sq=True,
            ),
            ioa_list=[3000],
            information_objects=objs,
        )
        encoded = encode_asdu(asdu)
        decoded = decode_asdu(encoded)
        assert isinstance(decoded, Asdu)
        assert len(decoded.information_objects) == 3
        for i, expected in enumerate(objs):
            actual = decoded.information_objects[i]
            assert isinstance(actual, C_SE_TC_1_Object)
            assert actual.sva == expected.sva
            assert actual.select_execute == expected.select_execute
            assert actual.qos.ql == expected.qos.ql
        assert decoded.ioa_list == [3000, 3001, 3002]


# ── SetPointCommandQualifier 与 select_execute 联合测试（Round 19 强化）────


class TestSetPointCommandQualifierSelectSync:
    """SetPointCommandQualifier ql / qualifier / select_execute 联合边界。"""

    def test_ql_to_byte_matches_qualifier(self) -> None:
        """ql 值 0..3 应正确映射 SetPointQualifier 枚举并编码。"""
        for ql, expected_qualifier in [
            (0, SetPointQualifier.NOT_PERMITTED),
            (1, SetPointQualifier.SHORT_PULSE),
            (2, SetPointQualifier.LONG_PULSE),
            (3, SetPointQualifier.PERSISTENT_OUTPUT),
        ]:
            qos = SetPointCommandQualifier(ql=ql)
            assert qos.qualifier == expected_qualifier
            # ql 编码：ql=0 -> 0x00, ql=1 -> 0x02, ql=2 -> 0x04, ql=3 -> 0x06
            assert qos.to_byte() == ql * 2

    def test_from_byte_ql_roundtrip(self) -> None:
        """ql 0..3 编码到 byte 再解码应回得相同 ql。"""
        for ql in range(4):
            qos = SetPointCommandQualifier(ql=ql)
            byte_val = qos.to_byte()
            decoded = SetPointCommandQualifier.from_byte(byte_val)
            assert decoded.ql == ql
            assert decoded.qualifier == qos.qualifier

    def test_select_execute_does_not_affect_ql(self) -> None:
        """select_execute 改变不应影响 ql/qualifier 编码。"""
        qos_se0 = SetPointCommandQualifier(ql=2, select_execute=0)
        qos_se1 = SetPointCommandQualifier(ql=2, select_execute=1)
        assert qos_se0.ql == qos_se1.ql == 2
        assert qos_se0.to_byte() == qos_se1.to_byte() == 0x04

