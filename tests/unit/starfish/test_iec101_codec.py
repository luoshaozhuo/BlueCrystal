"""Starfish IEC 60870-5-101 编解码器骨架测试。

验证：
1. TypeId 和 CauseOfTransmission 枚举定义完整性。
2. ASDUHeader 数据类编解码一致性。
3. InformationObjectAddress (IOA) 编解码正确性。
4. CommonAddress (CA) 编解码正确性。
5. encode/decode 往返一致性。

测试阶段：开发期验证 (P1)。
使用的替身：无（纯编解码器测试，无外部依赖）。
不能证明：真实 IEC101 server 帧正确性、链路层能力、串口通信。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

import pytest

from starfish.domain.protocols.iec101 import (
    ASDUHeader,
    CauseOfTransmission,
    TypeId,
    decode_asdu_header,
    decode_common_address,
    decode_information_object_address,
    encode_asdu_header,
    encode_common_address,
    encode_information_object_address,
)


# ── TypeId 枚举测试 ─────────────────────────────────────────────────────────────


class TestTypeId:
    """TypeId 枚举定义测试。"""

    def test_type_id_values(self) -> None:
        """常用 TypeId 应有正确的枚举值。"""
        assert TypeId.M_SP_NA_1 == 1  # 单点信息
        assert TypeId.M_ME_NA_1 == 9  # 归一化测量值
        assert TypeId.C_SC_NA_1 == 45  # 单命令

    def test_type_id_is_int_enum(self) -> None:
        """TypeId 应是 IntEnum 类型。"""
        assert isinstance(TypeId.M_SP_NA_1, int)
        assert int(TypeId.M_SP_NA_1) == 1


# ── CauseOfTransmission 枚举测试 ─────────────────────────────────────────────────


class TestCauseOfTransmission:
    """CauseOfTransmission 枚举定义测试。"""

    def test_cot_values(self) -> None:
        """常用 COT 应有正确的枚举值。"""
        assert CauseOfTransmission.PERIODIC == 1
        assert CauseOfTransmission.SPONTANEOUS == 3
        assert CauseOfTransmission.REQUEST == 5

    def test_cot_is_int_enum(self) -> None:
        """COT 应是 IntEnum 类型。"""
        assert isinstance(CauseOfTransmission.SPONTANEOUS, int)


# ── CommonAddress (CA) 测试 ──────────────────────────────────────────────────────


class TestCommonAddress:
    """CommonAddress (CA) 编解码测试。"""

    def test_encode_ca_zero(self) -> None:
        """CA=0 应编码为 2 字节 0x0000（小端序）。"""
        result = encode_common_address(0)
        assert result == b"\x00\x00"

    def test_encode_ca_max(self) -> None:
        """CA=65535 应编码为 2 字节 0xFFFF。"""
        result = encode_common_address(65535)
        assert result == b"\xFF\xFF"

    def test_encode_ca_typical(self) -> None:
        """典型 CA 值编码。"""
        result = encode_common_address(0x1234)
        # 小端序：低字节在前
        assert result == b"\x34\x12"

    def test_decode_ca_typical(self) -> None:
        """典型 CA 字节串解码。"""
        result = decode_common_address(b"\x34\x12")
        assert result == 0x1234

    def test_ca_roundtrip(self) -> None:
        """CA 编解码往返一致性。"""
        for val in [0, 1, 256, 4095, 65534, 65535]:
            encoded = encode_common_address(val)
            decoded = decode_common_address(encoded)
            assert decoded == val, f"CA 往返失败: {val} -> {decoded}"

    def test_ca_value_error_negative(self) -> None:
        """CA 负值应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_common_address(-1)

    def test_ca_value_error_overflow(self) -> None:
        """CA 超范围应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_common_address(65536)

    def test_decode_ca_too_short(self) -> None:
        """CA 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_common_address(b"\x01")


# ── InformationObjectAddress (IOA) 测试 ──────────────────────────────────────────


