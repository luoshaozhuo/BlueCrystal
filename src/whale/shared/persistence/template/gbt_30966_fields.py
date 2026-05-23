"""Field definitions per GB/T 30966.2-2022 (IEC 61400-25-2:2015).

Data objects extracted from the standard's data dictionary tables.
Each field includes:
  - key: OPC UA BrowseName (matches standard data object name)
  - mean: base simulation value
  - unit: engineering unit
  - desc: Chinese description from standard
  - data_type: OPC UA DataType (derived from CDC)
  - cdc: Common Data Class per IEC 61850-7-3
  - mo: Mandatory (M) / Optional (O) per standard Table 3

Logical nodes per GB/T 30966.2-2022 Table 2 & Table 3:
  Wind turbine: WTUR(M) WROT(M) WTRM(O) WGEN(M) WCNV(O) WTRF(O)
                WNAC(M) WYAW(M) WTOW(O) WALM(M) WMET(O)
                WSLG(O) WALG(O) WREP(O) WAVL(O)
  Wind farm:    WPPD(O) WAPC(O) WRPC(O) LTIM(O)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LogicalNodeField:
    key: str          # OPC UA BrowseName / data object name
    mean: float       # base simulation value
    unit: str         # engineering unit
    desc: str         # Chinese description from standard
    data_type: str = "FLOAT64"  # IEC 61850-7-2 basic type
    cdc: str = "MV"   # IEC 61850 Common Data Class
    mo: str = "O"     # M=Mandatory, O=Optional


@dataclass
class LogicalNodeDef:
    name: str
    desc: str
    fields: list[LogicalNodeField] = field(default_factory=list)


# CDC → IEC 61850-7-2 basic type name
_CDC_TYPE = {
    "MV": "FLOAT64", "STV": "INT32", "CMD": "INT32", "SPC": "INT32",
    "SPV": "FLOAT64", "INS": "INT32", "INC": "INT32", "BCR": "INT32",
    "WYE": "FLOAT64", "DEL": "FLOAT64", "ACT": "FLOAT64", "ACD": "FLOAT64",
    "ENC": "INT32", "ENG": "INT32", "DPL": "INT32", "DPC": "INT32",
    "HMV": "FLOAT64", "HST": "FLOAT64", "CSD": "VisString255", "CST": "VisString255",
    "ISC": "INT32", "LPL": "VisString255", "LPC": "VisString255",
}


def _f(key: str, mean: float, unit: str, desc: str, cdc: str = "MV", mo: str = "O") -> LogicalNodeField:
    return LogicalNodeField(key=key, mean=mean, unit=unit, desc=desc, data_type=_CDC_TYPE.get(cdc, "Double"), cdc=cdc, mo=mo)


# =============================================================================
# 6.2.1 WPPD — 风电场通用信息 (Wind Power Plant General)
# =============================================================================
WPPD = LogicalNodeDef(
    name="WPPD", desc="风电场通用信息",
    fields=[
        _f("DevSt",   1.0, "",   "设备状态", cdc="STV", mo="M"),
        _f("LocSta",  1.0, "",   "厂站级权限切换", cdc="SPC"),
        _f("EEHealth", 1.0, "",  "外部设备健康状态", cdc="INS"),
        _f("RsStat",  0.0, "",   "复位设备统计", cdc="SPC"),
        _f("CleRfTyp", 0.0, "",  "更新闻隔时间类型", cdc="ENG"),
        _f("OpCntRs", 0.0, "",   "操作计数器复位", cdc="INC"),
        _f("OpCnt",   500.0, "", "操作计数器", cdc="INS"),
        _f("OpTmh",   87600.0, "h", "以小时为单位运行时间", cdc="INS"),
        _f("NumPwrUp", 500.0, "", "上电次数", cdc="INS"),
        _f("WrmStr",  500.0, "", "软启动次数", cdc="INS"),
        _f("WacTrg",  3.0, "",   "检测到的看门狗复位次数", cdc="INS"),
        _f("OpTurNum", 2.0, "",  "实际运行风力发电机组数量", cdc="INS"),
        _f("CutHiTurNum", 0.0, "", "高风速下未运行的风力发电机组数量", cdc="INS"),
        _f("CutLoTurNum", 0.0, "", "低风速下未运行的风力发电机组数量", cdc="INS"),
        _f("Gra",     0.0, "deg", "风电场坡度", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.2 WTUR — 风力发电机组通用信息 (Wind Turbine General)
# =============================================================================
WTUR = LogicalNodeDef(
    name="WTUR", desc="风力发电机组通用信息",
    fields=[
        _f("TurSt",   1.0, "",   "风力发电机组状态", cdc="STV", mo="M"),
        _f("TurOp",   1.0, "",   "风力发电机组操作命令", cdc="CMD", mo="M"),
        _f("Ww",      1500.0, "kW", "有功电能", cdc="MV", mo="M"),
        _f("VAr",     200.0, "kVAr", "无功电能", cdc="MV"),
        _f("DmdWh",   1500.0, "kWh", "有功能量需求(默认需求方向:能量从变电站母线流入风力发电机组)", cdc="BCR"),
        _f("DmdVArh", 200.0, "kVArh", "无功能量需求(默认需求方向:能量从变电站母线流入风力发电机组)", cdc="BCR"),
        _f("SupWh",   1500.0, "kWh", "有功能量供给(默认供给方向:能量从风力发电机组流入变电站母线)", cdc="BCR"),
        _f("SupVArh", 200.0, "kVArh", "无功能量供给(默认供给方向:能量从风力发电机组流入变电站母线)", cdc="BCR"),
        _f("TurA",    800.0, "A", "风力发电机组侧三相电流", cdc="WYE"),
        _f("TurPNV",  690.0, "V", "风力发电机组侧三相相对中性点电压", cdc="WYE"),
        _f("TurPPV",  690.0, "V", "风力发电机组侧三相线电压", cdc="DEL"),
        _f("TurTmp",  45.0, "deg C", "风力发电机组侧温度", cdc="MV"),
        _f("VArOvW",  0.0, "",   "触发风力发电机组无功功率优先于有功功率", cdc="SPC"),
        _f("DmdVArSpt", 200.0, "kVAr", "风力发电机组无功设定值", cdc="SPV"),
        _f("DmdPFSpt", 0.95, "", "风力发电机组功率因数设定值", cdc="SPV"),
        _f("PF",      0.95, "",  "风电场实际功率因数", cdc="MV"),
        _f("PFSign",  1.0, "",   "功率因数符号规定", cdc="INS"),
    ],
)


# =============================================================================
# 6.2.3 WROT — 风力发电机组风轮信息 (Rotor)
# =============================================================================
WROT = LogicalNodeDef(
    name="WROT", desc="风轮信息",
    fields=[
        _f("RotSpd",  12.5, "r/min", "转速", cdc="MV"),
        _f("RotPos",  180.0, "deg", "风轮方位角", cdc="MV"),
        _f("HubTmp",  28.0, "deg C", "轮毂温度", cdc="MV"),
        _f("BISt",    1.0, "",   "变桨系统反馈叶片状态", cdc="STV"),
        _f("PthCtlst", 1.0, "", "变桨控制状态", cdc="STV"),
        _f("BIPthHyPres", 85.0, "bar", "液压变桨系统压力", cdc="MV"),
        _f("BIPthAngTgt", 8.5, "deg", "桨距角目标值", cdc="MV"),
        _f("BIPthAngVal", 8.5, "deg", "变桨系统反馈叶片桨距角", cdc="MV"),
        _f("PthEmgChk", 0.0, "",  "检查应急变桨系统", cdc="CMD"),
        _f("IceSt",   0.0, "",   "结冰探测状态", cdc="STV"),
        _f("RotBlk",  0.0, "",   "锁定风轮位置指令", cdc="CMD"),
        _f("Torq",    850.0, "kNm", "转矩值", cdc="MV"),
        _f("BrkOpSt", 0.0, "",   "主轴制动状态(风轮侧)", cdc="STV"),
        # 叶片扩展
        _f("BladeAPos", 0.0, "deg", "叶片A方位角", cdc="MV"),
        _f("BladeBPos", 120.0, "deg", "叶片B方位角", cdc="MV"),
        _f("BladeCPos", 240.0, "deg", "叶片C方位角", cdc="MV"),
        _f("TipSpd",  78.0, "m/s", "叶尖速度", cdc="MV"),
        _f("AeroNoise", 95.0, "dB", "气动噪声", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.4 WTRM — 风力发电机组传动信息 (Transmission)
# =============================================================================
WTRM = LogicalNodeDef(
    name="WTRM", desc="传动信息",
    fields=[
        # 状态信息
        _f("BrkOpSt", 0.0, "",  "主轴制动状态", cdc="STV"),
        _f("Lust",    1.0, "",  "齿轮箱润滑系统状态", cdc="STV"),
        _f("FilSt",   1.0, "",  "过滤系统状态", cdc="STV"),
        _f("Clst",    1.0, "",  "传动冷却系统状态", cdc="STV"),
        _f("HtSt",    0.0, "",  "加热系统状态", cdc="STV"),
        _f("OilLevSt", 1.0, "", "齿轮箱油箱油位状态", cdc="STV"),
        _f("OfFilSt", 0.0, "",  "离线过滤器污染状态", cdc="STV"),
        _f("InlFilSt", 0.0, "", "在线过滤器污染状态", cdc="STV"),
        # 测量和计量值
        _f("ShftBrgTmp", 42.0, "deg C", "主轴承的测量温度", cdc="MV"),
        _f("GbxOilTmp", 55.0, "deg C", "齿轮箱油测量温度", cdc="MV"),
        _f("ShftBrkTmp", 45.0, "deg C", "主轴制动表面测量温度", cdc="MV"),
        _f("GbxVbr",  0.15, "m/s2", "齿轮箱振动测量", cdc="MV"),
        _f("GsLev",   85.0, "%",  "主轴轴承润滑脂油位", cdc="MV"),
        _f("GbxOilLev", 85.0, "%", "齿轮箱油箱油位", cdc="MV"),
        _f("GbxOilPres", 2.5, "bar", "齿轮油压", cdc="MV"),
        _f("BrkHyPres", 30.0, "bar", "主轴制动液压压力", cdc="MV"),
        _f("OfFil",   0.0, "",   "离线过滤污物", cdc="MV"),
        _f("InlFil",  0.0, "",   "在线过滤污物", cdc="MV"),
        _f("Torq",    850.0, "kNm", "转矩值(传动侧)", cdc="MV"),
        # 扩展齿轮箱
        _f("GbxInShaftSpd", 12.5, "r/min", "齿轮箱输入轴转速", cdc="MV"),
        _f("GbxOutShaftSpd", 1500.0, "r/min", "齿轮箱输出轴转速", cdc="MV"),
        _f("GbxOilFilterDP", 0.8, "bar", "齿轮箱油滤压差", cdc="MV"),
        _f("GbxOilPumpSt", 1.0, "", "齿轮箱油泵状态", cdc="STV"),
        _f("GbxCoolPumpSt", 1.0, "", "齿轮箱冷却泵状态", cdc="STV"),
        _f("GbxHeatExchTmp", 52.0, "deg C", "齿轮箱换热器温度", cdc="MV"),
        _f("CouplingTmp", 48.0, "deg C", "联轴器温度", cdc="MV"),
        _f("CouplingVib", 0.09, "m/s2", "联轴器振动", cdc="MV"),
        _f("MechPwr",  1200.0, "kW", "机械功率", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.5 WGEN — 风力发电机组发电机信息 (Generator)
# =============================================================================
WGEN = LogicalNodeDef(
    name="WGEN", desc="发电机信息",
    fields=[
        # 定子
        _f("SttTmp",  85.0, "deg C", "发电机定子温度测量值", cdc="MV"),
        _f("SttA",    800.0, "A", "发电机定子三相电流", cdc="WYE"),
        _f("SttPNV",  690.0, "V", "发电机定子三相相对中性点电压", cdc="WYE"),
        _f("SttPPV",  690.0, "V", "发电机定子三相线电压", cdc="DEL"),
        # 转子
        _f("RotTmp",  60.0, "deg C", "发电机转子温度测量值", cdc="MV"),
        _f("RotA",    380.0, "A", "发电机转子三相电流", cdc="WYE"),
        _f("RotPNV",  690.0, "V", "发电机转子三相相对中性点电压", cdc="WYE"),
        _f("RotPPV",  690.0, "V", "发电机转子三相线电压", cdc="DEL"),
        _f("RotExtAC", 45.0, "V", "发电机转子交流励磁", cdc="MV"),
        _f("RotExtDC", 120.0, "V", "发电机转子直流励磁", cdc="MV"),
        # 冷却
        _f("InletTmp", 32.0, "deg C", "发电机入口空气/水温度测量值", cdc="MV"),
        # 发电机侧电气量
        _f("GnHz",    50.0, "Hz", "发电机侧频率值", cdc="MV"),
        _f("GnPF",    0.95, "",  "发电机侧三相功率因数", cdc="WYE"),
        _f("GnPNV",   690.0, "V", "发电机侧三相相对中性点电压", cdc="WYE"),
        _f("GnPPV",   690.0, "V", "发电机侧三相线电压", cdc="DEL"),
        _f("GnTmp",   55.0, "deg C", "发电机侧温度", cdc="MV"),
        # 转速
        _f("RotSpd",  1500.0, "r/min", "发电机转速", cdc="MV"),
        _f("GnOpSt",  1.0, "",   "发电机状态", cdc="STV"),
        _f("RotSt",   1.0, "",   "转子状态", cdc="STV"),
        _f("WwW",     1500.0, "kW", "发电机有功功率", cdc="WYE"),
        _f("VArW",    200.0, "kVAr", "发电机无功功率", cdc="WYE"),
        # 绕组温度（三相）
        _f("SttTmpW1", 85.0, "deg C", "发电机定子绕组W1温度", cdc="MV"),
        _f("SttTmpW2", 86.0, "deg C", "发电机定子绕组W2温度", cdc="MV"),
        _f("SttTmpW3", 84.0, "deg C", "发电机定子绕组W3温度", cdc="MV"),
        _f("RotTmpW1", 60.0, "deg C", "发电机转子绕组W1温度", cdc="MV"),
        _f("RotTmpW2", 61.0, "deg C", "发电机转子绕组W2温度", cdc="MV"),
        _f("RotTmpW3", 59.0, "deg C", "发电机转子绕组W3温度", cdc="MV"),
        # 轴承温度
        _f("BrgTmpDE", 60.0, "deg C", "发电机驱动端轴承温度", cdc="MV"),
        _f("BrgTmpNDE", 58.0, "deg C", "发电机非驱动端轴承温度", cdc="MV"),
        # 冷却
        _f("CoolAirInTmp", 32.0, "deg C", "发电机冷却风进风温度", cdc="MV"),
        _f("CoolAirOutTmp", 48.0, "deg C", "发电机冷却风出风温度", cdc="MV"),
        _f("CoolWatInTmp", 28.0, "deg C", "发电机冷却水进水温度", cdc="MV"),
        _f("CoolWatOutTmp", 35.0, "deg C", "发电机冷却水出水温度", cdc="MV"),
        _f("CoolFanSt", 1.0, "",  "发电机冷却风扇状态", cdc="STV"),
        # 振动
        _f("VbrX",    0.12, "m/s2", "发电机振动 X", cdc="MV"),
        _f("VbrY",    0.11, "m/s2", "发电机振动 Y", cdc="MV"),
        _f("VbrZ",    0.13, "m/s2", "发电机振动 Z", cdc="MV"),
        # 励磁
        _f("ExcitationV", 45.0, "V", "励磁电压", cdc="MV"),
        _f("ExcitationA", 120.0, "A", "励磁电流", cdc="MV"),
        _f("SlipRingTmp", 55.0, "deg C", "滑环温度", cdc="MV"),
        _f("BrushLng", 35.0, "mm", "碳刷长度", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.6 WCNV — 风力发电机组变流器信息 (Converter)
# =============================================================================
WCNV = LogicalNodeDef(
    name="WCNV", desc="变流器信息",
    fields=[
        _f("CnvOpSt", 1.0, "",   "变流器状态", cdc="STV", mo="M"),
        _f("ClSt",    1.0, "",   "变流器冷却系统状态", cdc="STV"),
        # DC link
        _f("DelA",    500.0, "A", "变流器内直流电流", cdc="MV"),
        _f("DelV",    800.0, "V", "变流器内直流电压", cdc="MV"),
        _f("DelTmp",  45.0, "deg C", "变流器内温度", cdc="MV"),
        _f("DelEna",  1.0, "",   "启用 delta 函数", cdc="STV"),
        _f("DelSpt",  0.0, "",   "设置风电场有功功率备用的 delta 函数参考值", cdc="SPV"),
        # 电网侧
        _f("GriA",    420.0, "A", "电网侧三相电流", cdc="WYE"),
        _f("GriHz",   50.0, "Hz", "电网侧频率值", cdc="MV"),
        _f("GriPF",   0.96, "",  "电网侧三相功率因数", cdc="WYE"),
        _f("GriPNV",  690.0, "V", "电网侧三相相对中性点电压", cdc="WYE"),
        _f("GriPPV",  690.0, "V", "电网侧三相线电压", cdc="DEL"),
        _f("GriTmp",  42.0, "deg C", "电网侧温度", cdc="MV"),
        # 发电机侧
        _f("GnA",     380.0, "A", "发电机侧三相电流", cdc="WYE"),
        _f("GnHz",    12.5, "Hz", "发电机侧频率值", cdc="MV"),
        _f("GnTmp",   48.0, "deg C", "发电机侧温度", cdc="MV"),
        # IGBT 模块温度
        _f("IGBTTmp1", 55.0, "deg C", "IGBT模块1温度", cdc="MV"),
        _f("IGBTTmp2", 56.0, "deg C", "IGBT模块2温度", cdc="MV"),
        _f("IGBTTmp3", 54.0, "deg C", "IGBT模块3温度", cdc="MV"),
        _f("IGBTTmp4", 57.0, "deg C", "IGBT模块4温度", cdc="MV"),
        _f("IGBTTmp5", 53.0, "deg C", "IGBT模块5温度", cdc="MV"),
        _f("IGBTTmp6", 55.0, "deg C", "IGBT模块6温度", cdc="MV"),
        # 其他部件温度
        _f("ChokeTmp", 48.0, "deg C", "电抗器温度", cdc="MV"),
        _f("CapTmp",   42.0, "deg C", "电容器温度", cdc="MV"),
        _f("CoolPlateTmp", 36.0, "deg C", "冷却板温度", cdc="MV"),
        _f("CabinetTmp", 38.0, "deg C", "变流器柜体温度", cdc="MV"),
        # Crowbar / Chopper
        _f("CrowbarSt", 0.0, "", "Crowbar状态", cdc="STV"),
        _f("ChopperSt", 0.0, "", "Chopper状态", cdc="STV"),
        # 效率
        _f("Efficiency", 0.97, "", "变流器效率", cdc="MV"),
        _f("TotalOpHrs", 48000.0, "h", "变流器累计运行时间", cdc="INS"),
    ],
)


# =============================================================================
# 6.2.7 WTRF — 风力发电机组变压器信息 (Transformer)
# =============================================================================
WTRF = LogicalNodeDef(
    name="WTRF", desc="变压器信息",
    fields=[
        _f("TnkPresSt", 1.0, "",  "变压器填充油主箱气压状态", cdc="STV"),
        _f("HtexSt",  1.0, "",   "换热器状态", cdc="STV"),
        _f("WtrTmp",  55.0, "deg C", "变压器绕组温度", cdc="MV"),
        _f("OilTmp",  55.0, "deg C", "变压器油温", cdc="MV"),
        _f("OilLev",  90.0, "%", "变压器油位", cdc="MV"),
        _f("Pres",    1.2, "bar", "变压器油压", cdc="MV"),
        _f("EnvTmp",  28.0, "deg C", "环境温度(变压器)", cdc="MV"),
        _f("FanSt",   1.0, "",   "变压器冷却风扇状态", cdc="STV"),
        _f("PumpSt",  1.0, "",   "变压器油泵状态", cdc="STV"),
        _f("Moisture", 12.0, "ppm", "变压器油中水分", cdc="MV"),
        _f("H2",      25.0, "ppm", "油中溶解氢 H2", cdc="MV"),
        _f("C2H2",    0.5, "ppm", "油中溶解乙炔 C2H2", cdc="MV"),
        _f("CO",      350.0, "ppm", "油中溶解一氧化碳 CO", cdc="MV"),
        _f("BuchholzSt", 0.0, "", "瓦斯继电器状态", cdc="STV"),
        _f("TapPos",  3.0, "",   "分接头位置", cdc="MV"),
        # 绕组温度 (三相)
        _f("WndTmpHVA", 62.0, "deg C", "高压绕组A相温度", cdc="MV"),
        _f("WndTmpHVB", 61.0, "deg C", "高压绕组B相温度", cdc="MV"),
        _f("WndTmpHVC", 63.0, "deg C", "高压绕组C相温度", cdc="MV"),
        _f("WndTmpLVA", 58.0, "deg C", "低压绕组A相温度", cdc="MV"),
        _f("WndTmpLVB", 57.0, "deg C", "低压绕组B相温度", cdc="MV"),
        _f("WndTmpLVC", 59.0, "deg C", "低压绕组C相温度", cdc="MV"),
        # 电气量
        _f("PhVHVA", 35000.0, "V", "高压侧A相电压", cdc="MV"),
        _f("PhVHVB", 35000.0, "V", "高压侧B相电压", cdc="MV"),
        _f("PhVHVC", 35000.0, "V", "高压侧C相电压", cdc="MV"),
        _f("PhVLVA", 690.0, "V", "低压侧A相电压", cdc="MV"),
        _f("PhVLVB", 690.0, "V", "低压侧B相电压", cdc="MV"),
        _f("PhVLVC", 690.0, "V", "低压侧C相电压", cdc="MV"),
        _f("AHVA",   25.0, "A",  "高压侧A相电流", cdc="MV"),
        _f("AHVB",   25.0, "A",  "高压侧B相电流", cdc="MV"),
        _f("AHVC",   25.0, "A",  "高压侧C相电流", cdc="MV"),
        _f("ALVA",   1260.0, "A", "低压侧A相电流", cdc="MV"),
        _f("ALVB",   1260.0, "A", "低压侧B相电流", cdc="MV"),
        _f("ALVC",   1260.0, "A", "低压侧C相电流", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.8 WNAC — 风力发电机组机舱信息 (Nacelle)
# =============================================================================
WNAC = LogicalNodeDef(
    name="WNAC", desc="机舱信息",
    fields=[
        _f("Dir",     180.0, "deg", "机舱方向", cdc="MV"),
        _f("EnvTmp",  28.0, "deg C", "周围环境温度", cdc="MV"),
        _f("EnvHum",  60.0, "%", "湿度", cdc="MV"),
        _f("DehumSt", 1.0, "",   "除湿机状态", cdc="STV"),
        _f("LftSt",   0.0, "",   "起重机系统状态", cdc="STV"),
        _f("LftPos",  0.0, "m",  "起重机位置", cdc="MV"),
        _f("IntnTmp", 32.0, "deg C", "部件内温度", cdc="MV"),
        _f("IntnHum", 55.0, "%", "部件内湿度", cdc="MV"),
        _f("BecBlbst", 1.0, "",  "航标灯状态", cdc="STV"),
        _f("BecLumLev", 500.0, "lux", "航标灯照明度值", cdc="MV"),
        _f("BecMod",  1.0, "",   "设置航标灯模式", cdc="CMD"),
        _f("BecLevSpt", 500.0, "lux", "航标灯中灯泡亮度设定值", cdc="SPV"),
        _f("FlshSpt", 30.0, "/min", "航标灯中闪光占空比设定值", cdc="SPV"),
        # Vibration
        _f("VbrX",    0.10, "m/s2", "机舱振动 X", cdc="MV"),
        _f("VbrY",    0.11, "m/s2", "机舱振动 Y", cdc="MV"),
        _f("VbrZ",    0.15, "m/s2", "机舱振动 Z", cdc="MV"),
        # 控制柜
        _f("CabTmp",  32.0, "deg C", "控制柜温度", cdc="MV"),
        _f("CabHum",  55.0, "%", "控制柜湿度", cdc="MV"),
        _f("CoolFanSt", 1.0, "", "机舱冷却风扇状态", cdc="STV"),
        _f("HtSt",    0.0, "",   "加热系统状态(机舱)", cdc="STV"),
        _f("SmokeDet", 0.0, "",  "烟雾检测", cdc="STV"),
        _f("DoorSt",  1.0, "",   "机舱门状态", cdc="STV"),
        # UPS
        _f("UPSSt",   1.0, "",   "UPS状态", cdc="STV"),
        _f("UPSBattV", 24.0, "V", "UPS电池电压", cdc="MV"),
        # 雷击
        _f("LightningCnt", 3.0, "", "雷击计数", cdc="INC"),
        # 急停
        _f("EmerStopSt", 0.0, "", "急停按钮状态", cdc="STV"),
        # 光照
        _f("LightIntensity", 500.0, "lux", "光照强度", cdc="MV"),
        # 加速度
        _f("AccelX",  0.05, "m/s2", "机舱加速度 X", cdc="MV"),
        _f("AccelY",  0.06, "m/s2", "机舱加速度 Y", cdc="MV"),
        _f("AccelZ",  0.04, "m/s2", "机舱加速度 Z", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.9 WYAW — 风力发电机组偏航信息 (Yaw)
# =============================================================================
WYAW = LogicalNodeDef(
    name="WYAW", desc="偏航信息",
    fields=[
        _f("YwOp",    1.0, "",   "偏航系统命令", cdc="CMD"),
        _f("SysGsLev", 85.0, "%", "偏航系统润滑油油位", cdc="MV"),
        _f("YawPos",  180.0, "deg", "偏航位置", cdc="MV"),
        _f("YawSpd",  0.3, "deg/s", "偏航速度", cdc="MV"),
        _f("YawSt",   1.0, "",   "偏航状态", cdc="STV"),
        _f("BrkSt",   0.0, "",   "偏航制动状态", cdc="STV"),
        _f("BrkPres", 30.0, "bar", "偏航制动液压压力", cdc="MV"),
        _f("BrkTmp",  48.0, "deg C", "偏航制动温度", cdc="MV"),
        # 偏航电机
        _f("Mot1Tmp", 42.0, "deg C", "偏航电机1温度", cdc="MV"),
        _f("Mot2Tmp", 43.0, "deg C", "偏航电机2温度", cdc="MV"),
        _f("Mot3Tmp", 41.0, "deg C", "偏航电机3温度", cdc="MV"),
        _f("Mot4Tmp", 44.0, "deg C", "偏航电机4温度", cdc="MV"),
        _f("Mot1A",   8.5, "A",  "偏航电机1电流", cdc="MV"),
        _f("Mot2A",   8.3, "A",  "偏航电机2电流", cdc="MV"),
        _f("Mot3A",   8.7, "A",  "偏航电机3电流", cdc="MV"),
        _f("Mot4A",   8.4, "A",  "偏航电机4电流", cdc="MV"),
        # 轴承与润滑
        _f("BrgTmp",  38.0, "deg C", "偏航轴承温度", cdc="MV"),
        _f("GearTmp", 45.0, "deg C", "偏航减速机温度", cdc="MV"),
        _f("LubPumpSt", 1.0, "", "偏航润滑泵状态", cdc="STV"),
        _f("CableTwist", 2.5, "turns", "电缆扭转圈数", cdc="MV"),
        _f("WindDirDev", 5.0, "deg", "风向偏差", cdc="MV"),
        _f("YawErr",  3.0, "deg", "偏航误差", cdc="MV"),
        _f("YawPosSet", 185.0, "deg", "偏航位置设定", cdc="SPV"),
        _f("YawMotCnt", 4.0, "", "偏航电机数量", cdc="INS"),
    ],
)


# =============================================================================
# 6.2.10 WTOW — 风力发电机组塔架信息 (Tower)
# =============================================================================
WTOW = LogicalNodeDef(
    name="WTOW", desc="塔架信息",
    fields=[
        _f("XdirDsp", 0.12, "m", "塔架位移(纵向)", cdc="MV"),
        _f("YdirDsp", 0.15, "m", "塔架位移(横向)", cdc="MV"),
        _f("IntmnHum", 70.0, "%", "塔架内湿度", cdc="MV"),
        # 振动
        _f("VbrX",    0.05, "m/s2", "塔架振动 X", cdc="MV"),
        _f("VbrY",    0.06, "m/s2", "塔架振动 Y", cdc="MV"),
        _f("VbrZ",    0.08, "m/s2", "塔架振动 Z", cdc="MV"),
        # 温度
        _f("TmpBot",  22.0, "deg C", "塔底温度", cdc="MV"),
        _f("TmpTop",  26.0, "deg C", "塔顶温度", cdc="MV"),
        # 门/照明/电梯
        _f("DoorSt",  1.0, "",   "塔架门状态", cdc="STV"),
        _f("LightSt", 1.0, "",   "塔架照明状态", cdc="STV"),
        _f("ElevSt",  0.0, "",   "电梯状态", cdc="STV"),
        _f("ElevPos", 0.0, "m",  "电梯位置", cdc="MV"),
        # 基础
        _f("FoundSettl", 2.0, "mm", "基础沉降", cdc="MV"),
        _f("FoundTiltX", 0.15, "mm/m", "基础倾斜X", cdc="MV"),
        _f("FoundTiltY", 0.12, "mm/m", "基础倾斜Y", cdc="MV"),
        # 锚栓拉力
        _f("BoltTension1", 450.0, "kN", "锚栓拉力1", cdc="MV"),
        _f("BoltTension2", 455.0, "kN", "锚栓拉力2", cdc="MV"),
        _f("BoltTension3", 448.0, "kN", "锚栓拉力3", cdc="MV"),
        _f("BoltTension4", 452.0, "kN", "锚栓拉力4", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.11 WMET — 气象信息 (Meteorological)
# =============================================================================
WMET = LogicalNodeDef(
    name="WMET", desc="气象信息",
    fields=[
        _f("HorWdSpd", 8.0, "m/s", "水平风速", cdc="MV"),
        _f("HorWdDir", 270.0, "deg", "水平风向", cdc="MV"),
        _f("VerWdSpd", 0.5, "m/s", "垂直风速", cdc="MV"),
        _f("VerWdDir", 90.0, "deg", "垂直风向", cdc="MV"),
        _f("EnvTmp",  15.0, "deg C", "周围环境温度", cdc="MV"),
        _f("EnvHum",  65.0, "%", "湿度", cdc="MV"),
        _f("AirDen",  1.225, "kg/m3", "空气密度", cdc="MV"),
        _f("RnFll",   0.0, "mm/h", "降雨量", cdc="MV"),
        _f("SnwDen",  0.1, "g/cm3", "降雪密度", cdc="MV"),
        _f("SnwFll",  0.0, "cm", "降雪量", cdc="MV"),
        _f("SnwTmp",  -2.0, "deg C", "降雪温度", cdc="MV"),
        _f("SnwEq",   0.0, "mm", "积雪水当量", cdc="MV"),
        _f("SnwCvr",  0.0, "%", "积雪覆盖率", cdc="MV"),
        _f("DetInsol", 500.0, "W/m2", "直接正常照度", cdc="MV"),
        _f("DffInsol", 200.0, "W/m2", "扩散照度", cdc="MV"),
        _f("DIDur",   12.0, "h", "日光持续时间(日出到日落经过的时间)", cdc="MV"),
        _f("WetBlbTmp", 12.0, "deg C", "湿球温度", cdc="MV"),
        _f("Alt",     100.0, "m", "传感器海拔高度", cdc="MV"),
        _f("AneSt",   1.0, "",   "主/次风速计状态", cdc="STV"),
        _f("wdHtSt",  1.0, "",   "风速传感器的加热器状态", cdc="STV"),
        _f("CloudCvr", 40.0, "%", "云层覆盖率", cdc="MV"),
        _f("IceSt",   0.0, "",   "结冰探测状态(气象)", cdc="STV"),
        _f("Pres",    1013.0, "hPa", "大气压力", cdc="MV"),
        # 扩展气象量
        _f("WsAvg10min", 7.8, "m/s", "10分钟平均风速", cdc="MV"),
        _f("WsMax3s", 12.0, "m/s", "3秒极大风速", cdc="MV"),
        _f("WsMin",  4.5, "m/s", "最小风速", cdc="MV"),
        _f("WdAvg10min", 268.0, "deg", "10分钟平均风向", cdc="MV"),
        _f("WdSd",   8.0, "deg", "风向标准差", cdc="MV"),
        _f("TmpMax", 22.0, "deg C", "最高温度", cdc="MV"),
        _f("TmpMin", 8.0, "deg C", "最低温度", cdc="MV"),
        _f("RainAccum", 12.5, "mm", "累计降雨量", cdc="MV"),
        _f("SnowDepth", 0.0, "cm", "积雪深度", cdc="MV"),
        _f("SolarRad", 500.0, "W/m2", "太阳辐射", cdc="MV"),
        _f("Visibility", 8000.0, "m", "能见度", cdc="MV"),
        _f("CloudH", 2000.0, "m", "云层高度", cdc="MV"),
        _f("LightningAct", 0.0, "", "雷击活动", cdc="STV"),
        _f("TSensorSt", 1.0, "", "温度传感器状态", cdc="STV"),
        _f("WsSensorSt", 1.0, "", "风速传感器状态", cdc="STV"),
        _f("WdSensorSt", 1.0, "", "风向传感器状态", cdc="STV"),
    ],
)


# =============================================================================
# 6.2.12 WALM — 报警信息 (Alarms)
# =============================================================================
WALM = LogicalNodeDef(
    name="WALM", desc="报警信息",
    fields=[
        _f("almAck",  0.0, "",  "确认", cdc="SPC"),
        _f("almRs",   0.0, "",  "报警重置", cdc="SPC"),
        _f("manRs",   0.0, "",  "手动强制复位", cdc="SPC"),
        _f("chrManRs", 0.0, "", "特征信息手动强制复位", cdc="SPC"),
        # 常见报警信号
        _f("Alm1",    0.0, "",  "报警信号1", cdc="STV"),
        _f("Alm2",    0.0, "",  "报警信号2", cdc="STV"),
        _f("Alm3",    0.0, "",  "报警信号3", cdc="STV"),
        _f("Alm4",    0.0, "",  "报警信号4", cdc="STV"),
        _f("Alm5",    0.0, "",  "报警信号5", cdc="STV"),
        _f("Wrn1",    0.0, "",  "预警信号1", cdc="STV"),
        _f("Wrn2",    0.0, "",  "预警信号2", cdc="STV"),
        _f("Wrn3",    0.0, "",  "预警信号3", cdc="STV"),
        _f("CommLoss", 0.0, "", "通信丢失告警", cdc="STV"),
        _f("GridLoss", 0.0, "", "电网丢失告警", cdc="STV"),
        _f("OverSpeed", 0.0, "", "超速告警", cdc="STV"),
        _f("VibrAlm", 0.0, "",  "振动告警", cdc="STV"),
        _f("TempAlm", 0.0, "",  "温度告警", cdc="STV"),
    ],
)


# =============================================================================
# 6.2.12 WSLG — 状态日志信息 (State Log)
# =============================================================================
WSLG = LogicalNodeDef(
    name="WSLG", desc="状态日志信息",
    fields=[
        _f("OpTmh",   87600.0, "h", "以小时为单位运行时间", cdc="INS"),
        _f("OpCnt",   500.0, "",  "操作计数器", cdc="INS"),
        _f("tmsVal",  87600.0, "h", "状态持续时间", cdc="INS", mo="M"),
        _f("oldTmsVal", 87600.0, "h", "较早的状态持续时间", cdc="INS"),
        _f("cntVal",  500.0, "",  "实际事件计数", cdc="BCR", mo="M"),
        _f("oldCntVal", 500.0, "", "较早的事件计数", cdc="BCR"),
        _f("hisRs",   0.0, "",    "复位历史信息", cdc="ENC"),
        _f("entTot",  500.0, "",  "入口总计数", cdc="BCR"),
        _f("tot",     500.0, "",  "总计数数据", cdc="BCR"),
        _f("st",      1.0, "",    "当前控制状态", cdc="ENC", mo="M"),
        # 发电量统计
        _f("TotalProd", 52000.0, "MWh", "累计发电量", cdc="BCR"),
        _f("YearProd", 6200.0, "MWh", "年发电量", cdc="BCR"),
        _f("MonthProd", 520.0, "MWh", "月发电量", cdc="BCR"),
        _f("DayProd", 17.5, "MWh", "日发电量", cdc="BCR"),
        _f("StrtCnt", 500.0, "",  "启动次数", cdc="INC"),
        _f("StopCnt", 498.0, "",  "停机次数", cdc="INC"),
        _f("EmerStopCnt", 5.0, "", "紧急停机次数", cdc="INC"),
        _f("GridLossCnt", 12.0, "", "电网丢失次数", cdc="INC"),
        _f("SWVer",   3.12, "",   "软件版本号", cdc="INS"),
        _f("ConfigChgCnt", 15.0, "", "配置变更次数", cdc="INC"),
    ],
)


# =============================================================================
# 6.2.12 WALG — 模拟量日志信息 (Analog Log)
# =============================================================================
WALG = LogicalNodeDef(
    name="WALG", desc="模拟量日志信息",
    fields=[
        _f("logVal1",  0.0, "",  "模拟量记录值1", cdc="MV"),
        _f("logVal2",  0.0, "",  "模拟量记录值2", cdc="MV"),
        _f("logVal3",  0.0, "",  "模拟量记录值3", cdc="MV"),
        _f("logVal4",  0.0, "",  "模拟量记录值4", cdc="MV"),
        _f("logVal5",  0.0, "",  "模拟量记录值5", cdc="MV"),
        _f("logTms",   0.0, "s", "模拟量记录时间戳", cdc="MV"),
        _f("logPer",   10.0, "min", "模拟量记录周期", cdc="MV"),
        _f("logNb",    100.0, "", "模拟量记录条数", cdc="INS"),
    ],
)


# =============================================================================
# 6.2.12 WREP — 报表信息 (Report)
# =============================================================================
WREP = LogicalNodeDef(
    name="WREP", desc="报表信息",
    fields=[
        _f("DAvail",  97.5, "%", "日可用率", cdc="MV"),
        _f("MAvail",  96.8, "%", "月可用率", cdc="MV"),
        _f("YAvail",  96.2, "%", "年可用率", cdc="MV"),
        _f("DProd",   18.2, "MWh", "日发电量", cdc="MV"),
        _f("MProd",   520.0, "MWh", "月发电量", cdc="MV"),
        _f("YProd",   6200.0, "MWh", "年发电量", cdc="MV"),
        _f("DDowntime", 0.6, "h", "日停机时间", cdc="MV"),
        _f("MDowntime", 18.0, "h", "月停机时间", cdc="MV"),
        _f("DAvgWs",  8.2, "m/s", "日平均风速", cdc="MV"),
        _f("MAvgWs",  7.8, "m/s", "月平均风速", cdc="MV"),
        _f("DAvgW",   1200.0, "kW", "日平均功率", cdc="MV"),
        _f("MAvgW",   1150.0, "kW", "月平均功率", cdc="MV"),
        _f("DPeakW",  1500.0, "kW", "日峰值功率", cdc="MV"),
        _f("MPeakW",  1550.0, "kW", "月峰值功率", cdc="MV"),
        _f("DGridLossCnt", 0.0, "", "日电网丢失次数", cdc="INC"),
        _f("MGridLossCnt", 2.0, "", "月电网丢失次数", cdc="INC"),
        _f("DFaultCnt", 0.0, "", "日故障次数", cdc="INC"),
        _f("MFaultCnt", 3.0, "", "月故障次数", cdc="INC"),
        _f("DAlarmCnt", 2.0, "", "日告警次数", cdc="INC"),
        _f("MAlarmCnt", 15.0, "", "月告警次数", cdc="INC"),
        _f("DStrtCnt", 2.0, "", "日启动次数", cdc="INC"),
        _f("MStrtCnt", 45.0, "", "月启动次数", cdc="INC"),
        _f("DCurtailHrs", 0.5, "h", "日限电小时数", cdc="MV"),
        _f("MCurtailHrs", 12.0, "h", "月限电小时数", cdc="MV"),
        _f("DCurtailE", 0.3, "MWh", "日限电损失电量", cdc="MV"),
        _f("MCurtailE", 8.0, "MWh", "月限电损失电量", cdc="MV"),
        _f("DServiceHrs", 0.0, "h", "日检修小时数", cdc="MV"),
        _f("MServiceHrs", 4.0, "h", "月检修小时数", cdc="MV"),
        _f("DTurbulence", 0.12, "", "日湍流强度", cdc="MV"),
        _f("DWindShear", 0.15, "", "日风剪切系数", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.13 WAVL — 可利用率信息 (Availability)
# =============================================================================
WAVL = LogicalNodeDef(
    name="WAVL", desc="可利用率信息",
    fields=[
        # 可用信息计数 (IEC 61400-25-2 Annex A availability model)
        _f("Ta",      8760.0, "h", "可用信息", cdc="INC"),
        _f("Tao",     8640.0, "h", "运行可用信息", cdc="INC"),
        _f("Iafm",    0.0, "h",  "不可抗力可用信息", cdc="INC"),
        _f("Iano",    120.0, "h", "非运行可用信息", cdc="INC"),
        _f("Ianofo",  24.0, "h", "非运行-强制停机可用信息", cdc="INC"),
        _f("Ianopca", 8.0, "h",  "非运行-计划性改进可用信息", cdc="INC"),
        _f("Ianos",   12.0, "h", "非运行-暂停作业可用信息", cdc="INC"),
        _f("Ianosm",  48.0, "h", "非运行-定期维护可用信息", cdc="INC"),
        _f("Iaog",    8500.0, "h", "发电运行可用信息", cdc="INC"),
        _f("Iaogfp",  8200.0, "h", "正常-发电运行可用信息", cdc="INC"),
        _f("Iaogpp",  300.0, "h", "非正常-发电和运行可用信息", cdc="INC"),
        _f("Iaong",   140.0, "h", "非发电运行可用信息", cdc="INC"),
        _f("Iaongen", 20.0, "h", "非发电运行-超出环境条件可用信息", cdc="INC"),
        _f("Iaongrs", 50.0, "h", "非发电运行-指令停机可用信息", cdc="INC"),
        _f("Iaongts", 70.0, "h", "非发电运行-技术待机可用信息", cdc="INC"),
        _f("laongel", 10.0, "h", "非发电运行-超出电气规范可用信息", cdc="INC"),
        _f("SysAvl",  97.5, "%", "系统可利用率(具体实施)", cdc="MV"),
        _f("TurAvl",  97.5, "%", "风力发电机组可利用率(具体实施)", cdc="MV"),
    ],
)


# =============================================================================
# 6.2.14 WAPC — 有功功率控制信息 (Active Power Control)
# =============================================================================
WAPC = LogicalNodeDef(
    name="WAPC", desc="有功功率控制信息",
    fields=[
        _f("WSpt",    1500.0, "kW", "设置风电场有功功率输出参考值", cdc="SPV", mo="M"),
        _f("WCap",    1500.0, "kW", "风电场有功功率输出容量", cdc="MV"),
        _f("WDnGraSpt", 100.0, "kW/min", "设置风电场有功功率输出梯度下降斜率参考值", cdc="SPV"),
        _f("WUpGraSpt", 100.0, "kW/min", "设置风电场有功功率输出梯度上升斜率参考值", cdc="SPV"),
        _f("WMinCap", 100.0, "kW", "风电场最小容量有功功率", cdc="MV"),
        _f("WLimEna", 0.0, "",   "启用有功功率限制模式", cdc="STV"),
        _f("WAct",    1.0, "",   "激活有功功率控制功能", cdc="CMD"),
        _f("DrpSpt",  0.0, "",   "设置电压跌落控制的斜坡参考值", cdc="SPV"),
        _f("GraAct",  1.0, "",   "激活梯度控制功能", cdc="CMD"),
        _f("GraEna",  1.0, "",   "启用梯度函数", cdc="STV"),
    ],
)


# =============================================================================
# 6.2.14 WRPC — 无功功率控制信息 (Reactive Power Control)
# =============================================================================
WRPC = LogicalNodeDef(
    name="WRPC", desc="无功功率控制信息",
    fields=[
        _f("VArSpt",  200.0, "kVAr", "设置风电场无功功率输出参考值", cdc="SPV"),
        _f("VArDnGraSpt", 50.0, "kVAr/min", "设置风电场无功功率输出梯度下降斜率参考值", cdc="SPV"),
        _f("VArUpGraSpt", 50.0, "kVAr/min", "设置风电场无功功率输出梯度上升斜率参考值", cdc="SPV"),
        _f("VArCapExpt", 200.0, "kVAr", "风电场无功功率输出(供应)容量", cdc="MV"),
        _f("VArCaplmpt", 200.0, "kVAr", "风电场无功功率输入(需求)容量", cdc="MV"),
        _f("VArMinCap", 0.0, "kVAr", "风电场最小无功功率容量", cdc="MV"),
        _f("VArMod",  1.0, "",   "无功功率控制模式", cdc="STV"),
        _f("VArAct",  1.0, "",   "激活无功功率控制功能", cdc="CMD"),
        _f("VSpt",    690.0, "V", "设置风电场电压输出参考值", cdc="SPV"),
        _f("VDnGraSpt", 10.0, "V/min", "设置风电场电压下降斜率参考值", cdc="SPV"),
        _f("VUpGraSpt", 10.0, "V/min", "设置风电场电压上升斜率参考值", cdc="SPV"),
        _f("VA",      1500.0, "kVA", "风电场视在功率", cdc="MV"),
        _f("VASpt",   1500.0, "kVA", "设置风电场视在功率输出参考值", cdc="SPV"),
        _f("VAAct",   1.0, "",   "激活视在功率控制功能", cdc="CMD"),
        _f("VAEna",   1.0, "",   "启用有功功率控制模式来控制视在功率", cdc="STV"),
    ],
)


# =============================================================================
# LTIM — 时间管理 (Time Management, ref DL/T 860.74)
# =============================================================================
LTIM = LogicalNodeDef(
    name="LTIM", desc="时间管理",
    fields=[
        _f("TmSrc",   1.0, "",  "时间源", cdc="STV"),
        _f("TmSync",  1.0, "",  "时间同步状态", cdc="STV"),
        _f("TmOfs",   0.0, "ms", "时间偏移", cdc="MV"),
        _f("TmAcc",   1.0, "ms", "时间精度", cdc="MV"),
    ],
)


# =============================================================================
# All logical nodes
# =============================================================================
ALL_LOGICAL_NODES: list[LogicalNodeDef] = [
    WPPD, WTUR, WROT, WTRM, WGEN, WCNV, WTRF, WNAC, WYAW, WTOW,
    WMET, WALM, WSLG, WALG, WREP, WAVL, WAPC, WRPC, LTIM,
]


def build_field_dict() -> dict[str, float]:
    """Build a flat {variable_key: mean_value} dict from all logical nodes."""
    result: dict[str, float] = {}
    for node in ALL_LOGICAL_NODES:
        for node_field in node.fields:
            result[node_field.key] = node_field.mean
    return result


def total_field_count() -> int:
    """Return the total number of fields across all logical nodes."""
    return sum(len(node.fields) for node in ALL_LOGICAL_NODES)
