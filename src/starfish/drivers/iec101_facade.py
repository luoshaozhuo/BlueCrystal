"""Starfish IEC 60870-5-101 协议 facade —— codec-enhanced-plus stub。

IEC101 是串行链路协议（需 RS-232/RS-485 串口或串口模拟环境）。
C runner 二进制 (iec101_simulator_slave) 已编译就绪，但缺少串口
链路环境（PTY 或真实串口）。

模式分级（Round 18 更新）：

- "codec-enhanced-plus"：编解码器时间增强就绪（Round 16 升级，
  Round 17 收口，Round 18 扩展命令方向），包含 SIQ/QDS/NVA/
  ShortFloat/SVA/CP56Time2a 信息体元素、13 个信息对象
  （4 监视不带时标 + 2 监视不带时标标度化/短浮点 Round 18
  新增 + 5 带时标监视 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/
  M_ME_TB_1/M_ME_TC_1 + 4 控制命令 C_SC_NA_1 + 3 设点命令
  C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 Round 18 新增）、ASDU 信息
  对象列表（SQ=0/SQ=1）编解码、FT1.2 固定/可变帧编解码
  （含 checksum）、C_SC_NA_1 QU 字段结构化语义
  （select_execute / qualifier / ql_value / persistent /
  CommandPulse 枚举）、C_SE_* QOS 字段结构化
  （SetPointCommandQualifier + SetPointQualifier 枚举）、
  链路层最小状态机 skeleton（LinkLayerMode/LinkState/
  LinkEvent/LinkLayer/LinkLayerTimers + FCB/FCV helper +
  balanced/unbalanced 差异化 skeleton 行为）。
- "codec-enhanced"：编解码器增强就绪，包含 SIQ/QDS/NVA 等信息体元素、
  M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 等信息对象、ASDU 信息对象
  列表（SQ=0/SQ=1）编解码、FT1.2 固定/可变帧编解码（含 checksum），
  但不含 CP56Time2a / 带时标 TypeID / link-layer skeleton。
- "codec-skeleton"：仅头部编解码（ASDU/COT/IOA/CA），不含信息体与
  链路层帧（Round 14 状态）。
- "environment-pending"：C runner 已编译但编解码器骨架和链路环境均未
  就绪。
- "codebase-pending"：C runner 未编译且无 Python 原生 IEC101 编解码器。

Round 18 变更（codec-enhanced-plus 命令方向扩展）:
    新增 ScaledValue IE（16-bit signed scaled value；
    information_elements.py）；
    新增 M_ME_NB_1 / M_ME_NC_1 不带时标标度化/短浮点信息对象；
    新增 C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1 三个不带时标设定值
    命令 + SetPointQualifier 枚举 + SetPointCommandQualifier
    结构化 QOS 字段（ql / qualifier / select_execute / qos 子
    字段）。C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 三个带时标设定
    值命令 deferred（**不**实现）。
    mode 从 "codec-enhanced-plus" 升级 capabilities：
    supported_type_ids 增 M_ME_NB_1 / M_ME_NC_1 / C_SE_NA_1 /
    C_SE_NB_1 / C_SE_NC_1（13 TypeId 矩阵）；
    supports_command_codec=true（新增）/ supports_scaled_value=
    true（新增）；
    supports_server=false（**不**创建 server）/
    supports_serial_runtime=false（**不**连接真实串口）/
    supports_write_runtime=false（**不**真实写命令；C_SE_* 仅
    是 command codec，**不**等效真实写能力）。
    reason_text 扩展支持 13 TypeId 矩阵 + QOS 结构化 + 显式
    supports_write_runtime=false 声明。
    probe_iec101_codec_enhanced_plus 验证扩展包含 ScaledValue
    roundtrip + M_ME_NB_1 / M_ME_NC_1 / C_SE_NA_1 / C_SE_NB_1 /
    C_SE_NC_1 信息对象 roundtrip。

Round 19 变更（codec-enhanced-plus 带时标命令方向扩展）:
    新增 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1 三个带时标设定值
    命令 + CP56Time2a 时标（与不带时标 C_SE_NA_1/C_SE_NB_1/
    C_SE_NC_1 同语义但末尾追加 CP56Time2a 7 字节；object body
    长度 12 / 12 / 14 字节）。mode "codec-enhanced-plus" 升级
    capabilities：
    supported_type_ids 增 C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1
    （**17 TypeId 矩阵** = 4 监视不带时标 + 2 监视不带时标
    标度化/短浮点 + 5 带时标监视 + 1 单命令 + 3 不带时标设定
    值命令 + 3 带时标设定值命令，**以 capability 实际值为准**）；
    supported_command_type_ids 增 C_SE_TA_1 / C_SE_TB_1 /
    C_SE_TC_1（**7 控制命令**，4 不带时标 + 3 带时标）；
    supported_time_tagged_command_type_ids 新增 C_SE_TA_1 /
    C_SE_TB_1 / C_SE_TC_1（**3 带时标命令**）。
    仍 supports_server=false / supports_serial_runtime=false /
    supports_write_runtime=false（C_SE_TA_1/TB_1/TC_1 仍是
    command codec，**不**等效真实写能力）。
    reason_text 升级至 17 TypeId 矩阵（**以 capability 实际值
    为准**；不得硬写 14 / 15 / 18 等错误数字）。
    probe_iec101_codec_enhanced_plus 验证扩展包含
    C_SE_TA_1/TB_1/TC_1 信息对象 roundtrip + CP56Time2a
    时标。

Round 20 变更（link-layer 计时器/翻转/序列骨架增量）:
    新增 capabilities（**仍**是 codec-enhanced-plus 模式增量；
    **不**实现真实 server / 串口 / 写能力）：
    - supports_link_layer_timers=true（LinkLayerTimerService 抽象
      + DefaultLinkLayerTimerService 基于 threading.Timer +
      FakeLinkLayerTimerService 测试替身；LinkLayer 默认
      enable_timers=False 不启动任何线程；测试可注入 fake 验证
      调度路径）
    - supports_balanced_fcb_auto_flip=true（balanced 模式 + FCV
      enabled 时 receive_ack 自动 flip_fcb()；NACK / timeout
      **不**触发翻 FCB；FCV disabled 不翻）
    - supports_retry_skeleton=true（receive_nack / on_timeout 显
      式 bump_retry；retry_count > max_retries 时 state -> ERROR
      保持）
    ShortFloat 编码端兼容扩展（**不**引入 numpy 硬依赖）：
    encode_short_float 接受 int / numbers.Real（Decimal / Fraction
    等）/ 带 __float__ 的对象（duck typing）；NaN / Inf 仍按
    Round 17 严格拒绝策略。
    仍 supports_server=false / supports_serial_runtime=false /
    supports_write_runtime=false（**不**实现真实 server / 串口 /
    写能力；新增 capabilities 仅是 codec 状态机骨架）。

NOT_IMPLEMENTED（所有模式）：
    - write() / subscribe() / report() 明确抛出 UnsupportedOperation。
      待 IEC101 链路环境就绪且完整 ASDU 类型矩阵/状态机就绪后补齐。
    - 不实现真实 server 生命周期、串口收发、完整 balanced/unbalanced
      链路层状态机。
    - link_layer.py 仅 skeleton，不等同 server；probe/profile/capacity
      对 IEC101 仍返回 NOT_RUN/CODEC_ONLY + reason，不得写 PASS。

安全边界：
    - 不得 import seahorse / whale.ingest / whale.shared.source。
    - 所有数据标注 synthetic。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starfish.domain import StarfishServerPlan, UnsupportedOperation


def probe_iec101_codec() -> tuple[bool, str]:
    """探测 IEC101 编解码器骨架可用性。

    检查 starfish.protocols.iec101 包是否可导入及其关键组件完整性。

    Returns:
        (True, reason) 当编解码器骨架可用。
        (False, reason) 当编解码器不可用或导入失败。
    """
    try:
        from importlib.util import find_spec
        if find_spec("starfish.protocols.iec101") is None:
            return (False, "IEC101 编解码器包 (starfish.protocols.iec101) 不存在")
        from starfish.protocols.iec101 import (  # noqa: E402 动态导入
            ASDUHeader,
            decode_asdu_header,
            encode_asdu_header,
        )
        # 基本功能验证：编解码一致性
        header = ASDUHeader(type_id=1, vsq=1, cot=3, ca=1, ioa_count=1, sq=False)
        encoded = encode_asdu_header(header)
        decoded = decode_asdu_header(encoded)
        if decoded.type_id == 1 and decoded.cot == 3:
            return (
                True,
                "IEC101 编解码器骨架就绪（ASDU/COT/IOA/CA 编解码可用）。"
                "不等同完整 IEC101 协议栈，无链路层/状态机/串口通信。",
            )
        return (False, "IEC101 编解码器编码/解码不一致")
    except ImportError as exc:
        return (False, f"IEC101 编解码器骨架不可用: {exc}")
    except Exception as exc:
        return (False, f"IEC101 编解码器验证失败: {exc}")


def probe_iec101_codec_enhanced() -> tuple[bool, str]:
    """探测 IEC101 增强编解码器（Round 15 新增）可用性。

    在 codec-skeleton 基础上，验证 SIQ/QDS/NVA 信息体元素、
    M_SP_NA_1/M_ME_NA_1/C_SC_NA_1 信息对象、ASDU 列表编解码、
    FT1.2 固定/可变帧编解码是否全部可用。

    Returns:
        (True, reason) 当增强编解码器全部可用。
        (False, reason) 当任一组件不可用或验证失败。
    """
    try:
        from starfish.protocols.iec101 import (
            Asdu,
            C_SC_NA_1_Object,
            FixedFrame,
            M_ME_NA_1_Object,
            M_SP_NA_1_Object,
            QDS,
            SIQ,
            VariableFrame,
            compute_checksum,
            decode_asdu,
            encode_asdu,
            encode_normalized_value,
        )
        from starfish.protocols.iec101.asdu import ASDUHeader
        # 基本信息体 roundtrip 验证
        siq = SIQ(value=True, blocked=False, substituted=False, not_topical=False, invalid=False)
        sp_obj = M_SP_NA_1_Object(siq=siq)
        sp_encoded = sp_obj.encode()
        sp_decoded = M_SP_NA_1_Object.decode(sp_encoded)
        assert sp_decoded.siq.value is True

        # M_ME_NA_1 信息体
        me_obj = M_ME_NA_1_Object(nva=0.5, qds=QDS())
        me_encoded = me_obj.encode()
        me_decoded = M_ME_NA_1_Object.decode(me_encoded)
        assert abs(me_decoded.nva - 0.5) < 1e-6

        # C_SC_NA_1 信息体
        sc_obj = C_SC_NA_1_Object(scs=1, select_execute=0, qualifier=0)
        sc_encoded = sc_obj.encode()
        sc_decoded = C_SC_NA_1_Object.decode(sc_encoded)
        assert sc_decoded.scs == 1

        # NVA 归一化值
        nva_bytes = encode_normalized_value(0.25)
        assert len(nva_bytes) == 2

        # ASDU SQ=0 roundtrip
        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x01, cot=3, ca=1, ioa_count=1, sq=False,
            ),
            ioa_list=[100],
            information_objects=[sp_obj],
        )
        asdu_encoded = encode_asdu(asdu)
        asdu_decoded = decode_asdu(asdu_encoded)
        assert isinstance(asdu_decoded, Asdu)
        assert asdu_decoded.information_objects[0].siq.value is True

        # FT1.2 固定帧
        fixed = FixedFrame(control=0x40)
        fixed_encoded = fixed.encode()
        fixed_decoded = FixedFrame.decode(fixed_encoded)
        assert fixed_decoded.control == 0x40

        # FT1.2 可变帧
        var = VariableFrame(data=b"\x01\x02\x03\x04")
        var_encoded = var.encode()
        var_decoded = VariableFrame.decode(var_encoded)
        assert var_decoded.data == b"\x01\x02\x03\x04"

        # checksum（sum=1+2+3=6, ~6=249=0xF9）
        assert compute_checksum(b"\x01\x02\x03") == 0xF9
        return (
            True,
            "IEC101 增强编解码器就绪（信息体/SIQ/QDS/NVA/M_SP_NA_1/M_DP_NA_1/"
            "M_ME_NA_1/C_SC_NA_1/ASDU 列表 SQ=0/SQ=1/FT1.2 帧）。"
            "不等同完整 IEC101 协议栈，无链路层/状态机/串口通信。",
        )
    except ImportError as exc:
        return (False, f"IEC101 增强编解码器组件导入失败: {exc}")
    except AssertionError as exc:
        return (False, f"IEC101 增强编解码器 roundtrip 失败: {exc}")
    except Exception as exc:
        return (False, f"IEC101 增强编解码器验证失败: {exc}")


def probe_iec101_codec_enhanced_plus() -> tuple[bool, str]:
    """探测 IEC101 编解码器时间增强（Round 16 新增，Round 18 扩展）可用性。

    在 codec-enhanced 基础上，验证：
    - CP56Time2a 7 字节时标 IE encode/decode roundtrip。
    - 带时标 TypeID M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1 至少其中一个可用。
    - C_SC_NA_1 QU 字段结构化（SingleCommandQualifier）可用。
    - 链路层最小状态机 skeleton（LinkLayer / LinkState / LinkEvent）可用。
    - Round 18 扩展：ScaledValue IE + M_ME_NB_1 / M_ME_NC_1 信息对象
      + C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1 设点命令
      + SetPointCommandQualifier QOS 结构化。

    Returns:
        (True, reason) 当时间增强编解码器全部可用。
        (False, reason) 当任一组件不可用或验证失败。
    """
    try:
        from starfish.protocols.iec101 import (  # noqa: E402
            CP56Time2a,
            C_SE_NA_1_Object,
            C_SE_NB_1_Object,
            C_SE_NC_1_Object,
            C_SE_TA_1_Object,
            C_SE_TB_1_Object,
            C_SE_TC_1_Object,
            M_ME_NB_1_Object,
            M_ME_NC_1_Object,
            M_ME_TA_1_Object,
            M_SP_TA_1_Object,
            M_DP_TA_1_Object,
            QDS,
            ScaledValue,
            SetPointCommandQualifier,
            SetPointQualifier,
            SingleCommandQualifier,
            LinkLayer,
            LinkLayerMode,
            LinkState,
            LinkControlHelper,
            decode_scaled_value,
            encode_scaled_value,
            encode_cp56time2a,
            decode_cp56time2a,
        )
        # CP56Time2a roundtrip
        t = CP56Time2a(
            milliseconds=12345,
            minute=59,
            hour=23,
            day_of_month=31,
            day_of_week=3,
            month=12,
            year=99,
            invalid=True,
            summer_time=True,
            substituted=True,
        )
        t_enc = encode_cp56time2a(t)
        assert len(t_enc) == 7
        t_dec = decode_cp56time2a(t_enc)
        assert t_dec.milliseconds == 12345
        assert t_dec.invalid is True

        # 带时标 M_SP_TA_1 roundtrip
        from starfish.protocols.iec101 import SIQ
        sp_t = M_SP_TA_1_Object(
            siq=SIQ(value=True),
            time=t,
        )
        sp_t_enc = sp_t.encode()
        sp_t_dec = M_SP_TA_1_Object.decode(sp_t_enc)
        assert sp_t_dec.siq.value is True
        assert sp_t_dec.time.invalid is True

        # 带时标 M_DP_TA_1 roundtrip
        dp_t = M_DP_TA_1_Object(dpi=2, time=t)
        dp_t_enc = dp_t.encode()
        dp_t_dec = M_DP_TA_1_Object.decode(dp_t_enc)
        assert dp_t_dec.dpi == 2
        assert dp_t_dec.time.year == 99

        # 带时标 M_ME_TA_1 roundtrip
        me_t = M_ME_TA_1_Object(nva=0.5, qds=QDS(), time=t)
        me_t_enc = me_t.encode()
        me_t_dec = M_ME_TA_1_Object.decode(me_t_enc)
        assert abs(me_t_dec.nva - 0.5) < 1e-6
        assert me_t_dec.time.milliseconds == 12345

        # C_SC_NA_1 QU 结构化字段
        qu = SingleCommandQualifier(ql_value=2, persistent=False)
        assert qu.to_byte() == 0x04
        qu_dec = SingleCommandQualifier.from_byte(0x04)
        assert qu_dec.ql_value == 2
        assert qu_dec.persistent is False

        # Round 18 扩展 1: ScaledValue IE roundtrip
        sva_bytes = encode_scaled_value(12345)
        assert len(sva_bytes) == 2
        sva_dec = decode_scaled_value(sva_bytes)
        assert sva_dec == 12345
        sv_obj = ScaledValue(value=-32768)
        sv_dec = ScaledValue.decode(sv_obj.encode())
        assert sv_dec.value == -32768

        # Round 18 扩展 2: M_ME_NB_1 / M_ME_NC_1 roundtrip
        me_nb = M_ME_NB_1_Object(sva=12345, qds=QDS())
        me_nb_dec = M_ME_NB_1_Object.decode(me_nb.encode())
        assert me_nb_dec.sva == 12345

        me_nc = M_ME_NC_1_Object(sva=2.5, qds=QDS())
        me_nc_dec = M_ME_NC_1_Object.decode(me_nc.encode())
        assert me_nc_dec.sva == 2.5

        # Round 18 扩展 3: C_SE_NA_1 / C_SE_NB_1 / C_SE_NC_1 roundtrip
        se_na = C_SE_NA_1_Object(nva=0.5, select_execute=1)
        se_na_dec = C_SE_NA_1_Object.decode(se_na.encode())
        assert abs(se_na_dec.nva - 0.5) < 1.0 / 32768.0
        assert se_na_dec.select_execute == 1

        se_nb = C_SE_NB_1_Object(sva=12345, select_execute=0)
        se_nb_dec = C_SE_NB_1_Object.decode(se_nb.encode())
        assert se_nb_dec.sva == 12345

        se_nc = C_SE_NC_1_Object(sva=2.5, select_execute=0)
        se_nc_dec = C_SE_NC_1_Object.decode(se_nc.encode())
        assert se_nc_dec.sva == 2.5

        # Round 18 扩展 4: SetPointCommandQualifier QOS 字段
        se_qos = SetPointCommandQualifier(ql=2, qualifier=SetPointQualifier.LONG_PULSE)
        assert se_qos.to_byte() == 0x04
        se_qos_dec = SetPointCommandQualifier.from_byte(0x06)
        assert se_qos_dec.ql == 3
        assert se_qos_dec.qualifier == SetPointQualifier.PERSISTENT_OUTPUT

        # Round 19 扩展 1: C_SE_TA_1 / C_SE_TB_1 / C_SE_TC_1
        # 带时标设定值命令 roundtrip（object body 12/12/14 字节，
        # 末尾追加 CP56Time2a 7 字节；与 C_SE_NA_1/NB_1/NC_1
        # 同语义但带时标）。
        se_ta = C_SE_TA_1_Object(
            nva=0.5, select_execute=1,
            qos=SetPointCommandQualifier(ql=2), time=t,
        )
        se_ta_dec = C_SE_TA_1_Object.decode(se_ta.encode())
        assert abs(se_ta_dec.nva - 0.5) < 1.0 / 32768.0
        assert se_ta_dec.select_execute == 1
        assert se_ta_dec.qos.ql == 2
        assert se_ta_dec.time.year == 99
        assert se_ta_dec.time.milliseconds == 12345

        se_tb = C_SE_TB_1_Object(
            sva=12345, select_execute=0,
            qos=SetPointCommandQualifier(ql=3), time=t,
        )
        se_tb_dec = C_SE_TB_1_Object.decode(se_tb.encode())
        assert se_tb_dec.sva == 12345
        assert se_tb_dec.select_execute == 0
        assert se_tb_dec.qos.ql == 3
        assert se_tb_dec.time.year == 99

        se_tc = C_SE_TC_1_Object(
            sva=2.5, select_execute=1,
            qos=SetPointCommandQualifier(ql=1), time=t,
        )
        se_tc_dec = C_SE_TC_1_Object.decode(se_tc.encode())
        assert se_tc_dec.sva == 2.5
        assert se_tc_dec.select_execute == 1
        assert se_tc_dec.qos.ql == 1
        assert se_tc_dec.time.year == 99

        # LinkLayer skeleton
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        assert ll.state == LinkState.IDLE
        ev = ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02\x03"))
        assert ev.is_user_data

        return (
            True,
            "IEC101 编解码器时间增强就绪（CP56Time2a + M_SP_TA_1/M_DP_TA_1/"
            "M_ME_TA_1 带时标 + C_SC_NA_1 QU 结构化 + M_ME_NB_1/M_ME_NC_1 "
            "不带时标标度化/短浮点 + C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 不带时"
            "标设点命令 + C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 带时标设点命令 "
            "+ QOS 结构化 + ScaledValue IE + link-layer skeleton）。"
            "不等同完整 IEC101 协议栈，无 server/无串口通信/无完整状态机/无"
            "真实写能力。",
        )
    except ImportError as exc:
        return (False, f"IEC101 时间增强编解码器组件导入失败: {exc}")
    except AssertionError as exc:
        return (False, f"IEC101 时间增强编解码器 roundtrip 失败: {exc}")
    except Exception as exc:
        return (False, f"IEC101 时间增强编解码器验证失败: {exc}")


def probe_iec101_binary() -> tuple[bool, str]:
    """探测 IEC101 二进制或运行时可用性。

    探测步骤（增强 Round 14）：
        1. 检查编解码器骨架可用性（starfish.protocols.iec101）。
        2. 检查 third_party/lib60870 目录是否存在（lib60870 包含 IEC101 支持）。
        3. 检查 src/starfish/native/bin/ 下是否有 iec101 相关 binary。
        4. 检查 PTY 模块是否可用（IEC101 可通过 PTY 模拟串口）。

    始终返回 (False, reason)，因为当前无完整 IEC101 server 实现。

    Returns:
        (False, reason) —— 无任何可用 IEC101 server 实现。
    """
    reasons: list[str] = []

    # 检测编解码器骨架（Round 14 新增）
    codec_ok, codec_msg = probe_iec101_codec()
    if codec_ok:
        reasons.append(f"编解码器骨架: {codec_msg}")
    else:
        reasons.append(f"编解码器骨架不可用: {codec_msg}")

    # 检测 third_party/lib60870（lib60870 包含 IEC101 支持）
    starfish_root = Path(__file__).resolve().parents[1]
    lib60870_path = starfish_root.parent.parent / "third_party" / "lib60870"
    if lib60870_path.exists():
        reasons.append(f"third_party/lib60870 存在（包含 IEC101 支持）: {lib60870_path}")
    else:
        reasons.append("third_party/lib60870 目录不存在")

    # 检测 native/bin/ 下 iec101 相关 binary
    native_bin = starfish_root / "native" / "bin"
    iec101_binaries: list[str] = []
    if native_bin.exists():
        for fname in native_bin.iterdir():
            if fname.is_file() and "iec101" in fname.name.lower():
                iec101_binaries.append(str(fname))
    if iec101_binaries:
        reasons.append(f"发现 iec101 相关文件: {iec101_binaries}")
    else:
        reasons.append("native/bin/ 下无 iec101 相关 binary")

    # 检测 PTY 模块可用性
    pty_available = False
    try:
        import pty as _pty
        _pty.openpty()
        pty_available = True
    except Exception:
        pass

    if pty_available:
        reasons.append(
            "PTY 可用，可用于模拟串口链路"
        )
    else:
        reasons.append("PTY 不可用，无法模拟串口链路")

    # 最终结论：编解码器骨架就绪但不具备完整 server 能力
    binary_found = len(iec101_binaries) > 0
    if codec_ok:
        env_status = "codec-skeleton"
        status_desc = "编解码器骨架就绪，不等同完整 server"
    elif binary_found:
        env_status = "environment-pending"
        status_desc = "C runner 已编译但编解码器骨架不可用"
    else:
        env_status = "codebase-pending"
        status_desc = "C runner 未编译且编解码器骨架不可用"
    full_reason = (
        f"IEC101 需串口链路，{status_desc}。"
        "检测结果: " + "; ".join(reasons)
        + f"。状态：{env_status}"
    )
    return (False, full_reason)


class Iec101Facade:
    """IEC 60870-5-101 协议 server 模拟门面。

    IEC101 依赖串口物理链路或 PTY 模拟。本 facade 以 in-memory 模式
    维护点位值。模式按可用能力分级：

    - "codec-enhanced"（Round 15 新增）：编解码器增强就绪，包含信息体
      SIQ/QDS/NVA、信息对象 M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1、
      ASDU 列表 SQ=0/SQ=1、FT1.2 帧编解码。
    - "codec-skeleton"：仅头部编解码（ASDU/COT/IOA/CA）。
    - "environment-pending": C runner 已编译但串口环境未就绪。
    - "codebase-pending": 纯 stub，所有能力未就绪。

    不负责：完整 ASDU 类型矩阵、平衡/非平衡链路层、真实串口通信。
    """

    def __init__(self) -> None:
        self._plan: StarfishServerPlan | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "IEC101"

    @property
    def mode(self) -> str:
        """返回运行模式（Round 15 新增 codec-enhanced 层级）。

        - "codec-enhanced": 增强编解码器就绪（信息体 + ASDU 列表 + FT1.2 帧）。
        - "codec-skeleton": 编解码器骨架就绪（ASDU/COT/IOA/CA 编解码）。
        - "environment-pending": C runner 已编译但串口链路环境和编解码器骨架未就绪。
        - "codebase-pending": C runner 未编译且编解码器骨架不可用。
        """
        # 优先检测时间增强编解码器（Round 16）
        plus_ok, _ = probe_iec101_codec_enhanced_plus()
        if plus_ok:
            return "codec-enhanced-plus"
        # 回退：增强编解码器（Round 15）
        enhanced_ok, _ = probe_iec101_codec_enhanced()
        if enhanced_ok:
            return "codec-enhanced"
        # 回退：基础编解码器骨架（Round 14）
        codec_ok, _ = probe_iec101_codec()
        if codec_ok:
            return "codec-skeleton"

        starfish_root = Path(__file__).resolve().parents[1]
        binary_path = starfish_root / "native" / "bin" / "iec101_simulator_slave"
        if binary_path.exists():
            return "environment-pending"
        return "codebase-pending"

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 IEC101 facade（in-memory stub）。

        仅设置内存状态，不启动任何协议 server。
        重复调用安全（幂等）。
        """
        if self._started:
            return
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 IEC101 facade。

        重置 in-memory 状态。不删除已加载的 plan 和 values。
        重复调用安全（幂等）。
        """
        if not self._started:
            return
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态（含增强诊断和编解码器信息）。

        包含 PTY 可用性、lib60870 存在性、编解码器就绪状态等诊断信息。

        Returns:
            包含 health 信息的 dict。
        """
        # 收集诊断信息
        diagnosis: dict[str, Any] = {}

        # 编解码器骨架就绪状态（Round 14 新增）
        codec_ok, codec_msg = probe_iec101_codec()
        diagnosis["codec_skeleton_ready"] = codec_ok
        diagnosis["codec_skeleton_reason"] = codec_msg

        # 增强编解码器就绪状态（Round 15 新增）
        enhanced_ok, enhanced_msg = probe_iec101_codec_enhanced()
        diagnosis["codec_enhanced_ready"] = enhanced_ok
        diagnosis["codec_enhanced_reason"] = enhanced_msg

        # 时间增强编解码器就绪状态（Round 16 新增，Round 17 收口）
        plus_ok, plus_msg = probe_iec101_codec_enhanced_plus()
        diagnosis["codec_enhanced_plus_ready"] = plus_ok
        diagnosis["codec_enhanced_plus_reason"] = plus_msg

        # PTY 可用性
        try:
            import pty as _pty
            _pty.openpty()
            diagnosis["pty_available"] = True
        except Exception:
            diagnosis["pty_available"] = False

        # lib60870 存在性
        starfish_root = Path(__file__).resolve().parents[1]
        lib60870_path = starfish_root.parent.parent / "third_party" / "lib60870"
        diagnosis["lib60870_exists"] = lib60870_path.exists()

        # native/binary 检查
        native_bin = starfish_root / "native" / "bin"
        iec101_files: list[str] = []
        if native_bin.exists():
            for fname in native_bin.iterdir():
                if fname.is_file() and "iec101" in fname.name.lower():
                    iec101_files.append(fname.name)
        diagnosis["iec101_binaries"] = iec101_files

        # mode 判定
        current_mode = self.mode
        if current_mode == "codec-enhanced-plus":
            reason_text = (
                "IEC101 codec-enhanced-plus ready。"
                "supports CP56Time2a + ShortFloat + ScaledValue IE。"
                "supports time-tagged TypeIDs (M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/"
                "M_ME_TB_1/M_ME_TC_1)。"
                "supports 17 TypeID 矩阵（4 监视不带时标 + 2 监视不带时标"
                "标度化/短浮点 + 1 单命令 + 3 不带时标设点命令 "
                "C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 3 带时标设点命令 "
                "C_SE_TA_1/C_SE_TB_1/C_SE_TC_1 + 5 带时标监视；"
                "**TypeId 数量以 capability 实际值为准**）。"
                "supports QU 字段结构化（CommandPulse + SingleCommandQualifier "
                "子字段 select_execute/qualifier/ql_value/persistent/pulse）"
                "+ QOS 字段结构化（SetPointQualifier + SetPointCommandQualifier"
                " 子字段 ql/qualifier/select_execute/qos）。"
                "supports time-tagged command codec (C_SE_TA_1/C_SE_TB_1/"
                "C_SE_TC_1 带 CP56Time2a 7 字节时标，**仅 command codec，"
                "不等效真实写能力**)。"
                "supports link-layer skeleton (IDLE/WAIT_ACK/SEND/RECEIVE/ERROR "
                "+ FCB/FCV + t1/t2/t3 timers + balanced/unbalanced skeleton)。"
                "supports link-layer timers (LinkLayerTimerService 抽象 + "
                "Default / Fake 实现；LinkLayer 默认 enable_timers=False "
                "不启动真实线程；测试可注入 fake 验证调度路径)。"
                "supports balanced FCB auto flip (balanced + FCV enabled 时 "
                "receive_ack 自动 flip_fcb；NACK / timeout **不**翻 FCB；"
                "FCV disabled 不翻)。"
                "supports retry skeleton (receive_nack / on_timeout 显式 "
                "bump_retry；retry_count > max_retries 时 state -> ERROR 保持)。"
                "supports_server=false（**非真实 server 生命周期**）。"
                "supports_serial_runtime=false（**不连接真实串口**）。"
                "supports_write_runtime=false（**C_SE_* 仅 command codec，"
                "不等效真实写能力**）。"
                "不等同完整 IEC101 协议栈。"
            )
        elif current_mode == "codec-enhanced":
            reason_text = (
                "IEC101 增强编解码器就绪（信息体 SIQ/QDS/NVA + M_SP_NA_1/M_DP_NA_1/"
                "M_ME_NA_1/C_SC_NA_1 信息对象 + ASDU 列表 SQ=0/SQ=1 + FT1.2 帧）。"
                "不等同完整 IEC101 协议栈，缺链路层/状态机/串口通信。"
            )
        elif current_mode == "codec-skeleton":
            reason_text = (
                "IEC101 编解码器骨架就绪（ASDU/COT/IOA/CA 编解码可用）。"
                "不等同完整 IEC101 协议栈，缺链路层/状态机/串口通信。"
            )
        elif current_mode == "environment-pending":
            reason_text = (
                "IEC101 C runner 已编译但编解码器骨架不可用，"
                "且缺串口链路环境"
            )
        else:
            reason_text = (
                "IEC101 帧编解码器未实现，"
                "不可用原因: 缺 ASDU/COT/IOA 编解码、"
                "缺串口通信层、缺 IEC 60870-5-101 状态机"
            )

        return {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": self.protocol,
            "mode": current_mode,
            "running": False,
            "diagnosis": diagnosis,
            "reason": reason_text,
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerPlan) -> None:
        """加载点位定义和初始值到内存存储。

        Args:
            plan: 已校验的 StarfishServerPlan 实例。
        """
        self._plan = plan
        self._values = dict(plan.initial_values)

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """从内存读取当前点位值。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        if point_ids is None:
            return dict(self._values)
        return {pid: self._values.get(pid) for pid in point_ids}

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新内存中的点位值。

        Args:
            values: point_id -> 新值 的 dict。
        """
        self._values.update(values)

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        当 plan 未加载时，返回 IEC101 增强编解码器的能力声明（Round 15 新增），
        包含 codec_mode、supported_type_ids、supports_ft12_frame_codec、
        supports_server、supports_serial_runtime。

        Returns:
            能力声明字符串列表。
        """
        if self._plan is None:
            return list(self.codec_capabilities())
        return list(self._plan.capabilities)

    def codec_capabilities(self) -> list[str]:
        """返回 IEC101 增强编解码器能力声明（Round 15 新增，Round 18 扩展，
        Round 19 二次扩展带时标命令）。

        描述当前 facade 在编解码层具备的能力，与 server 生命周期能力正交。
        即使未加载 plan，也可通过本方法查询 codec 能力。

        Returns:
            能力声明字符串列表：
            - "codec_mode=codec-enhanced-plus"（或 codec-enhanced / codec-skeleton）
            - "supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,M_ME_NB_1,
              M_ME_NC_1,C_SC_NA_1,C_SE_NA_1,C_SE_NB_1,C_SE_NC_1,
              C_SE_TA_1,C_SE_TB_1,C_SE_TC_1,
              M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1"
              （plus 模式时 17 TypeId：4 监视不带时标 + 2 监视不带时标
              标度化/短浮点 + 1 单命令 + 3 不带时标设定值命令 +
              3 带时标设定值命令 + 5 带时标监视；**TypeId 数量
              以 capability 实际值为准**）
            - "supported_measurement_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,
              M_ME_NB_1,M_ME_NC_1"（4 监视不带时标 + 2 标度化/短浮点
              不带时标，共 6 监视 TypeId）
            - "supported_command_type_ids=C_SC_NA_1,C_SE_NA_1,C_SE_NB_1,
              C_SE_NC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1"（1 单命令 +
              3 不带时标设点命令 + 3 带时标设点命令，共 7 控制命令
              TypeId，**Round 19 扩展**）
            - "supported_time_tagged_command_type_ids=C_SE_TA_1,
              C_SE_TB_1,C_SE_TC_1"（3 带时标设点命令，**Round 19
              新增分组**）
            - "supported_time_tagged_type_ids=M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,
              M_ME_TB_1,M_ME_TC_1"（5 带时标监视 TypeId）
            - "supports_ft12_frame_codec=true"
            - "supports_short_float=true"（plus 模式时存在）
            - "supports_scaled_value=true"（plus 模式时存在，Round 18 新增）
            - "supports_command_codec=true"（plus 模式时存在，Round 18 新增）
            - "supports_time_tagged_command_codec=true"（plus 模式时
              存在，**Round 19 新增**；C_SE_TA_1/TB_1/TC_1 仅
              command codec，**不**等效真实写能力）
            - "supports_cp56time2a=true"（plus 模式时存在）
            - "supports_link_layer_skeleton=true"（plus 模式时存在）
            - "supports_link_layer_timers=true"（plus 模式时存在，
              **Round 20 新增**；LinkLayerTimerService 抽象 +
              Default（threading.Timer） + Fake 测试替身；
              LinkLayer 默认 enable_timers=False 不启动线程）
            - "supports_balanced_fcb_auto_flip=true"（plus 模式时
              存在，**Round 20 新增**；balanced 模式 + FCV enabled
              时 receive_ack 自动 flip_fcb；NACK / timeout 不翻；
              FCV disabled 不翻）
            - "supports_retry_skeleton=true"（plus 模式时存在，
              **Round 20 新增**；receive_nack / on_timeout 显式
              bump_retry；retry_count > max_retries 时 state -> ERROR）
            - "supports_server=false"
            - "supports_serial_runtime=false"
            - "supports_write_runtime=false"（plus 模式时存在，Round 18
              新增；C_SE_* 仅 command codec，**不**等效真实写能力）
        """
        current_mode = self.mode
        if current_mode == "codec-enhanced-plus":
            codec_mode = "codec-enhanced-plus"
            type_ids_line = (
                "supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,"
                "M_ME_NB_1,M_ME_NC_1,C_SC_NA_1,C_SE_NA_1,C_SE_NB_1,"
                "C_SE_NC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1,"
                "M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1"
            )
            measurement_line = (
                "supported_measurement_type_ids=M_SP_NA_1,M_DP_NA_1,"
                "M_ME_NA_1,M_ME_NB_1,M_ME_NC_1"
            )
            command_line = (
                "supported_command_type_ids=C_SC_NA_1,C_SE_NA_1,"
                "C_SE_NB_1,C_SE_NC_1,C_SE_TA_1,C_SE_TB_1,C_SE_TC_1"
            )
            time_tagged_command_line = (
                "supported_time_tagged_command_type_ids="
                "C_SE_TA_1,C_SE_TB_1,C_SE_TC_1"
            )
            time_tagged_line = (
                "supported_time_tagged_type_ids="
                "M_SP_TA_1,M_DP_TA_1,M_ME_TA_1,M_ME_TB_1,M_ME_TC_1"
            )
            extras = [
                "supports_cp56time2a=true",
                "supports_short_float=true",
                "supports_scaled_value=true",
                "supports_command_codec=true",
                "supports_time_tagged_command_codec=true",
                time_tagged_command_line,
                time_tagged_line,
                measurement_line,
                command_line,
                "supports_link_layer_skeleton=true",
                # Round 20 新增 capabilities（计时器 / 翻转 / 重试骨架）
                "supports_link_layer_timers=true",
                "supports_balanced_fcb_auto_flip=true",
                "supports_retry_skeleton=true",
            ]
        elif current_mode == "codec-enhanced":
            codec_mode = "codec-enhanced"
            type_ids_line = (
                "supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1"
            )
            extras = []
        elif current_mode == "codec-skeleton":
            codec_mode = "codec-skeleton"
            type_ids_line = (
                "supported_type_ids=M_SP_NA_1,M_DP_NA_1,M_ME_NA_1,C_SC_NA_1"
            )
            extras = []
        elif current_mode == "environment-pending":
            codec_mode = "unavailable"
            type_ids_line = "supported_type_ids="
            extras = []
        else:
            codec_mode = "codebase-pending"
            type_ids_line = "supported_type_ids="
            extras = []
        result = [
            f"codec_mode={codec_mode}",
            type_ids_line,
            "supports_ft12_frame_codec=true",
            "supports_server=false",
            "supports_serial_runtime=false",
        ]
        if current_mode == "codec-enhanced-plus":
            result.append("supports_write_runtime=false")
        result.extend(extras)
        return result

    # ── NOT_IMPLEMENTED ───────────────────────────────────────────────────────

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值 —— 当前未实现。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "Iec101Facade.write 尚未实现，"
            "待 IEC101 串口链路环境及帧编解码器就绪后实现",
        )

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知 —— 当前未实现。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "Iec101Facade.subscribe 尚未实现，"
            "待 IEC101 串口链路环境及帧编解码器就绪后实现",
        )

    def report(self) -> dict[str, Any]:
        """上报门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "Iec101Facade.report 尚未实现，"
            "待 IEC101 链路环境及帧编解码器就绪后实现",
        )


__all__ = [
    "Iec101Facade",
    "probe_iec101_binary",
    "probe_iec101_codec",
    "probe_iec101_codec_enhanced",
    "probe_iec101_codec_enhanced_plus",
]
