-- BlueCrystal Whale 场站样例数据 DML v2.14.0
-- 基于 V2.11.0 场站样例继续演进；业务样例不变，仅同步 Meta 二级分类与 View/模式命名。
-- 当前通信样例仅覆盖外部 Remote Connection：IEC104 被控站与 ADS Server。
-- 不包含 Whale 本地 Server/监听场景；该部分待 serv_* 域设计后补充。

BEGIN;
SET search_path TO whale, public;


-- ============================================================================
-- 1. 组织、场站与人员样例
-- ============================================================================


INSERT INTO whale.org_organization (
    parent_org_organization_id, organization_identifier, meta_org_organization_type_id, name_zh, description_zh
) VALUES
(NULL, 'ORG_WHALE_GROUP', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'GROUP'), '鲸能集团', '沿用V1.5.17集团样例。'),
(whale.organization_id('ORG_WHALE_GROUP'), 'ORG_WHALE_REGION_EAST', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'REGIONAL_COMPANY'), '鲸能集团华东区域公司', '区域管理层级。'),
(whale.organization_id('ORG_WHALE_REGION_EAST'), 'ORG_BLUECRYSTAL_PLANT_CO', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'PROJECT_COMPANY'), '蓝水晶风光储电场公司', '沿用V1.5.17项目公司样例。'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'ORG_BLUECRYSTAL_OPERATIONS_DEPT', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'DEPARTMENT'), '运行管理部', '运行责任组织。'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'ORG_BLUECRYSTAL_MAINTENANCE_DEPT', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'DEPARTMENT'), '设备维保部', '设备维保责任组织。'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'ORG_BLUECRYSTAL_CONTROL_DEPT', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'DEPARTMENT'), '控制与通信部', '控制与通信责任组织。'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'ORG_BLUECRYSTAL_SAFETY_DEPT', (SELECT meta_org_organization_type_id FROM whale.meta_org_organization_type WHERE code = 'DEPARTMENT'), '安全管理部', '安全责任组织。');

INSERT INTO whale.org_site (
    operating_org_organization_id, site_identifier, meta_org_site_type_id, name_zh, wind_installed_capacity_mw, pv_installed_capacity_mw, storage_power_mw, storage_capacity_mwh, grid_voltage_kv, grid_connection_date, description_zh
) VALUES
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'PLANT_BLUECRYSTAL_001', (SELECT meta_org_site_type_id FROM whale.meta_org_site_type WHERE code = 'HYBRID_PLANT'), '蓝水晶风光储一体化电场', 10.000, 0.250, 2.500, 3.727, 220.000, DATE '2024-01-10', '沿用V1.5.17的风光储并网样例场站。');

INSERT INTO whale.org_employee (
    source_org_organization_id, employee_identifier, name_zh, email
) VALUES
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_001', '张建国', 'emp_001@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_002', '李明', 'emp_002@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_003', '王强', 'emp_003@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_004', '赵磊', 'emp_004@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_005', '陈宇', 'emp_005@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_006', '刘洋', 'emp_006@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_007', '孙涛', 'emp_007@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_008', '周杰', 'emp_008@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_009', '吴峰', 'emp_009@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_010', '郑浩', 'emp_010@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_011', '马超', 'emp_011@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_012', '胡斌', 'emp_012@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_013', '高翔', 'emp_013@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_014', '蒋锐', 'emp_014@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_015', '何敏', 'emp_015@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_016', '唐伟', 'emp_016@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_017', '罗宁', 'emp_017@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_018', '许凯', 'emp_018@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_019', '程亮', 'emp_019@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_020', '林青', 'emp_020@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_021', '方舟', 'emp_021@bluecrystal.local'),
(whale.organization_id('ORG_BLUECRYSTAL_PLANT_CO'), 'EMP_022', '何远', 'emp_022@bluecrystal.local');