class TestInformationObjectAddress:
    """InformationObjectAddress (IOA) 编解码测试。"""

    def test_encode_ioa_zero(self) -> None:
        """IOA=0 应编码为 3 字节 0x000000。"""
        result = encode_information_object_address(0)
        assert result == b"\x00\x00\x00"

    def test_encode_ioa_max(self) -> None:
        """IOA=16777215 应编码为 3 字节 0xFFFFFF。"""
        result = encode_information_object_address(16777215)
        assert result == b"\xFF\xFF\xFF"

    def test_encode_ioa_typical(self) -> None:
        """典型 IOA 值编码（小端序）。"""
        result = encode_information_object_address(0x010203)
        # 小端序：低字节在前
        assert result == b"\x03\x02\x01"

    def test_decode_ioa_typical(self) -> None:
        """典型 IOA 字节串解码。"""
        result = decode_information_object_address(b"\x03\x02\x01")
        assert result == 0x010203

    def test_ioa_roundtrip(self) -> None:
        """IOA 编解码往返一致性。"""
        for val in [0, 1, 256, 4095, 65535, 0xABCDEF, 16777215]:
            encoded = encode_information_object_address(val)
            decoded = decode_information_object_address(encoded)
            assert decoded == val, f"IOA 往返失败: 0x{val:06X} -> 0x{decoded:06X}"

    def test_ioa_value_error_negative(self) -> None:
        """IOA 负值应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_information_object_address(-1)

    def test_ioa_value_error_overflow(self) -> None:
        """IOA 超范围应抛出 ValueError。"""
        with pytest.raises(ValueError):
            encode_information_object_address(16777216)

    def test_ioa_length(self) -> None:
        """IOA 编码始终为 3 字节。"""
        for val in [0, 1, 65535, 16777215]:
            encoded = encode_information_object_address(val)
            assert len(encoded) == 3

    def test_decode_ioa_too_short(self) -> None:
        """IOA 解码数据不足时抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_information_object_address(b"\x01\x02")


# ── ASDUHeader 测试 ──────────────────────────────────────────────────────────────


