"""IEC 60870-5-101 协议类型标识和传输原因枚举。

本模块定义 IEC 60870-5-101 协议中使用的类型标识符（TypeId）
和传输原因（CauseOfTransmission, COT）枚举。

不负责: 完整 ASDU 类型矩阵、方向标志（P/N 位）解析、
         Originator Address（ORAD）、链路层控制域。
"""

from __future__ import annotations

from enum import IntEnum


class TypeId(IntEnum):
    """IEC 60870-5-101 ASDU 类型标识符。

    定义监视方向（M_*）和控制方向（C_*）的 ASDU 类型。
    范围 1-127 为 IEC 60870-5-101 标准定义类型。

    当前骨架仅包含常用类型的枚举定义，
    encode/decode 骨架支持 M_SP_NA_1 和 M_ME_NA_1。
    """

    # ── 监视方向（Monitor direction）──────────────────────────────────────

    M_SP_NA_1 = 1  # 单点信息（Single-point information）
    M_SP_TA_1 = 2  # 带时标单点信息（Single-point information with time tag）
    M_DP_NA_1 = 3  # 双点信息（Double-point information）
    M_DP_TA_1 = 4  # 带时标双点信息
    M_ST_NA_1 = 5  # 步位置信息（Step position information）
    M_ST_TA_1 = 6  # 带时标步位置信息
    M_BO_NA_1 = 7  # 32 位位串（Bitstring of 32 bit）

    # 测量值
    M_ME_NA_1 = 9   # 测量值归一化（Measured value, normalized）
    M_ME_TA_1 = 10  # 带时标归一化测量值
    M_ME_NB_1 = 11  # 测量值标度化（Measured value, scaled）
    M_ME_TB_1 = 12  # 带时标标度化测量值
    M_ME_NC_1 = 13  # 短浮点测量值（Measured value, short float）
    M_ME_TC_1 = 14  # 带时标短浮点测量值

    # 累积量
    M_IT_NA_1 = 15  # 累积量（Integrated totals）
    M_IT_TA_1 = 16  # 带时标累积量

    # ── 控制方向（Control direction）──────────────────────────────────────

    C_SC_NA_1 = 45  # 单命令（Single command）
    C_DC_NA_1 = 46  # 双命令（Double command）
    C_RC_NA_1 = 47  # 升降命令（Regulating step command）
    C_SE_NA_1 = 48  # 设点命令归一化（Set point command, normalized）
    C_SE_NB_1 = 49  # 设点命令标度化
    C_SE_NC_1 = 50  # 设点命令短浮点
    # ── 控制方向带时标命令────────────────────────────────
    C_SE_TA_1 = 58  # 设点命令归一化，带 CP56Time2a 时标
    C_SE_TB_1 = 59  # 设点命令标度化，带 CP56Time2a 时标
    C_SE_TC_1 = 60  # 设点命令短浮点，带 CP56Time2a 时标

    # ── 系统信息 ──────────────────────────────────────────────────────────

    M_EI_NA_1 = 70  # 初始化结束（End of initialization）
    C_IC_NA_1 = 100  # 总召唤命令（Interrogation command）
    C_CI_NA_1 = 101  # 计数器总召唤命令
    C_RD_NA_1 = 102  # 读命令（Read command）
    C_CS_NA_1 = 103  # 时钟同步命令（Clock synchronization command）


class CauseOfTransmission(IntEnum):
    """IEC 60870-5-101 传输原因（COT）。

    指示 ASDU 的传输触发原因。范围 1-63。
    注意：P/N 位（bit 6）表示肯定/否定确认，在 ASDUHeader.cot 字段中
    作为整数整体编码，枚举值仅表示原因码本体（不含 P/N 位）。
    """

    PERIODIC = 1  # 周期/循环（Periodic/cyclic）
    BACKGROUND = 2  # 背景扫描（Background scan）
    SPONTANEOUS = 3  # 突发（Spontaneous）
    INITIALIZED = 4  # 初始化（Initialized）
    REQUEST = 5  # 请求/被请求（Request/requested）
    ACTIVATION = 6  # 激活（Activation）
    ACTIVATION_CONFIRM = 7  # 激活确认（Activation confirmation）
    DEACTIVATION = 8  # 停止激活（Deactivation）
    DEACTIVATION_CONFIRM = 9  # 停止激活确认
    ACTIVATION_TERMINATION = 10  # 激活终止（Activation termination）
    RETURN_INFO_REMOTE = 11  # 远方返回信息（Return info remote）
    RETURN_INFO_LOCAL = 12  # 本地返回信息（Return info local）
    FILE_TRANSFER = 13  # 文件传输（File transfer）

    # 控制方向专用
    INTERROGATION_STATION = 20  # 站总召唤（Interrogated by station）
    INTERROGATION_GROUP_1 = 21  # 组 1 总召唤
    INTERROGATION_GROUP_2 = 22  # 组 2 总召唤
    INTERROGATION_GROUP_3 = 23  # 组 3 总召唤
    INTERROGATION_GROUP_4 = 24  # 组 4 总召唤
    INTERROGATION_GROUP_5 = 25  # 组 5 总召唤
    INTERROGATION_GROUP_6 = 26  # 组 6 总召唤


__all__ = ["TypeId", "CauseOfTransmission"]