INSERT INTO whale.org_employee_responsibility (
    org_employee_id, org_organization_id, org_site_id, meta_org_responsibility_category_id, valid_from, valid_to, description_zh
) VALUES
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_003' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_OPERATIONS_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'OPERATIONS'), TIMESTAMPTZ '2024-01-10 00:00:00+08', TIMESTAMPTZ '2025-06-30 23:59:59+08', '历史运行责任人。'),
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_004' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_OPERATIONS_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'OPERATIONS'), TIMESTAMPTZ '2025-07-01 00:00:00+08', NULL, '当前运行责任人。'),
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_007' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_MAINTENANCE_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'ELECTRICAL_MAINTENANCE'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL, '当前电气维保责任人。'),
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_013' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_MAINTENANCE_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'MECHANICAL_MAINTENANCE'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL, '当前机械维保责任人。'),
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_011' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_CONTROL_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'CONTROL_MAINTENANCE'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL, '当前控制维保责任人。'),
((SELECT org_employee_id FROM whale.org_employee WHERE employee_identifier='EMP_018' AND enabled=TRUE LIMIT 1), whale.organization_id('ORG_BLUECRYSTAL_SAFETY_DEPT'), whale.site_id('PLANT_BLUECRYSTAL_001'), (SELECT meta_org_responsibility_category_id FROM whale.meta_org_responsibility_category WHERE code = 'SAFETY'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL, '当前安全管理责任人。');

-- ============================================================================
-- 2. 设备类型、型号、参数、组成和实例样例
-- ============================================================================


INSERT INTO whale.equ_type (
    type_identifier, name_zh
) VALUES
('WIND_TURBINE', '风力发电机组'),
('MAIN_CONTROLLER', '主控系统'),
('CONVERTER', '变流器'),
('PITCH_SYSTEM', '变桨系统'),
('YAW_SYSTEM', '偏航系统'),
('GEARBOX', '齿轮箱'),
('GENERATOR', '发电机'),
('HUB', '轮毂'),
('BLADE', '叶片'),
('TOWER', '塔筒'),
('PAD_TRANSFORMER', '箱式变压器'),
('PV_INVERTER', '光伏逆变器'),
('PV_COMBINER', '光伏汇流箱'),
('PV_ARRAY', '光伏阵列'),
('BESS_CONTAINER', '储能集装箱'),
('PCS', '储能变流器'),
('BMS', '电池管理系统'),
('BATTERY_CLUSTER', '电池簇'),
('MAIN_TRANSFORMER', '主变压器'),
('SVG', '静止无功发生器'),
('GRID_METER', '关口电能表'),
('AGC_AVC_CONTROLLER', 'AGC/AVC控制器'),
('DISPATCH_GATEWAY', '远动通信网关'),
('MET_MAST', '测风塔'),
('WEATHER_STATION', '气象站');

INSERT INTO whale.equ_type (
    type_identifier, name_zh, description_zh, enabled
) VALUES
('BOX_TRANSFORMER', '风机箱式变压器', '将风机低压侧升压接入 35kV 集电系统。', TRUE),
('SWITCHGEAR', '开关柜', '35kV 集电系统开关柜或汇集柜。', TRUE),
('GRID_BREAKER', '并网断路器', '场站并网出口断路器。', TRUE),
('POI_METER', '并网点计量装置', '并网点电气量计量装置。', TRUE),
('OPTICAL_SWITCH', '工业光纤交换机', '风机侧环网交换设备。', TRUE),
('CORE_SWITCH', '核心交换机', '升压站站控层或生产控制区核心交换设备。', TRUE),
('SECURITY_ISOLATION_DEVICE', '安全隔离装置', '生产控制区与外部调度数据网之间的安全隔离设备。', TRUE),
('NTP_SERVER', '时钟服务器', '向场站设备提供 NTP/PTP 等时间同步服务。', TRUE);

INSERT INTO whale.equ_model (
    equ_type_id, model_identifier, manufacturer_name, model_name, version_label
) VALUES
(whale.equipment_type_id('WIND_TURBINE'), 'GE_2_5_120', 'GE', 'GE 2.5-120 风机', 'V1'),
(whale.equipment_type_id('MAIN_CONTROLLER'), 'GE_MAIN_CONTROLLER', 'GE', 'GE 风机主控', 'V1'),
(whale.equipment_type_id('CONVERTER'), 'GE_CONVERTER', 'GE', 'GE 变流器', 'V1'),
(whale.equipment_type_id('PITCH_SYSTEM'), 'GE_PITCH', 'GE', 'GE 变桨系统', 'V1'),
(whale.equipment_type_id('YAW_SYSTEM'), 'GE_YAW', 'GE', 'GE 偏航系统', 'V1'),
(whale.equipment_type_id('GEARBOX'), 'GE_GEARBOX_V1', 'GE', 'GE 齿轮箱 V1', 'V1'),
(whale.equipment_type_id('GEARBOX'), 'GE_GEARBOX_V2', 'GE', 'GE 齿轮箱 V2', 'V1'),
(whale.equipment_type_id('GENERATOR'), 'GE_GENERATOR', 'GE', 'GE 发电机', 'V1'),
(whale.equipment_type_id('HUB'), 'GE_HUB', 'GE', 'GE 轮毂', 'V1'),
(whale.equipment_type_id('BLADE'), 'GE_BLADE', 'GE', 'GE 叶片', 'V1'),
(whale.equipment_type_id('TOWER'), 'GE_TOWER', 'GE', 'GE 塔筒', 'V1'),
(whale.equipment_type_id('PAD_TRANSFORMER'), 'TBEA_PAD_TR_MODEL', 'TBEA', '风机箱变', 'V1'),
(whale.equipment_type_id('PV_INVERTER'), 'SG250HX', 'SUNGROW', '阳光 SG250HX', 'V1'),
(whale.equipment_type_id('PV_COMBINER'), 'PV_COMBINER_24', 'SUNGROW', '24路汇流箱', 'V1'),
(whale.equipment_type_id('PV_ARRAY'), 'PV_ARRAY_MODEL', 'GENERIC', '光伏阵列', 'V1'),
(whale.equipment_type_id('BESS_CONTAINER'), 'ENERONE_3727KWH', 'CATL', 'CATL EnerOne 3.727MWh', 'V1'),
(whale.equipment_type_id('PCS'), 'SC2500UD_MV', 'SUNGROW', '阳光 SC2500UD-MV', 'V1'),
(whale.equipment_type_id('BMS'), 'CATL_BMS', 'CATL', 'CATL BMS', 'V1'),
(whale.equipment_type_id('BATTERY_CLUSTER'), 'CATL_BAT_CLUSTER', 'CATL', 'CATL 电池簇', 'V1'),
(whale.equipment_type_id('MAIN_TRANSFORMER'), 'TBEA_MAIN_TRANSFORMER_120MVA', 'TBEA', '120MVA主变', 'V1'),
(whale.equipment_type_id('SVG'), 'NR_SVG_35KV', 'NR_ELECTRIC', '35kV SVG', 'V1'),
(whale.equipment_type_id('GRID_METER'), 'NARI_GRID_METER', 'NARI', '关口电能表', 'V1'),
(whale.equipment_type_id('AGC_AVC_CONTROLLER'), 'NARI_AGC_AVC', 'NARI', 'AGC/AVC控制器', 'V1'),
(whale.equipment_type_id('DISPATCH_GATEWAY'), 'NARI_DISPATCH_GATEWAY', 'NARI', '远动通信网关', 'V1'),
(whale.equipment_type_id('MET_MAST'), 'VAISALA_MET_MAST', 'VAISALA', '测风塔', 'V1'),
(whale.equipment_type_id('WEATHER_STATION'), 'VAISALA_WEATHER_STATION', 'VAISALA', '气象站', 'V1');

INSERT INTO whale.equ_model (
    equ_type_id, model_identifier, manufacturer_name, model_name, description_zh
) VALUES
(whale.equipment_type_id('WIND_TURBINE'), 'MODEL_WTG_GENERIC', 'BlueCrystal', 'WTG-5MW', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('BOX_TRANSFORMER'), 'MODEL_BOXTR_GENERIC', 'BlueCrystal', '0.69/35kV', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('SWITCHGEAR'), 'MODEL_SWGR_GENERIC', 'BlueCrystal', '35kV Switchgear', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('MAIN_TRANSFORMER'), 'MODEL_MAINTR_GENERIC', 'BlueCrystal', '35/220kV', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('GRID_BREAKER'), 'MODEL_BREAKER_GENERIC', 'BlueCrystal', '220kV Breaker', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('POI_METER'), 'MODEL_POI_METER_GENERIC', 'BlueCrystal', 'POI Meter', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('OPTICAL_SWITCH'), 'MODEL_OPT_SWITCH_GENERIC', 'BlueCrystal', 'Industrial Ring Switch', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('CORE_SWITCH'), 'MODEL_CORE_SWITCH_GENERIC', 'BlueCrystal', 'Core Switch', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('SECURITY_ISOLATION_DEVICE'), 'MODEL_ISO_GENERIC', 'BlueCrystal', 'Security Isolation', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('NTP_SERVER'), 'MODEL_NTP_GENERIC', 'BlueCrystal', 'NTP/PTP Server', '样例型号，用于结构和拓扑验证。'),
(whale.equipment_type_id('AGC_AVC_CONTROLLER'), 'MODEL_AGCAVC_GENERIC', 'BlueCrystal', 'AGC/AVC Controller', '样例型号，用于结构和拓扑验证。');

INSERT INTO whale.equ_parameter_definition (
    equ_type_id, parameter_identifier, name_zh, meta_point_data_type_id, meta_point_unit_id, required, numeric_min, numeric_max
) VALUES
(whale.equipment_type_id('WIND_TURBINE'), 'RATED_POWER', '额定功率', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MW'), TRUE, 0, 20),
(whale.equipment_type_id('WIND_TURBINE'), 'ROTOR_DIAMETER', '叶轮直径', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'M'), TRUE, 1, 300),
(whale.equipment_type_id('WIND_TURBINE'), 'HUB_HEIGHT', '轮毂高度', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'M'), TRUE, 1, 300),
(whale.equipment_type_id('WIND_TURBINE'), 'CUT_IN_WIND_SPEED', '切入风速', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MPS'), TRUE, 0, 20),
(whale.equipment_type_id('WIND_TURBINE'), 'CUT_OUT_WIND_SPEED', '切出风速', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MPS'), TRUE, 5, 60),
(whale.equipment_type_id('GEARBOX'), 'GEAR_RATIO', '传动比', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'NONE'), TRUE, 1, 300),
(whale.equipment_type_id('BESS_CONTAINER'), 'RATED_ENERGY', '额定能量', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MWH'), TRUE, 0, 1000),
(whale.equipment_type_id('BESS_CONTAINER'), 'RATED_POWER', '额定功率', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MW'), TRUE, 0, 1000),
(whale.equipment_type_id('PCS'), 'RATED_POWER', '额定功率', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MW'), TRUE, 0, 1000),
(whale.equipment_type_id('MAIN_TRANSFORMER'), 'RATED_CAPACITY', '额定容量', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'MVA'), TRUE, 0, 1000),
(whale.equipment_type_id('MAIN_TRANSFORMER'), 'HIGH_VOLTAGE', '高压侧电压', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'KV'), TRUE, 0, 1000),
(whale.equipment_type_id('MAIN_TRANSFORMER'), 'LOW_VOLTAGE', '低压侧电压', (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code = 'FLOAT32'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code = 'KV'), TRUE, 0, 1000);

INSERT INTO whale.equ_model_parameter (
    equ_model_id, equ_parameter_definition_id, parameter_value
) VALUES
(whale.equipment_model_id('GE_2_5_120'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('WIND_TURBINE') AND parameter_identifier='RATED_POWER'), to_jsonb(2.5::NUMERIC)),
(whale.equipment_model_id('GE_2_5_120'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('WIND_TURBINE') AND parameter_identifier='ROTOR_DIAMETER'), to_jsonb(120::NUMERIC)),
(whale.equipment_model_id('GE_2_5_120'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('WIND_TURBINE') AND parameter_identifier='HUB_HEIGHT'), to_jsonb(90::NUMERIC)),
(whale.equipment_model_id('GE_2_5_120'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('WIND_TURBINE') AND parameter_identifier='CUT_IN_WIND_SPEED'), to_jsonb(3.0::NUMERIC)),
(whale.equipment_model_id('GE_2_5_120'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('WIND_TURBINE') AND parameter_identifier='CUT_OUT_WIND_SPEED'), to_jsonb(25.0::NUMERIC)),
(whale.equipment_model_id('GE_GEARBOX_V1'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('GEARBOX') AND parameter_identifier='GEAR_RATIO'), to_jsonb(97.5::NUMERIC)),
(whale.equipment_model_id('GE_GEARBOX_V2'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('GEARBOX') AND parameter_identifier='GEAR_RATIO'), to_jsonb(98.2::NUMERIC)),
(whale.equipment_model_id('ENERONE_3727KWH'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('BESS_CONTAINER') AND parameter_identifier='RATED_ENERGY'), to_jsonb(3.727::NUMERIC)),
(whale.equipment_model_id('ENERONE_3727KWH'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('BESS_CONTAINER') AND parameter_identifier='RATED_POWER'), to_jsonb(2.5::NUMERIC)),
(whale.equipment_model_id('SC2500UD_MV'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('PCS') AND parameter_identifier='RATED_POWER'), to_jsonb(2.5::NUMERIC)),
(whale.equipment_model_id('TBEA_MAIN_TRANSFORMER_120MVA'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('MAIN_TRANSFORMER') AND parameter_identifier='RATED_CAPACITY'), to_jsonb(120::NUMERIC)),
(whale.equipment_model_id('TBEA_MAIN_TRANSFORMER_120MVA'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('MAIN_TRANSFORMER') AND parameter_identifier='HIGH_VOLTAGE'), to_jsonb(220::NUMERIC)),
(whale.equipment_model_id('TBEA_MAIN_TRANSFORMER_120MVA'), (SELECT equ_parameter_definition_id FROM whale.equ_parameter_definition WHERE equ_type_id=whale.equipment_type_id('MAIN_TRANSFORMER') AND parameter_identifier='LOW_VOLTAGE'), to_jsonb(35::NUMERIC));

INSERT INTO whale.equ_model_component (
    parent_equ_model_id, component_slot_code, component_slot_name_zh, child_equ_type_id, child_equ_model_id, required, quantity, sort_order
) VALUES
(whale.equipment_model_id('GE_2_5_120'), 'MAIN_CONTROLLER', '主控系统', whale.equipment_type_id('MAIN_CONTROLLER'), whale.equipment_model_id('GE_MAIN_CONTROLLER'), TRUE, 1, 1),
(whale.equipment_model_id('GE_2_5_120'), 'CONVERTER', '变流器', whale.equipment_type_id('CONVERTER'), whale.equipment_model_id('GE_CONVERTER'), TRUE, 1, 2),
(whale.equipment_model_id('GE_2_5_120'), 'PITCH_SYSTEM', '变桨系统', whale.equipment_type_id('PITCH_SYSTEM'), whale.equipment_model_id('GE_PITCH'), TRUE, 1, 3),
(whale.equipment_model_id('GE_2_5_120'), 'YAW_SYSTEM', '偏航系统', whale.equipment_type_id('YAW_SYSTEM'), whale.equipment_model_id('GE_YAW'), TRUE, 1, 4),
(whale.equipment_model_id('GE_2_5_120'), 'GEARBOX', '齿轮箱', whale.equipment_type_id('GEARBOX'), NULL, TRUE, 1, 5),
(whale.equipment_model_id('GE_2_5_120'), 'GENERATOR', '发电机', whale.equipment_type_id('GENERATOR'), whale.equipment_model_id('GE_GENERATOR'), TRUE, 1, 6),
(whale.equipment_model_id('GE_2_5_120'), 'HUB', '轮毂', whale.equipment_type_id('HUB'), whale.equipment_model_id('GE_HUB'), TRUE, 1, 7),
(whale.equipment_model_id('GE_2_5_120'), 'BLADE_1', '1号叶片', whale.equipment_type_id('BLADE'), whale.equipment_model_id('GE_BLADE'), TRUE, 1, 8),
(whale.equipment_model_id('GE_2_5_120'), 'BLADE_2', '2号叶片', whale.equipment_type_id('BLADE'), whale.equipment_model_id('GE_BLADE'), TRUE, 1, 9),
(whale.equipment_model_id('GE_2_5_120'), 'BLADE_3', '3号叶片', whale.equipment_type_id('BLADE'), whale.equipment_model_id('GE_BLADE'), TRUE, 1, 10),
(whale.equipment_model_id('GE_2_5_120'), 'TOWER', '塔筒', whale.equipment_type_id('TOWER'), whale.equipment_model_id('GE_TOWER'), TRUE, 1, 11),
(whale.equipment_model_id('GE_2_5_120'), 'PAD_TRANSFORMER', '箱变', whale.equipment_type_id('PAD_TRANSFORMER'), whale.equipment_model_id('TBEA_PAD_TR_MODEL'), TRUE, 1, 12),
(whale.equipment_model_id('ENERONE_3727KWH'), 'PCS', '储能变流器', whale.equipment_type_id('PCS'), whale.equipment_model_id('SC2500UD_MV'), TRUE, 1, 1),
(whale.equipment_model_id('ENERONE_3727KWH'), 'BMS', '电池管理系统', whale.equipment_type_id('BMS'), whale.equipment_model_id('CATL_BMS'), TRUE, 1, 2),
(whale.equipment_model_id('ENERONE_3727KWH'), 'BATTERY_CLUSTER_1', '1号电池簇', whale.equipment_type_id('BATTERY_CLUSTER'), whale.equipment_model_id('CATL_BAT_CLUSTER'), TRUE, 1, 3),
(whale.equipment_model_id('ENERONE_3727KWH'), 'BATTERY_CLUSTER_2', '2号电池簇', whale.equipment_type_id('BATTERY_CLUSTER'), whale.equipment_model_id('CATL_BAT_CLUSTER'), TRUE, 1, 4),
(whale.equipment_model_id('ENERONE_3727KWH'), 'BATTERY_CLUSTER_3', '3号电池簇', whale.equipment_type_id('BATTERY_CLUSTER'), whale.equipment_model_id('CATL_BAT_CLUSTER'), TRUE, 1, 5),
(whale.equipment_model_id('ENERONE_3727KWH'), 'BATTERY_CLUSTER_4', '4号电池簇', whale.equipment_type_id('BATTERY_CLUSTER'), whale.equipment_model_id('CATL_BAT_CLUSTER'), TRUE, 1, 6);

INSERT INTO whale.equ_equipment (
    org_site_id, equ_model_id, equipment_identifier, name_zh, manufacturer_serial_number, meta_equ_equipment_status_id, commissioned_at, decommissioned_at
) VALUES
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_2_5_120'), 'WTG_001', 'WTG_001 风机', 'WTG_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_MAIN_CONTROLLER'), 'WTG_001_MAIN_CONTROLLER', 'WTG_001 主控', 'WTG_001_MAIN_CONTROLLER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_CONVERTER'), 'WTG_001_CONVERTER', 'WTG_001 变流器', 'WTG_001_CONVERTER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_PITCH'), 'WTG_001_PITCH_SYSTEM', 'WTG_001 变桨系统', 'WTG_001_PITCH_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_YAW'), 'WTG_001_YAW_SYSTEM', 'WTG_001 偏航系统', 'WTG_001_YAW_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GENERATOR'), 'WTG_001_GENERATOR', 'WTG_001 发电机', 'WTG_001_GENERATOR-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_HUB'), 'WTG_001_HUB', 'WTG_001 轮毂', 'WTG_001_HUB-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_001_BLADE_1', 'WTG_001 1号叶片', 'WTG_001_BLADE_1-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_001_BLADE_2', 'WTG_001 2号叶片', 'WTG_001_BLADE_2-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_001_BLADE_3', 'WTG_001 3号叶片', 'WTG_001_BLADE_3-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_TOWER'), 'WTG_001_TOWER', 'WTG_001 塔筒', 'WTG_001_TOWER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('TBEA_PAD_TR_MODEL'), 'WTG_001_PAD_TRANSFORMER', 'WTG_001 箱变', 'WTG_001_PAD_TRANSFORMER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GEARBOX_V1'), 'WTG_001_GEARBOX_A', 'WTG_001 原齿轮箱', 'WTG_001_GEARBOX_A-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'OUT_OF_SERVICE'), DATE '2024-01-10', DATE '2025-05-31'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GEARBOX_V2'), 'WTG_001_GEARBOX_B', 'WTG_001 当前齿轮箱', 'WTG_001_GEARBOX_B-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2025-06-01', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_2_5_120'), 'WTG_002', 'WTG_002 风机', 'WTG_002-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_MAIN_CONTROLLER'), 'WTG_002_MAIN_CONTROLLER', 'WTG_002 主控', 'WTG_002_MAIN_CONTROLLER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_CONVERTER'), 'WTG_002_CONVERTER', 'WTG_002 变流器', 'WTG_002_CONVERTER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_PITCH'), 'WTG_002_PITCH_SYSTEM', 'WTG_002 变桨系统', 'WTG_002_PITCH_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_YAW'), 'WTG_002_YAW_SYSTEM', 'WTG_002 偏航系统', 'WTG_002_YAW_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GENERATOR'), 'WTG_002_GENERATOR', 'WTG_002 发电机', 'WTG_002_GENERATOR-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_HUB'), 'WTG_002_HUB', 'WTG_002 轮毂', 'WTG_002_HUB-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_002_BLADE_1', 'WTG_002 1号叶片', 'WTG_002_BLADE_1-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_002_BLADE_2', 'WTG_002 2号叶片', 'WTG_002_BLADE_2-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_002_BLADE_3', 'WTG_002 3号叶片', 'WTG_002_BLADE_3-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_TOWER'), 'WTG_002_TOWER', 'WTG_002 塔筒', 'WTG_002_TOWER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('TBEA_PAD_TR_MODEL'), 'WTG_002_PAD_TRANSFORMER', 'WTG_002 箱变', 'WTG_002_PAD_TRANSFORMER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GEARBOX_V1'), 'WTG_002_GEARBOX', 'WTG_002 齿轮箱', 'WTG_002_GEARBOX-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_2_5_120'), 'WTG_003', 'WTG_003 风机', 'WTG_003-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_MAIN_CONTROLLER'), 'WTG_003_MAIN_CONTROLLER', 'WTG_003 主控', 'WTG_003_MAIN_CONTROLLER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_CONVERTER'), 'WTG_003_CONVERTER', 'WTG_003 变流器', 'WTG_003_CONVERTER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_PITCH'), 'WTG_003_PITCH_SYSTEM', 'WTG_003 变桨系统', 'WTG_003_PITCH_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_YAW'), 'WTG_003_YAW_SYSTEM', 'WTG_003 偏航系统', 'WTG_003_YAW_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GENERATOR'), 'WTG_003_GENERATOR', 'WTG_003 发电机', 'WTG_003_GENERATOR-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_HUB'), 'WTG_003_HUB', 'WTG_003 轮毂', 'WTG_003_HUB-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_003_BLADE_1', 'WTG_003 1号叶片', 'WTG_003_BLADE_1-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_003_BLADE_2', 'WTG_003 2号叶片', 'WTG_003_BLADE_2-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_003_BLADE_3', 'WTG_003 3号叶片', 'WTG_003_BLADE_3-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_TOWER'), 'WTG_003_TOWER', 'WTG_003 塔筒', 'WTG_003_TOWER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('TBEA_PAD_TR_MODEL'), 'WTG_003_PAD_TRANSFORMER', 'WTG_003 箱变', 'WTG_003_PAD_TRANSFORMER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GEARBOX_V1'), 'WTG_003_GEARBOX', 'WTG_003 齿轮箱', 'WTG_003_GEARBOX-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_2_5_120'), 'WTG_004', 'WTG_004 风机', 'WTG_004-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_MAIN_CONTROLLER'), 'WTG_004_MAIN_CONTROLLER', 'WTG_004 主控', 'WTG_004_MAIN_CONTROLLER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_CONVERTER'), 'WTG_004_CONVERTER', 'WTG_004 变流器', 'WTG_004_CONVERTER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_PITCH'), 'WTG_004_PITCH_SYSTEM', 'WTG_004 变桨系统', 'WTG_004_PITCH_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_YAW'), 'WTG_004_YAW_SYSTEM', 'WTG_004 偏航系统', 'WTG_004_YAW_SYSTEM-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GENERATOR'), 'WTG_004_GENERATOR', 'WTG_004 发电机', 'WTG_004_GENERATOR-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_HUB'), 'WTG_004_HUB', 'WTG_004 轮毂', 'WTG_004_HUB-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_004_BLADE_1', 'WTG_004 1号叶片', 'WTG_004_BLADE_1-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_004_BLADE_2', 'WTG_004 2号叶片', 'WTG_004_BLADE_2-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_BLADE'), 'WTG_004_BLADE_3', 'WTG_004 3号叶片', 'WTG_004_BLADE_3-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_TOWER'), 'WTG_004_TOWER', 'WTG_004 塔筒', 'WTG_004_TOWER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('TBEA_PAD_TR_MODEL'), 'WTG_004_PAD_TRANSFORMER', 'WTG_004 箱变', 'WTG_004_PAD_TRANSFORMER-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('GE_GEARBOX_V1'), 'WTG_004_GEARBOX', 'WTG_004 齿轮箱', 'WTG_004_GEARBOX-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('SG250HX'), 'PV_INV_001', '光伏逆变器', 'PV_INV_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('PV_COMBINER_24'), 'PV_COMBINER_001', '光伏汇流箱', 'PV_COMBINER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('PV_ARRAY_MODEL'), 'PV_ARRAY_001', '光伏阵列', 'PV_ARRAY_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('ENERONE_3727KWH'), 'BESS_CONTAINER_001', '储能集装箱', 'BESS_CONTAINER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('SC2500UD_MV'), 'PCS_001', '储能变流器', 'PCS_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('CATL_BMS'), 'BMS_001', '电池管理系统', 'BMS_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('CATL_BAT_CLUSTER'), 'BAT_CLUSTER_001', '1号电池簇', 'BAT_CLUSTER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('CATL_BAT_CLUSTER'), 'BAT_CLUSTER_002', '2号电池簇', 'BAT_CLUSTER_002-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('CATL_BAT_CLUSTER'), 'BAT_CLUSTER_003', '3号电池簇', 'BAT_CLUSTER_003-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('CATL_BAT_CLUSTER'), 'BAT_CLUSTER_004', '4号电池簇', 'BAT_CLUSTER_004-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('TBEA_MAIN_TRANSFORMER_120MVA'), 'MAIN_TRANSFORMER_001', '1号主变', 'MAIN_TRANSFORMER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('NR_SVG_35KV'), 'SVG_001', '35kV SVG', 'SVG_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('NARI_GRID_METER'), 'GRID_METER_001', '关口电能表', 'GRID_METER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('NARI_AGC_AVC'), 'AGC_AVC_CONTROLLER_001', 'AGC/AVC控制器', 'AGC_AVC_CONTROLLER_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('NARI_DISPATCH_GATEWAY'), 'DISPATCH_GATEWAY_001', '远动通信网关', 'DISPATCH_GATEWAY_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('VAISALA_MET_MAST'), 'MET_MAST_001', '测风塔', 'MET_MAST_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('VAISALA_WEATHER_STATION'), 'WEATHER_STATION_001', '气象站', 'WEATHER_STATION_001-SN', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code = 'IN_SERVICE'), DATE '2024-01-10', NULL);