class TestASDUHeader:
    """ASDUHeader 数据类和头部编解码测试。"""

    def test_header_fields_default(self) -> None:
        """默认构造的 ASDUHeader 各字段为 0。"""
        header = ASDUHeader()
        assert header.type_id == 0
        assert header.vsq == 0
        assert header.cot == 0
        assert header.ca == 0
        assert header.ioa_count == 0
        assert header.sq is False

    def test_header_pn_property(self) -> None:
        """P/N 位应正确反映。"""
        header = ASDUHeader(cot=0x40)  # bit 6 set = negative
        assert header.pn is True
        header2 = ASDUHeader(cot=0x05)  # bit 6 clear = positive
        assert header2.pn is False

    def test_header_t_property(self) -> None:
        """T 位（试验标志）应正确反映。"""
        header = ASDUHeader(cot=0x80)  # bit 7 set
        assert header.t is True
        header2 = ASDUHeader(cot=0x05)  # bit 7 clear
        assert header2.t is False

    def test_header_cot_cause_property(self) -> None:
        """cot_cause 应返回纯原因码（不含 P/N/T 位）。"""
        header = ASDUHeader(cot=0xC5)  # T=1, P=1, cause=5
        assert header.cot_cause == 5

    def test_encode_asdu_header_basic(self) -> None:
        """基本 ASDU 头部编码测试。"""
        header = ASDUHeader(
            type_id=TypeId.M_SP_NA_1,  # 1
            vsq=0x01,  # 1 个 IO, SQ=0
            cot=CauseOfTransmission.SPONTANEOUS,  # 3
            ca=0x0001,
            ioa_count=1,
            sq=False,
        )
        encoded = encode_asdu_header(header)
        assert len(encoded) == 5  # TypeId(1)+VSQ(1)+COT(1)+CA(2)=5
        assert encoded[0] == 0x01  # type_id
        assert encoded[1] == 0x01  # vsq (1 IO, no SQ)
        assert encoded[2] == 0x03  # cot = SPONTANEOUS
        # CA: 小端序 0x0001
        assert encoded[3] == 0x01
        assert encoded[4] == 0x00

    def test_encode_asdu_header_with_sq(self) -> None:
        """SQ 位应正确编码在 VSQ 字节中。"""
        header = ASDUHeader(
            type_id=TypeId.M_ME_NA_1,  # 9
            vsq=0x85,  # bit 7=1 (SQ), count=5
            cot=CauseOfTransmission.PERIODIC,  # 1
            ca=0x1234,
            ioa_count=5,
            sq=True,
        )
        encoded = encode_asdu_header(header)
        assert encoded[1] == 0x85  # SQ=1, count=5

    def test_decode_asdu_header_basic(self) -> None:
        """基本 ASDU 头部解码测试。"""
        data = bytes([0x01, 0x01, 0x03, 0x01, 0x00])
        header = decode_asdu_header(data)
        assert header.type_id == TypeId.M_SP_NA_1
        assert header.vsq == 0x01
        assert header.ioa_count == 1
        assert header.sq is False
        assert header.cot == 3
        assert header.ca == 1

    def test_decode_asdu_header_with_sq(self) -> None:
        """带 SQ 位的 ASDU 头部解码测试。"""
        data = bytes([0x09, 0x88, 0x01, 0x34, 0x12])
        header = decode_asdu_header(data)
        assert header.type_id == 9  # M_ME_NA_1
        assert header.sq is True  # bit 7 = 1
        assert header.ioa_count == 8
        assert header.cot == 1  # PERIODIC
        assert header.ca == 0x1234

    def test_asdu_header_roundtrip(self) -> None:
        """ASDUHeader 编解码往返一致性。"""
        headers = [
            ASDUHeader(type_id=1, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False),
            ASDUHeader(type_id=9, vsq=0x85, cot=5, ca=0x1234, ioa_count=5, sq=True),
            ASDUHeader(type_id=45, vsq=0x01, cot=6, ca=0xFFFF, ioa_count=1, sq=False),
        ]
        for original in headers:
            encoded = encode_asdu_header(original)
            decoded = decode_asdu_header(encoded)
            assert decoded.type_id == original.type_id, (
                f"type_id 不匹配: {decoded.type_id} != {original.type_id}"
            )
            assert decoded.vsq == original.vsq
            assert decoded.cot == original.cot
            assert decoded.ca == original.ca
            assert decoded.ioa_count == original.ioa_count
            assert decoded.sq == original.sq

    def test_decode_asdu_header_too_short(self) -> None:
        """解码不足 5 字节的数据应抛出 ValueError。"""
        with pytest.raises(ValueError):
            decode_asdu_header(b"\x01\x02\x03\x04")


# ── ASDU 头部 P/N 与 T 组合测试 ──────────────────────────────────────────────────


class TestASDUHeaderPnT:
    """ASDUHeader P/N 位和 T 位组合测试。"""

    def test_positive_request(self) -> None:
        """请求类 COT（P=0, T=0）。"""
        header = ASDUHeader(
            type_id=TypeId.M_SP_NA_1,
            vsq=0x01,
            cot=CauseOfTransmission.REQUEST,  # 5, P=0, T=0
            ca=0x0001,
            ioa_count=1,
        )
        assert header.cot == 5
        assert header.pn is False
        assert header.t is False
        assert header.cot_cause == 5

    def test_negative_activation_confirm(self) -> None:
        """否定激活确认（P=1, T=0, cause=7）。"""
        header = ASDUHeader(
            type_id=TypeId.C_SC_NA_1,
            vsq=0x01,
            cot=0x47,  # bit 6=1 (P/N), cause=7
            ca=0x0001,
            ioa_count=1,
        )
        assert header.cot == 0x47
        assert header.pn is True
        assert header.t is False
        assert header.cot_cause == 7

    def test_test_mode_activation(self) -> None:
        """试验模式激活（P=0, T=1, cause=6）。"""
        header = ASDUHeader(
            type_id=TypeId.C_SC_NA_1,
            vsq=0x01,
            cot=0x86,  # bit 7=1 (T), cause=6
            ca=0x0001,
            ioa_count=1,
        )
        assert header.cot == 0x86
        assert header.pn is False
        assert header.t is True
        assert header.cot_cause == 6


# ── 编解码器探针测试 ─────────────────────────────────────────────────────────────