INSERT INTO whale.equ_equipment (
    org_site_id, equ_model_id, equipment_identifier, name_zh, meta_equ_equipment_status_id, commissioned_at, description_zh
) VALUES
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_BOXTR_GENERIC'), 'BOX_TR_001', '1号风机箱变', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_BOXTR_GENERIC'), 'BOX_TR_002', '2号风机箱变', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_SWGR_GENERIC'), 'SWGR_35KV_01', '35kV集电开关柜', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_MAINTR_GENERIC'), 'MAIN_TR_01', '1号主变', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_BREAKER_GENERIC'), 'GRID_BREAKER_01', '220kV并网断路器', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_POI_METER_GENERIC'), 'POI_METER_01', '并网点计量装置', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_OPT_SWITCH_GENERIC'), 'OPT_SWITCH_001', '1号风机光交换机', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_OPT_SWITCH_GENERIC'), 'OPT_SWITCH_002', '2号风机光交换机', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_CORE_SWITCH_GENERIC'), 'CORE_SWITCH_01', '升压站核心交换机', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_ISO_GENERIC'), 'ISO_DEVICE_01', '调度数据网安全隔离装置', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_NTP_GENERIC'), 'NTP_SERVER_01', '场站NTP时钟服务器', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。'),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_model_id('MODEL_AGCAVC_GENERIC'), 'AGC_AVC_01', '场站AGC/AVC控制器', (SELECT meta_equ_equipment_status_id FROM whale.meta_equ_equipment_status WHERE code='IN_SERVICE'), DATE '2024-01-10', '现场样例设备。');

INSERT INTO whale.equ_composition_record (
    parent_equ_equipment_id, equ_model_component_id, child_equ_equipment_id, valid_from, valid_to
) VALUES
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='MAIN_CONTROLLER'), whale.equipment_id('WTG_001_MAIN_CONTROLLER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='CONVERTER'), whale.equipment_id('WTG_001_CONVERTER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PITCH_SYSTEM'), whale.equipment_id('WTG_001_PITCH_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='YAW_SYSTEM'), whale.equipment_id('WTG_001_YAW_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GENERATOR'), whale.equipment_id('WTG_001_GENERATOR'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='HUB'), whale.equipment_id('WTG_001_HUB'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_1'), whale.equipment_id('WTG_001_BLADE_1'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_2'), whale.equipment_id('WTG_001_BLADE_2'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_3'), whale.equipment_id('WTG_001_BLADE_3'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='TOWER'), whale.equipment_id('WTG_001_TOWER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PAD_TRANSFORMER'), whale.equipment_id('WTG_001_PAD_TRANSFORMER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GEARBOX'), whale.equipment_id('WTG_001_GEARBOX_A'), TIMESTAMPTZ '2024-01-10 00:00:00+08', TIMESTAMPTZ '2025-06-01 00:00:00+08'),
(whale.equipment_id('WTG_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GEARBOX'), whale.equipment_id('WTG_001_GEARBOX_B'), TIMESTAMPTZ '2025-06-01 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='MAIN_CONTROLLER'), whale.equipment_id('WTG_002_MAIN_CONTROLLER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='CONVERTER'), whale.equipment_id('WTG_002_CONVERTER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PITCH_SYSTEM'), whale.equipment_id('WTG_002_PITCH_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='YAW_SYSTEM'), whale.equipment_id('WTG_002_YAW_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GENERATOR'), whale.equipment_id('WTG_002_GENERATOR'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='HUB'), whale.equipment_id('WTG_002_HUB'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_1'), whale.equipment_id('WTG_002_BLADE_1'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_2'), whale.equipment_id('WTG_002_BLADE_2'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_3'), whale.equipment_id('WTG_002_BLADE_3'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='TOWER'), whale.equipment_id('WTG_002_TOWER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PAD_TRANSFORMER'), whale.equipment_id('WTG_002_PAD_TRANSFORMER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_002'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GEARBOX'), whale.equipment_id('WTG_002_GEARBOX'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='MAIN_CONTROLLER'), whale.equipment_id('WTG_003_MAIN_CONTROLLER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='CONVERTER'), whale.equipment_id('WTG_003_CONVERTER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PITCH_SYSTEM'), whale.equipment_id('WTG_003_PITCH_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='YAW_SYSTEM'), whale.equipment_id('WTG_003_YAW_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GENERATOR'), whale.equipment_id('WTG_003_GENERATOR'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='HUB'), whale.equipment_id('WTG_003_HUB'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_1'), whale.equipment_id('WTG_003_BLADE_1'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_2'), whale.equipment_id('WTG_003_BLADE_2'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_3'), whale.equipment_id('WTG_003_BLADE_3'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='TOWER'), whale.equipment_id('WTG_003_TOWER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PAD_TRANSFORMER'), whale.equipment_id('WTG_003_PAD_TRANSFORMER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_003'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GEARBOX'), whale.equipment_id('WTG_003_GEARBOX'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='MAIN_CONTROLLER'), whale.equipment_id('WTG_004_MAIN_CONTROLLER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='CONVERTER'), whale.equipment_id('WTG_004_CONVERTER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PITCH_SYSTEM'), whale.equipment_id('WTG_004_PITCH_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='YAW_SYSTEM'), whale.equipment_id('WTG_004_YAW_SYSTEM'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GENERATOR'), whale.equipment_id('WTG_004_GENERATOR'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='HUB'), whale.equipment_id('WTG_004_HUB'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_1'), whale.equipment_id('WTG_004_BLADE_1'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_2'), whale.equipment_id('WTG_004_BLADE_2'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='BLADE_3'), whale.equipment_id('WTG_004_BLADE_3'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='TOWER'), whale.equipment_id('WTG_004_TOWER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='PAD_TRANSFORMER'), whale.equipment_id('WTG_004_PAD_TRANSFORMER'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('WTG_004'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('GE_2_5_120') AND component_slot_code='GEARBOX'), whale.equipment_id('WTG_004_GEARBOX'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='PCS'), whale.equipment_id('PCS_001'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='BMS'), whale.equipment_id('BMS_001'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='BATTERY_CLUSTER_1'), whale.equipment_id('BAT_CLUSTER_001'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='BATTERY_CLUSTER_2'), whale.equipment_id('BAT_CLUSTER_002'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='BATTERY_CLUSTER_3'), whale.equipment_id('BAT_CLUSTER_003'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL),
(whale.equipment_id('BESS_CONTAINER_001'), (SELECT equ_model_component_id FROM whale.equ_model_component WHERE parent_equ_model_id=whale.equipment_model_id('ENERONE_3727KWH') AND component_slot_code='BATTERY_CLUSTER_4'), whale.equipment_id('BAT_CLUSTER_004'), TIMESTAMPTZ '2024-01-10 00:00:00+08', NULL);

-- ============================================================================
-- 3. 电气、机械与通信拓扑样例：participant + interface + connection
-- ============================================================================

-- 3.1 电气拓扑参与对象
INSERT INTO whale.topo_elec_participant (
    org_site_id, equ_equipment_id, participant_identifier, name_zh, description_zh, enabled
) VALUES
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_001'), 'ELEC_PART_WTG_001', '1号风机', '电气拓扑中的1号风机参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_002'), 'ELEC_PART_WTG_002', '2号风机', '电气拓扑中的2号风机参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('BOX_TR_001'), 'ELEC_PART_BOX_TR_001', '1号箱变', '电气拓扑中的1号箱变。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('BOX_TR_002'), 'ELEC_PART_BOX_TR_002', '2号箱变', '电气拓扑中的2号箱变。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('SWGR_35KV_01'), 'ELEC_PART_SWGR_35KV_01', '35kV开关柜', '35kV集电系统开关柜。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('MAIN_TR_01'), 'ELEC_PART_MAIN_TR_01', '主变压器', '主变压器电气参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('GRID_BREAKER_01'), 'ELEC_PART_GRID_BREAKER_01', '并网断路器', '并网断路器电气参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('POI_METER_01'), 'ELEC_PART_POI_METER_01', '关口计量装置', '并网点计量装置。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), NULL, 'ELEC_PART_GRID_BOUNDARY', '公共电网边界', '场站与公共电网的220kV边界参与对象。', TRUE);