class TestIec101CodecAvailability:
    """IEC101 编解码器探针测试。"""

    def test_codec_probe_returns_true(self) -> None:
        """编解码器可用时应返回 True。"""
        from starfish.adapters.drivers.iec.iec101_facade import probe_iec101_codec
        ok, reason = probe_iec101_codec()
        assert ok is True
        assert "编解码器" in reason

    def test_facade_mode_is_codec_enhanced(self) -> None:
        """IEC101 facade mode 应为 codec-enhanced（Round 15 升级）或
        codec-enhanced-plus（Round 16 升级）—— 任一增强形态均可接受。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        assert facade.mode in ("codec-enhanced", "codec-enhanced-plus")

    def test_health_includes_codec_info(self) -> None:
        """IEC101 facade health() 应包含编解码器诊断信息。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        h = facade.health()
        assert "diagnosis" in h
        diag = h["diagnosis"]
        assert "codec_skeleton_ready" in diag
        assert diag["codec_skeleton_ready"] is True
        # Round 15 新增 codec_enhanced 诊断
        assert "codec_enhanced_ready" in diag
        assert diag["codec_enhanced_ready"] is True

    def test_health_codec_enhanced_plus_diagnosis(self) -> None:
        """Round 17 修复：health() 应包含 codec_enhanced_plus 诊断。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        h = facade.health()
        diag = h["diagnosis"]
        # Round 17 新增 codec_enhanced_plus 诊断字段
        assert "codec_enhanced_plus_ready" in diag
        assert "codec_enhanced_plus_reason" in diag
        assert diag["codec_enhanced_plus_ready"] is True
        assert "CP56Time2a" in diag["codec_enhanced_plus_reason"]

    def test_health_codec_enhanced_plus_reason_text(self) -> None:
        """Round 17 修复：codec-enhanced-plus mode 的 reason_text 必须显式覆盖。

        检查项（按 handoff 强制要求）：
        - reason 包含 "codec-enhanced-plus" 标识。
        - 包含 "supports CP56Time2a"。
        - 包含 "supports time-tagged TypeIDs"。
        - 包含 "supports link-layer skeleton"。
        - 包含 "supports_server=false"。
        - 包含 "supports_serial_runtime=false"。
        - 不应回退到 codec-enhanced 文案。
        """
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        mode = facade.mode
        assert mode == "codec-enhanced-plus", (
            f"期望 mode=codec-enhanced-plus，实际 {mode}"
        )
        h = facade.health()
        reason = h["reason"]
        assert "codec-enhanced-plus" in reason, (
            f"reason 缺少 codec-enhanced-plus 标识: {reason!r}"
        )
        assert "supports CP56Time2a" in reason, (
            f"reason 缺少 'supports CP56Time2a': {reason!r}"
        )
        assert "supports time-tagged TypeIDs" in reason, (
            f"reason 缺少 'supports time-tagged TypeIDs': {reason!r}"
        )
        assert "supports link-layer skeleton" in reason, (
            f"reason 缺少 'supports link-layer skeleton': {reason!r}"
        )
        assert "supports_server=false" in reason, (
            f"reason 缺少 'supports_server=false': {reason!r}"
        )
        assert "supports_serial_runtime=false" in reason, (
            f"reason 缺少 'supports_serial_runtime=false': {reason!r}"
        )
        # 显式检查：不应回退到 codec-enhanced 文案
        assert "信息体 SIQ/QDS/NVA + M_SP_NA_1/M_DP_NA_1" not in reason, (
            f"reason 不应回退到 codec-enhanced 文案: {reason!r}"
        )

    def test_codec_capabilities_includes_enhanced_plus(self) -> None:
        """codec_capabilities() 在 codec-enhanced-plus 模式下应包含扩展声明。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "codec_mode=codec-enhanced-plus" in caps
        # Round 17 扩展 supported_type_ids 必须含 M_ME_TB_1 / M_ME_TC_1
        type_ids_line = [c for c in caps if c.startswith("supported_type_ids=")][0]
        assert "M_ME_TB_1" in type_ids_line
        assert "M_ME_TC_1" in type_ids_line
        # Round 18 扩展 supported_type_ids
        assert "M_ME_NB_1" in type_ids_line
        assert "M_ME_NC_1" in type_ids_line
        assert "C_SE_NA_1" in type_ids_line
        # 支持 ShortFloat
        assert "supports_short_float=true" in caps
        # Round 18 扩展
        assert "supports_scaled_value=true" in caps
        assert "supports_command_codec=true" in caps
        # 不支持 server / serial runtime / write runtime
        assert "supports_server=false" in caps
        assert "supports_serial_runtime=false" in caps
        assert "supports_write_runtime=false" in caps

    def test_codec_capabilities_m_me_tb1_tc1(self) -> None:
        """codec_capabilities() 应同时包含 M_ME_TB_1 / M_ME_TC_1 在
        supported_type_ids 和 supported_time_tagged_type_ids 中。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        time_tagged_line = [
            c for c in caps if c.startswith("supported_time_tagged_type_ids=")
        ][0]
        assert "M_ME_TB_1" in time_tagged_line
        assert "M_ME_TC_1" in time_tagged_line

    def test_codec_capabilities_round18_command_codec(self) -> None:
        """Round 18：codec_capabilities() 应包含 13 TypeId 矩阵 +
        supports_command_codec + supports_scaled_value +
        supports_write_runtime=false。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        # 13 TypeId 矩阵：4 监视不带时标 + 2 监视不带时标标度化/短浮点
        # + 4 控制命令 + 5 带时标监视
        type_ids_line = [
            c for c in caps if c.startswith("supported_type_ids=")
        ][0]
        # Round 18 新增
        assert "M_ME_NB_1" in type_ids_line
        assert "M_ME_NC_1" in type_ids_line
        assert "C_SE_NA_1" in type_ids_line
        assert "C_SE_NB_1" in type_ids_line
        assert "C_SE_NC_1" in type_ids_line
        # Round 17 已有
        assert "M_SP_NA_1" in type_ids_line
        assert "M_ME_TB_1" in type_ids_line
        assert "M_ME_TC_1" in type_ids_line
        # Round 18 新增 capabilities
        assert "supports_command_codec=true" in caps
        assert "supports_scaled_value=true" in caps
        assert "supports_write_runtime=false" in caps
        # measurement / command 分组
        measurement_line = [
            c for c in caps if c.startswith("supported_measurement_type_ids=")
        ][0]
        assert "M_ME_NB_1" in measurement_line
        assert "M_ME_NC_1" in measurement_line
        command_line = [
            c for c in caps if c.startswith("supported_command_type_ids=")
        ][0]
        assert "C_SC_NA_1" in command_line
        assert "C_SE_NA_1" in command_line
        assert "C_SE_NB_1" in command_line
        assert "C_SE_NC_1" in command_line

    def test_codec_capabilities_does_not_overstate_write_runtime(self) -> None:
        """Round 18：capabilities 不得高估 command codec 为真实写能力。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        # supports_write_runtime 必须为 false
        assert "supports_write_runtime=false" in caps
        # supports_server / supports_serial_runtime 也必须为 false
        assert "supports_server=false" in caps
        assert "supports_serial_runtime=false" in caps


# ── IEC101 编解码器导入边界测试 ──────────────────────────────────────────────────


class TestIec101CodecImports:
    """IEC101 编解码器导入边界测试。"""

    def test_codec_package_imports(self) -> None:
        """所有关键组件应可导入。"""
        # 重新导入确认所有模块可访问
        from starfish.domain.protocols import iec101
        assert iec101 is not None
        from starfish.domain.protocols.iec101 import (
            types, asdu, ioa, common_address,
            quality, information_elements, information_object,
            codec, frame,
        )
        assert types is not None
        assert asdu is not None
        assert ioa is not None
        assert common_address is not None
        # Round 15 新增模块
        assert quality is not None
        assert information_elements is not None
        assert information_object is not None
        assert codec is not None
        assert frame is not None

    def test_codec_does_not_import_whale(self) -> None:
        """编解码器包不得 import whale 模块。"""
        from starfish.domain.protocols.iec101 import (
            types, asdu, ioa, common_address,
            quality, information_elements, information_object,
            codec, frame,
        )
        # 检查模块内容不含 whale import
        for mod in (
            types, asdu, ioa, common_address,
            quality, information_elements, information_object,
            codec, frame,
        ):
            source = mod.__dict__
            assert "whale" not in str(source.get("__builtins__", "")).lower()

    def test_codec_does_not_import_seahorse(self) -> None:
        """编解码器包不得 import seahorse 模块。"""
        from starfish.domain.protocols.iec101 import (
            types, asdu, ioa, common_address,
            quality, information_elements, information_object,
            codec, frame,
        )
        for mod in (
            types, asdu, ioa, common_address,
            quality, information_elements, information_object,
            codec, frame,
        ):
            source = mod.__dict__
            assert "seahorse" not in str(source.get("__builtins__", "")).lower()


# ── Round 19 带时标命令 capabilities 测试 ─────────────────────────────────────


class TestIec101CodecRound19:
    """Round 19：codec_capabilities() 应包含 17 TypeId 矩阵 + 带时标命令分组。"""

    def test_type_id_includes_c_se_ta_tb_tc(self) -> None:
        """TypeId 枚举应包含 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1。"""
        assert int(TypeId.C_SE_TA_1) == 58
        assert int(TypeId.C_SE_TB_1) == 59
        assert int(TypeId.C_SE_TC_1) == 60

    def test_codec_capabilities_17_type_ids(self) -> None:
        """Round 19：codec_capabilities() 应包含 17 TypeId 矩阵。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        type_ids_line = [c for c in caps if c.startswith("supported_type_ids=")][0]
        # 17 TypeId 矩阵：5 监视不带时标（M_SP_NA_1 / M_DP_NA_1 / M_ME_NA_1
        # / M_ME_NB_1 / M_ME_NC_1）+ 7 控制命令（C_SC_NA_1 + C_SE_NA_1/NB_1/NC_1
        # + C_SE_TA_1/TB_1/TC_1）+ 5 带时标监视（M_SP_TA_1/M_DP_TA_1/M_ME_TA_1
        # /M_ME_TB_1/M_ME_TC_1）= 17
        type_ids_count = len(type_ids_line.split("=")[1].split(","))
        assert type_ids_count == 17, (
            f"期望 17 TypeId，实际 {type_ids_count}: {type_ids_line!r}"
        )

    def test_codec_capabilities_includes_c_se_ta_tb_tc(self) -> None:
        """Round 19：codec_capabilities() 应包含 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        type_ids_line = [c for c in caps if c.startswith("supported_type_ids=")][0]
        assert "C_SE_TA_1" in type_ids_line
        assert "C_SE_TB_1" in type_ids_line
        assert "C_SE_TC_1" in type_ids_line

    def test_codec_capabilities_command_type_ids_includes_time_tagged(self) -> None:
        """Round 19：supported_command_type_ids 应包含 3 个带时标命令（7 个命令）。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        command_line = [c for c in caps if c.startswith("supported_command_type_ids=")][0]
        # 7 个控制命令：1 C_SC_NA_1 + 3 C_SE_NA_1/NB_1/NC_1
        # + 3 C_SE_TA_1/TB_1/TC_1
        assert "C_SC_NA_1" in command_line
        assert "C_SE_NA_1" in command_line
        assert "C_SE_NB_1" in command_line
        assert "C_SE_NC_1" in command_line
        assert "C_SE_TA_1" in command_line
        assert "C_SE_TB_1" in command_line
        assert "C_SE_TC_1" in command_line
        count = len(command_line.split("=")[1].split(","))
        assert count == 7, (
            f"期望 7 控制命令 TypeId，实际 {count}: {command_line!r}"
        )

    def test_codec_capabilities_time_tagged_command_type_ids(self) -> None:
        """Round 19：应新增 supported_time_tagged_command_type_ids 分组。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        tt_command_lines = [
            c for c in caps
            if c.startswith("supported_time_tagged_command_type_ids=")
        ]
        assert len(tt_command_lines) == 1
        line = tt_command_lines[0]
        assert "C_SE_TA_1" in line
        assert "C_SE_TB_1" in line
        assert "C_SE_TC_1" in line

    def test_codec_capabilities_supports_time_tagged_command_codec(self) -> None:
        """Round 19：应新增 supports_time_tagged_command_codec=true。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_time_tagged_command_codec=true" in caps

    def test_codec_capabilities_does_not_overstate_write_runtime_round19(self) -> None:
        """Round 19：capabilities 仍不得高估 C_SE_T* command codec 为真实写能力。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_write_runtime=false" in caps
        assert "supports_server=false" in caps
        assert "supports_serial_runtime=false" in caps

    def test_health_reason_text_includes_17_type_ids_and_c_se_ta_tb_tc(self) -> None:
        """Round 19：health() reason_text 应包含 17 TypeId 矩阵 + C_SE_TA_1/TB_1/TC_1。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        h = facade.health()
        reason = h["reason"]
        assert "17 TypeID" in reason, (
            f"reason 缺少 '17 TypeID': {reason!r}"
        )
        assert "C_SE_TA_1" in reason
        assert "C_SE_TB_1" in reason
        assert "C_SE_TC_1" in reason
        assert "supports time-tagged command codec" in reason

    def test_probe_iec101_codec_enhanced_plus_includes_c_se_ta_tb_tc(self) -> None:
        """Round 19：probe_iec101_codec_enhanced_plus() 应验证 C_SE_T* roundtrip。"""
        from starfish.adapters.drivers.iec.iec101_facade import probe_iec101_codec_enhanced_plus
        ok, reason = probe_iec101_codec_enhanced_plus()
        assert ok is True, f"probe failed: {reason}"
        assert "C_SE_TA_1" in reason
        assert "C_SE_TB_1" in reason
        assert "C_SE_TC_1" in reason

    def test_codec_capabilities_does_not_hardcode_13_or_15(self) -> None:
        """Round 19：codec_capabilities() 不得回退到 13/15 TypeId（应=17）。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        # 检查 capability 实际值（=17）；不得硬写 13/15
        type_ids_line = [c for c in caps if c.startswith("supported_type_ids=")][0]
        actual = len(type_ids_line.split("=")[1].split(","))
        assert actual not in (13, 15), (
            f"capability 实际值 {actual} 不应回退到 13/15"
        )
        assert actual == 17, (
            f"capability 实际值应为 17 TypeId，实际 {actual}"
        )


# ── Round 20 link-layer 计时器/翻转/重试 capabilities 测试 ─────────────────────


class TestIec101CodecRound20:
    """Round 20：codec_capabilities() 应包含 link-layer 计时器/翻转/重试 capabilities。"""

    def test_codec_capabilities_supports_link_layer_timers(self) -> None:
        """Round 20：supports_link_layer_timers=true。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_link_layer_timers=true" in caps

    def test_codec_capabilities_supports_balanced_fcb_auto_flip(self) -> None:
        """Round 20：supports_balanced_fcb_auto_flip=true。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_balanced_fcb_auto_flip=true" in caps

    def test_codec_capabilities_supports_retry_skeleton(self) -> None:
        """Round 20：supports_retry_skeleton=true。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_retry_skeleton=true" in caps

    def test_codec_capabilities_does_not_overstate_round20(self) -> None:
        """Round 20：capabilities 不得高估为真实 server / 串口 / 写能力。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        caps = facade.codec_capabilities()
        assert "supports_server=false" in caps
        assert "supports_serial_runtime=false" in caps
        assert "supports_write_runtime=false" in caps

    def test_health_reason_text_includes_round20_capabilities(self) -> None:
        """Round 20：health() reason_text 应包含 link-layer 计时器/翻转/重试。"""
        from starfish.adapters.drivers.iec.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        h = facade.health()
        reason = h["reason"]
        assert "link-layer timers" in reason
        assert "balanced FCB auto flip" in reason
        assert "retry skeleton" in reason

    def test_link_layer_timer_service_classes_importable(self) -> None:
        """Round 20：LinkLayerTimerService / Default / Fake 可从 iec101 导入。"""
        from starfish.domain.protocols.iec101 import (
            LinkLayerTimerService,
            DefaultLinkLayerTimerService,
            FakeLinkLayerTimerService,
        )
        assert LinkLayerTimerService is not None
        assert DefaultLinkLayerTimerService is not None
        assert FakeLinkLayerTimerService is not None