INSERT INTO whale.topo_elec_interface (
    topo_elec_participant_id, interface_identifier, meta_topo_elec_interface_type_id,
    name_zh, nominal_voltage_kv, description_zh, enabled
) VALUES
(whale.topo_elec_participant_id('ELEC_PART_WTG_001'), 'ELEC_IF_WTG_001_GRID_OUT', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '机组电气输出端', 0.69, '风机低压电气输出端。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_WTG_002'), 'ELEC_IF_WTG_002_GRID_OUT', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '机组电气输出端', 0.69, '风机低压电气输出端。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_BOX_TR_001'), 'ELEC_IF_BOX_TR_001_LV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '箱变低压侧', 0.69, '箱变低压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_BOX_TR_001'), 'ELEC_IF_BOX_TR_001_HV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '箱变35kV侧', 35, '箱变高压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_BOX_TR_002'), 'ELEC_IF_BOX_TR_002_LV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '箱变低压侧', 0.69, '箱变低压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_BOX_TR_002'), 'ELEC_IF_BOX_TR_002_HV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '箱变35kV侧', 35, '箱变高压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_SWGR_35KV_01'), 'ELEC_IF_SWGR_FEEDER_01', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '1号风机馈线端', 35, '35kV 1号风机馈线端。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_SWGR_35KV_01'), 'ELEC_IF_SWGR_FEEDER_02', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '2号风机馈线端', 35, '35kV 2号风机馈线端。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_SWGR_35KV_01'), 'ELEC_IF_SWGR_BUS', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '35kV母线端', 35, '35kV母线连接端。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_MAIN_TR_01'), 'ELEC_IF_MAIN_TR_LV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '主变35kV侧', 35, '主变低压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_MAIN_TR_01'), 'ELEC_IF_MAIN_TR_HV', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '主变220kV侧', 220, '主变高压侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_GRID_BREAKER_01'), 'ELEC_IF_GRID_BREAKER_IN', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '并网断路器场站侧', 220, '并网断路器场站侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_GRID_BREAKER_01'), 'ELEC_IF_GRID_BREAKER_OUT', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '并网断路器电网侧', 220, '并网断路器电网侧端子。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_POI_METER_01'), 'ELEC_IF_POI_METER_IN', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '关口表场站侧', 220, '并网点计量装置场站侧。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_POI_METER_01'), 'ELEC_IF_POI_METER_OUT', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '关口表电网侧', 220, '并网点计量装置电网侧。', TRUE),
(whale.topo_elec_participant_id('ELEC_PART_GRID_BOUNDARY'), 'ELEC_IF_GRID_BOUNDARY', (SELECT meta_topo_elec_interface_type_id FROM whale.meta_topo_elec_interface_type WHERE code='ELECTRICAL_TERMINAL'), '电网并网边界', 220, '场站与公共电网的电气边界接口。', TRUE);

INSERT INTO whale.topo_elec_connection (
    interface_a_id, interface_b_id, connection_identifier, meta_topo_elec_connection_type_id,
    name_zh, nominal_voltage_kv, length_m, description_zh, enabled
) VALUES
(whale.topo_elec_interface_id('ELEC_IF_WTG_001_GRID_OUT'), whale.topo_elec_interface_id('ELEC_IF_BOX_TR_001_LV'), 'ELEC_CONN_WTG1_LV', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '1号风机低压电缆', 0.69, 80, '1号风机至1号箱变低压侧。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_WTG_002_GRID_OUT'), whale.topo_elec_interface_id('ELEC_IF_BOX_TR_002_LV'), 'ELEC_CONN_WTG2_LV', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '2号风机低压电缆', 0.69, 80, '2号风机至2号箱变低压侧。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_BOX_TR_001_HV'), whale.topo_elec_interface_id('ELEC_IF_SWGR_FEEDER_01'), 'ELEC_CONN_WTG1_35KV', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '1号风机35kV集电电缆', 35, 850, '1号箱变至35kV开关柜。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_BOX_TR_002_HV'), whale.topo_elec_interface_id('ELEC_IF_SWGR_FEEDER_02'), 'ELEC_CONN_WTG2_35KV', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '2号风机35kV集电电缆', 35, 900, '2号箱变至35kV开关柜。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_SWGR_BUS'), whale.topo_elec_interface_id('ELEC_IF_MAIN_TR_LV'), 'ELEC_CONN_35KV_BUS_TO_MAIN_TR', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='BUSBAR'), '35kV母线至主变', 35, NULL, '35kV集电母线连接主变低压侧。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_MAIN_TR_HV'), whale.topo_elec_interface_id('ELEC_IF_GRID_BREAKER_IN'), 'ELEC_CONN_MAINTR_BREAKER', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '主变至并网断路器', 220, 60, '主变高压侧至并网断路器。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_GRID_BREAKER_OUT'), whale.topo_elec_interface_id('ELEC_IF_POI_METER_IN'), 'ELEC_CONN_BREAKER_POI', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '断路器至关口计量', 220, 20, '并网断路器至关口计量装置。', TRUE),
(whale.topo_elec_interface_id('ELEC_IF_POI_METER_OUT'), whale.topo_elec_interface_id('ELEC_IF_GRID_BOUNDARY'), 'ELEC_CONN_POI_GRID', (SELECT meta_topo_elec_connection_type_id FROM whale.meta_topo_elec_connection_type WHERE code='ELECTRICAL_CABLE'), '关口计量至电网边界', 220, 40, '关口计量装置至公共电网边界。', TRUE);

-- 3.2 机械拓扑：以 1 号风机传动链为样例
INSERT INTO whale.topo_mech_participant (
    org_site_id, equ_equipment_id, participant_identifier, name_zh, description_zh, enabled
) VALUES
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_001_HUB'), 'MECH_PART_WTG1_HUB', '1号风机轮毂', '传动链机械拓扑参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_001_GEARBOX_B'), 'MECH_PART_WTG1_GEARBOX', '1号风机齿轮箱', '当前有效齿轮箱。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_001_GENERATOR'), 'MECH_PART_WTG1_GENERATOR', '1号风机发电机', '传动链发电机参与对象。', TRUE);

INSERT INTO whale.topo_mech_interface (
    topo_mech_participant_id, interface_identifier, meta_topo_mech_interface_type_id, name_zh, description_zh, enabled
) VALUES
(whale.topo_mech_participant_id('MECH_PART_WTG1_HUB'), 'MECH_IF_WTG1_HUB_OUT', (SELECT meta_topo_mech_interface_type_id FROM whale.meta_topo_mech_interface_type WHERE code='SHAFT_END'), '轮毂传动输出端', '轮毂向传动链输出的轴端。', TRUE),
(whale.topo_mech_participant_id('MECH_PART_WTG1_GEARBOX'), 'MECH_IF_WTG1_GEARBOX_IN', (SELECT meta_topo_mech_interface_type_id FROM whale.meta_topo_mech_interface_type WHERE code='SHAFT_END'), '齿轮箱低速轴输入端', '齿轮箱低速轴侧。', TRUE),
(whale.topo_mech_participant_id('MECH_PART_WTG1_GEARBOX'), 'MECH_IF_WTG1_GEARBOX_OUT', (SELECT meta_topo_mech_interface_type_id FROM whale.meta_topo_mech_interface_type WHERE code='SHAFT_END'), '齿轮箱高速轴输出端', '齿轮箱高速轴侧。', TRUE),
(whale.topo_mech_participant_id('MECH_PART_WTG1_GENERATOR'), 'MECH_IF_WTG1_GENERATOR_IN', (SELECT meta_topo_mech_interface_type_id FROM whale.meta_topo_mech_interface_type WHERE code='SHAFT_END'), '发电机轴输入端', '发电机传动输入轴端。', TRUE);

INSERT INTO whale.topo_mech_connection (
    interface_a_id, interface_b_id, connection_identifier, meta_topo_mech_connection_type_id, name_zh, description_zh, enabled
) VALUES
(whale.topo_mech_interface_id('MECH_IF_WTG1_HUB_OUT'), whale.topo_mech_interface_id('MECH_IF_WTG1_GEARBOX_IN'), 'MECH_CONN_WTG1_LOW_SPEED_SHAFT', (SELECT meta_topo_mech_connection_type_id FROM whale.meta_topo_mech_connection_type WHERE code='SHAFT'), '低速传动连接', '轮毂至齿轮箱低速轴侧的机械连接。', TRUE),
(whale.topo_mech_interface_id('MECH_IF_WTG1_GEARBOX_OUT'), whale.topo_mech_interface_id('MECH_IF_WTG1_GENERATOR_IN'), 'MECH_CONN_WTG1_HIGH_SPEED_COUPLING', (SELECT meta_topo_mech_connection_type_id FROM whale.meta_topo_mech_connection_type WHERE code='COUPLING'), '高速轴联轴器连接', '齿轮箱高速轴至发电机的联轴器连接。', TRUE);

-- 3.3 通信拓扑参与对象
INSERT INTO whale.topo_comm_participant (
    org_site_id, equ_equipment_id, participant_identifier, name_zh, description_zh, enabled
) VALUES
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_001'), 'COMM_PART_WTG_001', '1号风机', '风机主控外部通信参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_002'), 'COMM_PART_WTG_002', '2号风机', '风机主控外部通信参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('WTG_003'), 'COMM_PART_WTG_003', '3号风机', 'ADS样例风机通信参与对象。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('OPT_SWITCH_001'), 'COMM_PART_OPT_SWITCH_001', '1号风机光交换机', '风机通信环网交换机。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('OPT_SWITCH_002'), 'COMM_PART_OPT_SWITCH_002', '2号风机光交换机', '风机通信环网交换机。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('CORE_SWITCH_01'), 'COMM_PART_CORE_SWITCH', '升压站核心交换机', '生产控制网络核心交换机。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('ISO_DEVICE_01'), 'COMM_PART_ISO', '安全隔离装置', '生产控制区与调度数据网边界设备。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('NTP_SERVER_01'), 'COMM_PART_NTP', 'NTP时钟服务器', '时间同步服务器。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), whale.equipment_id('AGC_AVC_01'), 'COMM_PART_AGC', 'AGC/AVC控制器', '场站功率控制设备。', TRUE),
(whale.site_id('PLANT_BLUECRYSTAL_001'), NULL, 'COMM_PART_DISPATCH_BOUNDARY', '调度数据网边界', '场站与外部调度数据网的通信边界参与对象。', TRUE);

INSERT INTO whale.topo_comm_interface (
    topo_comm_participant_id, interface_identifier, meta_topo_comm_interface_type_id, name_zh, description_zh, enabled
) VALUES
(whale.topo_comm_participant_id('COMM_PART_WTG_001'), 'COMM_IF_WTG_001_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '主控ETH1', '风机主控对外以太网通信口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_WTG_002'), 'COMM_IF_WTG_002_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '主控ETH1', '风机主控对外以太网通信口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_WTG_003'), 'COMM_IF_WTG_003_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '主控ETH1', 'ADS Remote Server 对外通信口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_001'), 'COMM_IF_OPT_SWITCH_001_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '设备接入口', '连接1号风机主控。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_001'), 'COMM_IF_OPT_SWITCH_001_FIBER_A', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口A', '风机通信环网光口A。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_001'), 'COMM_IF_OPT_SWITCH_001_FIBER_B', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口B', '风机通信环网光口B。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_002'), 'COMM_IF_OPT_SWITCH_002_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '设备接入口', '连接2号风机主控。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_002'), 'COMM_IF_OPT_SWITCH_002_FIBER_A', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口A', '风机通信环网光口A。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_OPT_SWITCH_002'), 'COMM_IF_OPT_SWITCH_002_FIBER_B', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口B', '风机通信环网光口B。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_CORE_SWITCH'), 'COMM_IF_CORE_SWITCH_FIBER_1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口1', '接入风机通信环网。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_CORE_SWITCH'), 'COMM_IF_CORE_SWITCH_FIBER_2', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='FIBER_PORT'), '环网光口2', '接入风机通信环网。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_CORE_SWITCH'), 'COMM_IF_CORE_SWITCH_ETH_ISO', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '隔离装置接入口', '连接安全隔离装置。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_CORE_SWITCH'), 'COMM_IF_CORE_SWITCH_ETH_NTP', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), 'NTP接入口', '连接NTP时钟服务器。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_CORE_SWITCH'), 'COMM_IF_CORE_SWITCH_ETH_AGC', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), 'AGC/AVC接入口', '连接AGC/AVC控制器。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_ISO'), 'COMM_IF_ISO_INTERNAL', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '隔离装置内网口', '生产控制区侧接口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_ISO'), 'COMM_IF_ISO_EXTERNAL', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '隔离装置外网口', '调度数据网侧接口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_NTP'), 'COMM_IF_NTP_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), 'NTP网络口', 'NTP/PTP时间服务器网络接口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_AGC'), 'COMM_IF_AGC_ETH1', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), 'AGC/AVC网络口', 'AGC/AVC控制器网络接口。', TRUE),
(whale.topo_comm_participant_id('COMM_PART_DISPATCH_BOUNDARY'), 'COMM_IF_DISPATCH_BOUNDARY', (SELECT meta_topo_comm_interface_type_id FROM whale.meta_topo_comm_interface_type WHERE code='ETHERNET_PORT'), '调度数据网边界', '场站与调度数据网之间的通信边界接口。', TRUE);

INSERT INTO whale.topo_comm_connection (
    interface_a_id, interface_b_id, connection_identifier, meta_topo_comm_connection_type_id,
    name_zh, length_m, description_zh, enabled
) VALUES
(whale.topo_comm_interface_id('COMM_IF_WTG_001_ETH1'), whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_001_ETH1'), 'COMM_CONN_WTG1_ETH', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '1号风机主控至光交换机', 5, '风机主控ETH1与光交换机电口连接。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_WTG_002_ETH1'), whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_002_ETH1'), 'COMM_CONN_WTG2_ETH', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '2号风机主控至光交换机', 5, '风机主控ETH1与光交换机电口连接。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_001_FIBER_A'), whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_002_FIBER_B'), 'COMM_CONN_RING_FIBER_01', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='FIBER'), '环网光纤段01', 850, '1号光交换机至2号光交换机。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_002_FIBER_A'), whale.topo_comm_interface_id('COMM_IF_CORE_SWITCH_FIBER_1'), 'COMM_CONN_RING_FIBER_02', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='FIBER'), '环网光纤段02', 900, '2号光交换机至升压站核心交换机。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_CORE_SWITCH_FIBER_2'), whale.topo_comm_interface_id('COMM_IF_OPT_SWITCH_001_FIBER_B'), 'COMM_CONN_RING_FIBER_03', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='FIBER'), '环网光纤段03', 1200, '核心交换机返回1号光交换机形成闭环。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_CORE_SWITCH_ETH_ISO'), whale.topo_comm_interface_id('COMM_IF_ISO_INTERNAL'), 'COMM_CONN_CORE_ISO', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '核心交换机至隔离装置', 10, '生产控制区核心交换机连接安全隔离装置内网口。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_ISO_EXTERNAL'), whale.topo_comm_interface_id('COMM_IF_DISPATCH_BOUNDARY'), 'COMM_CONN_ISO_DISPATCH', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '隔离装置至调度数据网边界', 10, '安全隔离装置外网口连接场站调度数据网边界。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_CORE_SWITCH_ETH_NTP'), whale.topo_comm_interface_id('COMM_IF_NTP_ETH1'), 'COMM_CONN_CORE_NTP', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '核心交换机至NTP服务器', 10, 'NTP时钟服务器接入生产控制网络。', TRUE),
(whale.topo_comm_interface_id('COMM_IF_CORE_SWITCH_ETH_AGC'), whale.topo_comm_interface_id('COMM_IF_AGC_ETH1'), 'COMM_CONN_CORE_AGC', (SELECT meta_topo_comm_connection_type_id FROM whale.meta_topo_comm_connection_type WHERE code='COPPER_ETHERNET'), '核心交换机至AGC/AVC', 10, 'AGC/AVC控制器接入生产控制网络。', TRUE);

-- ============================================================================
-- 4. Remote Connection：IEC104 + ADS
-- ============================================================================

INSERT INTO whale.comm_connection (
    topo_comm_interface_id, meta_comm_protocol_role_id, connection_identifier, host, port,
    reconnect_enabled, reconnect_interval_ms, enabled
) VALUES
(whale.topo_comm_interface_id('COMM_IF_WTG_001_ETH1'), whale.protocol_role_id('IEC104','CONTROLLED_STATION'), 'CONN_WTG_001_IEC104', '127.0.0.1', 61000, TRUE, 5000, TRUE),
(whale.topo_comm_interface_id('COMM_IF_WTG_002_ETH1'), whale.protocol_role_id('IEC104','CONTROLLED_STATION'), 'CONN_WTG_002_IEC104', '127.0.0.1', 61001, TRUE, 5000, TRUE),
(whale.topo_comm_interface_id('COMM_IF_WTG_003_ETH1'), whale.protocol_role_id('ADS','SERVER'), 'CONN_WTG_003_ADS', '127.0.0.1', 48898, TRUE, 3000, TRUE);

INSERT INTO whale.comm_iec104_connection_detail (
    comm_connection_id, t0_ms, t1_ms, t2_ms, t3_ms, k_value, w_value
) VALUES
(whale.comm_connection_id('CONN_WTG_001_IEC104'), 30000,15000,10000,20000,12,8),
(whale.comm_connection_id('CONN_WTG_002_IEC104'), 30000,15000,10000,20000,12,8);

INSERT INTO whale.comm_ads_connection_detail (
    comm_connection_id, ams_net_id, ams_port
) VALUES
(whale.comm_connection_id('CONN_WTG_003_ADS'), '127.0.0.1.1.1', 851);

-- ============================================================================
-- 5. 共享 PointDefinition、Source 能力与 Sink 需求
-- ============================================================================

INSERT INTO whale.meta_point_definition (
    point_definition_identifier, meta_point_measurement_semantic_id, meta_point_data_type_id, meta_point_unit_id,
    point_name_zh, scale_factor, offset_value, value_min, value_max, allowed_values, description_zh, enabled
) VALUES
('PD_ACTIVE_POWER', whale.measurement_semantic_id('ACTIVE_POWER'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='MW'), '有功功率', 1,0,0,5,NULL,'可复用于风机有功功率。',TRUE),
('PD_REACTIVE_POWER', whale.measurement_semantic_id('REACTIVE_POWER'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='MVAR'), '无功功率', 1,0,-5,5,NULL,'可复用于风机无功功率。',TRUE),
('PD_WIND_SPEED', whale.measurement_semantic_id('WIND_SPEED'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='MPS'), '风速', 1,0,0,60,NULL,'风机机舱风速。',TRUE),
('PD_ROTOR_SPEED', whale.measurement_semantic_id('ROTOR_SPEED'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='RPM'), '转子转速', 1,0,0,30,NULL,'风机转子转速。',TRUE),
('PD_RUNNING_STATUS', whale.measurement_semantic_id('RUNNING_STATUS'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='BOOLEAN'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='NONE'), '运行状态', 1,0,NULL,NULL,'[false,true]'::jsonb,'二值运行状态。',TRUE),
('PD_ACTIVE_POWER_SETPOINT', whale.measurement_semantic_id('ACTIVE_POWER_SETPOINT'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='MW'), '有功功率设点', 1,0,0,10,NULL,'有功控制设点。',TRUE),
('PD_REACTIVE_POWER_SETPOINT', whale.measurement_semantic_id('REACTIVE_POWER_SETPOINT'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='FLOAT64'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='MVAR'), '无功功率设点', 1,0,-10,10,NULL,'无功控制设点。',TRUE),
('PD_START_COMMAND', whale.measurement_semantic_id('START_COMMAND'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='BOOLEAN'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='NONE'), '启动命令', 1,0,NULL,NULL,'[false,true]'::jsonb,'启动命令。',TRUE),
('PD_STOP_COMMAND', whale.measurement_semantic_id('STOP_COMMAND'), (SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='BOOLEAN'), (SELECT meta_point_unit_id FROM whale.meta_point_unit WHERE code='NONE'), '停机命令', 1,0,NULL,NULL,'[false,true]'::jsonb,'停机命令。',TRUE);

INSERT INTO whale.src_point_table (
    comm_connection_id, source_point_table_identifier, version_label, published, description_zh, enabled
) VALUES
(whale.comm_connection_id('CONN_WTG_001_IEC104'),'SPT_WTG_001','V1',TRUE,'WTG_001 IEC104 Source 能力。',TRUE),
(whale.comm_connection_id('CONN_WTG_002_IEC104'),'SPT_WTG_002','V1',TRUE,'WTG_002 IEC104 Source 能力。',TRUE),
(whale.comm_connection_id('CONN_WTG_003_ADS'),'SPT_WTG_003_ADS','V1',TRUE,'WTG_003 ADS Source 能力。',TRUE);

INSERT INTO whale.sink_point_table (
    comm_connection_id, sink_point_table_identifier, version_label, published, description_zh, enabled
) VALUES
(whale.comm_connection_id('CONN_WTG_001_IEC104'),'SKT_WTG_001','V1',TRUE,'WTG_001 IEC104 Sink 需求。',TRUE),
(whale.comm_connection_id('CONN_WTG_002_IEC104'),'SKT_WTG_002','V1',TRUE,'WTG_002 IEC104 Sink 需求。',TRUE),
(whale.comm_connection_id('CONN_WTG_003_ADS'),'SKT_WTG_003_ADS','V1',TRUE,'WTG_003 ADS Sink 需求。',TRUE);

INSERT INTO whale.src_point_table_item (
    src_point_table_id, meta_point_definition_id, meta_point_source_value_update_mode_id, value_update_interval_ms,
    point_identifier, sort_order, enabled
) VALUES
(whale.source_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_ACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 100, 'ACTIVE_POWER',1,TRUE),
(whale.source_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_REACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 100, 'REACTIVE_POWER',2,TRUE),
(whale.source_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_WIND_SPEED'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 200, 'WIND_SPEED',3,TRUE),
(whale.source_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_RUNNING_STATUS'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='ON_CHANGE'), NULL, 'RUNNING_STATUS',4,TRUE),
(whale.source_point_table_id('CONN_WTG_002_IEC104'), whale.point_definition_id('PD_ACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 100, 'ACTIVE_POWER',1,TRUE),
(whale.source_point_table_id('CONN_WTG_002_IEC104'), whale.point_definition_id('PD_REACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 100, 'REACTIVE_POWER',2,TRUE),
(whale.source_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_ACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 50, 'ACTIVE_POWER',1,TRUE),
(whale.source_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_REACTIVE_POWER'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 50, 'REACTIVE_POWER',2,TRUE),
(whale.source_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_ROTOR_SPEED'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='PERIODIC'), 50, 'ROTOR_SPEED',3,TRUE),
(whale.source_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_RUNNING_STATUS'), (SELECT meta_point_source_value_update_mode_id FROM whale.meta_point_source_value_update_mode WHERE code='ON_CHANGE'), NULL, 'RUNNING_STATUS',4,TRUE);

INSERT INTO whale.sink_point_table_item (
    sink_point_table_id, meta_point_definition_id, point_identifier, sort_order, enabled
) VALUES
(whale.sink_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_ACTIVE_POWER_SETPOINT'), 'ACTIVE_POWER_SETPOINT',1,TRUE),
(whale.sink_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_REACTIVE_POWER_SETPOINT'), 'REACTIVE_POWER_SETPOINT',2,TRUE),
(whale.sink_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_START_COMMAND'), 'START_COMMAND',3,TRUE),
(whale.sink_point_table_id('CONN_WTG_001_IEC104'), whale.point_definition_id('PD_STOP_COMMAND'), 'STOP_COMMAND',4,TRUE),
(whale.sink_point_table_id('CONN_WTG_002_IEC104'), whale.point_definition_id('PD_ACTIVE_POWER_SETPOINT'), 'ACTIVE_POWER_SETPOINT',1,TRUE),
(whale.sink_point_table_id('CONN_WTG_002_IEC104'), whale.point_definition_id('PD_REACTIVE_POWER_SETPOINT'), 'REACTIVE_POWER_SETPOINT',2,TRUE),
(whale.sink_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_ACTIVE_POWER_SETPOINT'), 'ACTIVE_POWER_SETPOINT',1,TRUE),
(whale.sink_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_REACTIVE_POWER_SETPOINT'), 'REACTIVE_POWER_SETPOINT',2,TRUE),
(whale.sink_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_START_COMMAND'), 'START_COMMAND',3,TRUE),
(whale.sink_point_table_id('CONN_WTG_003_ADS'), whale.point_definition_id('PD_STOP_COMMAND'), 'STOP_COMMAND',4,TRUE);

INSERT INTO whale.src_iec104_point_item_detail (
    src_point_table_item_id, meta_iec104_type_id, common_address, information_object_address,
    general_interrogation_enabled, general_interrogation_group, counter_interrogation_enabled,
    periodic_transmission_enabled, periodic_interval_ms, spontaneous_transmission_enabled, deadband,
    background_transmission_enabled, quality_enabled
) VALUES
(whale.source_point_table_item_id('CONN_WTG_001_IEC104','ACTIVE_POWER'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_ME_NC_1'),1,1001,TRUE,NULL,FALSE,TRUE,1000,TRUE,0.05,FALSE,TRUE),
(whale.source_point_table_item_id('CONN_WTG_001_IEC104','REACTIVE_POWER'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_ME_NC_1'),1,1002,TRUE,NULL,FALSE,TRUE,1000,TRUE,0.05,FALSE,TRUE),
(whale.source_point_table_item_id('CONN_WTG_001_IEC104','WIND_SPEED'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_ME_NC_1'),1,1003,TRUE,NULL,FALSE,TRUE,2000,TRUE,0.2,FALSE,TRUE),
(whale.source_point_table_item_id('CONN_WTG_001_IEC104','RUNNING_STATUS'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_SP_NA_1'),1,1101,TRUE,NULL,FALSE,FALSE,NULL,TRUE,NULL,FALSE,TRUE),
(whale.source_point_table_item_id('CONN_WTG_002_IEC104','ACTIVE_POWER'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_ME_NC_1'),2,1001,TRUE,NULL,FALSE,TRUE,1000,TRUE,0.05,FALSE,TRUE),
(whale.source_point_table_item_id('CONN_WTG_002_IEC104','REACTIVE_POWER'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='M_ME_NC_1'),2,1002,TRUE,NULL,FALSE,TRUE,1000,TRUE,0.05,FALSE,TRUE);

INSERT INTO whale.sink_iec104_point_item_detail (
    sink_point_table_item_id, meta_iec104_type_id, common_address, information_object_address,
    general_interrogation_enabled, general_interrogation_group, counter_interrogation_enabled,
    periodic_transmission_enabled, periodic_interval_ms, spontaneous_transmission_enabled, deadband,
    background_transmission_enabled, quality_enabled
) VALUES
(whale.sink_point_table_item_id('CONN_WTG_001_IEC104','ACTIVE_POWER_SETPOINT'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SE_NC_1'),1,5001,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE),
(whale.sink_point_table_item_id('CONN_WTG_001_IEC104','REACTIVE_POWER_SETPOINT'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SE_NC_1'),1,5002,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE),
(whale.sink_point_table_item_id('CONN_WTG_001_IEC104','START_COMMAND'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SC_NA_1'),1,5101,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE),
(whale.sink_point_table_item_id('CONN_WTG_001_IEC104','STOP_COMMAND'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SC_NA_1'),1,5102,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE),
(whale.sink_point_table_item_id('CONN_WTG_002_IEC104','ACTIVE_POWER_SETPOINT'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SE_NC_1'),2,5001,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE),
(whale.sink_point_table_item_id('CONN_WTG_002_IEC104','REACTIVE_POWER_SETPOINT'), (SELECT meta_iec104_type_id FROM whale.meta_iec104_type WHERE code='C_SE_NC_1'),2,5002,FALSE,NULL,FALSE,FALSE,NULL,FALSE,NULL,FALSE,TRUE);

INSERT INTO whale.src_ads_point_item_detail (
    src_point_table_item_id, meta_ads_addressing_mode_id, meta_ads_data_type_id,
    symbol_name, index_group, index_offset, meta_ads_notification_mode_id, cycle_time_ms, max_delay_ms
) VALUES
(whale.source_point_table_item_id('CONN_WTG_003_ADS','ACTIVE_POWER'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='LREAL'), 'MAIN.ActivePower',NULL,NULL,(SELECT meta_ads_notification_mode_id FROM whale.meta_ads_notification_mode WHERE code='CYCLIC'),50,100),
(whale.source_point_table_item_id('CONN_WTG_003_ADS','REACTIVE_POWER'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='LREAL'), 'MAIN.ReactivePower',NULL,NULL,(SELECT meta_ads_notification_mode_id FROM whale.meta_ads_notification_mode WHERE code='CYCLIC'),50,100),
(whale.source_point_table_item_id('CONN_WTG_003_ADS','ROTOR_SPEED'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='LREAL'), 'MAIN.RotorSpeed',NULL,NULL,(SELECT meta_ads_notification_mode_id FROM whale.meta_ads_notification_mode WHERE code='CYCLIC'),50,100),
(whale.source_point_table_item_id('CONN_WTG_003_ADS','RUNNING_STATUS'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='BOOL'), 'MAIN.Running',NULL,NULL,(SELECT meta_ads_notification_mode_id FROM whale.meta_ads_notification_mode WHERE code='ON_CHANGE'),10,100);

INSERT INTO whale.sink_ads_point_item_detail (
    sink_point_table_item_id, meta_ads_addressing_mode_id, meta_ads_data_type_id,
    symbol_name, index_group, index_offset
) VALUES
(whale.sink_point_table_item_id('CONN_WTG_003_ADS','ACTIVE_POWER_SETPOINT'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='LREAL'), 'MAIN.ActivePowerSetpoint',NULL,NULL),
(whale.sink_point_table_item_id('CONN_WTG_003_ADS','REACTIVE_POWER_SETPOINT'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='LREAL'), 'MAIN.ReactivePowerSetpoint',NULL,NULL),
(whale.sink_point_table_item_id('CONN_WTG_003_ADS','START_COMMAND'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='BOOL'), 'MAIN.StartCommand',NULL,NULL),
(whale.sink_point_table_item_id('CONN_WTG_003_ADS','STOP_COMMAND'), (SELECT meta_ads_addressing_mode_id FROM whale.meta_ads_addressing_mode WHERE code='SYMBOL'), (SELECT meta_ads_data_type_id FROM whale.meta_ads_data_type WHERE code='BOOL'), 'MAIN.StopCommand',NULL,NULL);

-- ============================================================================
-- 6. Acquisition / Delivery 任务点子集与数据交换任务
-- ============================================================================

INSERT INTO whale.task_acquisition_point_table (
    src_point_table_id, task_acquisition_point_table_identifier, version_label, published, description_zh, enabled
) VALUES
(whale.source_point_table_id('CONN_WTG_001_IEC104'),'TAPT_WTG_001_GI','V1',TRUE,'WTG_001 总召采集点子集。',TRUE),
(whale.source_point_table_id('CONN_WTG_003_ADS'),'TAPT_WTG_003_ADS_READ','V1',TRUE,'WTG_003 ADS 周期读取点子集。',TRUE);

INSERT INTO whale.task_delivery_point_table (
    sink_point_table_id, task_delivery_point_table_identifier, version_label, published, description_zh, enabled
) VALUES
(whale.sink_point_table_id('CONN_WTG_001_IEC104'),'TDPT_WTG_001_CONTROL','V1',TRUE,'WTG_001 IEC104 控制点子集。',TRUE),
(whale.sink_point_table_id('CONN_WTG_003_ADS'),'TDPT_WTG_003_ADS_WRITE','V1',TRUE,'WTG_003 ADS 写入点子集。',TRUE);

INSERT INTO whale.task_acquisition_point_table_item (
    task_acquisition_point_table_id, src_point_table_item_id, sort_order, enabled
) VALUES
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_001_GI'), whale.source_point_table_item_id('CONN_WTG_001_IEC104','ACTIVE_POWER'),1,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_001_GI'), whale.source_point_table_item_id('CONN_WTG_001_IEC104','REACTIVE_POWER'),2,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_001_GI'), whale.source_point_table_item_id('CONN_WTG_001_IEC104','WIND_SPEED'),3,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_001_GI'), whale.source_point_table_item_id('CONN_WTG_001_IEC104','RUNNING_STATUS'),4,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_003_ADS_READ'), whale.source_point_table_item_id('CONN_WTG_003_ADS','ACTIVE_POWER'),1,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_003_ADS_READ'), whale.source_point_table_item_id('CONN_WTG_003_ADS','REACTIVE_POWER'),2,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_003_ADS_READ'), whale.source_point_table_item_id('CONN_WTG_003_ADS','ROTOR_SPEED'),3,TRUE),
((SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_003_ADS_READ'), whale.source_point_table_item_id('CONN_WTG_003_ADS','RUNNING_STATUS'),4,TRUE);

INSERT INTO whale.task_delivery_point_table_item (
    task_delivery_point_table_id, sink_point_table_item_id, sort_order, enabled
) VALUES
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_001_CONTROL'), whale.sink_point_table_item_id('CONN_WTG_001_IEC104','ACTIVE_POWER_SETPOINT'),1,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_001_CONTROL'), whale.sink_point_table_item_id('CONN_WTG_001_IEC104','REACTIVE_POWER_SETPOINT'),2,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_001_CONTROL'), whale.sink_point_table_item_id('CONN_WTG_001_IEC104','START_COMMAND'),3,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_001_CONTROL'), whale.sink_point_table_item_id('CONN_WTG_001_IEC104','STOP_COMMAND'),4,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_003_ADS_WRITE'), whale.sink_point_table_item_id('CONN_WTG_003_ADS','ACTIVE_POWER_SETPOINT'),1,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_003_ADS_WRITE'), whale.sink_point_table_item_id('CONN_WTG_003_ADS','REACTIVE_POWER_SETPOINT'),2,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_003_ADS_WRITE'), whale.sink_point_table_item_id('CONN_WTG_003_ADS','START_COMMAND'),3,TRUE),
((SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_003_ADS_WRITE'), whale.sink_point_table_item_id('CONN_WTG_003_ADS','STOP_COMMAND'),4,TRUE);

INSERT INTO whale.task_data_exchange (
    comm_connection_id, meta_task_protocol_operation_id,
    task_acquisition_point_table_id, task_delivery_point_table_id,
    task_identifier, name_zh, meta_task_trigger_mode_id, meta_task_status_id, description_zh, enabled
) VALUES
(whale.comm_connection_id('CONN_WTG_001_IEC104'), whale.protocol_operation_id('IEC104','CONTROLLED_STATION','GENERAL_INTERROGATION'),
 (SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_001_GI'), NULL,
 'TASK_WTG_001_GI','1号风机总召采集',(SELECT meta_task_trigger_mode_id FROM whale.meta_task_trigger_mode WHERE code='CYCLIC'),(SELECT meta_task_status_id FROM whale.meta_task_status WHERE code='SCHEDULED'),'周期执行 IEC104 总召获取数据。',TRUE),
(whale.comm_connection_id('CONN_WTG_001_IEC104'), whale.protocol_operation_id('IEC104','CONTROLLED_STATION','CONTROL_COMMAND'),
 NULL,(SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_001_CONTROL'),
 'TASK_WTG_001_CONTROL','1号风机控制',(SELECT meta_task_trigger_mode_id FROM whale.meta_task_trigger_mode WHERE code='MANUAL'),(SELECT meta_task_status_id FROM whale.meta_task_status WHERE code='SCHEDULED'),'向 IEC104 被控站推送设点或控制命令。',TRUE),
(whale.comm_connection_id('CONN_WTG_003_ADS'), whale.protocol_operation_id('ADS','SERVER','READ'),
 (SELECT task_acquisition_point_table_id FROM whale.task_acquisition_point_table WHERE task_acquisition_point_table_identifier='TAPT_WTG_003_ADS_READ'),NULL,
 'TASK_WTG_003_ADS_READ','3号风机ADS读取',(SELECT meta_task_trigger_mode_id FROM whale.meta_task_trigger_mode WHERE code='CYCLIC'),(SELECT meta_task_status_id FROM whale.meta_task_status WHERE code='SCHEDULED'),'周期读取 Remote ADS Server 数据点。',TRUE),
(whale.comm_connection_id('CONN_WTG_003_ADS'), whale.protocol_operation_id('ADS','SERVER','WRITE'),
 NULL,(SELECT task_delivery_point_table_id FROM whale.task_delivery_point_table WHERE task_delivery_point_table_identifier='TDPT_WTG_003_ADS_WRITE'),
 'TASK_WTG_003_ADS_WRITE','3号风机ADS写入',(SELECT meta_task_trigger_mode_id FROM whale.meta_task_trigger_mode WHERE code='MANUAL'),(SELECT meta_task_status_id FROM whale.meta_task_status WHERE code='SCHEDULED'),'向 Remote ADS Server 写入设点、参数或命令。',TRUE);

INSERT INTO whale.task_lifecycle_config (
    task_data_exchange_id, execution_timeout_ms, startup_delay_ms,
    retry_max_attempts, retry_interval_ms, retry_max_interval_ms, meta_task_retry_backoff_strategy_id,
    failure_max_consecutive_failures, meta_task_failure_action_id,
    meta_task_concurrency_policy_id, concurrency_max_instances, meta_task_misfire_policy_id
) VALUES
(whale.task_id('TASK_WTG_001_GI'),10000,0,3,3000,3000,(SELECT meta_task_retry_backoff_strategy_id FROM whale.meta_task_retry_backoff_strategy WHERE code='FIXED'),5,(SELECT meta_task_failure_action_id FROM whale.meta_task_failure_action WHERE code='SUSPEND'),(SELECT meta_task_concurrency_policy_id FROM whale.meta_task_concurrency_policy WHERE code='FORBID'),1,(SELECT meta_task_misfire_policy_id FROM whale.meta_task_misfire_policy WHERE code='SKIP')),
(whale.task_id('TASK_WTG_001_CONTROL'),5000,0,1,1000,1000,(SELECT meta_task_retry_backoff_strategy_id FROM whale.meta_task_retry_backoff_strategy WHERE code='FIXED'),3,(SELECT meta_task_failure_action_id FROM whale.meta_task_failure_action WHERE code='SUSPEND'),(SELECT meta_task_concurrency_policy_id FROM whale.meta_task_concurrency_policy WHERE code='FORBID'),1,(SELECT meta_task_misfire_policy_id FROM whale.meta_task_misfire_policy WHERE code='SKIP')),
(whale.task_id('TASK_WTG_003_ADS_READ'),3000,0,2,1000,2000,(SELECT meta_task_retry_backoff_strategy_id FROM whale.meta_task_retry_backoff_strategy WHERE code='FIXED'),5,(SELECT meta_task_failure_action_id FROM whale.meta_task_failure_action WHERE code='SUSPEND'),(SELECT meta_task_concurrency_policy_id FROM whale.meta_task_concurrency_policy WHERE code='FORBID'),1,(SELECT meta_task_misfire_policy_id FROM whale.meta_task_misfire_policy WHERE code='SKIP')),
(whale.task_id('TASK_WTG_003_ADS_WRITE'),3000,0,1,1000,1000,(SELECT meta_task_retry_backoff_strategy_id FROM whale.meta_task_retry_backoff_strategy WHERE code='FIXED'),3,(SELECT meta_task_failure_action_id FROM whale.meta_task_failure_action WHERE code='SUSPEND'),(SELECT meta_task_concurrency_policy_id FROM whale.meta_task_concurrency_policy WHERE code='FORBID'),1,(SELECT meta_task_misfire_policy_id FROM whale.meta_task_misfire_policy WHERE code='SKIP'));

INSERT INTO whale.task_operation_parameter_value (
    task_data_exchange_id, meta_task_operation_parameter_definition_id, parameter_value
) VALUES
(whale.task_id('TASK_WTG_001_GI'), whale.operation_parameter_definition_id('IEC104','CONTROLLED_STATION','GENERAL_INTERROGATION','QOI'), '20'::jsonb),
(whale.task_id('TASK_WTG_001_CONTROL'), whale.operation_parameter_definition_id('IEC104','CONTROLLED_STATION','CONTROL_COMMAND','COMMAND_MODE'), '"SELECT_EXECUTE"'::jsonb),
(whale.task_id('TASK_WTG_001_CONTROL'), whale.operation_parameter_definition_id('IEC104','CONTROLLED_STATION','CONTROL_COMMAND','CAUSE_OF_TRANSMISSION'), '"ACTIVATION"'::jsonb);

COMMIT;
