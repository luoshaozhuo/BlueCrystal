-- BlueCrystal shared basic data v1_5_13
-- Database: bluecrystal
-- Schema: whale
-- Purpose: platform-wide reference codes, standard semantics, protocol metadata,
--          standard permissions, standard roles, and protocol operation mappings.
-- Dependency: 02_bluecrystal_schema_ddl_v1_5_13.sql
-- Client: Navicat or any PostgreSQL SQL client; connect to database bluecrystal first.


BEGIN;
SET search_path TO whale, public;

-- 1. Platform reference codes
-- 1. reference codes
INSERT INTO ref_code(ref_type, code, name_zh, name_en, abbr_en, description_zh, description_en, sort_order, enabled) VALUES
('ORG_NATURE', 'GROUP', '集团', 'GROUP', NULL, '集团', 'GROUP', 1, true),
('ORG_NATURE', 'REGIONAL_COMPANY', '区域公司', 'REGIONAL_COMPANY', NULL, '区域公司', 'REGIONAL_COMPANY', 2, true),
('ORG_NATURE', 'POWER_PLANT_COMPANY', '电场公司', 'POWER_PLANT_COMPANY', NULL, '电场公司', 'POWER_PLANT_COMPANY', 3, true),
('ORG_NATURE', 'DISPATCH_CENTER', '调度中心', 'DISPATCH_CENTER', NULL, '调度中心', 'DISPATCH_CENTER', 4, true),
('ORG_NATURE', 'SERVICE_PROVIDER', '服务商', 'SERVICE_PROVIDER', NULL, '服务商', 'SERVICE_PROVIDER', 5, true),
('POWER_PLANT_TYPE', 'GRID_CONNECTED_PLANT', '并网型风光储电场', 'Grid-connected hybrid plant', NULL, '并网型风光储电场', 'Grid-connected hybrid plant', 1, true),
('WORK_TEAM_TYPE', 'MANAGEMENT_TEAM', '管理组', 'MANAGEMENT_TEAM', NULL, '管理组', 'MANAGEMENT_TEAM', 1, true),
('WORK_TEAM_TYPE', 'OPERATIONS_TEAM', '运行值班组', 'OPERATIONS_TEAM', NULL, '运行值班组', 'OPERATIONS_TEAM', 2, true),
('WORK_TEAM_TYPE', 'ELECTRICAL_TEAM', '电气检修班组', 'ELECTRICAL_TEAM', NULL, '电气检修班组', 'ELECTRICAL_TEAM', 3, true),
('WORK_TEAM_TYPE', 'PROTECTION_TEAM', '保护自动化班组', 'PROTECTION_TEAM', NULL, '保护自动化班组', 'PROTECTION_TEAM', 4, true),
('WORK_TEAM_TYPE', 'COMMUNICATION_TEAM', '通信网络班组', 'COMMUNICATION_TEAM', NULL, '通信网络班组', 'COMMUNICATION_TEAM', 5, true),
('WORK_TEAM_TYPE', 'WIND_TEAM', '风机检修班组', 'WIND_TEAM', NULL, '风机检修班组', 'WIND_TEAM', 6, true),
('WORK_TEAM_TYPE', 'PV_TEAM', '光伏检修班组', 'PV_TEAM', NULL, '光伏检修班组', 'PV_TEAM', 7, true),
('WORK_TEAM_TYPE', 'BESS_TEAM', '储能检修班组', 'BESS_TEAM', NULL, '储能检修班组', 'BESS_TEAM', 8, true),
('WORK_TEAM_TYPE', 'SAFETY_TEAM', '安全管理组', 'SAFETY_TEAM', NULL, '安全管理组', 'SAFETY_TEAM', 9, true),
('WORK_TEAM_TYPE', 'DATA_TEAM', '数据治理组', 'DATA_TEAM', NULL, '数据治理组', 'DATA_TEAM', 10, true),
('WORK_TEAM_TYPE', 'IT_TEAM', '信息化运维组', 'IT_TEAM', NULL, '信息化运维组', 'IT_TEAM', 11, true),
('WORK_TEAM_TYPE', 'AUDIT_TEAM', '审计组', 'AUDIT_TEAM', NULL, '审计组', 'AUDIT_TEAM', 12, true),
('WORK_TEAM_TYPE', 'VENDOR_TEAM', '外委厂家组', 'VENDOR_TEAM', NULL, '外委厂家组', 'VENDOR_TEAM', 13, true),
('PROTOCOL', 'MODBUS', 'MODBUS', 'MODBUS', NULL, 'MODBUS', 'MODBUS', 1, true),
('PROTOCOL', 'IEC101', 'IEC101', 'IEC101', NULL, 'IEC101', 'IEC101', 2, true),
('PROTOCOL', 'IEC104', 'IEC104', 'IEC104', NULL, 'IEC104', 'IEC104', 3, true),
('PROTOCOL', 'IEC61850_MMS', 'IEC61850_MMS', 'IEC61850_MMS', NULL, 'IEC61850_MMS', 'IEC61850_MMS', 4, true),
('PROTOCOL', 'IEC61850_GOOSE', 'IEC61850_GOOSE', 'IEC61850_GOOSE', NULL, 'IEC61850_GOOSE', 'IEC61850_GOOSE', 5, true),
('PROTOCOL', 'IEC61850_SV', 'IEC61850_SV', 'IEC61850_SV', NULL, 'IEC61850_SV', 'IEC61850_SV', 6, true),
('PROTOCOL', 'OPCUA', 'OPCUA', 'OPCUA', NULL, 'OPCUA', 'OPCUA', 7, true),
('PROTOCOL', 'MQTT', 'MQTT', 'MQTT', NULL, 'MQTT', 'MQTT', 8, true),
('PROTOCOL', 'ADS', 'ADS', 'ADS', NULL, 'ADS', 'ADS', 9, true),
('PROTOCOL', 'HTTP_REST', 'HTTP_REST', 'HTTP_REST', NULL, 'HTTP_REST', 'HTTP_REST', 10, true),
('PROTOCOL_TABLE_ROLE', 'CONN', '协议连接参数表', 'CONN', NULL, '协议连接参数表', 'CONN', 1, true),
('PROTOCOL_TABLE_ROLE', 'POINT_TABLE', '协议能力点表表头', 'POINT_TABLE', NULL, '协议能力点表表头', 'POINT_TABLE', 2, true),
('PROTOCOL_TABLE_ROLE', 'POINT_ITEM', '协议能力点明细表', 'POINT_ITEM', NULL, '协议能力点明细表', 'POINT_ITEM', 3, true),
('PROTOCOL_TABLE_ROLE', 'POINT_ITEM_VIEW', '协议点位执行视图', 'Point item execution view', NULL, '协议驱动读取点位配置时使用的真实执行视图；名称必须显式注册，不得按协议名推导。', 'Actual point-item execution view used by protocol drivers; the name must be registered explicitly.', 4, true),
('ASSET_TYPE', 'WIND_TURBINE', '风力发电机组', 'WIND_TURBINE', NULL, '风力发电机组', 'WIND_TURBINE', 1, true),
('ASSET_TYPE', 'MAIN_CONTROLLER', '主控系统', 'MAIN_CONTROLLER', NULL, '主控系统', 'MAIN_CONTROLLER', 2, true),
('ASSET_TYPE', 'CONVERTER', '变流器', 'CONVERTER', NULL, '变流器', 'CONVERTER', 3, true),
('ASSET_TYPE', 'PITCH_SYSTEM', '变桨系统', 'PITCH_SYSTEM', NULL, '变桨系统', 'PITCH_SYSTEM', 4, true),
('ASSET_TYPE', 'YAW_SYSTEM', '偏航系统', 'YAW_SYSTEM', NULL, '偏航系统', 'YAW_SYSTEM', 5, true),
('ASSET_TYPE', 'GEARBOX', '齿轮箱', 'GEARBOX', NULL, '齿轮箱', 'GEARBOX', 6, true),
('ASSET_TYPE', 'GENERATOR', '发电机', 'GENERATOR', NULL, '发电机', 'GENERATOR', 7, true),
('ASSET_TYPE', 'HUB', '轮毂', 'HUB', NULL, '轮毂', 'HUB', 8, true),
('ASSET_TYPE', 'BLADE', '叶片', 'BLADE', NULL, '叶片', 'BLADE', 9, true),
('ASSET_TYPE', 'TOWER', '塔筒', 'TOWER', NULL, '塔筒', 'TOWER', 10, true),
('ASSET_TYPE', 'COMM_INTERFACE', '通信接口', 'COMM_INTERFACE', NULL, '通信接口', 'COMM_INTERFACE', 11, true),
('ASSET_TYPE', 'ELEC_INTERFACE', '电气接口', 'ELEC_INTERFACE', NULL, '电气接口', 'ELEC_INTERFACE', 12, true),
('ASSET_TYPE', 'PV_INVERTER', '光伏逆变器', 'PV_INVERTER', NULL, '光伏逆变器', 'PV_INVERTER', 13, true),
('ASSET_TYPE', 'PV_COMBINER', '光伏汇流箱', 'PV_COMBINER', NULL, '光伏汇流箱', 'PV_COMBINER', 14, true),
('ASSET_TYPE', 'PV_ARRAY', '光伏阵列', 'PV_ARRAY', NULL, '光伏阵列', 'PV_ARRAY', 15, true),
('ASSET_TYPE', 'BESS_CONTAINER', '储能舱', 'BESS_CONTAINER', NULL, '储能舱', 'BESS_CONTAINER', 16, true),
('ASSET_TYPE', 'PCS', '储能PCS', 'PCS', NULL, '储能PCS', 'PCS', 17, true),
('ASSET_TYPE', 'BMS', '电池管理系统', 'BMS', NULL, '电池管理系统', 'BMS', 18, true),
('ASSET_TYPE', 'BATTERY_CLUSTER', '电池簇', 'BATTERY_CLUSTER', NULL, '电池簇', 'BATTERY_CLUSTER', 19, true),
('ASSET_TYPE', 'EMS', '能量管理系统', 'EMS', NULL, '能量管理系统', 'EMS', 20, true),
('ASSET_TYPE', 'SCADA_SERVER', 'SCADA系统', 'SCADA_SERVER', NULL, 'SCADA系统', 'SCADA_SERVER', 21, true),
('ASSET_TYPE', 'RTU', '远动终端', 'RTU', NULL, '远动终端', 'RTU', 22, true),
('ASSET_TYPE', 'GRID_DISPATCH_LINK', '调度链路对象', 'GRID_DISPATCH_LINK', NULL, '调度链路对象', 'GRID_DISPATCH_LINK', 23, true),
('ASSET_TYPE', 'COMM_GATEWAY', '通信网关', 'COMM_GATEWAY', NULL, '通信网关', 'COMM_GATEWAY', 24, true),
('ASSET_TYPE', 'PROTECTION_IED', '保护IED', 'PROTECTION_IED', NULL, '保护IED', 'PROTECTION_IED', 25, true),
('ASSET_TYPE', 'BAY_CONTROL_UNIT', '测控装置', 'BAY_CONTROL_UNIT', NULL, '测控装置', 'BAY_CONTROL_UNIT', 26, true),
('ASSET_TYPE', 'REACTOR', '并联电抗器', 'REACTOR', NULL, '并联电抗器', 'REACTOR', 27, true),
('ASSET_TYPE', 'MERGING_UNIT', '合并单元', 'MERGING_UNIT', NULL, '合并单元', 'MERGING_UNIT', 28, true),
('ASSET_TYPE', 'MAIN_TRANSFORMER', '主变压器', 'MAIN_TRANSFORMER', NULL, '主变压器', 'MAIN_TRANSFORMER', 29, true),
('ASSET_TYPE', 'PAD_TRANSFORMER', '箱式变压器', 'PAD_TRANSFORMER', NULL, '箱式变压器', 'PAD_TRANSFORMER', 30, true),
('ASSET_TYPE', 'SVG', 'SVG无功补偿装置', 'SVG', NULL, 'SVG无功补偿装置', 'SVG', 31, true),
('ASSET_TYPE', 'GRID_METER', '关口电能表', 'GRID_METER', NULL, '关口电能表', 'GRID_METER', 32, true),
('ASSET_TYPE', 'POWER_QUALITY_DEVICE', '电能质量装置', 'POWER_QUALITY_DEVICE', NULL, '电能质量装置', 'POWER_QUALITY_DEVICE', 33, true),
('ASSET_TYPE', 'MET_MAST', '测风塔', 'MET_MAST', NULL, '测风塔', 'MET_MAST', 34, true),
('ASSET_TYPE', 'WEATHER_STATION', '气象站', 'WEATHER_STATION', NULL, '气象站', 'WEATHER_STATION', 35, true),
('ASSET_TYPE', 'AGC_AVC_CONTROLLER', 'AGC/AVC控制器', 'AGC_AVC_CONTROLLER', NULL, 'AGC/AVC控制器', 'AGC_AVC_CONTROLLER', 36, true),
('ASSET_TYPE', 'THIRD_PARTY_SYSTEM', '第三方系统', 'THIRD_PARTY_SYSTEM', NULL, '第三方系统', 'THIRD_PARTY_SYSTEM', 37, true),
('ASSET_TYPE', 'MQTT_GATEWAY', 'MQTT边缘网关', 'MQTT_GATEWAY', NULL, 'MQTT边缘网关', 'MQTT_GATEWAY', 38, true),
('ASSET_TYPE', 'DATABASE_SERVER', '数据库服务器', 'DATABASE_SERVER', NULL, '数据库服务器', 'DATABASE_SERVER', 39, true),
('ASSET_TYPE', 'NTP_SERVER', 'NTP服务器', 'NTP_SERVER', NULL, 'NTP服务器', 'NTP_SERVER', 40, true),
('ASSET_TYPE', 'NETWORK_SWITCH', '工业交换机', 'NETWORK_SWITCH', NULL, '工业交换机', 'NETWORK_SWITCH', 41, true),
('ASSET_TYPE', 'FIREWALL', '防火墙', 'FIREWALL', NULL, '防火墙', 'FIREWALL', 42, true),
('ASSET_TYPE', 'BUSBAR', '母线', 'BUSBAR', NULL, '母线', 'BUSBAR', 43, true),
('ASSET_TYPE', 'CABLE', '电缆/线路', 'CABLE', NULL, '电缆/线路', 'CABLE', 44, true),
('ASSET_TYPE', 'FIBER', '光纤/通信链路', 'FIBER', NULL, '光纤/通信链路', 'FIBER', 45, true),
('ASSET_TYPE', 'CIRCUIT_BREAKER', '断路器', 'CIRCUIT_BREAKER', NULL, '断路器', 'CIRCUIT_BREAKER', 46, true),
('ASSET_TYPE', 'DISCONNECTOR', '隔离开关', 'DISCONNECTOR', NULL, '隔离开关', 'DISCONNECTOR', 47, true),
('ASSET_TYPE', 'EARTHING_SWITCH', '接地开关', 'EARTHING_SWITCH', NULL, '接地开关', 'EARTHING_SWITCH', 48, true),
('ASSET_TYPE', 'GROUNDING_POINT', '接地点', 'GROUNDING_POINT', NULL, '接地点', 'GROUNDING_POINT', 49, true),
('ASSET_TYPE', 'CURRENT_TRANSFORMER', '电流互感器', 'CURRENT_TRANSFORMER', NULL, '电流互感器', 'CURRENT_TRANSFORMER', 50, true),
('ASSET_TYPE', 'VOLTAGE_TRANSFORMER', '电压互感器', 'VOLTAGE_TRANSFORMER', NULL, '电压互感器', 'VOLTAGE_TRANSFORMER', 51, true),
('ASSET_TYPE', 'SURGE_ARRESTER', '避雷器', 'SURGE_ARRESTER', NULL, '避雷器', 'SURGE_ARRESTER', 52, true),
('ASSET_TYPE', 'SWITCHGEAR', '开关柜', 'SWITCHGEAR', NULL, '开关柜', 'SWITCHGEAR', 53, true),
('ASSET_TYPE', 'FEEDER_BAY', '馈线间隔', 'FEEDER_BAY', NULL, '馈线间隔', 'FEEDER_BAY', 54, true),
('ASSET_TYPE', 'GRID_EQUIVALENT', '外部电网等值节点', 'GRID_EQUIVALENT', NULL, '外部电网等值节点', 'GRID_EQUIVALENT', 55, true),
('ASSET_TYPE', 'CLIENT_TERMINAL', '客户端/工作站', 'CLIENT_TERMINAL', NULL, '客户端/工作站', 'CLIENT_TERMINAL', 56, true),
('ASSET_TYPE', 'DISPATCH_ROUTER', '调度路由器', 'DISPATCH_ROUTER', NULL, '调度路由器', 'DISPATCH_ROUTER', 57, true),
('ASSET_LIFECYCLE_STATUS', 'MANUFACTURED', '已生产', 'MANUFACTURED', NULL, '已生产', 'MANUFACTURED', 1, true),
('ASSET_LIFECYCLE_STATUS', 'INSTALLED', '已安装', 'INSTALLED', NULL, '已安装', 'INSTALLED', 2, true),
('ASSET_LIFECYCLE_STATUS', 'COMMISSIONED', '已投运', 'COMMISSIONED', NULL, '已投运', 'COMMISSIONED', 3, true),
('ASSET_LIFECYCLE_STATUS', 'IN_OPERATION', '运行中', 'IN_OPERATION', NULL, '运行中', 'IN_OPERATION', 4, true),
('ASSET_LIFECYCLE_STATUS', 'MAINTENANCE', '检修中', 'MAINTENANCE', NULL, '检修中', 'MAINTENANCE', 5, true),
('ASSET_LIFECYCLE_STATUS', 'RETIRED', '已退役', 'RETIRED', NULL, '已退役', 'RETIRED', 6, true),
('UNIT', 'NONE', '无', 'NONE', NULL, '无', 'NONE', 1, true),
('UNIT', 'MW', '兆瓦', 'MW', NULL, '兆瓦', 'MW', 2, true),
('UNIT', 'MWH', '兆瓦时', 'MWH', NULL, '兆瓦时', 'MWH', 3, true),
('UNIT', 'KW', '千瓦', 'KW', NULL, '千瓦', 'KW', 4, true),
('UNIT', 'KV', '千伏', 'KV', NULL, '千伏', 'KV', 5, true),
('UNIT', 'V', '伏', 'V', NULL, '伏', 'V', 6, true),
('UNIT', 'A', '安培', 'A', NULL, '安培', 'A', 7, true),
('UNIT', 'MVAR', '兆乏', 'MVAR', NULL, '兆乏', 'MVAR', 8, true),
('UNIT', 'HZ', '赫兹', 'HZ', NULL, '赫兹', 'HZ', 9, true),
('UNIT', 'RPM', '转每分', 'RPM', NULL, '转每分', 'RPM', 10, true),
('UNIT', 'MPS', '米每秒', 'MPS', NULL, '米每秒', 'MPS', 11, true),
('UNIT', 'DEGREE', '角度', 'DEGREE', NULL, '角度', 'DEGREE', 12, true),
('UNIT', 'DEG_C', '摄氏度', 'DEG_C', NULL, '摄氏度', 'DEG_C', 13, true),
('UNIT', 'PERCENT', '百分比', 'PERCENT', NULL, '百分比', 'PERCENT', 14, true),
('UNIT', 'MS', '毫秒', 'MS', NULL, '毫秒', 'MS', 15, true),
('UNIT', 'M', '米', 'M', NULL, '米', 'M', 16, true),
('UNIT', 'KM', '千米', 'KM', NULL, '千米', 'KM', 17, true),
('UNIT', 'W_M2', '瓦每平方米', 'W_M2', NULL, '瓦每平方米', 'W_M2', 18, true),
('UNIT', 'KPA', '千帕', 'KPA', NULL, '千帕', 'KPA', 19, true),
('UNIT', 'GB', 'GB', 'GB', NULL, 'GB', 'GB', 20, true),
('UNIT', 'TB', 'TB', 'TB', NULL, 'TB', 'TB', 21, true),
('UNIT', 'MBPS', 'Mbps', 'MBPS', NULL, 'Mbps', 'MBPS', 22, true),
('UNIT', 'GBPS', 'Gbps', 'GBPS', NULL, 'Gbps', 'GBPS', 23, true),
('DATA_TYPE', 'BOOL', 'BOOL', 'BOOL', NULL, 'BOOL', 'BOOL', 1, true),
('DATA_TYPE', 'INT32', 'INT32', 'INT32', NULL, 'INT32', 'INT32', 2, true),
('DATA_TYPE', 'FLOAT32', 'FLOAT32', 'FLOAT32', NULL, 'FLOAT32', 'FLOAT32', 3, true),
('DATA_TYPE', 'FLOAT64', 'FLOAT64', 'FLOAT64', NULL, 'FLOAT64', 'FLOAT64', 4, true),
('DATA_TYPE', 'DECIMAL', 'DECIMAL', 'DECIMAL', NULL, 'DECIMAL', 'DECIMAL', 5, true),
('DATA_TYPE', 'STRING', 'STRING', 'STRING', NULL, 'STRING', 'STRING', 6, true),
('DATA_TYPE', 'TIMESTAMP', 'TIMESTAMP', 'TIMESTAMP', NULL, 'TIMESTAMP', 'TIMESTAMP', 7, true),
('DATA_TYPE', 'JSON', 'JSON', 'JSON', NULL, 'JSON', 'JSON', 8, true),
('PROTOCOL_DATA_TYPE', 'BOOL', 'BOOL', 'BOOL', NULL, 'BOOL', 'BOOL', 1, true),
('PROTOCOL_DATA_TYPE', 'INT16', 'INT16', 'INT16', NULL, 'INT16', 'INT16', 2, true),
('PROTOCOL_DATA_TYPE', 'UINT16', 'UINT16', 'UINT16', NULL, 'UINT16', 'UINT16', 3, true),
('PROTOCOL_DATA_TYPE', 'INT32', 'INT32', 'INT32', NULL, 'INT32', 'INT32', 4, true),
('PROTOCOL_DATA_TYPE', 'UINT32', 'UINT32', 'UINT32', NULL, 'UINT32', 'UINT32', 5, true),
('PROTOCOL_DATA_TYPE', 'FLOAT32', 'FLOAT32', 'FLOAT32', NULL, 'FLOAT32', 'FLOAT32', 6, true),
('PROTOCOL_DATA_TYPE', 'FLOAT64', 'FLOAT64', 'FLOAT64', NULL, 'FLOAT64', 'FLOAT64', 7, true),
('PROTOCOL_DATA_TYPE', 'STRING', 'STRING', 'STRING', NULL, 'STRING', 'STRING', 8, true),
('PROTOCOL_DATA_TYPE', 'BITSTRING', 'BITSTRING', 'BITSTRING', NULL, 'BITSTRING', 'BITSTRING', 9, true),
('PROTOCOL_DATA_TYPE', 'QUALITY', 'QUALITY', 'QUALITY', NULL, 'QUALITY', 'QUALITY', 10, true),
('PROTOCOL_DATA_TYPE', 'TIMESTAMP', 'TIMESTAMP', 'TIMESTAMP', NULL, 'TIMESTAMP', 'TIMESTAMP', 11, true),
('PROTOCOL_DATA_TYPE', 'JSON', 'JSON', 'JSON', NULL, 'JSON', 'JSON', 12, true),
('PHYSICAL_QUANTITY_CATEGORY', 'POWER', '功率', 'POWER', NULL, '功率', 'POWER', 1, true),
('PHYSICAL_QUANTITY_CATEGORY', 'ENERGY', '电量', 'ENERGY', NULL, '电量', 'ENERGY', 2, true),
('PHYSICAL_QUANTITY_CATEGORY', 'VOLTAGE', '电压', 'VOLTAGE', NULL, '电压', 'VOLTAGE', 3, true),
('PHYSICAL_QUANTITY_CATEGORY', 'CURRENT', '电流', 'CURRENT', NULL, '电流', 'CURRENT', 4, true),
('PHYSICAL_QUANTITY_CATEGORY', 'FREQUENCY', '频率', 'FREQUENCY', NULL, '频率', 'FREQUENCY', 5, true),
('PHYSICAL_QUANTITY_CATEGORY', 'SPEED', '速度', 'SPEED', NULL, '速度', 'SPEED', 6, true),
('PHYSICAL_QUANTITY_CATEGORY', 'TEMPERATURE', '温度', 'TEMPERATURE', NULL, '温度', 'TEMPERATURE', 7, true),
('PHYSICAL_QUANTITY_CATEGORY', 'STATE', '状态', 'STATE', NULL, '状态', 'STATE', 8, true),
('PHYSICAL_QUANTITY_CATEGORY', 'COMMAND', '命令', 'COMMAND', NULL, '命令', 'COMMAND', 9, true),
('PHYSICAL_QUANTITY_CATEGORY', 'ALARM', '报警', 'ALARM', NULL, '报警', 'ALARM', 10, true),
('PHYSICAL_QUANTITY_CATEGORY', 'QUALITY', '质量', 'QUALITY', NULL, '质量', 'QUALITY', 11, true),
('PHYSICAL_QUANTITY_CATEGORY', 'WIND', '风况', 'WIND', NULL, '风况', 'WIND', 12, true),
('PHYSICAL_QUANTITY_CATEGORY', 'IRRADIANCE', '辐照度', 'IRRADIANCE', NULL, '辐照度', 'IRRADIANCE', 13, true),
('PHYSICAL_QUANTITY_CATEGORY', 'PRESSURE', '压力', 'PRESSURE', NULL, '压力', 'PRESSURE', 14, true),
('PHYSICAL_QUANTITY_CATEGORY', 'HUMIDITY', '湿度', 'HUMIDITY', NULL, '湿度', 'HUMIDITY', 15, true),
('PHYSICAL_QUANTITY_CATEGORY', 'STORAGE', '储能', 'STORAGE', NULL, '储能', 'STORAGE', 16, true),
('PHYSICAL_QUANTITY_CATEGORY', 'COMMUNICATION', '通信', 'COMMUNICATION', NULL, '通信', 'COMMUNICATION', 17, true),
('MODBUS_FUNCTION_CODE', 'READ_COILS', 'READ_COILS', 'READ_COILS', NULL, 'READ_COILS', 'READ_COILS', 1, true),
('MODBUS_FUNCTION_CODE', 'READ_DISCRETE_INPUTS', 'READ_DISCRETE_INPUTS', 'READ_DISCRETE_INPUTS', NULL, 'READ_DISCRETE_INPUTS', 'READ_DISCRETE_INPUTS', 2, true),
('MODBUS_FUNCTION_CODE', 'READ_HOLDING_REGISTERS', 'READ_HOLDING_REGISTERS', 'READ_HOLDING_REGISTERS', NULL, 'READ_HOLDING_REGISTERS', 'READ_HOLDING_REGISTERS', 3, true),
('MODBUS_FUNCTION_CODE', 'READ_INPUT_REGISTERS', 'READ_INPUT_REGISTERS', 'READ_INPUT_REGISTERS', NULL, 'READ_INPUT_REGISTERS', 'READ_INPUT_REGISTERS', 4, true),
('MODBUS_FUNCTION_CODE', 'WRITE_SINGLE_COIL', 'WRITE_SINGLE_COIL', 'WRITE_SINGLE_COIL', NULL, 'WRITE_SINGLE_COIL', 'WRITE_SINGLE_COIL', 5, true),
('MODBUS_FUNCTION_CODE', 'WRITE_SINGLE_REGISTER', 'WRITE_SINGLE_REGISTER', 'WRITE_SINGLE_REGISTER', NULL, 'WRITE_SINGLE_REGISTER', 'WRITE_SINGLE_REGISTER', 6, true),
('MODBUS_FUNCTION_CODE', 'WRITE_MULTIPLE_REGISTERS', 'WRITE_MULTIPLE_REGISTERS', 'WRITE_MULTIPLE_REGISTERS', NULL, 'WRITE_MULTIPLE_REGISTERS', 'WRITE_MULTIPLE_REGISTERS', 7, true),
('BYTE_ORDER', 'BIG_ENDIAN', 'BIG_ENDIAN', 'BIG_ENDIAN', NULL, 'BIG_ENDIAN', 'BIG_ENDIAN', 1, true),
('WORD_ORDER', 'BIG_ENDIAN', 'BIG_ENDIAN', 'BIG_ENDIAN', NULL, 'BIG_ENDIAN', 'BIG_ENDIAN', 1, true),
('BYTE_ORDER', 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', NULL, 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', 2, true),
('WORD_ORDER', 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', NULL, 'LITTLE_ENDIAN', 'LITTLE_ENDIAN', 2, true),
('TRANSPORT', 'TCP', 'TCP', 'TCP', NULL, 'TCP', 'TCP', 1, true),
('TRANSPORT', 'SERIAL', 'SERIAL', 'SERIAL', NULL, 'SERIAL', 'SERIAL', 2, true),
('TRANSPORT', 'RTU', 'RTU', 'RTU', NULL, 'RTU', 'RTU', 3, true),
('TRANSPORT', 'UDP', 'UDP', 'UDP', NULL, 'UDP', 'UDP', 4, true),
('IEC101_TYPE_ID', 'M_SP_NA_1', 'M_SP_NA_1', 'M_SP_NA_1', NULL, 'M_SP_NA_1', 'M_SP_NA_1', 1, true),
('IEC101_TYPE_ID', 'M_DP_NA_1', 'M_DP_NA_1', 'M_DP_NA_1', NULL, 'M_DP_NA_1', 'M_DP_NA_1', 2, true),
('IEC101_TYPE_ID', 'M_ME_NC_1', 'M_ME_NC_1', 'M_ME_NC_1', NULL, 'M_ME_NC_1', 'M_ME_NC_1', 3, true),
('IEC101_TYPE_ID', 'M_IT_NA_1', 'M_IT_NA_1', 'M_IT_NA_1', NULL, 'M_IT_NA_1', 'M_IT_NA_1', 4, true),
('IEC101_TYPE_ID', 'C_SC_NA_1', 'C_SC_NA_1', 'C_SC_NA_1', NULL, 'C_SC_NA_1', 'C_SC_NA_1', 5, true),
('IEC101_TYPE_ID', 'C_DC_NA_1', 'C_DC_NA_1', 'C_DC_NA_1', NULL, 'C_DC_NA_1', 'C_DC_NA_1', 6, true),
('IEC101_TYPE_ID', 'C_SE_NC_1', 'C_SE_NC_1', 'C_SE_NC_1', NULL, 'C_SE_NC_1', 'C_SE_NC_1', 7, true),
('IEC101_TYPE_ID', 'C_CS_NA_1', 'C_CS_NA_1', 'C_CS_NA_1', NULL, 'C_CS_NA_1', 'C_CS_NA_1', 8, true),
('IEC104_TYPE_CATEGORY', 'PROCESS_MONITOR', '过程监视', 'Process monitor', NULL, '过程监视。', 'Process monitor.', 1, true),
('IEC104_TYPE_CATEGORY', 'COUNTER_MONITOR', '累计量监视', 'Counter monitor', NULL, '累计量监视。', 'Counter monitor.', 2, true),
('IEC104_TYPE_CATEGORY', 'PROTECTION_MONITOR', '保护监视', 'Protection monitor', NULL, '保护监视。', 'Protection monitor.', 3, true),
('IEC104_TYPE_CATEGORY', 'CONTROL_COMMAND', '控制命令', 'Control command', NULL, '控制命令。', 'Control command.', 4, true),
('IEC104_TYPE_CATEGORY', 'INITIALIZATION', '初始化通知', 'Initialization', NULL, '初始化通知。', 'Initialization.', 5, true),
('IEC104_TYPE_CATEGORY', 'SYSTEM_COMMAND', '系统命令', 'System command', NULL, '系统命令。', 'System command.', 6, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SINGLE_POINT', 'SINGLE POINT', 'SINGLE POINT', NULL, 'SINGLE POINT。', 'SINGLE POINT.', 1, true),
('IEC104_INFORMATION_VALUE_TYPE', 'DOUBLE_POINT', 'DOUBLE POINT', 'DOUBLE POINT', NULL, 'DOUBLE POINT。', 'DOUBLE POINT.', 2, true),
('IEC104_INFORMATION_VALUE_TYPE', 'STEP_POSITION', 'STEP POSITION', 'STEP POSITION', NULL, 'STEP POSITION。', 'STEP POSITION.', 3, true),
('IEC104_INFORMATION_VALUE_TYPE', 'BITSTRING32', 'BITSTRING32', 'BITSTRING32', NULL, 'BITSTRING32。', 'BITSTRING32.', 4, true),
('IEC104_INFORMATION_VALUE_TYPE', 'NORMALIZED_VALUE', 'NORMALIZED VALUE', 'NORMALIZED VALUE', NULL, 'NORMALIZED VALUE。', 'NORMALIZED VALUE.', 5, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SCALED_VALUE', 'SCALED VALUE', 'SCALED VALUE', NULL, 'SCALED VALUE。', 'SCALED VALUE.', 6, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SHORT_FLOAT', 'SHORT FLOAT', 'SHORT FLOAT', NULL, 'SHORT FLOAT。', 'SHORT FLOAT.', 7, true),
('IEC104_INFORMATION_VALUE_TYPE', 'BINARY_COUNTER', 'BINARY COUNTER', 'BINARY COUNTER', NULL, 'BINARY COUNTER。', 'BINARY COUNTER.', 8, true),
('IEC104_INFORMATION_VALUE_TYPE', 'PROTECTION_EVENT', 'PROTECTION EVENT', 'PROTECTION EVENT', NULL, 'PROTECTION EVENT。', 'PROTECTION EVENT.', 9, true),
('IEC104_INFORMATION_VALUE_TYPE', 'PROTECTION_START', 'PROTECTION START', 'PROTECTION START', NULL, 'PROTECTION START。', 'PROTECTION START.', 10, true),
('IEC104_INFORMATION_VALUE_TYPE', 'PROTECTION_OUTPUT', 'PROTECTION OUTPUT', 'PROTECTION OUTPUT', NULL, 'PROTECTION OUTPUT。', 'PROTECTION OUTPUT.', 11, true),
('IEC104_INFORMATION_VALUE_TYPE', 'PACKED_SINGLE_POINT', 'PACKED SINGLE POINT', 'PACKED SINGLE POINT', NULL, 'PACKED SINGLE POINT。', 'PACKED SINGLE POINT.', 12, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SINGLE_COMMAND', 'SINGLE COMMAND', 'SINGLE COMMAND', NULL, 'SINGLE COMMAND。', 'SINGLE COMMAND.', 13, true),
('IEC104_INFORMATION_VALUE_TYPE', 'DOUBLE_COMMAND', 'DOUBLE COMMAND', 'DOUBLE COMMAND', NULL, 'DOUBLE COMMAND。', 'DOUBLE COMMAND.', 14, true),
('IEC104_INFORMATION_VALUE_TYPE', 'REGULATING_STEP_COMMAND', 'REGULATING STEP COMMAND', 'REGULATING STEP COMMAND', NULL, 'REGULATING STEP COMMAND。', 'REGULATING STEP COMMAND.', 15, true),
('IEC104_INFORMATION_VALUE_TYPE', 'NORMALIZED_COMMAND', 'NORMALIZED COMMAND', 'NORMALIZED COMMAND', NULL, 'NORMALIZED COMMAND。', 'NORMALIZED COMMAND.', 16, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SCALED_COMMAND', 'SCALED COMMAND', 'SCALED COMMAND', NULL, 'SCALED COMMAND。', 'SCALED COMMAND.', 17, true),
('IEC104_INFORMATION_VALUE_TYPE', 'SHORT_FLOAT_COMMAND', 'SHORT FLOAT COMMAND', 'SHORT FLOAT COMMAND', NULL, 'SHORT FLOAT COMMAND。', 'SHORT FLOAT COMMAND.', 18, true),
('IEC104_INFORMATION_VALUE_TYPE', 'BITSTRING32_COMMAND', 'BITSTRING32 COMMAND', 'BITSTRING32 COMMAND', NULL, 'BITSTRING32 COMMAND。', 'BITSTRING32 COMMAND.', 19, true),
('IEC104_INFORMATION_VALUE_TYPE', 'NONE', 'NONE', 'NONE', NULL, 'NONE。', 'NONE.', 20, true),
('IEC104_INFORMATION_VALUE_TYPE', 'INTERROGATION_COMMAND', 'INTERROGATION COMMAND', 'INTERROGATION COMMAND', NULL, 'INTERROGATION COMMAND。', 'INTERROGATION COMMAND.', 21, true),
('IEC104_INFORMATION_VALUE_TYPE', 'COUNTER_INTERROGATION_COMMAND', 'COUNTER INTERROGATION COMMAND', 'COUNTER INTERROGATION COMMAND', NULL, 'COUNTER INTERROGATION COMMAND。', 'COUNTER INTERROGATION COMMAND.', 22, true),
('IEC104_INFORMATION_VALUE_TYPE', 'READ_COMMAND', 'READ COMMAND', 'READ COMMAND', NULL, 'READ COMMAND。', 'READ COMMAND.', 23, true),
('IEC104_INFORMATION_VALUE_TYPE', 'CLOCK_SYNC_COMMAND', 'CLOCK SYNC COMMAND', 'CLOCK SYNC COMMAND', NULL, 'CLOCK SYNC COMMAND。', 'CLOCK SYNC COMMAND.', 24, true),
('IEC104_INFORMATION_VALUE_TYPE', 'TEST_COMMAND', 'TEST COMMAND', 'TEST COMMAND', NULL, 'TEST COMMAND。', 'TEST COMMAND.', 25, true),
('IEC104_INFORMATION_VALUE_TYPE', 'RESET_PROCESS_COMMAND', 'RESET PROCESS COMMAND', 'RESET PROCESS COMMAND', NULL, 'RESET PROCESS COMMAND。', 'RESET PROCESS COMMAND.', 26, true),
('IEC104_INFORMATION_VALUE_TYPE', 'DELAY_ACQUISITION_COMMAND', 'DELAY ACQUISITION COMMAND', 'DELAY ACQUISITION COMMAND', NULL, 'DELAY ACQUISITION COMMAND。', 'DELAY ACQUISITION COMMAND.', 27, true),
('IEC104_TIME_TAG_TYPE', 'NONE', '无时标', 'No time tag', NULL, '无时标。', 'No time tag.', 1, true),
('IEC104_TIME_TAG_TYPE', 'CP16TIME2A', 'CP16Time2a', 'CP16Time2a', NULL, 'CP16Time2a。', 'CP16Time2a.', 2, true),
('IEC104_TIME_TAG_TYPE', 'CP24TIME2A', 'CP24Time2a', 'CP24Time2a', NULL, 'CP24Time2a。', 'CP24Time2a.', 3, true),
('IEC104_TIME_TAG_TYPE', 'CP56TIME2A', 'CP56Time2a', 'CP56Time2a', NULL, 'CP56Time2a。', 'CP56Time2a.', 4, true),
('IEC104_COMMAND_MODE', 'DIRECT', '直接执行', 'Direct', NULL, '直接执行。', 'Direct.', 1, true),
('IEC104_COMMAND_MODE', 'SELECT_AND_EXECUTE', '选择后执行', 'Select and execute', NULL, '选择后执行。', 'Select and execute.', 2, true),
('IEC104_TYPE_ID', 'M_SP_NA_1', '单点信息，无时标', 'Single-point information without time tag', 'M_SP_NA_1', 'IEC104 Type ID 1。', 'IEC104 Type ID 1.', 1, true),
('IEC104_TYPE_ID', 'M_SP_TA_1', '单点信息，CP24Time2a', 'Single-point information with CP24Time2a', 'M_SP_TA_1', 'IEC104 Type ID 2。', 'IEC104 Type ID 2.', 2, true),
('IEC104_TYPE_ID', 'M_DP_NA_1', '双点信息，无时标', 'Double-point information without time tag', 'M_DP_NA_1', 'IEC104 Type ID 3。', 'IEC104 Type ID 3.', 3, true),
('IEC104_TYPE_ID', 'M_DP_TA_1', '双点信息，CP24Time2a', 'Double-point information with CP24Time2a', 'M_DP_TA_1', 'IEC104 Type ID 4。', 'IEC104 Type ID 4.', 4, true),
('IEC104_TYPE_ID', 'M_ST_NA_1', '步位置信息，无时标', 'Step-position information without time tag', 'M_ST_NA_1', 'IEC104 Type ID 5。', 'IEC104 Type ID 5.', 5, true),
('IEC104_TYPE_ID', 'M_ST_TA_1', '步位置信息，CP24Time2a', 'Step-position information with CP24Time2a', 'M_ST_TA_1', 'IEC104 Type ID 6。', 'IEC104 Type ID 6.', 6, true),
('IEC104_TYPE_ID', 'M_BO_NA_1', '32位比特串，无时标', 'Bitstring of 32 bits without time tag', 'M_BO_NA_1', 'IEC104 Type ID 7。', 'IEC104 Type ID 7.', 7, true),
('IEC104_TYPE_ID', 'M_BO_TA_1', '32位比特串，CP24Time2a', 'Bitstring of 32 bits with CP24Time2a', 'M_BO_TA_1', 'IEC104 Type ID 8。', 'IEC104 Type ID 8.', 8, true),
('IEC104_TYPE_ID', 'M_ME_NA_1', '归一化遥测值，无时标', 'Normalized measured value without time tag', 'M_ME_NA_1', 'IEC104 Type ID 9。', 'IEC104 Type ID 9.', 9, true),
('IEC104_TYPE_ID', 'M_ME_TA_1', '归一化遥测值，CP24Time2a', 'Normalized measured value with CP24Time2a', 'M_ME_TA_1', 'IEC104 Type ID 10。', 'IEC104 Type ID 10.', 10, true),
('IEC104_TYPE_ID', 'M_ME_NB_1', '标度化遥测值，无时标', 'Scaled measured value without time tag', 'M_ME_NB_1', 'IEC104 Type ID 11。', 'IEC104 Type ID 11.', 11, true),
('IEC104_TYPE_ID', 'M_ME_TB_1', '标度化遥测值，CP24Time2a', 'Scaled measured value with CP24Time2a', 'M_ME_TB_1', 'IEC104 Type ID 12。', 'IEC104 Type ID 12.', 12, true),
('IEC104_TYPE_ID', 'M_ME_NC_1', '短浮点遥测，无时标', 'Short floating-point measured value without time tag', 'M_ME_NC_1', 'IEC104 Type ID 13。', 'IEC104 Type ID 13.', 13, true),
('IEC104_TYPE_ID', 'M_ME_TC_1', '短浮点遥测，CP24Time2a', 'Short floating-point measured value with CP24Time2a', 'M_ME_TC_1', 'IEC104 Type ID 14。', 'IEC104 Type ID 14.', 14, true),
('IEC104_TYPE_ID', 'M_IT_NA_1', '累计量，无时标', 'Integrated total without time tag', 'M_IT_NA_1', 'IEC104 Type ID 15。', 'IEC104 Type ID 15.', 15, true),
('IEC104_TYPE_ID', 'M_IT_TA_1', '累计量，CP24Time2a', 'Integrated total with CP24Time2a', 'M_IT_TA_1', 'IEC104 Type ID 16。', 'IEC104 Type ID 16.', 16, true),
('IEC104_TYPE_ID', 'M_EP_TA_1', '继电保护事件，CP24Time2a', 'Protection event with CP24Time2a', 'M_EP_TA_1', 'IEC104 Type ID 17。', 'IEC104 Type ID 17.', 17, true),
('IEC104_TYPE_ID', 'M_EP_TB_1', '继电保护启动事件，CP24Time2a', 'Protection start event with CP24Time2a', 'M_EP_TB_1', 'IEC104 Type ID 18。', 'IEC104 Type ID 18.', 18, true),
('IEC104_TYPE_ID', 'M_EP_TC_1', '继电保护输出回路信息，CP24Time2a', 'Protection output-circuit information with CP24Time2a', 'M_EP_TC_1', 'IEC104 Type ID 19。', 'IEC104 Type ID 19.', 19, true),
('IEC104_TYPE_ID', 'M_PS_NA_1', '带状态变位检测的成组单点信息', 'Packed single-point information with status change detection', 'M_PS_NA_1', 'IEC104 Type ID 20。', 'IEC104 Type ID 20.', 20, true),
('IEC104_TYPE_ID', 'M_ME_ND_1', '不带质量描述词的归一化遥测', 'Normalized measured value without quality descriptor', 'M_ME_ND_1', 'IEC104 Type ID 21。', 'IEC104 Type ID 21.', 21, true),
('IEC104_TYPE_ID', 'M_SP_TB_1', '单点信息，CP56Time2a', 'Single-point information with CP56Time2a', 'M_SP_TB_1', 'IEC104 Type ID 30。', 'IEC104 Type ID 30.', 30, true),
('IEC104_TYPE_ID', 'M_DP_TB_1', '双点信息，CP56Time2a', 'Double-point information with CP56Time2a', 'M_DP_TB_1', 'IEC104 Type ID 31。', 'IEC104 Type ID 31.', 31, true),
('IEC104_TYPE_ID', 'M_ST_TB_1', '步位置信息，CP56Time2a', 'Step-position information with CP56Time2a', 'M_ST_TB_1', 'IEC104 Type ID 32。', 'IEC104 Type ID 32.', 32, true),
('IEC104_TYPE_ID', 'M_BO_TB_1', '32位比特串，CP56Time2a', 'Bitstring of 32 bits with CP56Time2a', 'M_BO_TB_1', 'IEC104 Type ID 33。', 'IEC104 Type ID 33.', 33, true),
('IEC104_TYPE_ID', 'M_ME_TD_1', '归一化遥测，CP56Time2a', 'Normalized measured value with CP56Time2a', 'M_ME_TD_1', 'IEC104 Type ID 34。', 'IEC104 Type ID 34.', 34, true),
('IEC104_TYPE_ID', 'M_ME_TE_1', '标度化遥测，CP56Time2a', 'Scaled measured value with CP56Time2a', 'M_ME_TE_1', 'IEC104 Type ID 35。', 'IEC104 Type ID 35.', 35, true),
('IEC104_TYPE_ID', 'M_ME_TF_1', '短浮点遥测，CP56Time2a', 'Short floating-point measured value with CP56Time2a', 'M_ME_TF_1', 'IEC104 Type ID 36。', 'IEC104 Type ID 36.', 36, true),
('IEC104_TYPE_ID', 'M_IT_TB_1', '累计量，CP56Time2a', 'Integrated total with CP56Time2a', 'M_IT_TB_1', 'IEC104 Type ID 37。', 'IEC104 Type ID 37.', 37, true),
('IEC104_TYPE_ID', 'M_EP_TD_1', '继电保护事件，CP56Time2a', 'Protection event with CP56Time2a', 'M_EP_TD_1', 'IEC104 Type ID 38。', 'IEC104 Type ID 38.', 38, true),
('IEC104_TYPE_ID', 'M_EP_TE_1', '继电保护启动事件，CP56Time2a', 'Protection start event with CP56Time2a', 'M_EP_TE_1', 'IEC104 Type ID 39。', 'IEC104 Type ID 39.', 39, true),
('IEC104_TYPE_ID', 'M_EP_TF_1', '继电保护输出回路信息，CP56Time2a', 'Protection output-circuit information with CP56Time2a', 'M_EP_TF_1', 'IEC104 Type ID 40。', 'IEC104 Type ID 40.', 40, true),
('IEC104_TYPE_ID', 'C_SC_NA_1', '单点遥控命令', 'Single command', 'C_SC_NA_1', 'IEC104 Type ID 45。', 'IEC104 Type ID 45.', 45, true),
('IEC104_TYPE_ID', 'C_DC_NA_1', '双点遥控命令', 'Double command', 'C_DC_NA_1', 'IEC104 Type ID 46。', 'IEC104 Type ID 46.', 46, true),
('IEC104_TYPE_ID', 'C_RC_NA_1', '升降步调节命令', 'Regulating step command', 'C_RC_NA_1', 'IEC104 Type ID 47。', 'IEC104 Type ID 47.', 47, true),
('IEC104_TYPE_ID', 'C_SE_NA_1', '归一化设点命令', 'Normalized set-point command', 'C_SE_NA_1', 'IEC104 Type ID 48。', 'IEC104 Type ID 48.', 48, true),
('IEC104_TYPE_ID', 'C_SE_NB_1', '标度化设点命令', 'Scaled set-point command', 'C_SE_NB_1', 'IEC104 Type ID 49。', 'IEC104 Type ID 49.', 49, true),
('IEC104_TYPE_ID', 'C_SE_NC_1', '短浮点设点命令', 'Short floating-point set-point command', 'C_SE_NC_1', 'IEC104 Type ID 50。', 'IEC104 Type ID 50.', 50, true),
('IEC104_TYPE_ID', 'C_BO_NA_1', '32位比特串命令', 'Bitstring of 32 bits command', 'C_BO_NA_1', 'IEC104 Type ID 51。', 'IEC104 Type ID 51.', 51, true),
('IEC104_TYPE_ID', 'C_SC_TA_1', '单点遥控，CP56Time2a', 'Single command with CP56Time2a', 'C_SC_TA_1', 'IEC104 Type ID 58。', 'IEC104 Type ID 58.', 58, true),
('IEC104_TYPE_ID', 'C_DC_TA_1', '双点遥控，CP56Time2a', 'Double command with CP56Time2a', 'C_DC_TA_1', 'IEC104 Type ID 59。', 'IEC104 Type ID 59.', 59, true),
('IEC104_TYPE_ID', 'C_RC_TA_1', '升降步调节，CP56Time2a', 'Regulating step command with CP56Time2a', 'C_RC_TA_1', 'IEC104 Type ID 60。', 'IEC104 Type ID 60.', 60, true),
('IEC104_TYPE_ID', 'C_SE_TA_1', '归一化设点，CP56Time2a', 'Normalized set-point command with CP56Time2a', 'C_SE_TA_1', 'IEC104 Type ID 61。', 'IEC104 Type ID 61.', 61, true),
('IEC104_TYPE_ID', 'C_SE_TB_1', '标度化设点，CP56Time2a', 'Scaled set-point command with CP56Time2a', 'C_SE_TB_1', 'IEC104 Type ID 62。', 'IEC104 Type ID 62.', 62, true),
('IEC104_TYPE_ID', 'C_SE_TC_1', '短浮点设点，CP56Time2a', 'Short floating-point set-point command with CP56Time2a', 'C_SE_TC_1', 'IEC104 Type ID 63。', 'IEC104 Type ID 63.', 63, true),
('IEC104_TYPE_ID', 'C_BO_TA_1', '32位比特串命令，CP56Time2a', 'Bitstring of 32 bits command with CP56Time2a', 'C_BO_TA_1', 'IEC104 Type ID 64。', 'IEC104 Type ID 64.', 64, true),
('IEC104_TYPE_ID', 'M_EI_NA_1', '初始化结束通知', 'End of initialization', 'M_EI_NA_1', 'IEC104 Type ID 70。', 'IEC104 Type ID 70.', 70, true),
('IEC104_TYPE_ID', 'C_IC_NA_1', '总召/组召命令', 'Interrogation command', 'C_IC_NA_1', 'IEC104 Type ID 100。', 'IEC104 Type ID 100.', 100, true),
('IEC104_TYPE_ID', 'C_CI_NA_1', '累计量召唤命令', 'Counter interrogation command', 'C_CI_NA_1', 'IEC104 Type ID 101。', 'IEC104 Type ID 101.', 101, true),
('IEC104_TYPE_ID', 'C_RD_NA_1', '读指定信息对象', 'Read command', 'C_RD_NA_1', 'IEC104 Type ID 102。', 'IEC104 Type ID 102.', 102, true),
('IEC104_TYPE_ID', 'C_CS_NA_1', '时钟同步命令', 'Clock synchronization command', 'C_CS_NA_1', 'IEC104 Type ID 103。', 'IEC104 Type ID 103.', 103, true),
('IEC104_TYPE_ID', 'C_TS_NA_1', '测试命令', 'Test command', 'C_TS_NA_1', 'IEC104 Type ID 104。', 'IEC104 Type ID 104.', 104, true),
('IEC104_TYPE_ID', 'C_RP_NA_1', '复位进程命令', 'Reset process command', 'C_RP_NA_1', 'IEC104 Type ID 105。', 'IEC104 Type ID 105.', 105, true),
('IEC104_TYPE_ID', 'C_CD_NA_1', '延时采集命令', 'Delay acquisition command', 'C_CD_NA_1', 'IEC104 Type ID 106。', 'IEC104 Type ID 106.', 106, true),
('IEC104_TYPE_ID', 'C_TS_TA_1', '带CP56Time2a的测试命令', 'Test command with CP56Time2a', 'C_TS_TA_1', 'IEC104 Type ID 107。', 'IEC104 Type ID 107.', 107, true),
('IEC104_STATION_ROLE', 'CONTROLLING_STATION', '控制站/主站', 'Controlling station', 'CLIENT', '主动建立 TCP 连接、发送 STARTDT、召唤和控制命令，并接收监视数据。', 'Initiates TCP, sends STARTDT/interrogation/control commands, and receives monitor data.', 1, true),
('IEC104_STATION_ROLE', 'CONTROLLED_STATION', '被控站/子站', 'Controlled station', 'SERVER', '监听 TCP 端口，响应 STARTDT、总召和控制命令，并主动上送监视数据。', 'Listens on TCP, responds to STARTDT/interrogation/control, and publishes monitor data.', 2, true),
('IEC61850_FC', 'ST', 'ST', 'ST', NULL, 'ST', 'ST', 1, true),
('IEC61850_FC', 'MX', 'MX', 'MX', NULL, 'MX', 'MX', 2, true),
('IEC61850_FC', 'CO', 'CO', 'CO', NULL, 'CO', 'CO', 3, true),
('IEC61850_FC', 'SP', 'SP', 'SP', NULL, 'SP', 'SP', 4, true),
('IEC61850_FC', 'SG', 'SG', 'SG', NULL, 'SG', 'SG', 5, true),
('IEC61850_FC', 'CF', 'CF', 'CF', NULL, 'CF', 'CF', 6, true),
('IEC61850_FC', 'DC', 'DC', 'DC', NULL, 'DC', 'DC', 7, true),
('IEC61850_CDC', 'SPS', 'SPS', 'SPS', NULL, 'SPS', 'SPS', 1, true),
('IEC61850_CDC', 'DPS', 'DPS', 'DPS', NULL, 'DPS', 'DPS', 2, true),
('IEC61850_CDC', 'INS', 'INS', 'INS', NULL, 'INS', 'INS', 3, true),
('IEC61850_CDC', 'ENS', 'ENS', 'ENS', NULL, 'ENS', 'ENS', 4, true),
('IEC61850_CDC', 'MV', 'MV', 'MV', NULL, 'MV', 'MV', 5, true),
('IEC61850_CDC', 'CMV', 'CMV', 'CMV', NULL, 'CMV', 'CMV', 6, true),
('IEC61850_CDC', 'ACT', 'ACT', 'ACT', NULL, 'ACT', 'ACT', 7, true),
('IEC61850_CDC', 'ACD', 'ACD', 'ACD', NULL, 'ACD', 'ACD', 8, true),
('IEC61850_CDC', 'SPC', 'SPC', 'SPC', NULL, 'SPC', 'SPC', 9, true),
('IEC61850_CDC', 'DPC', 'DPC', 'DPC', NULL, 'DPC', 'DPC', 10, true),
('OPCUA_SECURITY_POLICY', 'NONE', 'NONE', 'NONE', NULL, 'NONE', 'NONE', 1, true),
('OPCUA_SECURITY_POLICY', 'BASIC256SHA256', 'BASIC256SHA256', 'BASIC256SHA256', NULL, 'BASIC256SHA256', 'BASIC256SHA256', 2, true),
('OPCUA_SECURITY_MODE', 'NONE', 'NONE', 'NONE', NULL, 'NONE', 'NONE', 1, true),
('OPCUA_SECURITY_MODE', 'SIGN', 'SIGN', 'SIGN', NULL, 'SIGN', 'SIGN', 2, true),
('OPCUA_SECURITY_MODE', 'SIGN_AND_ENCRYPT', 'SIGN_AND_ENCRYPT', 'SIGN_AND_ENCRYPT', NULL, 'SIGN_AND_ENCRYPT', 'SIGN_AND_ENCRYPT', 3, true),
('PAYLOAD_FORMAT', 'JSON', 'JSON', 'JSON', NULL, 'JSON', 'JSON', 1, true),
('MQTT_PAYLOAD_FORMAT', 'JSON', 'JSON', 'JSON', NULL, 'JSON', 'JSON', 1, true),
('PAYLOAD_FORMAT', 'TEXT', 'TEXT', 'TEXT', NULL, 'TEXT', 'TEXT', 2, true),
('MQTT_PAYLOAD_FORMAT', 'TEXT', 'TEXT', 'TEXT', NULL, 'TEXT', 'TEXT', 2, true),
('HTTP_METHOD', 'GET', 'GET', 'GET', NULL, 'GET', 'GET', 1, true),
('HTTP_METHOD', 'POST', 'POST', 'POST', NULL, 'POST', 'POST', 2, true),
('HTTP_METHOD', 'PUT', 'PUT', 'PUT', NULL, 'PUT', 'PUT', 3, true),
('HTTP_AUTH_TYPE', 'NONE', 'NONE', 'NONE', NULL, 'NONE', 'NONE', 1, true),
('HTTP_AUTH_TYPE', 'BASIC', 'BASIC', 'BASIC', NULL, 'BASIC', 'BASIC', 2, true),
('HTTP_AUTH_TYPE', 'BEARER', 'BEARER', 'BEARER', NULL, 'BEARER', 'BEARER', 3, true),
('PROTOCOL_ROLE', 'MODBUS_CLIENT', '客户端', 'Client', NULL, 'MODBUS 客户端，主动发起读写请求。', 'MODBUS client initiating read/write requests.', 1, true),
('PROTOCOL_ROLE', 'OPCUA_CLIENT', '客户端', 'Client', NULL, 'OPC UA Client。', 'OPC UA Client.', 2, true),
('PROTOCOL_ROLE', 'ADS_CLIENT', '客户端', 'Client', NULL, 'ADS Client。', 'ADS Client.', 3, true),
('PROTOCOL_ROLE', 'IEC101_CONTROLLING_STATION', '控制站（主站）', 'Controlling station', NULL, 'IEC101 控制站。', 'IEC101 controlling station.', 4, true),
('PROTOCOL_ROLE', 'IEC101_CONTROLLED_STATION', '被控站（子站）', 'Controlled station', NULL, 'IEC101 被控站。', 'IEC101 controlled station.', 5, true),
('PROTOCOL_ROLE', 'IEC104_CONTROLLING_STATION', '控制站（主站）', 'Controlling station', NULL, 'IEC104 控制站。', 'IEC104 controlling station.', 6, true),
('PROTOCOL_ROLE', 'IEC104_CONTROLLED_STATION', '被控站（子站）', 'Controlled station', NULL, 'IEC104 被控站。', 'IEC104 controlled station.', 7, true),
('PROTOCOL_ROLE', 'IEC61850_MMS_CLIENT', 'MMS客户端', 'MMS client', NULL, 'IEC 61850 MMS Client。', 'IEC 61850 MMS client.', 8, true),
('PROTOCOL_ROLE', 'IEC61850_GOOSE_PUBLISHER', 'GOOSE发布者', 'GOOSE publisher', NULL, 'IEC 61850 GOOSE Publisher。', 'IEC 61850 GOOSE publisher.', 9, true),
('PROTOCOL_ROLE', 'IEC61850_GOOSE_SUBSCRIBER', 'GOOSE订阅者', 'GOOSE subscriber', NULL, 'IEC 61850 GOOSE Subscriber。', 'IEC 61850 GOOSE subscriber.', 10, true),
('PROTOCOL_ROLE', 'IEC61850_SV_PUBLISHER', 'SV发布者', 'SV publisher', NULL, 'IEC 61850 SV Publisher。', 'IEC 61850 SV publisher.', 11, true),
('PROTOCOL_ROLE', 'IEC61850_SV_SUBSCRIBER', 'SV订阅者', 'SV subscriber', NULL, 'IEC 61850 SV Subscriber。', 'IEC 61850 SV subscriber.', 12, true),
('PROTOCOL_ROLE', 'MQTT_PUBLISHER', '发布者', 'Publisher', NULL, 'MQTT Publisher。', 'MQTT publisher.', 13, true),
('PROTOCOL_ROLE', 'MQTT_SUBSCRIBER', '订阅者', 'Subscriber', NULL, 'MQTT Subscriber。', 'MQTT subscriber.', 14, true),
('PROTOCOL_ROLE', 'HTTP_REST_CLIENT', '客户端', 'Client', NULL, 'HTTP REST Client。', 'HTTP REST client.', 15, true),
('POINT_TABLE_USAGE', 'ACQUIRE_POINT_SET', 'ACQUIRE_POINT_SET', 'ACQUIRE_POINT_SET', NULL, 'ACQUIRE_POINT_SET', 'ACQUIRE_POINT_SET', 1, true),
('POINT_TABLE_USAGE', 'COMMAND_TARGET_SET', 'COMMAND_TARGET_SET', 'COMMAND_TARGET_SET', NULL, 'COMMAND_TARGET_SET', 'COMMAND_TARGET_SET', 2, true),
('POINT_TABLE_USAGE', 'CONTROL_TARGET_SET', 'CONTROL_TARGET_SET', 'CONTROL_TARGET_SET', NULL, 'CONTROL_TARGET_SET', 'CONTROL_TARGET_SET', 3, true),
('POINT_TABLE_USAGE', 'PUBLISH_PAYLOAD_SET', 'PUBLISH_PAYLOAD_SET', 'PUBLISH_PAYLOAD_SET', NULL, 'PUBLISH_PAYLOAD_SET', 'PUBLISH_PAYLOAD_SET', 4, true),
('POINT_TABLE_USAGE', 'REPORT_DATASET', 'REPORT_DATASET', 'REPORT_DATASET', NULL, 'REPORT_DATASET', 'REPORT_DATASET', 5, true),
('POINT_TABLE_USAGE', 'SERVE_RESPONSE_SET', 'SERVE_RESPONSE_SET', 'SERVE_RESPONSE_SET', NULL, 'SERVE_RESPONSE_SET', 'SERVE_RESPONSE_SET', 6, true),
('PROTOCOL_OPERATION_SEMANTIC', 'READ', 'READ', 'READ', NULL, 'READ', 'READ', 1, true),
('PROTOCOL_OPERATION_SEMANTIC', 'WRITE', 'WRITE', 'WRITE', NULL, 'WRITE', 'WRITE', 2, true),
('PROTOCOL_OPERATION_SEMANTIC', 'CONTROL', 'CONTROL', 'CONTROL', NULL, 'CONTROL', 'CONTROL', 3, true),
('PROTOCOL_OPERATION_SEMANTIC', 'PUBLISH', 'PUBLISH', 'PUBLISH', NULL, 'PUBLISH', 'PUBLISH', 4, true),
('PROTOCOL_OPERATION_SEMANTIC', 'SUBSCRIBE', 'SUBSCRIBE', 'SUBSCRIBE', NULL, 'SUBSCRIBE', 'SUBSCRIBE', 5, true),
('PROTOCOL_OPERATION_SEMANTIC', 'REPORT', 'REPORT', 'REPORT', NULL, 'REPORT', 'REPORT', 6, true),
('PROTOCOL_OPERATION_SEMANTIC', 'INTERROGATION', 'INTERROGATION', 'INTERROGATION', NULL, 'INTERROGATION', 'INTERROGATION', 7, true),
('PROTOCOL_OPERATION_SEMANTIC', 'COUNTER_INTERROGATION', 'COUNTER_INTERROGATION', 'COUNTER_INTERROGATION', NULL, 'COUNTER_INTERROGATION', 'COUNTER_INTERROGATION', 8, true),
('PROTOCOL_OPERATION_SEMANTIC', 'TIME_SYNC', 'TIME_SYNC', 'TIME_SYNC', NULL, 'TIME_SYNC', 'TIME_SYNC', 9, true),
('PROTOCOL_OPERATION_SEMANTIC', 'METHOD_CALL', 'METHOD_CALL', 'METHOD_CALL', NULL, 'METHOD_CALL', 'METHOD_CALL', 10, true),
('PROTOCOL_OPERATION_SEMANTIC', 'EVENT', 'EVENT', 'EVENT', NULL, 'EVENT', 'EVENT', 11, true),
('PROTOCOL_OPERATION_SEMANTIC', 'NOTIFICATION', 'NOTIFICATION', 'NOTIFICATION', NULL, 'NOTIFICATION', 'NOTIFICATION', 12, true),
('PROTOCOL_OPERATION_SEMANTIC', 'ACCEPT_CONTROL', 'ACCEPT_CONTROL', 'ACCEPT_CONTROL', NULL, 'ACCEPT_CONTROL', 'ACCEPT_CONTROL', 13, true),
('PROTOCOL_OPERATION_DIRECTION', 'LOCAL_TO_REMOTE', 'LOCAL_TO_REMOTE', 'LOCAL_TO_REMOTE', NULL, 'LOCAL_TO_REMOTE', 'LOCAL_TO_REMOTE', 1, true),
('PROTOCOL_OPERATION_DIRECTION', 'REMOTE_TO_LOCAL', 'REMOTE_TO_LOCAL', 'REMOTE_TO_LOCAL', NULL, 'REMOTE_TO_LOCAL', 'REMOTE_TO_LOCAL', 2, true),
('PROTOCOL_OPERATION_DIRECTION', 'LOCAL_REPORT_REMOTE', 'LOCAL_REPORT_REMOTE', 'LOCAL_REPORT_REMOTE', NULL, 'LOCAL_REPORT_REMOTE', 'LOCAL_REPORT_REMOTE', 3, true),
('REQUEST_RESPONSE_MODE', 'REQUEST_RESPONSE', 'REQUEST_RESPONSE', 'REQUEST_RESPONSE', NULL, 'REQUEST_RESPONSE', 'REQUEST_RESPONSE', 1, true),
('REQUEST_RESPONSE_MODE', 'REPORTING', 'REPORTING', 'REPORTING', NULL, 'REPORTING', 'REPORTING', 2, true),
('REQUEST_RESPONSE_MODE', 'NOTIFICATION', 'NOTIFICATION', 'NOTIFICATION', NULL, 'NOTIFICATION', 'NOTIFICATION', 3, true),
('REQUEST_RESPONSE_MODE', 'PUBLISH_SUBSCRIBE', 'PUBLISH_SUBSCRIBE', 'PUBLISH_SUBSCRIBE', NULL, 'PUBLISH_SUBSCRIBE', 'PUBLISH_SUBSCRIBE', 4, true),
('TRIGGER_MODE', 'SCHEDULED', 'SCHEDULED', 'SCHEDULED', NULL, 'SCHEDULED', 'SCHEDULED', 1, true),
('TRIGGER_MODE', 'MANUAL', 'MANUAL', 'MANUAL', NULL, 'MANUAL', 'MANUAL', 2, true),
('TRIGGER_MODE', 'EVENT', 'EVENT', 'EVENT', NULL, 'EVENT', 'EVENT', 3, true),
('TASK_CONSTRAINT_FIELD', 'TRIGGER_MODE', '触发方式', 'Trigger mode', NULL, '约束 task.trigger_mode_ref_id。', 'Constrains task.trigger_mode_ref_id.', 1, true),
('TASK_CONSTRAINT_FIELD', 'POINT_ROLE', '任务点角色', 'Task point role', NULL, '约束 task_point_item.point_role_ref_id。', 'Constrains task_point_item.point_role_ref_id.', 2, true),
('TASK_CONSTRAINT_FIELD', 'SAMPLE_MODE', '采样方式', 'Sample mode', NULL, '约束 task_point_item.sample_mode_ref_id。', 'Constrains task_point_item.sample_mode_ref_id.', 3, true),
('TASK_CONSTRAINT_FIELD', 'PROTOCOL_TYPE_ID', '协议类型标识', 'Protocol type identifier', NULL, '约束协议点位的 Type ID 等协议专属类型标识。', 'Constrains protocol-specific point type identifiers such as IEC104 Type ID.', 4, true),
('VALIDATION_OPERATOR', 'EQUALS', '等于', 'Equals', NULL, '条件字段等于指定值。', 'Condition field equals the specified value.', 1, true),
('VALIDATION_OPERATOR', 'NOT_EQUALS', '不等于', 'Not equals', NULL, '条件字段不等于指定值。', 'Condition field does not equal the specified value.', 2, true),
('PARAM_RULE_ACTION', 'REQUIRED', '必填', 'Required', NULL, '条件成立时目标参数必须存在或具有有效默认值。', 'The target parameter is required when the condition is true.', 1, true),
('PARAM_RULE_ACTION', 'FORBIDDEN', '禁止', 'Forbidden', NULL, '条件成立时目标参数不得显式配置。', 'The target parameter must not be explicitly configured when the condition is true.', 2, true),
('TASK_RUN_SCOPE', 'SINGLE', 'SINGLE', 'SINGLE', NULL, 'SINGLE', 'SINGLE', 1, true),
('TASK_RUN_SCOPE', 'BATCH', 'BATCH', 'BATCH', NULL, 'BATCH', 'BATCH', 2, true),
('TASK_RUN_STATUS', 'SUCCESS', 'SUCCESS', 'SUCCESS', NULL, 'SUCCESS', 'SUCCESS', 1, true),
('TASK_RUN_STATUS', 'FAILED', 'FAILED', 'FAILED', NULL, 'FAILED', 'FAILED', 2, true),
('TASK_RUN_STATUS', 'PARTIAL', 'PARTIAL', 'PARTIAL', NULL, 'PARTIAL', 'PARTIAL', 3, true),
('TOPO_ELEMENT_KIND', 'NODE', 'NODE', 'NODE', NULL, 'NODE', 'NODE', 1, true),
('TOPO_ELEMENT_KIND', 'INTERFACE', 'INTERFACE', 'INTERFACE', NULL, 'INTERFACE', 'INTERFACE', 2, true),
('TOPO_ELEMENT_KIND', 'EDGE', 'EDGE', 'EDGE', NULL, 'EDGE', 'EDGE', 3, true),
('ELEC_TOPO_ELEMENT_TYPE', 'GENERATION_UNIT', '发电单元', 'GENERATION_UNIT', NULL, '发电单元', 'GENERATION_UNIT', 1, true),
('ELEC_TOPO_ELEMENT_TYPE', 'TRANSFORMER', '变压器', 'TRANSFORMER', NULL, '变压器', 'TRANSFORMER', 2, true),
('ELEC_TOPO_ELEMENT_TYPE', 'BUSBAR', '母线', 'BUSBAR', NULL, '母线', 'BUSBAR', 3, true),
('ELEC_TOPO_ELEMENT_TYPE', 'FEEDER_BAY', '馈线间隔', 'FEEDER_BAY', NULL, '馈线间隔', 'FEEDER_BAY', 4, true),
('ELEC_TOPO_ELEMENT_TYPE', 'CIRCUIT_BREAKER', '断路器', 'CIRCUIT_BREAKER', NULL, '断路器', 'CIRCUIT_BREAKER', 5, true),
('ELEC_TOPO_ELEMENT_TYPE', 'DISCONNECTOR', '隔离开关', 'DISCONNECTOR', NULL, '隔离开关', 'DISCONNECTOR', 6, true),
('ELEC_TOPO_ELEMENT_TYPE', 'EARTHING_SWITCH', '接地开关', 'EARTHING_SWITCH', NULL, '接地开关', 'EARTHING_SWITCH', 7, true),
('ELEC_TOPO_ELEMENT_TYPE', 'GROUNDING_POINT', '接地点', 'GROUNDING_POINT', NULL, '接地点', 'GROUNDING_POINT', 8, true),
('ELEC_TOPO_ELEMENT_TYPE', 'CT', '电流互感器', 'CT', NULL, '电流互感器', 'CT', 9, true),
('ELEC_TOPO_ELEMENT_TYPE', 'PT', '电压互感器', 'PT', NULL, '电压互感器', 'PT', 10, true),
('ELEC_TOPO_ELEMENT_TYPE', 'CABLE', '电缆线路', 'CABLE', NULL, '电缆线路', 'CABLE', 11, true),
('ELEC_TOPO_ELEMENT_TYPE', 'LINE', '线路', 'LINE', NULL, '线路', 'LINE', 12, true),
('ELEC_TOPO_ELEMENT_TYPE', 'TERMINAL', '电气接口', 'TERMINAL', NULL, '电气接口', 'TERMINAL', 13, true),
('ELEC_TOPO_ELEMENT_TYPE', 'GRID', '电网节点', 'GRID', NULL, '电网节点', 'GRID', 14, true),
('COMM_TOPO_ELEMENT_TYPE', 'DEVICE', '通信设备', 'DEVICE', NULL, '通信设备', 'DEVICE', 1, true),
('COMM_TOPO_ELEMENT_TYPE', 'SERVER', '服务器', 'SERVER', NULL, '服务器', 'SERVER', 2, true),
('COMM_TOPO_ELEMENT_TYPE', 'NETWORK_SWITCH', '交换机', 'NETWORK_SWITCH', NULL, '交换机', 'NETWORK_SWITCH', 3, true),
('COMM_TOPO_ELEMENT_TYPE', 'FIREWALL', '防火墙', 'FIREWALL', NULL, '防火墙', 'FIREWALL', 4, true),
('COMM_TOPO_ELEMENT_TYPE', 'ROUTER', '路由器', 'ROUTER', NULL, '路由器', 'ROUTER', 5, true),
('COMM_TOPO_ELEMENT_TYPE', 'ETHERNET_PORT', '以太网端口', 'ETHERNET_PORT', NULL, '以太网端口', 'ETHERNET_PORT', 6, true),
('COMM_TOPO_ELEMENT_TYPE', 'FIBER_LINK', '光纤链路', 'FIBER_LINK', NULL, '光纤链路', 'FIBER_LINK', 7, true),
('COMM_TOPO_ELEMENT_TYPE', 'LOGICAL_LINK', '逻辑链路', 'LOGICAL_LINK', NULL, '逻辑链路', 'LOGICAL_LINK', 8, true),
('COMM_TOPO_ELEMENT_TYPE', 'EXTERNAL_SYSTEM', '外部系统', 'EXTERNAL_SYSTEM', NULL, '外部系统', 'EXTERNAL_SYSTEM', 9, true),
('DISPATCH_LEVEL', 'PROVINCIAL', '省调', 'PROVINCIAL', NULL, '省调', 'PROVINCIAL', 1, true),
('DISPATCH_LEVEL', 'REGIONAL', '地调', 'REGIONAL', NULL, '地调', 'REGIONAL', 2, true),
('DISPATCH_LEVEL', 'PLANT', '场站', 'PLANT', NULL, '场站', 'PLANT', 3, true),
('DISPATCH_CHANNEL_ROLE', 'PRIMARY', '主通道', 'PRIMARY', NULL, '主通道', 'PRIMARY', 1, true),
('DISPATCH_CHANNEL_ROLE', 'BACKUP', '备通道', 'BACKUP', NULL, '备通道', 'BACKUP', 2, true),
('PERMISSION_TYPE', 'FUNCTION', 'FUNCTION', 'FUNCTION', NULL, 'FUNCTION', 'FUNCTION', 1, true),
('PERMISSION_TYPE', 'DATA', 'DATA', 'DATA', NULL, 'DATA', 'DATA', 2, true),
('PERMISSION_TYPE', 'SYSTEM', 'SYSTEM', 'SYSTEM', NULL, 'SYSTEM', 'SYSTEM', 3, true),
('PERMISSION_CODE', 'ASSET_VIEW', 'ASSET_VIEW', 'ASSET_VIEW', NULL, 'ASSET_VIEW', 'ASSET_VIEW', 1, true),
('PERMISSION_CODE', 'ASSET_EDIT', 'ASSET_EDIT', 'ASSET_EDIT', NULL, 'ASSET_EDIT', 'ASSET_EDIT', 2, true),
('PERMISSION_CODE', 'PROTOCOL_VIEW', 'PROTOCOL_VIEW', 'PROTOCOL_VIEW', NULL, 'PROTOCOL_VIEW', 'PROTOCOL_VIEW', 3, true),
('PERMISSION_CODE', 'PROTOCOL_CONFIG_EDIT', 'PROTOCOL_CONFIG_EDIT', 'PROTOCOL_CONFIG_EDIT', NULL, 'PROTOCOL_CONFIG_EDIT', 'PROTOCOL_CONFIG_EDIT', 4, true),
('PERMISSION_CODE', 'POINT_TABLE_VIEW', 'POINT_TABLE_VIEW', 'POINT_TABLE_VIEW', NULL, 'POINT_TABLE_VIEW', 'POINT_TABLE_VIEW', 5, true),
('PERMISSION_CODE', 'POINT_TABLE_EDIT', 'POINT_TABLE_EDIT', 'POINT_TABLE_EDIT', NULL, 'POINT_TABLE_EDIT', 'POINT_TABLE_EDIT', 6, true),
('PERMISSION_CODE', 'TASK_VIEW', 'TASK_VIEW', 'TASK_VIEW', NULL, 'TASK_VIEW', 'TASK_VIEW', 7, true),
('PERMISSION_CODE', 'TASK_EDIT', 'TASK_EDIT', 'TASK_EDIT', NULL, 'TASK_EDIT', 'TASK_EDIT', 8, true),
('PERMISSION_CODE', 'TOPO_VIEW', 'TOPO_VIEW', 'TOPO_VIEW', NULL, 'TOPO_VIEW', 'TOPO_VIEW', 9, true),
('PERMISSION_CODE', 'TOPO_EDIT', 'TOPO_EDIT', 'TOPO_EDIT', NULL, 'TOPO_EDIT', 'TOPO_EDIT', 10, true),
('PERMISSION_CODE', 'DISPATCH_VIEW', 'DISPATCH_VIEW', 'DISPATCH_VIEW', NULL, 'DISPATCH_VIEW', 'DISPATCH_VIEW', 11, true),
('PERMISSION_CODE', 'DISPATCH_CONFIG_EDIT', 'DISPATCH_CONFIG_EDIT', 'DISPATCH_CONFIG_EDIT', NULL, 'DISPATCH_CONFIG_EDIT', 'DISPATCH_CONFIG_EDIT', 12, true),
('PERMISSION_CODE', 'QUALITY_VIEW', 'QUALITY_VIEW', 'QUALITY_VIEW', NULL, 'QUALITY_VIEW', 'QUALITY_VIEW', 13, true),
('PERMISSION_CODE', 'QUALITY_DOMAIN_EDIT', 'QUALITY_DOMAIN_EDIT', 'QUALITY_DOMAIN_EDIT', NULL, 'QUALITY_DOMAIN_EDIT', 'QUALITY_DOMAIN_EDIT', 14, true),
('PERMISSION_CODE', 'USER_VIEW', 'USER_VIEW', 'USER_VIEW', NULL, 'USER_VIEW', 'USER_VIEW', 15, true),
('PERMISSION_CODE', 'USER_EDIT', 'USER_EDIT', 'USER_EDIT', NULL, 'USER_EDIT', 'USER_EDIT', 16, true),
('PERMISSION_CODE', 'ROLE_VIEW', 'ROLE_VIEW', 'ROLE_VIEW', NULL, 'ROLE_VIEW', 'ROLE_VIEW', 17, true),
('PERMISSION_CODE', 'ROLE_EDIT', 'ROLE_EDIT', 'ROLE_EDIT', NULL, 'ROLE_EDIT', 'ROLE_EDIT', 18, true),
('PERMISSION_CODE', 'AUDIT_VIEW', 'AUDIT_VIEW', 'AUDIT_VIEW', NULL, 'AUDIT_VIEW', 'AUDIT_VIEW', 19, true),
('PERMISSION_CODE', 'SYSTEM_CONFIG_VIEW', 'SYSTEM_CONFIG_VIEW', 'SYSTEM_CONFIG_VIEW', NULL, 'SYSTEM_CONFIG_VIEW', 'SYSTEM_CONFIG_VIEW', 20, true),
('PERMISSION_CODE', 'SYSTEM_CONFIG_EDIT', 'SYSTEM_CONFIG_EDIT', 'SYSTEM_CONFIG_EDIT', NULL, 'SYSTEM_CONFIG_EDIT', 'SYSTEM_CONFIG_EDIT', 21, true)
ON CONFLICT (ref_type, code) DO NOTHING;



INSERT INTO ref_code(ref_type, code, name_zh, name_en, abbr_en, description_zh, description_en, sort_order, enabled) VALUES
('MODBUS_REGISTER_AREA','COIL','线圈区','COIL',NULL,'Modbus 0x 线圈区。','Modbus coil area.',1,true),
('MODBUS_REGISTER_AREA','DISCRETE_INPUT','离散输入区','DISCRETE_INPUT',NULL,'Modbus 1x 离散输入区。','Modbus discrete input area.',2,true),
('MODBUS_REGISTER_AREA','INPUT_REGISTER','输入寄存器区','INPUT_REGISTER',NULL,'Modbus 3x 输入寄存器区。','Modbus input register area.',3,true),
('MODBUS_REGISTER_AREA','HOLDING_REGISTER','保持寄存器区','HOLDING_REGISTER',NULL,'Modbus 4x 保持寄存器区。','Modbus holding register area.',4,true),
('IEC101_COT','INTERROGATED','总召响应','INTERROGATED',NULL,'IEC101 总召响应传送原因。','IEC101 interrogation response COT.',1,true),
('IEC101_COT','SPONTANEOUS','突发上送','SPONTANEOUS',NULL,'IEC101 突发上送传送原因。','IEC101 spontaneous COT.',2,true),
('IEC101_COT','CYCLIC','周期上送','CYCLIC',NULL,'IEC101 周期上送传送原因。','IEC101 cyclic COT.',3,true),
('IEC101_COT','ACTIVATION','激活命令','ACTIVATION',NULL,'IEC101 命令激活传送原因。','IEC101 activation COT.',4,true),
('IEC104_COT','INTERROGATED','总召响应','INTERROGATED',NULL,'IEC104 总召响应传送原因。','IEC104 interrogation response COT.',1,true),
('IEC104_COT','SPONTANEOUS','突发上送','SPONTANEOUS',NULL,'IEC104 突发上送传送原因。','IEC104 spontaneous COT.',2,true),
('IEC104_COT','CYCLIC','周期上送','CYCLIC',NULL,'IEC104 周期上送传送原因。','IEC104 cyclic COT.',3,true),
('IEC104_COT','ACTIVATION','激活命令','ACTIVATION',NULL,'IEC104 命令激活传送原因。','IEC104 activation COT.',4,true),
('IEC104_COT','BACKGROUND','背景扫描','BACKGROUND',NULL,'子站按后台扫描策略低频刷新当前值。','Controlled station sends a low-priority background refresh.',5,true),
('IEC104_COT','INTERROGATED_BY_STATION','站总召响应','INTERROGATED_BY_STATION',NULL,'QOI=20 的数据响应传送原因。','Data response COT for QOI=20.',6,true),
('IEC104_COT','ACTIVATION_CONFIRMATION','激活确认','ACTIVATION_CONFIRMATION',NULL,'对激活请求的确认。','Confirmation of an activation request.',7,true),
('IEC104_COT','ACTIVATION_TERMINATION','激活终止','ACTIVATION_TERMINATION',NULL,'激活流程执行结束。','Termination of an activation procedure.',8,true),
('IEC104_COT','INTERROGATED_BY_GROUP_1','第1组召唤响应','INTERROGATED_BY_GROUP_1',NULL,'QOI=21 的数据响应传送原因。','Data response COT for QOI=21.',9,true),
('IEC104_COT','INTERROGATED_BY_GROUP_2','第2组召唤响应','INTERROGATED_BY_GROUP_2',NULL,'QOI=22 的数据响应传送原因。','Data response COT for QOI=22.',10,true),
('IEC104_COT','INTERROGATED_BY_GROUP_3','第3组召唤响应','INTERROGATED_BY_GROUP_3',NULL,'QOI=23 的数据响应传送原因。','Data response COT for QOI=23.',11,true),
('IEC104_COT','INTERROGATED_BY_GROUP_4','第4组召唤响应','INTERROGATED_BY_GROUP_4',NULL,'QOI=24 的数据响应传送原因。','Data response COT for QOI=24.',12,true),
('IEC104_COT','INTERROGATED_BY_GROUP_5','第5组召唤响应','INTERROGATED_BY_GROUP_5',NULL,'QOI=25 的数据响应传送原因。','Data response COT for QOI=25.',13,true),
('IEC104_COT','INTERROGATED_BY_GROUP_6','第6组召唤响应','INTERROGATED_BY_GROUP_6',NULL,'QOI=26 的数据响应传送原因。','Data response COT for QOI=26.',14,true),
('IEC104_COT','INTERROGATED_BY_GROUP_7','第7组召唤响应','INTERROGATED_BY_GROUP_7',NULL,'QOI=27 的数据响应传送原因。','Data response COT for QOI=27.',15,true),
('IEC104_COT','INTERROGATED_BY_GROUP_8','第8组召唤响应','INTERROGATED_BY_GROUP_8',NULL,'QOI=28 的数据响应传送原因。','Data response COT for QOI=28.',16,true),
('IEC104_COT','INTERROGATED_BY_GROUP_9','第9组召唤响应','INTERROGATED_BY_GROUP_9',NULL,'QOI=29 的数据响应传送原因。','Data response COT for QOI=29.',17,true),
('IEC104_COT','INTERROGATED_BY_GROUP_10','第10组召唤响应','INTERROGATED_BY_GROUP_10',NULL,'QOI=30 的数据响应传送原因。','Data response COT for QOI=30.',18,true),
('IEC104_COT','INTERROGATED_BY_GROUP_11','第11组召唤响应','INTERROGATED_BY_GROUP_11',NULL,'QOI=31 的数据响应传送原因。','Data response COT for QOI=31.',19,true),
('IEC104_COT','INTERROGATED_BY_GROUP_12','第12组召唤响应','INTERROGATED_BY_GROUP_12',NULL,'QOI=32 的数据响应传送原因。','Data response COT for QOI=32.',20,true),
('IEC104_COT','INTERROGATED_BY_GROUP_13','第13组召唤响应','INTERROGATED_BY_GROUP_13',NULL,'QOI=33 的数据响应传送原因。','Data response COT for QOI=33.',21,true),
('IEC104_COT','INTERROGATED_BY_GROUP_14','第14组召唤响应','INTERROGATED_BY_GROUP_14',NULL,'QOI=34 的数据响应传送原因。','Data response COT for QOI=34.',22,true),
('IEC104_COT','INTERROGATED_BY_GROUP_15','第15组召唤响应','INTERROGATED_BY_GROUP_15',NULL,'QOI=35 的数据响应传送原因。','Data response COT for QOI=35.',23,true),
('IEC104_COT','INTERROGATED_BY_GROUP_16','第16组召唤响应','INTERROGATED_BY_GROUP_16',NULL,'QOI=36 的数据响应传送原因。','Data response COT for QOI=36.',24,true),
('PHASE','A','A相','A',NULL,'A 相。','Phase A.',1,true),
('PHASE','B','B相','B',NULL,'B 相。','Phase B.',2,true),
('PHASE','C','C相','C',NULL,'C 相。','Phase C.',3,true),
('PHASE','N','中性线','N',NULL,'中性线。','Neutral.',4,true),
('SV_QUANTITY','CURRENT','电流采样','CURRENT',NULL,'SV 电流采样量。','SV current quantity.',1,true),
('SV_QUANTITY','VOLTAGE','电压采样','VOLTAGE',NULL,'SV 电压采样量。','SV voltage quantity.',2,true)
ON CONFLICT (ref_type, code) DO NOTHING;

-- v1.4.0: enrich ref_code descriptions with meaning/source/usage/impact.
UPDATE ref_code
SET description_zh = '含义：' || name_zh || '。来源：' ||
    CASE
      WHEN ref_type IN ('PROTOCOL','MODBUS_FUNCTION_CODE','IEC101_TYPE_ID','IEC104_TYPE_ID','IEC61850_FC','IEC61850_CDC','HTTP_METHOD','BYTE_ORDER','WORD_ORDER') THEN '协议标准或协议驱动包约定'
      WHEN ref_type IN ('TASK_STATUS','PROTOCOL_ROLE','TASK_POINT_ROLE','SAMPLE_MODE') THEN 'BlueCrystal 任务调度与点表治理抽象'
      WHEN ref_type IN ('ASSET_TYPE','ASSET_LIFECYCLE_STATUS','WORK_TEAM_TYPE','ORG_NATURE','POWER_PLANT_TYPE') THEN '风光储电场资产台账与组织管理工程约定'
      ELSE 'BlueCrystal 数据治理参考数据'
    END || '。用途：被字段 ref_type=' || ref_type || '、code=' || code || ' 引用，用于约束 DDL 外键、DML 样例、视图展示和驱动参数解释。影响：误用会导致资产分类、协议驱动调用、任务调度、点值解析或权限展示口径错误。',
    description_en = 'Meaning: ' || name_en || '. Source: ' ||
    CASE
      WHEN ref_type IN ('PROTOCOL','MODBUS_FUNCTION_CODE','IEC101_TYPE_ID','IEC104_TYPE_ID','IEC61850_FC','IEC61850_CDC','HTTP_METHOD','BYTE_ORDER','WORD_ORDER') THEN 'protocol standards or protocol driver conventions'
      WHEN ref_type IN ('TASK_STATUS','PROTOCOL_ROLE','TASK_POINT_ROLE','SAMPLE_MODE') THEN 'BlueCrystal task scheduling and point-governance abstraction'
      WHEN ref_type IN ('ASSET_TYPE','ASSET_LIFECYCLE_STATUS','WORK_TEAM_TYPE','ORG_NATURE','POWER_PLANT_TYPE') THEN 'hybrid power plant asset and organization engineering convention'
      ELSE 'BlueCrystal reference data'
    END || '. Usage: referenced by ref_type=' || ref_type || ', code=' || code || ' to constrain foreign keys, sample data, views, and driver parameter interpretation. Impact: misuse may break asset classification, protocol driver dispatch, task scheduling, point decoding, or permission display.'
WHERE enabled = TRUE;

UPDATE ref_code SET description_zh = '含义：Modbus 读线圈功能码 FC01，用于读取可读线圈布尔量。来源：Modbus Application Protocol。用途：cfg_modbus_point_item.function_code_ref_id，驱动 facade 据此调用 pymodbus.read_coils。影响：误配会导致后端读取错误地址区。', description_en = 'Meaning: Modbus FC01 Read Coils. Source: Modbus Application Protocol. Usage: cfg_modbus_point_item.function_code_ref_id; the driver facade dispatches to pymodbus.read_coils. Impact: wrong mapping reads the wrong address area.' WHERE ref_type='MODBUS_FUNCTION_CODE' AND code='READ_COILS';
UPDATE ref_code SET description_zh = '含义：Modbus 读离散输入功能码 FC02，用于读取只读遥信输入。来源：Modbus Application Protocol。用途：cfg_modbus_point_item.function_code_ref_id，驱动 facade 据此调用 pymodbus.read_discrete_inputs。影响：误配会导致遥信读取错误。', description_en = 'Meaning: Modbus FC02 Read Discrete Inputs. Source: Modbus Application Protocol. Usage: cfg_modbus_point_item.function_code_ref_id; the driver facade dispatches to pymodbus.read_discrete_inputs. Impact: wrong mapping breaks digital input reads.' WHERE ref_type='MODBUS_FUNCTION_CODE' AND code='READ_DISCRETE_INPUTS';
UPDATE ref_code SET description_zh = '含义：Modbus 读保持寄存器功能码 FC03，用于读取可读写寄存器、设点或参数。来源：Modbus Application Protocol。用途：cfg_modbus_point_item.function_code_ref_id，驱动 facade 据此调用 pymodbus.read_holding_registers。影响：误配会导致遥测或设点解析错误。', description_en = 'Meaning: Modbus FC03 Read Holding Registers. Source: Modbus Application Protocol. Usage: cfg_modbus_point_item.function_code_ref_id; the driver facade dispatches to pymodbus.read_holding_registers. Impact: wrong mapping breaks telemetry or setpoint decoding.' WHERE ref_type='MODBUS_FUNCTION_CODE' AND code='READ_HOLDING_REGISTERS';
UPDATE ref_code SET description_zh = '含义：Modbus 读输入寄存器功能码 FC04，用于读取只读模拟量。来源：Modbus Application Protocol。用途：cfg_modbus_point_item.function_code_ref_id，驱动 facade 据此调用 pymodbus.read_input_registers。影响：误配会导致模拟量读取错误。', description_en = 'Meaning: Modbus FC04 Read Input Registers. Source: Modbus Application Protocol. Usage: cfg_modbus_point_item.function_code_ref_id; the driver facade dispatches to pymodbus.read_input_registers. Impact: wrong mapping breaks analog input reads.' WHERE ref_type='MODBUS_FUNCTION_CODE' AND code='READ_INPUT_REGISTERS';

-- 2. Standard measurement semantics and required semantic reference codes
-- 4. cfg_measurement_semantic: 396 records with meaningful engineering names and matched units

-- 4.0 additional semantic reference codes required by meaningful engineering semantics
INSERT INTO ref_code(ref_type, code, name_zh, name_en, abbr_en, description_zh, description_en, sort_order, enabled) VALUES
('UNIT', 'N_M', '牛米', 'newton metre', 'N·m', '扭矩单位，用于风机叶轮、发电机和传动链扭矩。', 'Torque unit for rotor, generator, and drivetrain torque.', 24, true),
('UNIT', 'MM_S', '毫米每秒', 'millimetre per second', 'mm/s', '振动速度单位。', 'Vibration velocity unit.', 25, true),
('UNIT', 'M_S2', '米每二次方秒', 'metre per second squared', 'm/s²', '振动加速度单位。', 'Vibration acceleration unit.', 26, true),
('PHYSICAL_QUANTITY_CATEGORY', 'TORQUE', '扭矩', 'torque', NULL, '扭矩类物理量。', 'Torque physical quantity category.', 18, true),
('PHYSICAL_QUANTITY_CATEGORY', 'POSITION', '位置/角度', 'position or angle', NULL, '位置、角度、档位类物理量。', 'Position, angle, or tap position physical quantity category.', 19, true),
('PHYSICAL_QUANTITY_CATEGORY', 'VIBRATION', '振动', 'vibration', NULL, '振动速度、振动加速度等物理量。', 'Vibration velocity and acceleration category.', 20, true);

INSERT INTO cfg_measurement_semantic(measurement_identifier, standard_source, logical_node_code, data_object_name, cdc_code, name_zh, name_en, physical_quantity_category_ref_id, standard_unit_ref_id, standard_data_type_ref_id, description_zh, description_en) VALUES
('gbt30966_wppd_001', 'GB/T 30966.2-2022', 'WPPD', 'OpSt', 'SPS', '风电场运行状态', 'Wind power plant operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风电场运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind power plant operating status.'),
('gbt30966_wppd_002', 'GB/T 30966.2-2022', 'WPPD', 'TotW', 'MV', '风电场有功功率', 'Wind power plant active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风电场有功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind power plant active power.'),
('gbt30966_wppd_003', 'GB/T 30966.2-2022', 'WPPD', 'TotVAr', 'MV', '风电场无功功率', 'Wind power plant reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风电场无功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind power plant reactive power.'),
('gbt30966_wppd_004', 'GB/T 30966.2-2022', 'WPPD', 'TotWh', 'MV', '风电场累计发电量', 'Wind power plant accumulated energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风电场累计发电量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind power plant accumulated energy.'),
('gbt30966_wtur_001', 'GB/T 30966.2-2022', 'WTUR', 'OpSt', 'SPS', '风机运行状态', 'Wind turbine operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine operating status.'),
('gbt30966_wtur_002', 'GB/T 30966.2-2022', 'WTUR', 'ComSt', 'SPS', '风机通信状态', 'Wind turbine communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机通信状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine communication status.'),
('gbt30966_wtur_003', 'GB/T 30966.2-2022', 'WTUR', 'GridSt', 'SPS', '风机并网状态', 'Wind turbine grid connection status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机并网状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine grid connection status.'),
('gbt30966_wtur_004', 'GB/T 30966.2-2022', 'WTUR', 'FltSt', 'SPS', '风机故障状态', 'Wind turbine fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine fault status.'),
('gbt30966_wtur_005', 'GB/T 30966.2-2022', 'WTUR', 'AlmSt', 'SPS', '风机告警状态', 'Wind turbine alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine alarm status.'),
('gbt30966_wtur_006', 'GB/T 30966.2-2022', 'WTUR', 'W', 'MV', '风机有功功率', 'Wind turbine active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机有功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine active power.'),
('gbt30966_wtur_007', 'GB/T 30966.2-2022', 'WTUR', 'VAr', 'MV', '风机无功功率', 'Wind turbine reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机无功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine reactive power.'),
('gbt30966_wtur_008', 'GB/T 30966.2-2022', 'WTUR', 'Wh', 'MV', '风机累计发电量', 'Wind turbine accumulated energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机累计发电量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine accumulated energy.'),
('gbt30966_wtur_009', 'GB/T 30966.2-2022', 'WTUR', 'DWh', 'MV', '风机日发电量', 'Wind turbine daily energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机日发电量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine daily energy.'),
('gbt30966_wtur_010', 'GB/T 30966.2-2022', 'WTUR', 'Avl', 'MV', '风机可利用率', 'Wind turbine availability', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机可利用率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine availability.'),
('gbt30966_wtur_011', 'GB/T 30966.2-2022', 'WTUR', 'CtlMod', 'INS', '风机控制模式', 'Wind turbine control mode', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机控制模式。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine control mode.'),
('gbt30966_wtur_012', 'GB/T 30966.2-2022', 'WTUR', 'StrStpCmd', 'SPC', '风机启停命令', 'Wind turbine start stop command', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMAND'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机启停命令。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine start stop command.'),
('gbt30966_wtur_013', 'GB/T 30966.2-2022', 'WTUR', 'WLimSet', 'APC', '风机限功率设定', 'Wind turbine active power limit setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机限功率设定。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine active power limit setpoint.'),
('gbt30966_wtur_014', 'GB/T 30966.2-2022', 'WTUR', 'PF', 'MV', '风机功率因数', 'Wind turbine power factor', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机功率因数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine power factor.'),
('gbt30966_wtur_015', 'GB/T 30966.2-2022', 'WTUR', 'Hz', 'MV', '风机电网频率', 'Wind turbine grid frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机电网频率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine grid frequency.'),
('gbt30966_wtur_016', 'GB/T 30966.2-2022', 'WTUR', 'NacTmp', 'MV', '风机机舱温度', 'Wind turbine nacelle temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机机舱温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine nacelle temperature.'),
('gbt30966_wtur_017', 'GB/T 30966.2-2022', 'WTUR', 'AmbTmp', 'MV', '风机环境温度', 'Wind turbine ambient temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机环境温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine ambient temperature.'),
('gbt30966_wrot_001', 'GB/T 30966.2-2022', 'WROT', 'RotSpd', 'MV', '转子转速', 'Rotor speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：转子转速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Rotor speed.'),
('gbt30966_wrot_002', 'GB/T 30966.2-2022', 'WROT', 'RotAzm', 'MV', '转子方位角', 'Rotor azimuth angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：转子方位角。', 'GB/T 30966.2-2022 wind information model engineering semantic: Rotor azimuth angle.'),
('gbt30966_wrot_003', 'GB/T 30966.2-2022', 'WROT', 'HubSpd', 'MV', '轮毂转速', 'Hub speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：轮毂转速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Hub speed.'),
('gbt30966_wrot_004', 'GB/T 30966.2-2022', 'WROT', 'RotTrq', 'MV', '叶轮转矩', 'Rotor torque', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TORQUE'), ref_code_id('UNIT','N_M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶轮转矩。', 'GB/T 30966.2-2022 wind information model engineering semantic: Rotor torque.'),
('gbt30966_wrot_005', 'GB/T 30966.2-2022', 'WROT', 'RotW', 'MV', '叶轮气动功率', 'Rotor aerodynamic power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶轮气动功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Rotor aerodynamic power.'),
('gbt30966_wrot_006', 'GB/T 30966.2-2022', 'WROT', 'BldAPit', 'MV', '叶片A桨距角', 'Blade A pitch angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片A桨距角。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade A pitch angle.'),
('gbt30966_wrot_007', 'GB/T 30966.2-2022', 'WROT', 'BldBPit', 'MV', '叶片B桨距角', 'Blade B pitch angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片B桨距角。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade B pitch angle.'),
('gbt30966_wrot_008', 'GB/T 30966.2-2022', 'WROT', 'BldCPit', 'MV', '叶片C桨距角', 'Blade C pitch angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片C桨距角。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade C pitch angle.'),
('gbt30966_wrot_009', 'GB/T 30966.2-2022', 'WROT', 'BldALd', 'MV', '叶片A根部载荷', 'Blade A root load', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TORQUE'), ref_code_id('UNIT','N_M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片A根部载荷。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade A root load.'),
('gbt30966_wrot_010', 'GB/T 30966.2-2022', 'WROT', 'BldBLd', 'MV', '叶片B根部载荷', 'Blade B root load', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TORQUE'), ref_code_id('UNIT','N_M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片B根部载荷。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade B root load.'),
('gbt30966_wrot_011', 'GB/T 30966.2-2022', 'WROT', 'BldCLd', 'MV', '叶片C根部载荷', 'Blade C root load', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TORQUE'), ref_code_id('UNIT','N_M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：叶片C根部载荷。', 'GB/T 30966.2-2022 wind information model engineering semantic: Blade C root load.'),
('gbt30966_wtrm_001', 'GB/T 30966.2-2022', 'WTRM', 'OpSt', 'SPS', '传动链运行状态', 'Drive train operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：传动链运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Drive train operating status.'),
('gbt30966_wtrm_002', 'GB/T 30966.2-2022', 'WTRM', 'LSSSpd', 'MV', '低速轴转速', 'Low speed shaft speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：低速轴转速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Low speed shaft speed.'),
('gbt30966_wtrm_003', 'GB/T 30966.2-2022', 'WTRM', 'HSSSpd', 'MV', '高速轴转速', 'High speed shaft speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：高速轴转速。', 'GB/T 30966.2-2022 wind information model engineering semantic: High speed shaft speed.'),
('gbt30966_wtrm_004', 'GB/T 30966.2-2022', 'WTRM', 'GbOilTmp', 'MV', '齿轮箱油温', 'Gearbox oil temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：齿轮箱油温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Gearbox oil temperature.'),
('gbt30966_wtrm_005', 'GB/T 30966.2-2022', 'WTRM', 'GbBrgTmp', 'MV', '齿轮箱轴承温度', 'Gearbox bearing temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：齿轮箱轴承温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Gearbox bearing temperature.'),
('gbt30966_wtrm_006', 'GB/T 30966.2-2022', 'WTRM', 'GbOilPres', 'MV', '齿轮箱油压', 'Gearbox oil pressure', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：齿轮箱油压。', 'GB/T 30966.2-2022 wind information model engineering semantic: Gearbox oil pressure.'),
('gbt30966_wtrm_007', 'GB/T 30966.2-2022', 'WTRM', 'GbOilLev', 'MV', '齿轮箱油位', 'Gearbox oil level', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：齿轮箱油位。', 'GB/T 30966.2-2022 wind information model engineering semantic: Gearbox oil level.'),
('gbt30966_wtrm_008', 'GB/T 30966.2-2022', 'WTRM', 'MainBrgTmp', 'MV', '主轴承温度', 'Main bearing temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：主轴承温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Main bearing temperature.'),
('gbt30966_wtrm_009', 'GB/T 30966.2-2022', 'WTRM', 'MainVibVel', 'MV', '主轴振动速度', 'Main shaft vibration velocity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','MM_S'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：主轴振动速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Main shaft vibration velocity.'),
('gbt30966_wtrm_010', 'GB/T 30966.2-2022', 'WTRM', 'MainVibAcc', 'MV', '主轴振动加速度', 'Main shaft vibration acceleration', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','M_S2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：主轴振动加速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Main shaft vibration acceleration.'),
('gbt30966_wtrm_011', 'GB/T 30966.2-2022', 'WTRM', 'CplTmp', 'MV', '联轴器温度', 'Coupling temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：联轴器温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Coupling temperature.'),
('gbt30966_wtrm_012', 'GB/T 30966.2-2022', 'WTRM', 'BrkPres', 'MV', '刹车压力', 'Brake pressure', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：刹车压力。', 'GB/T 30966.2-2022 wind information model engineering semantic: Brake pressure.'),
('gbt30966_wtrm_013', 'GB/T 30966.2-2022', 'WTRM', 'BrkSt', 'SPS', '刹车状态', 'Brake status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：刹车状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Brake status.'),
('gbt30966_wtrm_014', 'GB/T 30966.2-2022', 'WTRM', 'LubPumpSt', 'SPS', '润滑泵状态', 'Lubrication pump status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：润滑泵状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Lubrication pump status.'),
('gbt30966_wtrm_015', 'GB/T 30966.2-2022', 'WTRM', 'HydPres', 'MV', '液压站压力', 'Hydraulic station pressure', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：液压站压力。', 'GB/T 30966.2-2022 wind information model engineering semantic: Hydraulic station pressure.'),
('gbt30966_wtrm_016', 'GB/T 30966.2-2022', 'WTRM', 'HydOilTmp', 'MV', '液压站油温', 'Hydraulic oil temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：液压站油温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Hydraulic oil temperature.'),
('gbt30966_wtrm_017', 'GB/T 30966.2-2022', 'WTRM', 'FltSt', 'SPS', '传动链故障状态', 'Drive train fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：传动链故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Drive train fault status.'),
('gbt30966_wtrm_018', 'GB/T 30966.2-2022', 'WTRM', 'MntSt', 'SPS', '传动链维护状态', 'Drive train maintenance status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：传动链维护状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Drive train maintenance status.'),
('gbt30966_wgen_001', 'GB/T 30966.2-2022', 'WGEN', 'OpSt', 'SPS', '发电机运行状态', 'Generator operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator operating status.'),
('gbt30966_wgen_002', 'GB/T 30966.2-2022', 'WGEN', 'W', 'MV', '发电机有功功率', 'Generator active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机有功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator active power.'),
('gbt30966_wgen_003', 'GB/T 30966.2-2022', 'WGEN', 'VAr', 'MV', '发电机无功功率', 'Generator reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机无功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator reactive power.'),
('gbt30966_wgen_004', 'GB/T 30966.2-2022', 'WGEN', 'Vol', 'MV', '发电机电压', 'Generator voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机电压。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator voltage.'),
('gbt30966_wgen_005', 'GB/T 30966.2-2022', 'WGEN', 'Amp', 'MV', '发电机电流', 'Generator current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator current.'),
('gbt30966_wgen_006', 'GB/T 30966.2-2022', 'WGEN', 'Hz', 'MV', '发电机频率', 'Generator frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机频率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator frequency.'),
('gbt30966_wgen_007', 'GB/T 30966.2-2022', 'WGEN', 'GnSpd', 'MV', '发电机转速', 'Generator speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机转速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator speed.'),
('gbt30966_wgen_008', 'GB/T 30966.2-2022', 'WGEN', 'GnTrq', 'MV', '发电机转矩', 'Generator torque', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TORQUE'), ref_code_id('UNIT','N_M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机转矩。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator torque.'),
('gbt30966_wgen_009', 'GB/T 30966.2-2022', 'WGEN', 'StaATmp', 'MV', '定子A相温度', 'Stator phase A temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：定子A相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Stator phase A temperature.'),
('gbt30966_wgen_010', 'GB/T 30966.2-2022', 'WGEN', 'StaBTmp', 'MV', '定子B相温度', 'Stator phase B temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：定子B相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Stator phase B temperature.'),
('gbt30966_wgen_011', 'GB/T 30966.2-2022', 'WGEN', 'StaCTmp', 'MV', '定子C相温度', 'Stator phase C temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：定子C相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Stator phase C temperature.'),
('gbt30966_wgen_012', 'GB/T 30966.2-2022', 'WGEN', 'FrBrgTmp', 'MV', '发电机轴承前端温度', 'Generator front bearing temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机轴承前端温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator front bearing temperature.'),
('gbt30966_wgen_013', 'GB/T 30966.2-2022', 'WGEN', 'RrBrgTmp', 'MV', '发电机轴承后端温度', 'Generator rear bearing temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机轴承后端温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator rear bearing temperature.'),
('gbt30966_wgen_014', 'GB/T 30966.2-2022', 'WGEN', 'CoolTmp', 'MV', '发电机冷却水温', 'Generator cooling water temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机冷却水温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator cooling water temperature.'),
('gbt30966_wgen_015', 'GB/T 30966.2-2022', 'WGEN', 'InsRes', 'MV', '发电机绝缘电阻', 'Generator insulation resistance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机绝缘电阻。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator insulation resistance.'),
('gbt30966_wgen_016', 'GB/T 30966.2-2022', 'WGEN', 'FltSt', 'SPS', '发电机故障状态', 'Generator fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator fault status.'),
('gbt30966_wgen_017', 'GB/T 30966.2-2022', 'WGEN', 'AlmSt', 'SPS', '发电机告警状态', 'Generator alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：发电机告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Generator alarm status.'),
('gbt30966_wcnv_001', 'GB/T 30966.2-2022', 'WCNV', 'OpSt', 'SPS', '变流器运行状态', 'Converter operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter operating status.'),
('gbt30966_wcnv_002', 'GB/T 30966.2-2022', 'WCNV', 'GridW', 'MV', '网侧有功功率', 'Grid-side active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：网侧有功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Grid-side active power.'),
('gbt30966_wcnv_003', 'GB/T 30966.2-2022', 'WCNV', 'WCNV_003', 'MV', '网侧无功功率', 'GridVAr', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：网侧无功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: GridVAr.'),
('gbt30966_wcnv_004', 'GB/T 30966.2-2022', 'WCNV', 'DcVol', 'MV', '直流母线电压', 'DC link voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：直流母线电压。', 'GB/T 30966.2-2022 wind information model engineering semantic: DC link voltage.'),
('gbt30966_wcnv_005', 'GB/T 30966.2-2022', 'WCNV', 'DcAmp', 'MV', '直流母线电流', 'DC link current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：直流母线电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: DC link current.'),
('gbt30966_wcnv_006', 'GB/T 30966.2-2022', 'WCNV', 'AcVol', 'MV', '交流侧电压', 'AC side voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：交流侧电压。', 'GB/T 30966.2-2022 wind information model engineering semantic: AC side voltage.'),
('gbt30966_wcnv_007', 'GB/T 30966.2-2022', 'WCNV', 'AcAmp', 'MV', '交流侧电流', 'AC side current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：交流侧电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: AC side current.'),
('gbt30966_wcnv_008', 'GB/T 30966.2-2022', 'WCNV', 'Hz', 'MV', '变流器频率', 'Converter frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器频率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter frequency.'),
('gbt30966_wcnv_009', 'GB/T 30966.2-2022', 'WCNV', 'IGBTATmp', 'MV', 'IGBT A相温度', 'IGBT phase A temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：IGBT A相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: IGBT phase A temperature.'),
('gbt30966_wcnv_010', 'GB/T 30966.2-2022', 'WCNV', 'WCNV_010', 'MV', 'IGBT B相温度', 'IGBTBTmp', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：IGBT B相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: IGBTBTmp.'),
('gbt30966_wcnv_011', 'GB/T 30966.2-2022', 'WCNV', 'WCNV_011', 'MV', 'IGBT C相温度', 'IGBTCTmp', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：IGBT C相温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: IGBTCTmp.'),
('gbt30966_wcnv_012', 'GB/T 30966.2-2022', 'WCNV', 'CoolTmp', 'MV', '变流器冷却水温', 'Converter cooling water temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器冷却水温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter cooling water temperature.'),
('gbt30966_wcnv_013', 'GB/T 30966.2-2022', 'WCNV', 'CabTmp', 'MV', '变流器柜内温度', 'Converter cabinet temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器柜内温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter cabinet temperature.'),
('gbt30966_wcnv_014', 'GB/T 30966.2-2022', 'WCNV', 'PF', 'MV', '变流器功率因数', 'Converter power factor', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器功率因数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter power factor.'),
('gbt30966_wcnv_015', 'GB/T 30966.2-2022', 'WCNV', 'WLimSet', 'APC', '变流器限功率设定', 'Converter power limit setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器限功率设定。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter power limit setpoint.'),
('gbt30966_wcnv_016', 'GB/T 30966.2-2022', 'WCNV', 'FltSt', 'SPS', '变流器故障状态', 'Converter fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter fault status.'),
('gbt30966_wcnv_017', 'GB/T 30966.2-2022', 'WCNV', 'AlmSt', 'SPS', '变流器告警状态', 'Converter alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter alarm status.'),
('gbt30966_wcnv_018', 'GB/T 30966.2-2022', 'WCNV', 'RdySt', 'SPS', '变流器就绪状态', 'Converter ready status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器就绪状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter ready status.'),
('gbt30966_wcnv_019', 'GB/T 30966.2-2022', 'WCNV', 'ComSt', 'SPS', '变流器通信状态', 'Converter communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：变流器通信状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Converter communication status.'),
('gbt30966_wtrf_001', 'GB/T 30966.2-2022', 'WTRF', 'OpSt', 'SPS', '箱变运行状态', 'Transformer operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer operating status.'),
('gbt30966_wtrf_002', 'GB/T 30966.2-2022', 'WTRF', 'HVVol', 'MV', '箱变高压侧电压', 'Transformer HV voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变高压侧电压。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer HV voltage.'),
('gbt30966_wtrf_003', 'GB/T 30966.2-2022', 'WTRF', 'LVVol', 'MV', '箱变低压侧电压', 'Transformer LV voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变低压侧电压。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer LV voltage.'),
('gbt30966_wtrf_004', 'GB/T 30966.2-2022', 'WTRF', 'HVAmp', 'MV', '箱变高压侧电流', 'Transformer HV current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变高压侧电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer HV current.'),
('gbt30966_wtrf_005', 'GB/T 30966.2-2022', 'WTRF', 'LVAmp', 'MV', '箱变低压侧电流', 'Transformer LV current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变低压侧电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer LV current.'),
('gbt30966_wtrf_006', 'GB/T 30966.2-2022', 'WTRF', 'W', 'MV', '箱变有功功率', 'Transformer active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变有功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer active power.'),
('gbt30966_wtrf_007', 'GB/T 30966.2-2022', 'WTRF', 'VAr', 'MV', '箱变无功功率', 'Transformer reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变无功功率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer reactive power.'),
('gbt30966_wtrf_008', 'GB/T 30966.2-2022', 'WTRF', 'OilTmp', 'MV', '箱变油温', 'Transformer oil temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变油温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer oil temperature.'),
('gbt30966_wtrf_009', 'GB/T 30966.2-2022', 'WTRF', 'WndTmp', 'MV', '箱变绕组温度', 'Transformer winding temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变绕组温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer winding temperature.'),
('gbt30966_wtrf_010', 'GB/T 30966.2-2022', 'WTRF', 'OilLev', 'MV', '箱变油位', 'Transformer oil level', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变油位。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer oil level.'),
('gbt30966_wtrf_011', 'GB/T 30966.2-2022', 'WTRF', 'LoadPct', 'MV', '箱变负载率', 'Transformer load rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变负载率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer load rate.'),
('gbt30966_wtrf_012', 'GB/T 30966.2-2022', 'WTRF', 'FltSt', 'SPS', '箱变故障状态', 'Transformer fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer fault status.'),
('gbt30966_wtrf_013', 'GB/T 30966.2-2022', 'WTRF', 'AlmSt', 'SPS', '箱变告警状态', 'Transformer alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：箱变告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Transformer alarm status.'),
('gbt30966_wnac_001', 'GB/T 30966.2-2022', 'WNAC', 'OpSt', 'SPS', '机舱运行状态', 'Nacelle operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle operating status.'),
('gbt30966_wnac_002', 'GB/T 30966.2-2022', 'WNAC', 'Tmp', 'MV', '机舱温度', 'Nacelle temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle temperature.'),
('gbt30966_wnac_003', 'GB/T 30966.2-2022', 'WNAC', 'Hum', 'MV', '机舱湿度', 'Nacelle humidity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','HUMIDITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱湿度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle humidity.'),
('gbt30966_wnac_004', 'GB/T 30966.2-2022', 'WNAC', 'WndSpd', 'MV', '机舱风速', 'Nacelle wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle wind speed.'),
('gbt30966_wnac_005', 'GB/T 30966.2-2022', 'WNAC', 'WndDir', 'MV', '机舱风向', 'Nacelle wind direction', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱风向。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle wind direction.'),
('gbt30966_wnac_006', 'GB/T 30966.2-2022', 'WNAC', 'VibVel', 'MV', '机舱振动速度', 'Nacelle vibration velocity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','MM_S'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱振动速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle vibration velocity.'),
('gbt30966_wnac_007', 'GB/T 30966.2-2022', 'WNAC', 'VibAcc', 'MV', '机舱振动加速度', 'Nacelle vibration acceleration', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','M_S2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱振动加速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle vibration acceleration.'),
('gbt30966_wnac_008', 'GB/T 30966.2-2022', 'WNAC', 'YawAng', 'MV', '机舱偏航角', 'Nacelle yaw angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱偏航角。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle yaw angle.'),
('gbt30966_wnac_009', 'GB/T 30966.2-2022', 'WNAC', 'CabTmp', 'MV', '机舱柜温', 'Nacelle cabinet temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱柜温。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle cabinet temperature.'),
('gbt30966_wnac_010', 'GB/T 30966.2-2022', 'WNAC', 'SmkAlm', 'SPS', '机舱烟雾报警', 'Nacelle smoke alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱烟雾报警。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle smoke alarm.'),
('gbt30966_wnac_011', 'GB/T 30966.2-2022', 'WNAC', 'FireAlm', 'SPS', '机舱消防报警', 'Nacelle fire alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱消防报警。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle fire alarm.'),
('gbt30966_wnac_012', 'GB/T 30966.2-2022', 'WNAC', 'DoorSt', 'SPS', '机舱门状态', 'Nacelle door status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱门状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle door status.'),
('gbt30966_wnac_013', 'GB/T 30966.2-2022', 'WNAC', 'LightSt', 'SPS', '机舱照明状态', 'Nacelle lighting status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱照明状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle lighting status.'),
('gbt30966_wnac_014', 'GB/T 30966.2-2022', 'WNAC', 'MntSwSt', 'SPS', '机舱维护开关状态', 'Nacelle maintenance switch status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：机舱维护开关状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Nacelle maintenance switch status.'),
('gbt30966_wyaw_001', 'GB/T 30966.2-2022', 'WYAW', 'OpSt', 'SPS', '偏航运行状态', 'Yaw operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航运行状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw operating status.'),
('gbt30966_wyaw_002', 'GB/T 30966.2-2022', 'WYAW', 'YawAng', 'MV', '偏航角度', 'Yaw angle', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航角度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw angle.'),
('gbt30966_wyaw_003', 'GB/T 30966.2-2022', 'WYAW', 'YawSpd', 'MV', '偏航速度', 'Yaw speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','SPEED'), ref_code_id('UNIT','RPM'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw speed.'),
('gbt30966_wyaw_004', 'GB/T 30966.2-2022', 'WYAW', 'YawMotAmp', 'MV', '偏航电机电流', 'Yaw motor current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航电机电流。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw motor current.'),
('gbt30966_wyaw_005', 'GB/T 30966.2-2022', 'WYAW', 'YawMotTmp', 'MV', '偏航电机温度', 'Yaw motor temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航电机温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw motor temperature.'),
('gbt30966_wyaw_006', 'GB/T 30966.2-2022', 'WYAW', 'YawBrkPres', 'MV', '偏航制动压力', 'Yaw brake pressure', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航制动压力。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw brake pressure.'),
('gbt30966_wyaw_007', 'GB/T 30966.2-2022', 'WYAW', 'YawBrkSt', 'SPS', '偏航制动状态', 'Yaw brake status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航制动状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw brake status.'),
('gbt30966_wyaw_008', 'GB/T 30966.2-2022', 'WYAW', 'LeftLimSt', 'SPS', '偏航左限位状态', 'Yaw left limit status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航左限位状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw left limit status.'),
('gbt30966_wyaw_009', 'GB/T 30966.2-2022', 'WYAW', 'RightLimSt', 'SPS', '偏航右限位状态', 'Yaw right limit status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航右限位状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw right limit status.'),
('gbt30966_wyaw_010', 'GB/T 30966.2-2022', 'WYAW', 'FltSt', 'SPS', '偏航故障状态', 'Yaw fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw fault status.'),
('gbt30966_wyaw_011', 'GB/T 30966.2-2022', 'WYAW', 'AlmSt', 'SPS', '偏航告警状态', 'Yaw alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：偏航告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Yaw alarm status.'),
('gbt30966_wtow_001', 'GB/T 30966.2-2022', 'WTOW', 'BaseTmp', 'MV', '塔筒基础温度', 'Tower foundation temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：塔筒基础温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Tower foundation temperature.'),
('gbt30966_wtow_002', 'GB/T 30966.2-2022', 'WTOW', 'TopTmp', 'MV', '塔筒顶部温度', 'Tower top temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：塔筒顶部温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Tower top temperature.'),
('gbt30966_wtow_003', 'GB/T 30966.2-2022', 'WTOW', 'VibVel', 'MV', '塔筒振动速度', 'Tower vibration velocity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','MM_S'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：塔筒振动速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Tower vibration velocity.'),
('gbt30966_wtow_004', 'GB/T 30966.2-2022', 'WTOW', 'VibAcc', 'MV', '塔筒振动加速度', 'Tower vibration acceleration', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VIBRATION'), ref_code_id('UNIT','M_S2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：塔筒振动加速度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Tower vibration acceleration.'),
('gbt30966_wtow_005', 'GB/T 30966.2-2022', 'WTOW', 'DoorSt', 'SPS', '塔筒门状态', 'Tower door status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：塔筒门状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Tower door status.'),
('gbt30966_wmet_001', 'GB/T 30966.2-2022', 'WMET', 'WndSpdInst', 'MV', '瞬时风速', 'Instantaneous wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：瞬时风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Instantaneous wind speed.'),
('gbt30966_wmet_002', 'GB/T 30966.2-2022', 'WMET', 'WndSpdAvg', 'MV', '平均风速', 'Average wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：平均风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Average wind speed.'),
('gbt30966_wmet_003', 'GB/T 30966.2-2022', 'WMET', 'WndSpdMax', 'MV', '最大风速', 'Maximum wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：最大风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Maximum wind speed.'),
('gbt30966_wmet_004', 'GB/T 30966.2-2022', 'WMET', 'WndSpdMin', 'MV', '最小风速', 'Minimum wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：最小风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Minimum wind speed.'),
('gbt30966_wmet_005', 'GB/T 30966.2-2022', 'WMET', 'WndDir', 'MV', '风向', 'Wind direction', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风向。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind direction.'),
('gbt30966_wmet_006', 'GB/T 30966.2-2022', 'WMET', 'WndDirAvg', 'MV', '平均风向', 'Average wind direction', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：平均风向。', 'GB/T 30966.2-2022 wind information model engineering semantic: Average wind direction.'),
('gbt30966_wmet_007', 'GB/T 30966.2-2022', 'WMET', 'TurbInt', 'MV', '湍流强度', 'Turbulence intensity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：湍流强度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Turbulence intensity.'),
('gbt30966_wmet_008', 'GB/T 30966.2-2022', 'WMET', 'AirTmp', 'MV', '空气温度', 'Air temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：空气温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Air temperature.'),
('gbt30966_wmet_009', 'GB/T 30966.2-2022', 'WMET', 'AirHum', 'MV', '空气湿度', 'Air humidity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','HUMIDITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：空气湿度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Air humidity.'),
('gbt30966_wmet_010', 'GB/T 30966.2-2022', 'WMET', 'AtmPres', 'MV', '大气压力', 'Atmospheric pressure', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：大气压力。', 'GB/T 30966.2-2022 wind information model engineering semantic: Atmospheric pressure.'),
('gbt30966_wmet_011', 'GB/T 30966.2-2022', 'WMET', 'Irr', 'MV', '太阳辐照度', 'Solar irradiance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','IRRADIANCE'), ref_code_id('UNIT','W_M2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：太阳辐照度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Solar irradiance.'),
('gbt30966_wmet_012', 'GB/T 30966.2-2022', 'WMET', 'GHI', 'MV', '水平总辐照度', 'Global horizontal irradiance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','IRRADIANCE'), ref_code_id('UNIT','W_M2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：水平总辐照度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Global horizontal irradiance.'),
('gbt30966_wmet_013', 'GB/T 30966.2-2022', 'WMET', 'POAIrr', 'MV', '倾斜面辐照度', 'Plane of array irradiance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','IRRADIANCE'), ref_code_id('UNIT','W_M2'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：倾斜面辐照度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Plane of array irradiance.'),
('gbt30966_wmet_014', 'GB/T 30966.2-2022', 'WMET', 'Rain', 'MV', '降雨量', 'Rainfall', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：降雨量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Rainfall.'),
('gbt30966_wmet_015', 'GB/T 30966.2-2022', 'WMET', 'Vis', 'MV', '能见度', 'Visibility', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','M'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：能见度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Visibility.'),
('gbt30966_wmet_016', 'GB/T 30966.2-2022', 'WMET', 'PwrSt', 'SPS', '测风塔供电状态', 'Met mast power supply status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：测风塔供电状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Met mast power supply status.'),
('gbt30966_wmet_017', 'GB/T 30966.2-2022', 'WMET', 'ComSt', 'SPS', '测风塔通信状态', 'Met mast communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：测风塔通信状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Met mast communication status.'),
('gbt30966_wmet_018', 'GB/T 30966.2-2022', 'WMET', 'THSensorSt', 'SPS', '温湿度传感器状态', 'Temperature humidity sensor status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：温湿度传感器状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Temperature humidity sensor status.'),
('gbt30966_wmet_019', 'GB/T 30966.2-2022', 'WMET', 'AnemSt', 'SPS', '风速仪状态', 'Anemometer status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风速仪状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Anemometer status.'),
('gbt30966_wmet_020', 'GB/T 30966.2-2022', 'WMET', 'VaneSt', 'SPS', '风向标状态', 'Wind vane status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风向标状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind vane status.'),
('gbt30966_wmet_021', 'GB/T 30966.2-2022', 'WMET', 'FltSt', 'SPS', '气象站故障状态', 'Weather station fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：气象站故障状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Weather station fault status.'),
('gbt30966_wmet_022', 'GB/T 30966.2-2022', 'WMET', 'AlmSt', 'SPS', '气象站告警状态', 'Weather station alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：气象站告警状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Weather station alarm status.'),
('gbt30966_wmet_023', 'GB/T 30966.2-2022', 'WMET', 'WndSpd10m', 'MV', '10分钟平均风速', '10 minute average wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：10分钟平均风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: 10 minute average wind speed.'),
('gbt30966_wmet_024', 'GB/T 30966.2-2022', 'WMET', 'WndDir10m', 'MV', '10分钟平均风向', '10 minute average wind direction', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','DEGREE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：10分钟平均风向。', 'GB/T 30966.2-2022 wind information model engineering semantic: 10 minute average wind direction.'),
('gbt30966_wmet_025', 'GB/T 30966.2-2022', 'WMET', 'GustSpd', 'MV', '阵风风速', 'Gust wind speed', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','WIND'), ref_code_id('UNIT','MPS'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：阵风风速。', 'GB/T 30966.2-2022 wind information model engineering semantic: Gust wind speed.'),
('gbt30966_wmet_026', 'GB/T 30966.2-2022', 'WMET', 'PresTrend', 'MV', '气压趋势', 'Pressure trend', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','PRESSURE'), ref_code_id('UNIT','KPA'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：气压趋势。', 'GB/T 30966.2-2022 wind information model engineering semantic: Pressure trend.'),
('gbt30966_wmet_027', 'GB/T 30966.2-2022', 'WMET', 'DewTmp', 'MV', '露点温度', 'Dew point temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：露点温度。', 'GB/T 30966.2-2022 wind information model engineering semantic: Dew point temperature.'),
('gbt30966_wmet_028', 'GB/T 30966.2-2022', 'WMET', 'IceAlm', 'SPS', '结冰报警', 'Icing alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：结冰报警。', 'GB/T 30966.2-2022 wind information model engineering semantic: Icing alarm.'),
('gbt30966_walm_001', 'GB/T 30966.2-2022', 'WALM', 'GenAlm', 'SPS', '风机综合报警', 'Wind turbine general alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机综合报警。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine general alarm.'),
('gbt30966_walm_002', 'GB/T 30966.2-2022', 'WALM', 'GenFlt', 'SPS', '风机综合故障', 'Wind turbine general fault', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机综合故障。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine general fault.'),
('gbt30966_wavl_001', 'GB/T 30966.2-2022', 'WAVL', 'AvlSt', 'SPS', '风机可用状态', 'Wind turbine available status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机可用状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine available status.'),
('gbt30966_wavl_002', 'GB/T 30966.2-2022', 'WAVL', 'AvlPct', 'MV', '风机可利用率', 'Wind turbine availability rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机可利用率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine availability rate.'),
('gbt30966_wavl_003', 'GB/T 30966.2-2022', 'WAVL', 'PlanOutSt', 'SPS', '风机计划停机状态', 'Wind turbine planned outage status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机计划停机状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine planned outage status.'),
('gbt30966_wavl_004', 'GB/T 30966.2-2022', 'WAVL', 'UnplanOutSt', 'SPS', '风机非计划停机状态', 'Wind turbine unplanned outage status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机非计划停机状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine unplanned outage status.'),
('gbt30966_wavl_005', 'GB/T 30966.2-2022', 'WAVL', 'CurtSt', 'SPS', '风机限电状态', 'Wind turbine curtailment status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机限电状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine curtailment status.'),
('gbt30966_wavl_006', 'GB/T 30966.2-2022', 'WAVL', 'MntSt', 'SPS', '风机检修状态', 'Wind turbine maintenance status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机检修状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine maintenance status.'),
('gbt30966_wavl_007', 'GB/T 30966.2-2022', 'WAVL', 'StbySt', 'SPS', '风机待机状态', 'Wind turbine standby status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机待机状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine standby status.'),
('gbt30966_wavl_008', 'GB/T 30966.2-2022', 'WAVL', 'RunHrs', 'MV', '风机运行小时数', 'Wind turbine running hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机运行小时数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine running hours.'),
('gbt30966_wavl_009', 'GB/T 30966.2-2022', 'WAVL', 'FltHrs', 'MV', '风机故障小时数', 'Wind turbine fault hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机故障小时数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine fault hours.'),
('gbt30966_wavl_010', 'GB/T 30966.2-2022', 'WAVL', 'OutHrs', 'MV', '风机停机小时数', 'Wind turbine outage hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机停机小时数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine outage hours.'),
('gbt30966_wavl_011', 'GB/T 30966.2-2022', 'WAVL', 'AvlHrs', 'MV', '风机可用小时数', 'Wind turbine available hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机可用小时数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine available hours.'),
('gbt30966_wavl_012', 'GB/T 30966.2-2022', 'WAVL', 'UnavlHrs', 'MV', '风机不可用小时数', 'Wind turbine unavailable hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机不可用小时数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine unavailable hours.'),
('gbt30966_wavl_013', 'GB/T 30966.2-2022', 'WAVL', 'StrCnt', 'INS', '风机启机次数', 'Wind turbine start count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机启机次数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine start count.'),
('gbt30966_wavl_014', 'GB/T 30966.2-2022', 'WAVL', 'StpCnt', 'INS', '风机停机次数', 'Wind turbine stop count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机停机次数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine stop count.'),
('gbt30966_wavl_015', 'GB/T 30966.2-2022', 'WAVL', 'FltCnt', 'INS', '风机故障次数', 'Wind turbine fault count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机故障次数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine fault count.'),
('gbt30966_wavl_016', 'GB/T 30966.2-2022', 'WAVL', 'AlmCnt', 'INS', '风机告警次数', 'Wind turbine alarm count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：风机告警次数。', 'GB/T 30966.2-2022 wind information model engineering semantic: Wind turbine alarm count.'),
('gbt30966_wavl_017', 'GB/T 30966.2-2022', 'WAVL', 'AvlPer', 'INS', '可用性统计周期', 'Availability statistics period', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：可用性统计周期。', 'GB/T 30966.2-2022 wind information model engineering semantic: Availability statistics period.'),
('gbt30966_wavl_018', 'GB/T 30966.2-2022', 'WAVL', 'UtilHrs', 'MV', '利用小时', 'Utilization hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：利用小时。', 'GB/T 30966.2-2022 wind information model engineering semantic: Utilization hours.'),
('gbt30966_wavl_019', 'GB/T 30966.2-2022', 'WAVL', 'EqFullHrs', 'MV', '等效满发小时', 'Equivalent full load hours', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：等效满发小时。', 'GB/T 30966.2-2022 wind information model engineering semantic: Equivalent full load hours.'),
('gbt30966_wavl_020', 'GB/T 30966.2-2022', 'WAVL', 'TimeAvl', 'MV', '时间可利用率', 'Time availability', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：时间可利用率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Time availability.'),
('gbt30966_wavl_021', 'GB/T 30966.2-2022', 'WAVL', 'EnAvl', 'MV', '电量可利用率', 'Energy availability', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：电量可利用率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Energy availability.'),
('gbt30966_wapc_001', 'GB/T 30966.2-2022', 'WAPC', 'APCEn', 'SPS', '有功控制投入状态', 'Active power control enable status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制投入状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control enable status.'),
('gbt30966_wapc_002', 'GB/T 30966.2-2022', 'WAPC', 'WSet', 'APC', '有功功率设定值', 'Active power setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功功率设定值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power setpoint.'),
('gbt30966_wapc_003', 'GB/T 30966.2-2022', 'WAPC', 'WMax', 'MV', '有功功率上限', 'Active power upper limit', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功功率上限。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power upper limit.'),
('gbt30966_wapc_004', 'GB/T 30966.2-2022', 'WAPC', 'WMin', 'MV', '有功功率下限', 'Active power lower limit', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功功率下限。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power lower limit.'),
('gbt30966_wapc_005', 'GB/T 30966.2-2022', 'WAPC', 'WRamp', 'MV', '有功爬坡率', 'Active power ramp rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功爬坡率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power ramp rate.'),
('gbt30966_wapc_006', 'GB/T 30966.2-2022', 'WAPC', 'WFb', 'MV', '有功功率反馈值', 'Active power feedback', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功功率反馈值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power feedback.'),
('gbt30966_wapc_007', 'GB/T 30966.2-2022', 'WAPC', 'WLimSt', 'SPS', '限功率状态', 'Active power limitation status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：限功率状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power limitation status.'),
('gbt30966_wapc_008', 'GB/T 30966.2-2022', 'WAPC', 'AGCComSt', 'SPS', 'AGC通信状态', 'AGC communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：AGC通信状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: AGC communication status.'),
('gbt30966_wapc_009', 'GB/T 30966.2-2022', 'WAPC', 'AGCCmd', 'SPC', 'AGC遥控命令', 'AGC remote control command', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMAND'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：AGC遥控命令。', 'GB/T 30966.2-2022 wind information model engineering semantic: AGC remote control command.'),
('gbt30966_wapc_010', 'GB/T 30966.2-2022', 'WAPC', 'AGCMod', 'INS', 'AGC控制模式', 'AGC control mode', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：AGC控制模式。', 'GB/T 30966.2-2022 wind information model engineering semantic: AGC control mode.'),
('gbt30966_wapc_011', 'GB/T 30966.2-2022', 'WAPC', 'APCBlkSt', 'SPS', '有功控制闭锁状态', 'Active power control block status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制闭锁状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control block status.'),
('gbt30966_wapc_012', 'GB/T 30966.2-2022', 'WAPC', 'PFCEn', 'SPS', '一次调频投入状态', 'Primary frequency control enable status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：一次调频投入状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Primary frequency control enable status.'),
('gbt30966_wapc_013', 'GB/T 30966.2-2022', 'WAPC', 'PFCWResp', 'MV', '一次调频功率响应', 'Primary frequency control response', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：一次调频功率响应。', 'GB/T 30966.2-2022 wind information model engineering semantic: Primary frequency control response.'),
('gbt30966_wapc_014', 'GB/T 30966.2-2022', 'WAPC', 'FreqDev', 'MV', '频率偏差', 'Frequency deviation', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：频率偏差。', 'GB/T 30966.2-2022 wind information model engineering semantic: Frequency deviation.'),
('gbt30966_wapc_015', 'GB/T 30966.2-2022', 'WAPC', 'WDeadband', 'MV', '有功控制死区', 'Active power control deadband', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制死区。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control deadband.'),
('gbt30966_wapc_016', 'GB/T 30966.2-2022', 'WAPC', 'TargetPct', 'MV', '有功控制目标完成率', 'Active power control target completion rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制目标完成率。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control target completion rate.'),
('gbt30966_wapc_017', 'GB/T 30966.2-2022', 'WAPC', 'WReserve', 'MV', '有功备用容量', 'Active power reserve capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功备用容量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power reserve capacity.'),
('gbt30966_wapc_018', 'GB/T 30966.2-2022', 'WAPC', 'WUpCap', 'MV', '有功可调上调容量', 'Active power upward regulating capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功可调上调容量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power upward regulating capacity.'),
('gbt30966_wapc_019', 'GB/T 30966.2-2022', 'WAPC', 'WDownCap', 'MV', '有功可调下调容量', 'Active power downward regulating capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功可调下调容量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power downward regulating capacity.'),
('gbt30966_wapc_020', 'GB/T 30966.2-2022', 'WAPC', 'WRespTm', 'MV', '有功控制响应时间', 'Active power control response time', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制响应时间。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control response time.'),
('gbt30966_wapc_021', 'GB/T 30966.2-2022', 'WAPC', 'WDev', 'MV', '有功控制偏差', 'Active power control deviation', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制偏差。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control deviation.'),
('gbt30966_wapc_022', 'GB/T 30966.2-2022', 'WAPC', 'WCtrlQual', 'MV', '有功控制品质', 'Active power control quality', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：有功控制品质。', 'GB/T 30966.2-2022 wind information model engineering semantic: Active power control quality.'),
('gbt30966_wrpc_001', 'GB/T 30966.2-2022', 'WRPC', 'RPCEn', 'SPS', '无功控制投入状态', 'Reactive power control enable status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制投入状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control enable status.'),
('gbt30966_wrpc_002', 'GB/T 30966.2-2022', 'WRPC', 'VArSet', 'APC', '无功功率设定值', 'Reactive power setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功功率设定值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power setpoint.'),
('gbt30966_wrpc_003', 'GB/T 30966.2-2022', 'WRPC', 'VSet', 'APC', '电压设定值', 'Voltage setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：电压设定值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Voltage setpoint.'),
('gbt30966_wrpc_004', 'GB/T 30966.2-2022', 'WRPC', 'PFSet', 'APC', '功率因数设定值', 'Power factor setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：功率因数设定值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Power factor setpoint.'),
('gbt30966_wrpc_005', 'GB/T 30966.2-2022', 'WRPC', 'VArMax', 'MV', '无功功率上限', 'Reactive power upper limit', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功功率上限。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power upper limit.'),
('gbt30966_wrpc_006', 'GB/T 30966.2-2022', 'WRPC', 'VArMin', 'MV', '无功功率下限', 'Reactive power lower limit', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功功率下限。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power lower limit.'),
('gbt30966_wrpc_007', 'GB/T 30966.2-2022', 'WRPC', 'VArFb', 'MV', '无功功率反馈值', 'Reactive power feedback', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功功率反馈值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power feedback.'),
('gbt30966_wrpc_008', 'GB/T 30966.2-2022', 'WRPC', 'VFb', 'MV', '电压反馈值', 'Voltage feedback', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：电压反馈值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Voltage feedback.'),
('gbt30966_wrpc_009', 'GB/T 30966.2-2022', 'WRPC', 'PFFb', 'MV', '功率因数反馈值', 'Power factor feedback', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：功率因数反馈值。', 'GB/T 30966.2-2022 wind information model engineering semantic: Power factor feedback.'),
('gbt30966_wrpc_010', 'GB/T 30966.2-2022', 'WRPC', 'AVCComSt', 'SPS', 'AVC通信状态', 'AVC communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：AVC通信状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: AVC communication status.'),
('gbt30966_wrpc_011', 'GB/T 30966.2-2022', 'WRPC', 'AVCMod', 'INS', 'AVC控制模式', 'AVC control mode', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：AVC控制模式。', 'GB/T 30966.2-2022 wind information model engineering semantic: AVC control mode.'),
('gbt30966_wrpc_012', 'GB/T 30966.2-2022', 'WRPC', 'AVCCmd', 'SPC', 'AVC遥控命令', 'AVC remote control command', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMAND'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：AVC遥控命令。', 'GB/T 30966.2-2022 wind information model engineering semantic: AVC remote control command.'),
('gbt30966_wrpc_013', 'GB/T 30966.2-2022', 'WRPC', 'RPCBlkSt', 'SPS', '无功控制闭锁状态', 'Reactive power control block status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制闭锁状态。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control block status.'),
('gbt30966_wrpc_014', 'GB/T 30966.2-2022', 'WRPC', 'VArDeadband', 'MV', '无功控制死区', 'Reactive power control deadband', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制死区。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control deadband.'),
('gbt30966_wrpc_015', 'GB/T 30966.2-2022', 'WRPC', 'VArReserve', 'MV', '无功备用容量', 'Reactive power reserve capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功备用容量。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power reserve capacity.'),
('gbt30966_wrpc_016', 'GB/T 30966.2-2022', 'WRPC', 'VArRespTm', 'MV', '无功控制响应时间', 'Reactive power control response time', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制响应时间。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control response time.'),
('gbt30966_wrpc_017', 'GB/T 30966.2-2022', 'WRPC', 'VArDev', 'MV', '无功控制偏差', 'Reactive power control deviation', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制偏差。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control deviation.'),
('gbt30966_wrpc_018', 'GB/T 30966.2-2022', 'WRPC', 'VArCtrlQual', 'MV', '无功控制品质', 'Reactive power control quality', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), 'GB/T 30966.2-2022 风电信息模型工程语义：无功控制品质。', 'GB/T 30966.2-2022 wind information model engineering semantic: Reactive power control quality.'),
('ext_pv_001', 'PROJECT_EXTENSION', NULL, 'PvInvW', 'MV', '光伏逆变器有功功率', 'PV inverter active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器有功功率。', 'Project extension engineering semantic: PV inverter active power.'),
('ext_pv_002', 'PROJECT_EXTENSION', NULL, 'PvInvVAr', 'MV', '光伏逆变器无功功率', 'PV inverter reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器无功功率。', 'Project extension engineering semantic: PV inverter reactive power.'),
('ext_pv_003', 'PROJECT_EXTENSION', NULL, 'PvDcVol', 'MV', '光伏逆变器直流电压', 'PV inverter DC voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器直流电压。', 'Project extension engineering semantic: PV inverter DC voltage.'),
('ext_pv_004', 'PROJECT_EXTENSION', NULL, 'PvDcAmp', 'MV', '光伏逆变器直流电流', 'PV inverter DC current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器直流电流。', 'Project extension engineering semantic: PV inverter DC current.'),
('ext_pv_005', 'PROJECT_EXTENSION', NULL, 'PvAcVol', 'MV', '光伏逆变器交流电压', 'PV inverter AC voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器交流电压。', 'Project extension engineering semantic: PV inverter AC voltage.'),
('ext_pv_006', 'PROJECT_EXTENSION', NULL, 'PvAcAmp', 'MV', '光伏逆变器交流电流', 'PV inverter AC current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器交流电流。', 'Project extension engineering semantic: PV inverter AC current.'),
('ext_pv_007', 'PROJECT_EXTENSION', NULL, 'PvHz', 'MV', '光伏逆变器频率', 'PV inverter frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器频率。', 'Project extension engineering semantic: PV inverter frequency.'),
('ext_pv_008', 'PROJECT_EXTENSION', NULL, 'PvInvTmp', 'MV', '光伏逆变器温度', 'PV inverter temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器温度。', 'Project extension engineering semantic: PV inverter temperature.'),
('ext_pv_009', 'PROJECT_EXTENSION', NULL, 'PvInvEff', 'MV', '光伏逆变器效率', 'PV inverter efficiency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器效率。', 'Project extension engineering semantic: PV inverter efficiency.'),
('ext_pv_010', 'PROJECT_EXTENSION', NULL, 'PvInvOpSt', 'SPS', '光伏逆变器运行状态', 'PV inverter operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器运行状态。', 'Project extension engineering semantic: PV inverter operating status.'),
('ext_pv_011', 'PROJECT_EXTENSION', NULL, 'PvInvFltSt', 'SPS', '光伏逆变器故障状态', 'PV inverter fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器故障状态。', 'Project extension engineering semantic: PV inverter fault status.'),
('ext_pv_012', 'PROJECT_EXTENSION', NULL, 'PvInvAlmSt', 'SPS', '光伏逆变器告警状态', 'PV inverter alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：光伏逆变器告警状态。', 'Project extension engineering semantic: PV inverter alarm status.'),
('ext_pv_013', 'PROJECT_EXTENSION', NULL, 'PvStrVol', 'MV', '光伏组串电压', 'PV string voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏组串电压。', 'Project extension engineering semantic: PV string voltage.'),
('ext_pv_014', 'PROJECT_EXTENSION', NULL, 'PvStrAmp', 'MV', '光伏组串电流', 'PV string current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏组串电流。', 'Project extension engineering semantic: PV string current.'),
('ext_pv_015', 'PROJECT_EXTENSION', NULL, 'PvStrW', 'MV', '光伏组串功率', 'PV string power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','KW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏组串功率。', 'Project extension engineering semantic: PV string power.'),
('ext_pv_016', 'PROJECT_EXTENSION', NULL, 'CmbInAmp', 'MV', '汇流箱输入电流', 'Combiner input current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：汇流箱输入电流。', 'Project extension engineering semantic: Combiner input current.'),
('ext_pv_017', 'PROJECT_EXTENSION', NULL, 'CmbBusVol', 'MV', '汇流箱母线电压', 'Combiner bus voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：汇流箱母线电压。', 'Project extension engineering semantic: Combiner bus voltage.'),
('ext_pv_018', 'PROJECT_EXTENSION', NULL, 'CmbOutAmp', 'MV', '汇流箱输出电流', 'Combiner output current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：汇流箱输出电流。', 'Project extension engineering semantic: Combiner output current.'),
('ext_pv_019', 'PROJECT_EXTENSION', NULL, 'CmbOutW', 'MV', '汇流箱输出功率', 'Combiner output power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','KW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：汇流箱输出功率。', 'Project extension engineering semantic: Combiner output power.'),
('ext_pv_020', 'PROJECT_EXTENSION', NULL, 'CmbTmp', 'MV', '汇流箱温度', 'Combiner temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：汇流箱温度。', 'Project extension engineering semantic: Combiner temperature.'),
('ext_pv_021', 'PROJECT_EXTENSION', NULL, 'CmbSPDSt', 'SPS', '汇流箱防雷器状态', 'Combiner SPD status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：汇流箱防雷器状态。', 'Project extension engineering semantic: Combiner SPD status.'),
('ext_pv_022', 'PROJECT_EXTENSION', NULL, 'CmbBrkSt', 'SPS', '汇流箱断路器状态', 'Combiner breaker status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：汇流箱断路器状态。', 'Project extension engineering semantic: Combiner breaker status.'),
('ext_pv_023', 'PROJECT_EXTENSION', NULL, 'PvModTmp', 'MV', '光伏组件温度', 'PV module temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏组件温度。', 'Project extension engineering semantic: PV module temperature.'),
('ext_pv_024', 'PROJECT_EXTENSION', NULL, 'PvBackTmp', 'MV', '组件背板温度', 'PV module backsheet temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：组件背板温度。', 'Project extension engineering semantic: PV module backsheet temperature.'),
('ext_pv_025', 'PROJECT_EXTENSION', NULL, 'POAIrr', 'MV', '平面阵列辐照度', 'Plane of array irradiance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','IRRADIANCE'), ref_code_id('UNIT','W_M2'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：平面阵列辐照度。', 'Project extension engineering semantic: Plane of array irradiance.'),
('ext_pv_026', 'PROJECT_EXTENSION', NULL, 'GHI', 'MV', '水平总辐照度', 'Global horizontal irradiance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','IRRADIANCE'), ref_code_id('UNIT','W_M2'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：水平总辐照度。', 'Project extension engineering semantic: Global horizontal irradiance.'),
('ext_pv_027', 'PROJECT_EXTENSION', NULL, 'PvDWh', 'MV', '光伏日发电量', 'PV daily energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏日发电量。', 'Project extension engineering semantic: PV daily energy.'),
('ext_pv_028', 'PROJECT_EXTENSION', NULL, 'PvWh', 'MV', '光伏累计发电量', 'PV accumulated energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏累计发电量。', 'Project extension engineering semantic: PV accumulated energy.'),
('ext_pv_029', 'PROJECT_EXTENSION', NULL, 'PvWLimSet', 'APC', '光伏限功率设定', 'PV active power limit setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏限功率设定。', 'Project extension engineering semantic: PV active power limit setpoint.'),
('ext_pv_030', 'PROJECT_EXTENSION', NULL, 'PvPF', 'MV', '光伏功率因数', 'PV power factor', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏功率因数。', 'Project extension engineering semantic: PV power factor.'),
('ext_pv_031', 'PROJECT_EXTENSION', NULL, 'PvGridSt', 'SPS', '光伏并网状态', 'PV grid connection status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：光伏并网状态。', 'Project extension engineering semantic: PV grid connection status.'),
('ext_pv_032', 'PROJECT_EXTENSION', NULL, 'PvComSt', 'SPS', '光伏通信状态', 'PV communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：光伏通信状态。', 'Project extension engineering semantic: PV communication status.'),
('ext_pv_033', 'PROJECT_EXTENSION', NULL, 'PvTrOilTmp', 'MV', '光伏箱变油温', 'PV pad transformer oil temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏箱变油温。', 'Project extension engineering semantic: PV pad transformer oil temperature.'),
('ext_pv_034', 'PROJECT_EXTENSION', NULL, 'PvTrLVAmp', 'MV', '光伏箱变低压侧电流', 'PV pad transformer LV current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏箱变低压侧电流。', 'Project extension engineering semantic: PV pad transformer LV current.'),
('ext_pv_035', 'PROJECT_EXTENSION', NULL, 'PvTrHVVol', 'MV', '光伏箱变高压侧电压', 'PV pad transformer HV voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏箱变高压侧电压。', 'Project extension engineering semantic: PV pad transformer HV voltage.'),
('ext_pv_036', 'PROJECT_EXTENSION', NULL, 'PvAvlCap', 'MV', '光伏可用容量', 'PV available capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：光伏可用容量。', 'Project extension engineering semantic: PV available capacity.'),
('ext_bess_001', 'PROJECT_EXTENSION', NULL, 'BessW', 'MV', '储能系统有功功率', 'BESS active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统有功功率。', 'Project extension engineering semantic: BESS active power.'),
('ext_bess_002', 'PROJECT_EXTENSION', NULL, 'BessVAr', 'MV', '储能系统无功功率', 'BESS reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统无功功率。', 'Project extension engineering semantic: BESS reactive power.'),
('ext_bess_003', 'PROJECT_EXTENSION', NULL, 'BessChgW', 'MV', '储能系统充电功率', 'BESS charging power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统充电功率。', 'Project extension engineering semantic: BESS charging power.'),
('ext_bess_004', 'PROJECT_EXTENSION', NULL, 'BessDisW', 'MV', '储能系统放电功率', 'BESS discharging power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统放电功率。', 'Project extension engineering semantic: BESS discharging power.'),
('ext_bess_005', 'PROJECT_EXTENSION', NULL, 'BessSOC', 'MV', '储能系统SOC', 'BESS state of charge', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STORAGE'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统SOC。', 'Project extension engineering semantic: BESS state of charge.'),
('ext_bess_006', 'PROJECT_EXTENSION', NULL, 'BessSOH', 'MV', '储能系统SOH', 'BESS state of health', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STORAGE'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统SOH。', 'Project extension engineering semantic: BESS state of health.'),
('ext_bess_007', 'PROJECT_EXTENSION', NULL, 'BessChgWh', 'MV', '储能系统可充电量', 'BESS chargeable energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统可充电量。', 'Project extension engineering semantic: BESS chargeable energy.'),
('ext_bess_008', 'PROJECT_EXTENSION', NULL, 'BessDisWh', 'MV', '储能系统可放电量', 'BESS dischargeable energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能系统可放电量。', 'Project extension engineering semantic: BESS dischargeable energy.'),
('ext_bess_009', 'PROJECT_EXTENSION', NULL, 'BessChgAccWh', 'MV', '储能累计充电量', 'BESS accumulated charge energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能累计充电量。', 'Project extension engineering semantic: BESS accumulated charge energy.'),
('ext_bess_010', 'PROJECT_EXTENSION', NULL, 'BessDisAccWh', 'MV', '储能累计放电量', 'BESS accumulated discharge energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能累计放电量。', 'Project extension engineering semantic: BESS accumulated discharge energy.'),
('ext_bess_011', 'PROJECT_EXTENSION', NULL, 'PcsDcVol', 'MV', 'PCS直流电压', 'PCS DC voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS直流电压。', 'Project extension engineering semantic: PCS DC voltage.'),
('ext_bess_012', 'PROJECT_EXTENSION', NULL, 'PcsDcAmp', 'MV', 'PCS直流电流', 'PCS DC current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS直流电流。', 'Project extension engineering semantic: PCS DC current.'),
('ext_bess_013', 'PROJECT_EXTENSION', NULL, 'PcsAcVol', 'MV', 'PCS交流电压', 'PCS AC voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS交流电压。', 'Project extension engineering semantic: PCS AC voltage.'),
('ext_bess_014', 'PROJECT_EXTENSION', NULL, 'PcsAcAmp', 'MV', 'PCS交流电流', 'PCS AC current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS交流电流。', 'Project extension engineering semantic: PCS AC current.'),
('ext_bess_015', 'PROJECT_EXTENSION', NULL, 'PcsHz', 'MV', 'PCS频率', 'PCS frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS频率。', 'Project extension engineering semantic: PCS frequency.'),
('ext_bess_016', 'PROJECT_EXTENSION', NULL, 'PcsTmp', 'MV', 'PCS温度', 'PCS temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：PCS温度。', 'Project extension engineering semantic: PCS temperature.'),
('ext_bess_017', 'PROJECT_EXTENSION', NULL, 'PcsOpSt', 'SPS', 'PCS运行状态', 'PCS operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：PCS运行状态。', 'Project extension engineering semantic: PCS operating status.'),
('ext_bess_018', 'PROJECT_EXTENSION', NULL, 'PcsFltSt', 'SPS', 'PCS故障状态', 'PCS fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：PCS故障状态。', 'Project extension engineering semantic: PCS fault status.'),
('ext_bess_019', 'PROJECT_EXTENSION', NULL, 'PcsAlmSt', 'SPS', 'PCS告警状态', 'PCS alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：PCS告警状态。', 'Project extension engineering semantic: PCS alarm status.'),
('ext_bess_020', 'PROJECT_EXTENSION', NULL, 'BmsOpSt', 'SPS', 'BMS运行状态', 'BMS operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：BMS运行状态。', 'Project extension engineering semantic: BMS operating status.'),
('ext_bess_021', 'PROJECT_EXTENSION', NULL, 'BmsFltSt', 'SPS', 'BMS故障状态', 'BMS fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：BMS故障状态。', 'Project extension engineering semantic: BMS fault status.'),
('ext_bess_022', 'PROJECT_EXTENSION', NULL, 'BmsAlmSt', 'SPS', 'BMS告警状态', 'BMS alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：BMS告警状态。', 'Project extension engineering semantic: BMS alarm status.'),
('ext_bess_023', 'PROJECT_EXTENSION', NULL, 'RackVol', 'MV', '电池簇电压', 'Battery rack voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电池簇电压。', 'Project extension engineering semantic: Battery rack voltage.'),
('ext_bess_024', 'PROJECT_EXTENSION', NULL, 'RackAmp', 'MV', '电池簇电流', 'Battery rack current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电池簇电流。', 'Project extension engineering semantic: Battery rack current.'),
('ext_bess_025', 'PROJECT_EXTENSION', NULL, 'RackSOC', 'MV', '电池簇SOC', 'Battery rack SOC', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STORAGE'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电池簇SOC。', 'Project extension engineering semantic: Battery rack SOC.'),
('ext_bess_026', 'PROJECT_EXTENSION', NULL, 'CellVolMax', 'MV', '单体最高电压', 'Maximum cell voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体最高电压。', 'Project extension engineering semantic: Maximum cell voltage.'),
('ext_bess_027', 'PROJECT_EXTENSION', NULL, 'CellVolMin', 'MV', '单体最低电压', 'Minimum cell voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体最低电压。', 'Project extension engineering semantic: Minimum cell voltage.'),
('ext_bess_028', 'PROJECT_EXTENSION', NULL, 'CellVolAvg', 'MV', '单体平均电压', 'Average cell voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体平均电压。', 'Project extension engineering semantic: Average cell voltage.'),
('ext_bess_029', 'PROJECT_EXTENSION', NULL, 'CellTmpMax', 'MV', '单体最高温度', 'Maximum cell temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体最高温度。', 'Project extension engineering semantic: Maximum cell temperature.'),
('ext_bess_030', 'PROJECT_EXTENSION', NULL, 'CellTmpMin', 'MV', '单体最低温度', 'Minimum cell temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体最低温度。', 'Project extension engineering semantic: Minimum cell temperature.'),
('ext_bess_031', 'PROJECT_EXTENSION', NULL, 'CellTmpAvg', 'MV', '单体平均温度', 'Average cell temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：单体平均温度。', 'Project extension engineering semantic: Average cell temperature.'),
('ext_bess_032', 'PROJECT_EXTENSION', NULL, 'ContTmp', 'MV', '电池舱温度', 'Battery container temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电池舱温度。', 'Project extension engineering semantic: Battery container temperature.'),
('ext_bess_033', 'PROJECT_EXTENSION', NULL, 'ContHum', 'MV', '电池舱湿度', 'Battery container humidity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','HUMIDITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电池舱湿度。', 'Project extension engineering semantic: Battery container humidity.'),
('ext_bess_034', 'PROJECT_EXTENSION', NULL, 'FireAlm', 'SPS', '消防报警状态', 'Fire alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：消防报警状态。', 'Project extension engineering semantic: Fire alarm status.'),
('ext_bess_035', 'PROJECT_EXTENSION', NULL, 'ThermRunAlm', 'SPS', '热失控报警状态', 'Thermal runaway alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：热失控报警状态。', 'Project extension engineering semantic: Thermal runaway alarm status.'),
('ext_bess_036', 'PROJECT_EXTENSION', NULL, 'BessGridSt', 'SPS', '储能并网状态', 'BESS grid connection status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：储能并网状态。', 'Project extension engineering semantic: BESS grid connection status.'),
('ext_bess_037', 'PROJECT_EXTENSION', NULL, 'BessComSt', 'SPS', '储能通信状态', 'BESS communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：储能通信状态。', 'Project extension engineering semantic: BESS communication status.'),
('ext_bess_038', 'PROJECT_EXTENSION', NULL, 'BessCtlMod', 'INS', '储能控制模式', 'BESS control mode', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：储能控制模式。', 'Project extension engineering semantic: BESS control mode.'),
('ext_bess_039', 'PROJECT_EXTENSION', NULL, 'BessWSet', 'APC', '储能功率设定值', 'BESS power setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能功率设定值。', 'Project extension engineering semantic: BESS power setpoint.'),
('ext_bess_040', 'PROJECT_EXTENSION', NULL, 'BessVArSet', 'APC', '储能无功设定值', 'BESS reactive power setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：储能无功设定值。', 'Project extension engineering semantic: BESS reactive power setpoint.'),
('ext_grid_001', 'PROJECT_EXTENSION', NULL, 'PoiW', 'MV', '并网点有功功率', 'POI active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点有功功率。', 'Project extension engineering semantic: POI active power.'),
('ext_grid_002', 'PROJECT_EXTENSION', NULL, 'PoiVAr', 'MV', '并网点无功功率', 'POI reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点无功功率。', 'Project extension engineering semantic: POI reactive power.'),
('ext_grid_003', 'PROJECT_EXTENSION', NULL, 'PoiVol', 'MV', '并网点电压', 'POI voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点电压。', 'Project extension engineering semantic: POI voltage.'),
('ext_grid_004', 'PROJECT_EXTENSION', NULL, 'PoiAmp', 'MV', '并网点电流', 'POI current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点电流。', 'Project extension engineering semantic: POI current.'),
('ext_grid_005', 'PROJECT_EXTENSION', NULL, 'PoiHz', 'MV', '并网点频率', 'POI frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点频率。', 'Project extension engineering semantic: POI frequency.'),
('ext_grid_006', 'PROJECT_EXTENSION', NULL, 'PoiPF', 'MV', '并网点功率因数', 'POI power factor', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：并网点功率因数。', 'Project extension engineering semantic: POI power factor.'),
('ext_grid_007', 'PROJECT_EXTENSION', NULL, 'MtHVVol', 'MV', '主变高压侧电压', 'Main transformer HV voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变高压侧电压。', 'Project extension engineering semantic: Main transformer HV voltage.'),
('ext_grid_008', 'PROJECT_EXTENSION', NULL, 'MtHVAmp', 'MV', '主变高压侧电流', 'Main transformer HV current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变高压侧电流。', 'Project extension engineering semantic: Main transformer HV current.'),
('ext_grid_009', 'PROJECT_EXTENSION', NULL, 'MtLVVol', 'MV', '主变低压侧电压', 'Main transformer LV voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变低压侧电压。', 'Project extension engineering semantic: Main transformer LV voltage.'),
('ext_grid_010', 'PROJECT_EXTENSION', NULL, 'MtLVAmp', 'MV', '主变低压侧电流', 'Main transformer LV current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变低压侧电流。', 'Project extension engineering semantic: Main transformer LV current.'),
('ext_grid_011', 'PROJECT_EXTENSION', NULL, 'MtW', 'MV', '主变有功功率', 'Main transformer active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变有功功率。', 'Project extension engineering semantic: Main transformer active power.'),
('ext_grid_012', 'PROJECT_EXTENSION', NULL, 'MtVAr', 'MV', '主变无功功率', 'Main transformer reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变无功功率。', 'Project extension engineering semantic: Main transformer reactive power.'),
('ext_grid_013', 'PROJECT_EXTENSION', NULL, 'MtOilTmp', 'MV', '主变油温', 'Main transformer oil temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变油温。', 'Project extension engineering semantic: Main transformer oil temperature.'),
('ext_grid_014', 'PROJECT_EXTENSION', NULL, 'MtWndTmp', 'MV', '主变绕组温度', 'Main transformer winding temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：主变绕组温度。', 'Project extension engineering semantic: Main transformer winding temperature.'),
('ext_grid_015', 'PROJECT_EXTENSION', NULL, 'MtTapPos', 'INS', '主变分接头档位', 'Main transformer tap position', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POSITION'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：主变分接头档位。', 'Project extension engineering semantic: Main transformer tap position.'),
('ext_grid_016', 'PROJECT_EXTENSION', NULL, 'Brk220Pos', 'SPS', '220kV断路器位置', '220kV breaker position', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：220kV断路器位置。', 'Project extension engineering semantic: 220kV breaker position.'),
('ext_grid_017', 'PROJECT_EXTENSION', NULL, 'Brk35Pos', 'SPS', '35kV断路器位置', '35kV breaker position', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：35kV断路器位置。', 'Project extension engineering semantic: 35kV breaker position.'),
('ext_grid_018', 'PROJECT_EXTENSION', NULL, 'DsPos', 'SPS', '隔离开关位置', 'Disconnector position', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：隔离开关位置。', 'Project extension engineering semantic: Disconnector position.'),
('ext_grid_019', 'PROJECT_EXTENSION', NULL, 'EsPos', 'SPS', '接地开关位置', 'Earthing switch position', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：接地开关位置。', 'Project extension engineering semantic: Earthing switch position.'),
('ext_grid_020', 'PROJECT_EXTENSION', NULL, 'BusVol', 'MV', '母线电压', 'Busbar voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：母线电压。', 'Project extension engineering semantic: Busbar voltage.'),
('ext_grid_021', 'PROJECT_EXTENSION', NULL, 'BusHz', 'MV', '母线频率', 'Busbar frequency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','FREQUENCY'), ref_code_id('UNIT','HZ'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：母线频率。', 'Project extension engineering semantic: Busbar frequency.'),
('ext_grid_022', 'PROJECT_EXTENSION', NULL, 'LineW', 'MV', '线路有功功率', 'Line active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：线路有功功率。', 'Project extension engineering semantic: Line active power.'),
('ext_grid_023', 'PROJECT_EXTENSION', NULL, 'LineVAr', 'MV', '线路无功功率', 'Line reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：线路无功功率。', 'Project extension engineering semantic: Line reactive power.'),
('ext_grid_024', 'PROJECT_EXTENSION', NULL, 'LineAmp', 'MV', '线路电流', 'Line current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：线路电流。', 'Project extension engineering semantic: Line current.'),
('ext_grid_025', 'PROJECT_EXTENSION', NULL, 'LineVol', 'MV', '线路电压', 'Line voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：线路电压。', 'Project extension engineering semantic: Line voltage.'),
('ext_grid_026', 'PROJECT_EXTENSION', NULL, 'FwdWh', 'MV', '计量正向有功电量', 'Forward active energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：计量正向有功电量。', 'Project extension engineering semantic: Forward active energy.'),
('ext_grid_027', 'PROJECT_EXTENSION', NULL, 'RevWh', 'MV', '计量反向有功电量', 'Reverse active energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：计量反向有功电量。', 'Project extension engineering semantic: Reverse active energy.'),
('ext_grid_028', 'PROJECT_EXTENSION', NULL, 'FwdVarh', 'MV', '计量正向无功电量', 'Forward reactive energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：计量正向无功电量。', 'Project extension engineering semantic: Forward reactive energy.'),
('ext_grid_029', 'PROJECT_EXTENSION', NULL, 'RevVarh', 'MV', '计量反向无功电量', 'Reverse reactive energy', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ENERGY'), ref_code_id('UNIT','MWH'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：计量反向无功电量。', 'Project extension engineering semantic: Reverse reactive energy.'),
('ext_grid_030', 'PROJECT_EXTENSION', NULL, 'VolTHD', 'MV', '电压总谐波畸变率', 'Voltage THD', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电压总谐波畸变率。', 'Project extension engineering semantic: Voltage THD.'),
('ext_grid_031', 'PROJECT_EXTENSION', NULL, 'AmpTHD', 'MV', '电流总谐波畸变率', 'Current THD', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电流总谐波畸变率。', 'Project extension engineering semantic: Current THD.'),
('ext_grid_032', 'PROJECT_EXTENSION', NULL, 'VolUnbal', 'MV', '三相电压不平衡度', 'Voltage unbalance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：三相电压不平衡度。', 'Project extension engineering semantic: Voltage unbalance.'),
('ext_grid_033', 'PROJECT_EXTENSION', NULL, 'AmpUnbal', 'MV', '三相电流不平衡度', 'Current unbalance', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：三相电流不平衡度。', 'Project extension engineering semantic: Current unbalance.'),
('ext_grid_034', 'PROJECT_EXTENSION', NULL, 'DispCmd', 'SPC', '调度遥控命令', 'Dispatch remote control command', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMAND'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：调度遥控命令。', 'Project extension engineering semantic: Dispatch remote control command.'),
('ext_grid_035', 'PROJECT_EXTENSION', NULL, 'DispSet', 'APC', '调度遥调设定值', 'Dispatch analog setpoint', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：调度遥调设定值。', 'Project extension engineering semantic: Dispatch analog setpoint.'),
('ext_grid_036', 'PROJECT_EXTENSION', NULL, 'DispComSt', 'SPS', '调度通信状态', 'Dispatch communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：调度通信状态。', 'Project extension engineering semantic: Dispatch communication status.'),
('ext_grid_037', 'PROJECT_EXTENSION', NULL, 'DispInterSt', 'SPS', '调度总召状态', 'Dispatch interrogation status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：调度总召状态。', 'Project extension engineering semantic: Dispatch interrogation status.'),
('ext_grid_038', 'PROJECT_EXTENSION', NULL, 'PoiVolAlm', 'SPS', '并网点电压越限报警', 'POI voltage limit alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：并网点电压越限报警。', 'Project extension engineering semantic: POI voltage limit alarm.'),
('ext_substation_001', 'PROJECT_EXTENSION', NULL, 'SvgW', 'MV', 'SVG有功功率', 'SVG active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG有功功率。', 'Project extension engineering semantic: SVG active power.'),
('ext_substation_002', 'PROJECT_EXTENSION', NULL, 'SvgVAr', 'MV', 'SVG无功功率', 'SVG reactive power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','MVAR'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG无功功率。', 'Project extension engineering semantic: SVG reactive power.'),
('ext_substation_003', 'PROJECT_EXTENSION', NULL, 'SvgVol', 'MV', 'SVG交流电压', 'SVG AC voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG交流电压。', 'Project extension engineering semantic: SVG AC voltage.'),
('ext_substation_004', 'PROJECT_EXTENSION', NULL, 'SvgAmp', 'MV', 'SVG交流电流', 'SVG AC current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG交流电流。', 'Project extension engineering semantic: SVG AC current.'),
('ext_substation_005', 'PROJECT_EXTENSION', NULL, 'SvgDcVol', 'MV', 'SVG直流母线电压', 'SVG DC link voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG直流母线电压。', 'Project extension engineering semantic: SVG DC link voltage.'),
('ext_substation_006', 'PROJECT_EXTENSION', NULL, 'SvgModTmp', 'MV', 'SVG模块温度', 'SVG module temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：SVG模块温度。', 'Project extension engineering semantic: SVG module temperature.'),
('ext_substation_007', 'PROJECT_EXTENSION', NULL, 'SvgOpSt', 'SPS', 'SVG运行状态', 'SVG operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：SVG运行状态。', 'Project extension engineering semantic: SVG operating status.'),
('ext_substation_008', 'PROJECT_EXTENSION', NULL, 'SvgFltSt', 'SPS', 'SVG故障状态', 'SVG fault status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：SVG故障状态。', 'Project extension engineering semantic: SVG fault status.'),
('ext_substation_009', 'PROJECT_EXTENSION', NULL, 'SvgAlmSt', 'SPS', 'SVG告警状态', 'SVG alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：SVG告警状态。', 'Project extension engineering semantic: SVG alarm status.'),
('ext_substation_010', 'PROJECT_EXTENSION', NULL, 'ReacAmp', 'MV', '35kV电抗器电流', '35kV reactor current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：35kV电抗器电流。', 'Project extension engineering semantic: 35kV reactor current.'),
('ext_substation_011', 'PROJECT_EXTENSION', NULL, 'ReacVol', 'MV', '35kV电抗器电压', '35kV reactor voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','KV'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：35kV电抗器电压。', 'Project extension engineering semantic: 35kV reactor voltage.'),
('ext_substation_012', 'PROJECT_EXTENSION', NULL, 'ReacWndTmp', 'MV', '电抗器绕组温度', 'Reactor winding temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电抗器绕组温度。', 'Project extension engineering semantic: Reactor winding temperature.'),
('ext_substation_013', 'PROJECT_EXTENSION', NULL, 'ReacInSt', 'SPS', '电抗器投入状态', 'Reactor in-service status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：电抗器投入状态。', 'Project extension engineering semantic: Reactor in-service status.'),
('ext_substation_014', 'PROJECT_EXTENSION', NULL, 'ProtOpSt', 'SPS', '保护装置运行状态', 'Protection IED operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：保护装置运行状态。', 'Project extension engineering semantic: Protection IED operating status.'),
('ext_substation_015', 'PROJECT_EXTENSION', NULL, 'ProtAlmSt', 'SPS', '保护装置告警状态', 'Protection IED alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：保护装置告警状态。', 'Project extension engineering semantic: Protection IED alarm status.'),
('ext_substation_016', 'PROJECT_EXTENSION', NULL, 'ProtTrip', 'SPS', '保护动作信号', 'Protection trip signal', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：保护动作信号。', 'Project extension engineering semantic: Protection trip signal.'),
('ext_substation_017', 'PROJECT_EXTENSION', NULL, 'RecloseAct', 'SPS', '重合闸动作信号', 'Reclosing action signal', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：重合闸动作信号。', 'Project extension engineering semantic: Reclosing action signal.'),
('ext_substation_018', 'PROJECT_EXTENSION', NULL, 'BcuOpSt', 'SPS', '测控装置运行状态', 'Bay control unit operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：测控装置运行状态。', 'Project extension engineering semantic: Bay control unit operating status.'),
('ext_substation_019', 'PROJECT_EXTENSION', NULL, 'BcuComSt', 'SPS', '测控装置通信状态', 'Bay control unit communication status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：测控装置通信状态。', 'Project extension engineering semantic: Bay control unit communication status.'),
('ext_substation_020', 'PROJECT_EXTENSION', NULL, 'MuOpSt', 'SPS', '合并单元运行状态', 'Merging unit operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：合并单元运行状态。', 'Project extension engineering semantic: Merging unit operating status.'),
('ext_substation_021', 'PROJECT_EXTENSION', NULL, 'MuSyncSt', 'SPS', '合并单元同步状态', 'Merging unit synchronization status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：合并单元同步状态。', 'Project extension engineering semantic: Merging unit synchronization status.'),
('ext_substation_022', 'PROJECT_EXTENSION', NULL, 'AuxVol', 'MV', '站用电电压', 'Station service voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：站用电电压。', 'Project extension engineering semantic: Station service voltage.'),
('ext_substation_023', 'PROJECT_EXTENSION', NULL, 'AuxAmp', 'MV', '站用电电流', 'Station service current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：站用电电流。', 'Project extension engineering semantic: Station service current.'),
('ext_substation_024', 'PROJECT_EXTENSION', NULL, 'AuxW', 'MV', '站用电有功功率', 'Station service active power', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','POWER'), ref_code_id('UNIT','KW'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：站用电有功功率。', 'Project extension engineering semantic: Station service active power.'),
('ext_substation_025', 'PROJECT_EXTENSION', NULL, 'DcSysVol', 'MV', '直流系统母线电压', 'DC system bus voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：直流系统母线电压。', 'Project extension engineering semantic: DC system bus voltage.'),
('ext_substation_026', 'PROJECT_EXTENSION', NULL, 'DcSysAmp', 'MV', '直流系统母线电流', 'DC system bus current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：直流系统母线电流。', 'Project extension engineering semantic: DC system bus current.'),
('ext_substation_027', 'PROJECT_EXTENSION', NULL, 'UpsInVol', 'MV', 'UPS输入电压', 'UPS input voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：UPS输入电压。', 'Project extension engineering semantic: UPS input voltage.'),
('ext_substation_028', 'PROJECT_EXTENSION', NULL, 'UpsOutVol', 'MV', 'UPS输出电压', 'UPS output voltage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','VOLTAGE'), ref_code_id('UNIT','V'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：UPS输出电压。', 'Project extension engineering semantic: UPS output voltage.'),
('ext_substation_029', 'PROJECT_EXTENSION', NULL, 'UpsLoad', 'MV', 'UPS负载率', 'UPS load rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：UPS负载率。', 'Project extension engineering semantic: UPS load rate.'),
('ext_substation_030', 'PROJECT_EXTENSION', NULL, 'SubAmbTmp', 'MV', '站内环境温度', 'Substation ambient temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：站内环境温度。', 'Project extension engineering semantic: Substation ambient temperature.'),
('ext_substation_031', 'PROJECT_EXTENSION', NULL, 'SubAmbHum', 'MV', '站内环境湿度', 'Substation ambient humidity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','HUMIDITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：站内环境湿度。', 'Project extension engineering semantic: Substation ambient humidity.'),
('ext_substation_032', 'PROJECT_EXTENSION', NULL, 'SwgPD', 'MV', '开关柜局放水平', 'Switchgear partial discharge level', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：开关柜局放水平。', 'Project extension engineering semantic: Switchgear partial discharge level.'),
('ext_substation_033', 'PROJECT_EXTENSION', NULL, 'CabJointTmp', 'MV', '电缆接头温度', 'Cable joint temperature', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','TEMPERATURE'), ref_code_id('UNIT','DEG_C'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：电缆接头温度。', 'Project extension engineering semantic: Cable joint temperature.'),
('ext_substation_034', 'PROJECT_EXTENSION', NULL, 'SaLeakAmp', 'MV', '避雷器泄漏电流', 'Surge arrester leakage current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：避雷器泄漏电流。', 'Project extension engineering semantic: Surge arrester leakage current.'),
('ext_substation_035', 'PROJECT_EXTENSION', NULL, 'GndAmp', 'MV', '接地点电流', 'Grounding point current', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','CURRENT'), ref_code_id('UNIT','A'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：接地点电流。', 'Project extension engineering semantic: Grounding point current.'),
('ext_substation_036', 'PROJECT_EXTENSION', NULL, 'SubFireAlm', 'SPS', '升压站消防报警', 'Substation fire alarm', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：升压站消防报警。', 'Project extension engineering semantic: Substation fire alarm.'),
('ext_it_001', 'PROJECT_EXTENSION', NULL, 'SvcAvl', 'SPS', '系统服务可用状态', 'System service availability', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：系统服务可用状态。', 'Project extension engineering semantic: System service availability.'),
('ext_it_002', 'PROJECT_EXTENSION', NULL, 'ApiRespMs', 'MV', '系统接口响应时间', 'API response time', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：系统接口响应时间。', 'Project extension engineering semantic: API response time.'),
('ext_it_003', 'PROJECT_EXTENSION', NULL, 'ApiSuccPct', 'MV', '系统接口成功率', 'API success rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：系统接口成功率。', 'Project extension engineering semantic: API success rate.'),
('ext_it_004', 'PROJECT_EXTENSION', NULL, 'DbCpuPct', 'MV', '数据库CPU使用率', 'Database CPU usage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：数据库CPU使用率。', 'Project extension engineering semantic: Database CPU usage.'),
('ext_it_005', 'PROJECT_EXTENSION', NULL, 'DbMemPct', 'MV', '数据库内存使用率', 'Database memory usage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：数据库内存使用率。', 'Project extension engineering semantic: Database memory usage.'),
('ext_it_006', 'PROJECT_EXTENSION', NULL, 'DbDiskPct', 'MV', '数据库磁盘使用率', 'Database disk usage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：数据库磁盘使用率。', 'Project extension engineering semantic: Database disk usage.'),
('ext_it_007', 'PROJECT_EXTENSION', NULL, 'DbFreeGB', 'MV', '数据库可用容量', 'Database free capacity', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','GB'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：数据库可用容量。', 'Project extension engineering semantic: Database free capacity.'),
('ext_it_008', 'PROJECT_EXTENSION', NULL, 'DbConnCnt', 'INS', '数据库连接数', 'Database connection count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：数据库连接数。', 'Project extension engineering semantic: Database connection count.'),
('ext_it_009', 'PROJECT_EXTENSION', NULL, 'DbReplDelay', 'MV', '数据库复制延迟', 'Database replication delay', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：数据库复制延迟。', 'Project extension engineering semantic: Database replication delay.'),
('ext_it_010', 'PROJECT_EXTENSION', NULL, 'NtpSyncSt', 'SPS', 'NTP同步状态', 'NTP synchronization status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：NTP同步状态。', 'Project extension engineering semantic: NTP synchronization status.'),
('ext_it_011', 'PROJECT_EXTENSION', NULL, 'NtpOffset', 'MV', 'NTP时间偏差', 'NTP time offset', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','QUALITY'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：NTP时间偏差。', 'Project extension engineering semantic: NTP time offset.'),
('ext_it_012', 'PROJECT_EXTENSION', NULL, 'SwPortSt', 'SPS', '交换机端口状态', 'Switch port status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：交换机端口状态。', 'Project extension engineering semantic: Switch port status.'),
('ext_it_013', 'PROJECT_EXTENSION', NULL, 'SwUplinkMbps', 'MV', '交换机上行带宽', 'Switch uplink bandwidth', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','MBPS'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：交换机上行带宽。', 'Project extension engineering semantic: Switch uplink bandwidth.'),
('ext_it_014', 'PROJECT_EXTENSION', NULL, 'SwPortTraffic', 'MV', '交换机端口流量', 'Switch port traffic', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','MBPS'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：交换机端口流量。', 'Project extension engineering semantic: Switch port traffic.'),
('ext_it_015', 'PROJECT_EXTENSION', NULL, 'SwPktLoss', 'MV', '交换机丢包率', 'Switch packet loss rate', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：交换机丢包率。', 'Project extension engineering semantic: Switch packet loss rate.'),
('ext_it_016', 'PROJECT_EXTENSION', NULL, 'FwOpSt', 'SPS', '防火墙运行状态', 'Firewall operating status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：防火墙运行状态。', 'Project extension engineering semantic: Firewall operating status.'),
('ext_it_017', 'PROJECT_EXTENSION', NULL, 'FwCpuPct', 'MV', '防火墙CPU使用率', 'Firewall CPU usage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：防火墙CPU使用率。', 'Project extension engineering semantic: Firewall CPU usage.'),
('ext_it_018', 'PROJECT_EXTENSION', NULL, 'FwMemPct', 'MV', '防火墙内存使用率', 'Firewall memory usage', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','PERCENT'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：防火墙内存使用率。', 'Project extension engineering semantic: Firewall memory usage.'),
('ext_it_019', 'PROJECT_EXTENSION', NULL, 'FwSessCnt', 'INS', '防火墙会话数', 'Firewall session count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：防火墙会话数。', 'Project extension engineering semantic: Firewall session count.'),
('ext_it_020', 'PROJECT_EXTENSION', NULL, 'FwBlockCnt', 'INS', '防火墙阻断事件数', 'Firewall blocked event count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：防火墙阻断事件数。', 'Project extension engineering semantic: Firewall blocked event count.'),
('ext_it_021', 'PROJECT_EXTENSION', NULL, 'MqttConnCnt', 'INS', 'MQTT Broker连接数', 'MQTT broker connection count', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：MQTT Broker连接数。', 'Project extension engineering semantic: MQTT broker connection count.'),
('ext_it_022', 'PROJECT_EXTENSION', NULL, 'MqttMsgRate', 'MV', 'MQTT消息吞吐量', 'MQTT message throughput', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','FLOAT32'), '风光储/升压站/调度/IT工程扩展语义：MQTT消息吞吐量。', 'Project extension engineering semantic: MQTT message throughput.'),
('ext_it_023', 'PROJECT_EXTENSION', NULL, 'MqttMsgDelay', 'MV', 'MQTT消息延迟', 'MQTT message latency', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','COMMUNICATION'), ref_code_id('UNIT','MS'), ref_code_id('DATA_TYPE','INT32'), '风光储/升压站/调度/IT工程扩展语义：MQTT消息延迟。', 'Project extension engineering semantic: MQTT message latency.'),
('ext_it_024', 'PROJECT_EXTENSION', NULL, 'FcApiSt', 'SPS', '第三方预测接口状态', 'Third-party forecast API status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：第三方预测接口状态。', 'Project extension engineering semantic: Third-party forecast API status.'),
('ext_it_025', 'PROJECT_EXTENSION', NULL, 'MntApiSt', 'SPS', '第三方检修接口状态', 'Third-party maintenance API status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','STATE'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：第三方检修接口状态。', 'Project extension engineering semantic: Third-party maintenance API status.'),
('ext_it_026', 'PROJECT_EXTENSION', NULL, 'CyberAlm', 'SPS', '网络安全告警状态', 'Cyber security alarm status', ref_code_id('PHYSICAL_QUANTITY_CATEGORY','ALARM'), ref_code_id('UNIT','NONE'), ref_code_id('DATA_TYPE','BOOL'), '风光储/升压站/调度/IT工程扩展语义：网络安全告警状态。', 'Project extension engineering semantic: Cyber security alarm status.');

-- 3. Additional platform reference codes
-- 1.1 extra reference codes required by v1_4_0
INSERT INTO ref_code(ref_type, code, name_zh, name_en, abbr_en, description_zh, description_en, sort_order, enabled) VALUES
('TASK_STATUS','SCHEDULED','安排运行','Scheduled',NULL,'任务已安排运行。','Task is scheduled to run.',1,true),
('TASK_STATUS','STOPPED','停止','Stopped',NULL,'任务已正常停止。','Task stopped normally.',2,true),
('TASK_STATUS','FAILED','失败退出','Failed',NULL,'任务因不可恢复错误而退出。','Task exited because of an unrecoverable error.',3,true),
('TASK_STATUS','DELETED','删除','Deleted',NULL,'任务已逻辑删除。','Task is logically deleted.',4,true),
('TASK_POINT_ROLE','READ_SOURCE','读取源点','Read source',NULL,'任务读取的数据源点。','Point used as read source.',1,true),
('TASK_POINT_ROLE','WRITE_TARGET','写入目标','Write target',NULL,'任务写入的目标点。','Point used as write target.',2,true),
('TASK_POINT_ROLE','CONTROL_TARGET','控制目标','Control target',NULL,'任务控制的目标点。','Point used as control target.',3,true),
('TASK_POINT_ROLE','PUBLISH_FIELD','发布字段','Publish field',NULL,'任务发布载荷字段。','Field used in published payload.',4,true),
('TASK_POINT_ROLE','REPORT_FIELD','报告字段','Report field',NULL,'任务上报或报告字段。','Field used in report.',5,true),
('SAMPLE_MODE','CYCLIC','周期采样','Cyclic',NULL,'周期采样。','Cyclic sampling.',1,true),
('SAMPLE_MODE','EVENT','事件触发','Event',NULL,'事件触发采样。','Event-triggered sampling.',2,true),
('SAMPLE_MODE','MANUAL','手动触发','Manual',NULL,'手动触发。','Manual trigger.',3,true),
('CONNECTION_STATUS','ONLINE','在线','Online',NULL,'连接在线。','Connection online.',1,true),
('CONNECTION_STATUS','OFFLINE','离线','Offline',NULL,'连接离线。','Connection offline.',2,true),
('CONNECTION_STATUS','FAULT','故障','Fault',NULL,'连接故障。','Connection fault.',3,true),
('MODEL_FILE_FORMAT','GLTF','glTF','glTF',NULL,'glTF 模型文件。','glTF model file.',1,true),
('ASSET_MAINTENANCE_EVENT_TYPE','INSPECTION','巡检','Inspection',NULL,'资产巡检事件。','Asset inspection event.',1,true),
('ASSET_MAINTENANCE_EVENT_TYPE','MAINTENANCE','保养','Maintenance',NULL,'资产保养事件。','Asset maintenance event.',2,true),
('ASSET_MAINTENANCE_EVENT_TYPE','REPAIR','维修','Repair',NULL,'资产维修事件。','Asset repair event.',3,true),
('EVENT_STATUS','OPEN','打开','Open',NULL,'事件未闭环。','Event is open.',1,true),
('EVENT_STATUS','CLOSED','已关闭','Closed',NULL,'事件已闭环。','Event is closed.',2,true)
ON CONFLICT (ref_type, code) DO NOTHING;

-- 4. Protocol physical-table registry
-- 8.1 protocol physical table registry
INSERT INTO cfg_protocol_table_registry(protocol_ref_id, table_role_ref_id, table_schema, table_name, description_zh, description_en) VALUES
(ref_code_id('PROTOCOL','MODBUS'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_modbus_conn', 'MODBUS CONN 物理表。', 'MODBUS CONN table.'),
(ref_code_id('PROTOCOL','MODBUS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_modbus_point_table', 'MODBUS POINT_TABLE 物理表。', 'MODBUS POINT_TABLE table.'),
(ref_code_id('PROTOCOL','MODBUS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_modbus_point_item', 'MODBUS POINT_ITEM 物理表。', 'MODBUS POINT_ITEM table.'),
(ref_code_id('PROTOCOL','IEC101'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_iec101_conn', 'IEC101 CONN 物理表。', 'IEC101 CONN table.'),
(ref_code_id('PROTOCOL','IEC101'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_iec101_point_table', 'IEC101 POINT_TABLE 物理表。', 'IEC101 POINT_TABLE table.'),
(ref_code_id('PROTOCOL','IEC101'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_iec101_point_item', 'IEC101 POINT_ITEM 物理表。', 'IEC101 POINT_ITEM table.'),
(ref_code_id('PROTOCOL','IEC104'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_iec104_conn', 'IEC104 CONN 物理表。', 'IEC104 CONN table.'),
(ref_code_id('PROTOCOL','IEC104'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_iec104_point_table', 'IEC104 POINT_TABLE 物理表。', 'IEC104 POINT_TABLE table.'),
(ref_code_id('PROTOCOL','IEC104'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_iec104_point_item', 'IEC104 POINT_ITEM 物理表。', 'IEC104 POINT_ITEM table.'),
(ref_code_id('PROTOCOL','IEC104'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_iec104_point_item', 'IEC104 统一点位执行视图。', 'IEC104 unified point-item execution view.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_iec61850_mms_conn', 'IEC61850_MMS CONN 物理表。', 'IEC61850_MMS CONN table.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_iec61850_mms_point_table', 'IEC61850_MMS POINT_TABLE 物理表。', 'IEC61850_MMS POINT_TABLE table.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_iec61850_mms_point_item', 'IEC61850_MMS POINT_ITEM 物理表。', 'IEC61850_MMS POINT_ITEM table.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_iec61850_goose_conn', 'IEC61850_GOOSE CONN 物理表。', 'IEC61850_GOOSE CONN table.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_iec61850_goose_point_table', 'IEC61850_GOOSE POINT_TABLE 物理表。', 'IEC61850_GOOSE POINT_TABLE table.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_iec61850_goose_point_item', 'IEC61850_GOOSE POINT_ITEM 物理表。', 'IEC61850_GOOSE POINT_ITEM table.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_iec61850_sv_conn', 'IEC61850_SV CONN 物理表。', 'IEC61850_SV CONN table.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_iec61850_sv_point_table', 'IEC61850_SV POINT_TABLE 物理表。', 'IEC61850_SV POINT_TABLE table.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_iec61850_sv_point_item', 'IEC61850_SV POINT_ITEM 物理表。', 'IEC61850_SV POINT_ITEM table.'),
(ref_code_id('PROTOCOL','OPCUA'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_opcua_conn', 'OPCUA CONN 物理表。', 'OPCUA CONN table.'),
(ref_code_id('PROTOCOL','OPCUA'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_opcua_point_table', 'OPCUA POINT_TABLE 物理表。', 'OPCUA POINT_TABLE table.'),
(ref_code_id('PROTOCOL','OPCUA'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_opcua_point_item', 'OPCUA POINT_ITEM 物理表。', 'OPCUA POINT_ITEM table.'),
(ref_code_id('PROTOCOL','MQTT'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_mqtt_conn', 'MQTT CONN 物理表。', 'MQTT CONN table.'),
(ref_code_id('PROTOCOL','MQTT'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_mqtt_point_table', 'MQTT POINT_TABLE 物理表。', 'MQTT POINT_TABLE table.'),
(ref_code_id('PROTOCOL','MQTT'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_mqtt_point_item', 'MQTT POINT_ITEM 物理表。', 'MQTT POINT_ITEM table.'),
(ref_code_id('PROTOCOL','ADS'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_ads_conn', 'ADS CONN 物理表。', 'ADS CONN table.'),
(ref_code_id('PROTOCOL','ADS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_ads_point_table', 'ADS POINT_TABLE 物理表。', 'ADS POINT_TABLE table.'),
(ref_code_id('PROTOCOL','ADS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_ads_point_item', 'ADS POINT_ITEM 物理表。', 'ADS POINT_ITEM table.'),
(ref_code_id('PROTOCOL','HTTP_REST'), ref_code_id('PROTOCOL_TABLE_ROLE','CONN'), 'whale', 'cfg_http_rest_conn', 'HTTP_REST CONN 物理表。', 'HTTP_REST CONN table.'),
(ref_code_id('PROTOCOL','HTTP_REST'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_TABLE'), 'whale', 'cfg_http_rest_point_table', 'HTTP_REST POINT_TABLE 物理表。', 'HTTP_REST POINT_TABLE table.'),
(ref_code_id('PROTOCOL','HTTP_REST'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM'), 'whale', 'cfg_http_rest_point_item', 'HTTP_REST POINT_ITEM 物理表。', 'HTTP_REST POINT_ITEM table.'),
(ref_code_id('PROTOCOL','MODBUS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_modbus_point_item', 'MODBUS 点位执行视图。', 'MODBUS point-item execution view.'),
(ref_code_id('PROTOCOL','IEC101'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_iec101_point_item', 'IEC101 点位执行视图。', 'IEC101 point-item execution view.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_iec61850_mms_point_item', 'IEC61850_MMS 点位执行视图。', 'IEC61850_MMS point-item execution view.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_iec61850_goose_point_item', 'IEC61850_GOOSE 点位执行视图。', 'IEC61850_GOOSE point-item execution view.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_iec61850_sv_point_item', 'IEC61850_SV 点位执行视图。', 'IEC61850_SV point-item execution view.'),
(ref_code_id('PROTOCOL','OPCUA'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_opcua_point_item', 'OPCUA 点位执行视图。', 'OPCUA point-item execution view.'),
(ref_code_id('PROTOCOL','MQTT'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_mqtt_point_item', 'MQTT 点位执行视图。', 'MQTT point-item execution view.'),
(ref_code_id('PROTOCOL','ADS'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_ads_point_item', 'ADS 点位执行视图。', 'ADS point-item execution view.'),
(ref_code_id('PROTOCOL','HTTP_REST'), ref_code_id('PROTOCOL_TABLE_ROLE','POINT_ITEM_VIEW'), 'whale', 'vw_http_rest_point_item', 'HTTP_REST 点位执行视图。', 'HTTP_REST point-item execution view.');

-- 4.1 iec104-python c104.Type complete metadata (55 visible Type IDs)
INSERT INTO cfg_iec104_type_def(
    type_id_ref_id,type_id_value,type_category_ref_id,information_value_type_ref_id,time_tag_type_ref_id,
    point_registration_supported,general_interrogation_supported,counter_interrogation_supported,
    periodic_transmission_supported,spontaneous_transmission_supported,command_mode_supported,related_io_supported,
    sort_order,enabled
) VALUES
(ref_code_id('IEC104_TYPE_ID','M_SP_NA_1'), 1, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SINGLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 1, true),
(ref_code_id('IEC104_TYPE_ID','M_SP_TA_1'), 2, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SINGLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 2, true),
(ref_code_id('IEC104_TYPE_ID','M_DP_NA_1'), 3, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DOUBLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 3, true),
(ref_code_id('IEC104_TYPE_ID','M_DP_TA_1'), 4, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DOUBLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 4, true),
(ref_code_id('IEC104_TYPE_ID','M_ST_NA_1'), 5, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','STEP_POSITION'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 5, true),
(ref_code_id('IEC104_TYPE_ID','M_ST_TA_1'), 6, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','STEP_POSITION'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 6, true),
(ref_code_id('IEC104_TYPE_ID','M_BO_NA_1'), 7, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BITSTRING32'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 7, true),
(ref_code_id('IEC104_TYPE_ID','M_BO_TA_1'), 8, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BITSTRING32'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 8, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_NA_1'), 9, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 9, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TA_1'), 10, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 10, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_NB_1'), 11, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SCALED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 11, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TB_1'), 12, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SCALED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, true, false, true, true, false, false, 12, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_NC_1'), 13, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SHORT_FLOAT'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, true, false, true, true, false, false, 13, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TC_1'), 14, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SHORT_FLOAT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, false, false, true, true, false, false, 14, true),
(ref_code_id('IEC104_TYPE_ID','M_IT_NA_1'), 15, ref_code_id('IEC104_TYPE_CATEGORY','COUNTER_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BINARY_COUNTER'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, true, true, true, false, false, 15, true),
(ref_code_id('IEC104_TYPE_ID','M_IT_TA_1'), 16, ref_code_id('IEC104_TYPE_CATEGORY','COUNTER_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BINARY_COUNTER'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, false, true, true, true, false, false, 16, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TA_1'), 17, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_EVENT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, false, false, true, true, false, false, 17, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TB_1'), 18, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_START'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, false, false, true, true, false, false, 18, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TC_1'), 19, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_OUTPUT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP24TIME2A'), true, false, false, true, true, false, false, 19, true),
(ref_code_id('IEC104_TYPE_ID','M_PS_NA_1'), 20, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PACKED_SINGLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, true, true, false, false, 20, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_ND_1'), 21, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, true, true, false, false, 21, true),
(ref_code_id('IEC104_TYPE_ID','M_SP_TB_1'), 30, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SINGLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 30, true),
(ref_code_id('IEC104_TYPE_ID','M_DP_TB_1'), 31, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DOUBLE_POINT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 31, true),
(ref_code_id('IEC104_TYPE_ID','M_ST_TB_1'), 32, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','STEP_POSITION'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 32, true),
(ref_code_id('IEC104_TYPE_ID','M_BO_TB_1'), 33, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BITSTRING32'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 33, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TD_1'), 34, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 34, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TE_1'), 35, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SCALED_VALUE'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 35, true),
(ref_code_id('IEC104_TYPE_ID','M_ME_TF_1'), 36, ref_code_id('IEC104_TYPE_CATEGORY','PROCESS_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SHORT_FLOAT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, true, false, true, true, false, false, 36, true),
(ref_code_id('IEC104_TYPE_ID','M_IT_TB_1'), 37, ref_code_id('IEC104_TYPE_CATEGORY','COUNTER_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BINARY_COUNTER'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, true, true, true, false, false, 37, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TD_1'), 38, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_EVENT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, true, true, false, false, 38, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TE_1'), 39, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_START'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, true, true, false, false, 39, true),
(ref_code_id('IEC104_TYPE_ID','M_EP_TF_1'), 40, ref_code_id('IEC104_TYPE_CATEGORY','PROTECTION_MONITOR'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','PROTECTION_OUTPUT'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, true, true, false, false, 40, true),
(ref_code_id('IEC104_TYPE_ID','C_SC_NA_1'), 45, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SINGLE_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 45, true),
(ref_code_id('IEC104_TYPE_ID','C_DC_NA_1'), 46, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DOUBLE_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 46, true),
(ref_code_id('IEC104_TYPE_ID','C_RC_NA_1'), 47, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','REGULATING_STEP_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 47, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_NA_1'), 48, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 48, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_NB_1'), 49, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SCALED_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 49, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_NC_1'), 50, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SHORT_FLOAT_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 50, true),
(ref_code_id('IEC104_TYPE_ID','C_BO_NA_1'), 51, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BITSTRING32_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), true, false, false, false, false, true, true, 51, true),
(ref_code_id('IEC104_TYPE_ID','C_SC_TA_1'), 58, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SINGLE_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 58, true),
(ref_code_id('IEC104_TYPE_ID','C_DC_TA_1'), 59, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DOUBLE_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 59, true),
(ref_code_id('IEC104_TYPE_ID','C_RC_TA_1'), 60, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','REGULATING_STEP_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 60, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_TA_1'), 61, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NORMALIZED_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 61, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_TB_1'), 62, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SCALED_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 62, true),
(ref_code_id('IEC104_TYPE_ID','C_SE_TC_1'), 63, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','SHORT_FLOAT_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 63, true),
(ref_code_id('IEC104_TYPE_ID','C_BO_TA_1'), 64, ref_code_id('IEC104_TYPE_CATEGORY','CONTROL_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','BITSTRING32_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), true, false, false, false, false, true, true, 64, true),
(ref_code_id('IEC104_TYPE_ID','M_EI_NA_1'), 70, ref_code_id('IEC104_TYPE_CATEGORY','INITIALIZATION'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','NONE'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 70, true),
(ref_code_id('IEC104_TYPE_ID','C_IC_NA_1'), 100, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','INTERROGATION_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 100, true),
(ref_code_id('IEC104_TYPE_ID','C_CI_NA_1'), 101, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','COUNTER_INTERROGATION_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 101, true),
(ref_code_id('IEC104_TYPE_ID','C_RD_NA_1'), 102, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','READ_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 102, true),
(ref_code_id('IEC104_TYPE_ID','C_CS_NA_1'), 103, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','CLOCK_SYNC_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), false, false, false, false, false, false, false, 103, true),
(ref_code_id('IEC104_TYPE_ID','C_TS_NA_1'), 104, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','TEST_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 104, true),
(ref_code_id('IEC104_TYPE_ID','C_RP_NA_1'), 105, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','RESET_PROCESS_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','NONE'), false, false, false, false, false, false, false, 105, true),
(ref_code_id('IEC104_TYPE_ID','C_CD_NA_1'), 106, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','DELAY_ACQUISITION_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP16TIME2A'), false, false, false, false, false, false, false, 106, true),
(ref_code_id('IEC104_TYPE_ID','C_TS_TA_1'), 107, ref_code_id('IEC104_TYPE_CATEGORY','SYSTEM_COMMAND'), ref_code_id('IEC104_INFORMATION_VALUE_TYPE','TEST_COMMAND'), ref_code_id('IEC104_TIME_TAG_TYPE','CP56TIME2A'), false, false, false, false, false, false, false, 107, true);

-- 5. Standard permissions, standard roles, and role-permission templates
-- 9. security permissions, roles, employees
INSERT INTO sec_permission(permission_identifier, permission_type_ref_id, permission_code_ref_id, name_zh, name_en, description_zh, description_en)
SELECT 'PERM_' || code, ref_code_id('PERMISSION_TYPE', CASE WHEN code LIKE '%EDIT' THEN 'FUNCTION' WHEN code LIKE '%CONFIG%' THEN 'SYSTEM' ELSE 'DATA' END), ref_code_id('PERMISSION_CODE', code), code, code, code || ' 权限。', code || ' permission.' FROM ref_code WHERE ref_type='PERMISSION_CODE' ORDER BY sort_order;
INSERT INTO sec_role(role_identifier, name_zh, name_en, description_zh, description_en) VALUES
('PLANT_ADMIN', '场站管理员', 'PLANT_ADMIN', '场站管理员。', 'PLANT_ADMIN role.'),
('SHIFT_LEADER', '值长', 'SHIFT_LEADER', '值长。', 'SHIFT_LEADER role.'),
('OPERATOR', '运行员', 'OPERATOR', '运行员。', 'OPERATOR role.'),
('DISPATCH_OPERATOR', '调度联系员', 'DISPATCH_OPERATOR', '调度联系员。', 'DISPATCH_OPERATOR role.'),
('ELECTRICAL_MAINTAINER', '电气一次专责', 'ELECTRICAL_MAINTAINER', '电气一次专责。', 'ELECTRICAL_MAINTAINER role.'),
('PROTECTION_ENGINEER', '继保专责', 'PROTECTION_ENGINEER', '继保专责。', 'PROTECTION_ENGINEER role.'),
('AUTOMATION_ENGINEER', '自动化SCADA专责', 'AUTOMATION_ENGINEER', '自动化SCADA专责。', 'AUTOMATION_ENGINEER role.'),
('COMMUNICATION_ENGINEER', '通信网络专责', 'COMMUNICATION_ENGINEER', '通信网络专责。', 'COMMUNICATION_ENGINEER role.'),
('WIND_ENGINEER', '风机检修工程师', 'WIND_ENGINEER', '风机检修工程师。', 'WIND_ENGINEER role.'),
('PV_ENGINEER', '光伏检修工程师', 'PV_ENGINEER', '光伏检修工程师。', 'PV_ENGINEER role.'),
('BESS_ENGINEER', '储能检修工程师', 'BESS_ENGINEER', '储能检修工程师。', 'BESS_ENGINEER role.'),
('METERING_ENGINEER', '计量电能质量专责', 'METERING_ENGINEER', '计量电能质量专责。', 'METERING_ENGINEER role.'),
('SAFETY_OFFICER', '安全员', 'SAFETY_OFFICER', '安全员。', 'SAFETY_OFFICER role.'),
('ASSET_MANAGER', '资产管理员', 'ASSET_MANAGER', '资产管理员。', 'ASSET_MANAGER role.'),
('DATA_STEWARD', '数据治理工程师', 'DATA_STEWARD', '数据治理工程师。', 'DATA_STEWARD role.'),
('SYSTEM_ADMIN', '系统管理员', 'SYSTEM_ADMIN', '系统管理员。', 'SYSTEM_ADMIN role.'),
('CYBER_SECURITY_ADMIN', '网络安全管理员', 'CYBER_SECURITY_ADMIN', '网络安全管理员。', 'CYBER_SECURITY_ADMIN role.'),
('AUDITOR', '审计员', 'AUDITOR', '审计员。', 'AUDITOR role.'),
('VENDOR_ENGINEER', '厂家工程师', 'VENDOR_ENGINEER', '厂家工程师。', 'VENDOR_ENGINEER role.'),
('READ_ONLY_VIEWER', '只读监管用户', 'READ_ONLY_VIEWER', '只读监管用户。', 'READ_ONLY_VIEWER role.');

-- Map all permissions at least through SYSTEM_ADMIN; map other roles to their practical subset.
INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON true
WHERE r.role_identifier = 'SYSTEM_ADMIN';

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier IN ('PERM_ASSET_VIEW','PERM_ASSET_EDIT','PERM_PROTOCOL_VIEW','PERM_POINT_TABLE_VIEW','PERM_TASK_VIEW','PERM_TOPO_VIEW','PERM_DISPATCH_VIEW','PERM_QUALITY_VIEW','PERM_AUDIT_VIEW')
WHERE r.role_identifier IN ('PLANT_ADMIN','ASSET_MANAGER');

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier IN ('PERM_ASSET_VIEW','PERM_PROTOCOL_VIEW','PERM_POINT_TABLE_VIEW','PERM_TASK_VIEW','PERM_TOPO_VIEW','PERM_DISPATCH_VIEW')
WHERE r.role_identifier IN ('SHIFT_LEADER','OPERATOR','DISPATCH_OPERATOR','WIND_ENGINEER','PV_ENGINEER','BESS_ENGINEER','METERING_ENGINEER','VENDOR_ENGINEER');

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier IN ('PERM_PROTOCOL_VIEW','PERM_PROTOCOL_CONFIG_EDIT','PERM_POINT_TABLE_VIEW','PERM_POINT_TABLE_EDIT','PERM_TASK_VIEW','PERM_TASK_EDIT','PERM_TOPO_VIEW','PERM_TOPO_EDIT')
WHERE r.role_identifier IN ('PROTECTION_ENGINEER','AUTOMATION_ENGINEER','COMMUNICATION_ENGINEER','ELECTRICAL_MAINTAINER');

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier IN ('PERM_QUALITY_VIEW','PERM_QUALITY_DOMAIN_EDIT','PERM_POINT_TABLE_VIEW','PERM_POINT_TABLE_EDIT')
WHERE r.role_identifier = 'DATA_STEWARD';

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier IN ('PERM_AUDIT_VIEW','PERM_ASSET_VIEW','PERM_TASK_VIEW','PERM_PROTOCOL_VIEW')
WHERE r.role_identifier IN ('AUDITOR','SAFETY_OFFICER','CYBER_SECURITY_ADMIN');

INSERT INTO sec_role_permission(role_id, permission_id)
SELECT r.sec_role_id, p.sec_permission_id
FROM sec_role r
JOIN sec_permission p ON p.permission_identifier LIKE '%VIEW'
WHERE r.role_identifier = 'READ_ONLY_VIEWER';

-- 6. Protocol operation definitions and operation-role combinations
-- 10. protocol operation definitions and role combinations
INSERT INTO cfg_protocol_operation_def(protocol_ref_id, operation_identifier, name_zh, name_en, native_operation_code, native_operation_name, operation_semantic_ref_id, operation_direction_ref_id, request_response_mode_ref_id, standard_ref, description_zh, description_en) VALUES
(ref_code_id('PROTOCOL','MODBUS'), 'MODBUS_MODBUS_READ', 'Read coils/registers', 'MODBUS_READ', 'MODBUS_READ', 'Read coils/registers', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'MODBUS engineering practice', 'Read coils/registers。', 'Read coils/registers.'),
(ref_code_id('PROTOCOL','MODBUS'), 'MODBUS_MODBUS_POLL_READ', 'Poll coils/registers', 'MODBUS_POLL_READ', 'MODBUS_POLL_READ', 'Poll coils/registers', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'MODBUS engineering practice', 'Poll coils/registers。', 'Poll coils/registers.'),
(ref_code_id('PROTOCOL','MODBUS'), 'MODBUS_MODBUS_WRITE', 'Write coil/register', 'MODBUS_WRITE', 'MODBUS_WRITE', 'Write coil/register', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'MODBUS engineering practice', 'Write coil/register。', 'Write coil/register.'),
(ref_code_id('PROTOCOL','MODBUS'), 'MODBUS_MODBUS_CONTROL', 'Control by write', 'MODBUS_CONTROL', 'MODBUS_CONTROL', 'Control by write', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'MODBUS engineering practice', 'Control by write。', 'Control by write.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_READ', 'Read', 'OPCUA_READ', 'OPCUA_READ', 'Read', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'OPCUA engineering practice', 'Read。', 'Read.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_POLL_READ', 'Poll read', 'OPCUA_POLL_READ', 'OPCUA_POLL_READ', 'Poll read', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'OPCUA engineering practice', 'Poll read。', 'Poll read.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_SUBSCRIBE', 'Subscribe monitored item', 'OPCUA_SUBSCRIBE', 'OPCUA_SUBSCRIBE', 'Subscribe monitored item', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','SUBSCRIBE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','NOTIFICATION'), 'OPCUA engineering practice', 'Subscribe monitored item。', 'Subscribe monitored item.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_WRITE', 'Write', 'OPCUA_WRITE', 'OPCUA_WRITE', 'Write', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'OPCUA engineering practice', 'Write。', 'Write.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_CONTROL', 'Control via write', 'OPCUA_CONTROL', 'OPCUA_CONTROL', 'Control via write', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'OPCUA engineering practice', 'Control via write。', 'Control via write.'),
(ref_code_id('PROTOCOL','OPCUA'), 'OPCUA_OPCUA_CALL_METHOD', 'Call method', 'OPCUA_CALL_METHOD', 'OPCUA_CALL_METHOD', 'Call method', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','METHOD_CALL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'OPCUA engineering practice', 'Call method。', 'Call method.'),
(ref_code_id('PROTOCOL','ADS'), 'ADS_ADS_READ', 'Read symbol', 'ADS_READ', 'ADS_READ', 'Read symbol', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'ADS engineering practice', 'Read symbol。', 'Read symbol.'),
(ref_code_id('PROTOCOL','ADS'), 'ADS_ADS_POLL_READ', 'Poll symbol', 'ADS_POLL_READ', 'ADS_POLL_READ', 'Poll symbol', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'ADS engineering practice', 'Poll symbol。', 'Poll symbol.'),
(ref_code_id('PROTOCOL','ADS'), 'ADS_ADS_NOTIFICATION', 'Device notification', 'ADS_NOTIFICATION', 'ADS_NOTIFICATION', 'Device notification', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','NOTIFICATION'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','NOTIFICATION'), 'ADS engineering practice', 'Device notification。', 'Device notification.'),
(ref_code_id('PROTOCOL','ADS'), 'ADS_ADS_WRITE', 'Write symbol', 'ADS_WRITE', 'ADS_WRITE', 'Write symbol', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'ADS engineering practice', 'Write symbol。', 'Write symbol.'),
(ref_code_id('PROTOCOL','ADS'), 'ADS_ADS_CONTROL', 'Control symbol', 'ADS_CONTROL', 'ADS_CONTROL', 'Control symbol', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'ADS engineering practice', 'Control symbol。', 'Control symbol.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_INTERROGATION_MASTER', 'General interrogation as master', 'IEC101_INTERROGATION_MASTER', 'IEC101_INTERROGATION_MASTER', 'General interrogation as master', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','INTERROGATION'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC101 engineering practice', 'General interrogation as master。', 'General interrogation as master.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_PERIODIC_READ', 'Cyclic polling as master', 'IEC101_PERIODIC_READ', 'IEC101_PERIODIC_READ', 'Cyclic polling as master', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC101 engineering practice', 'Cyclic polling as master。', 'Cyclic polling as master.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_RESPOND_INTERROGATION', 'Respond general interrogation', 'IEC101_RESPOND_INTERROGATION', 'IEC101_RESPOND_INTERROGATION', 'Respond general interrogation', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','INTERROGATION'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC101 engineering practice', 'Respond general interrogation。', 'Respond general interrogation.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_SERVE_REPORT', 'Spontaneous/cyclic transmission', 'IEC101_SERVE_REPORT', 'IEC101_SERVE_REPORT', 'Spontaneous/cyclic transmission', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','REPORT'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC101 engineering practice', 'Spontaneous/cyclic transmission。', 'Spontaneous/cyclic transmission.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_CLOCK_SYNC_ACCEPT', 'Accept clock sync', 'IEC101_CLOCK_SYNC_ACCEPT', 'IEC101_CLOCK_SYNC_ACCEPT', 'Accept clock sync', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','TIME_SYNC'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC101 engineering practice', 'Accept clock sync。', 'Accept clock sync.'),
(ref_code_id('PROTOCOL','IEC101'), 'IEC101_IEC101_ACCEPT_CONTROL', 'Accept command', 'IEC101_ACCEPT_CONTROL', 'IEC101_ACCEPT_CONTROL', 'Accept command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','ACCEPT_CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC101 engineering practice', 'Accept command。', 'Accept command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_GENERAL_INTERROGATION', '发送站总召', 'Send general interrogation', 'C_IC_NA_1/QOI20', 'Send station interrogation', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','INTERROGATION'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '控制站发送 QOI=20 的站总召命令。', 'Controlling station sends a station interrogation with QOI=20.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_RECEIVE_MONITOR_DATA', '接收监视数据', 'Receive monitor data', 'I-format monitor ASDU', 'Receive monitor data', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','SUBSCRIBE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC 60870-5-104', '控制站统一接收周期、自发、背景及召唤响应监视数据。', 'Controlling station receives cyclic, spontaneous, background, and interrogation-response monitor data.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_RESPOND_GENERAL_INTERROGATION', '响应站总召', 'Respond general interrogation', 'C_IC_NA_1/QOI20', 'Respond station interrogation', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','INTERROGATION'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '被控站响应 QOI=20，发送激活确认、当前值及激活终止。', 'Controlled station responds to QOI=20 with activation confirmation, current values, and activation termination.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_CYCLIC_DATA', '周期上送', 'Send cyclic data', 'COT=CYCLIC', 'Cyclic transmission', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','REPORT'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC 60870-5-104', '被控站按固定周期主动上送监视数据。', 'Controlled station actively sends monitor data at a fixed cycle.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_SPONTANEOUS_DATA', '变化上送', 'Send spontaneous data', 'COT=SPONTANEOUS', 'Spontaneous transmission', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','REPORT'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC 60870-5-104', '被控站在状态变化或模拟量越过死区时主动上送。', 'Controlled station sends data when a state changes or an analog deadband is crossed.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_BACKGROUND_DATA', '背景上送', 'Send background data', 'COT=BACKGROUND', 'Background transmission', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','REPORT'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC 60870-5-104', '被控站按低优先级背景刷新周期上送当前值。', 'Controlled station sends low-priority background refreshes.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_SETPOINT_COMMAND', '发送设点命令', 'Send setpoint command', 'C_SE_NA/NB/NC_1', 'Send setpoint command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '控制站发送归一化、标度化或短浮点设点命令。', 'Controlling station sends normalized, scaled, or short-float setpoint commands.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_SINGLE_COMMAND', '发送单点遥控', 'Send single command', 'C_SC_NA_1', 'Send single command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '控制站发送单点遥控命令。', 'Controlling station sends a single command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_DOUBLE_COMMAND', '发送双点遥控', 'Send double command', 'C_DC_NA_1', 'Send double command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '控制站发送双点遥控命令。', 'Controlling station sends a double command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_ACCEPT_SETPOINT_COMMAND', '接收设点命令', 'Accept setpoint command', 'C_SE_NA/NB/NC_1', 'Accept setpoint command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '被控站接收并处理设点命令。', 'Controlled station accepts and processes setpoint commands.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_ACCEPT_SINGLE_COMMAND', '接收单点遥控', 'Accept single command', 'C_SC_NA_1', 'Accept single command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','ACCEPT_CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '被控站接收并处理单点遥控。', 'Controlled station accepts and processes a single command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_ACCEPT_DOUBLE_COMMAND', '接收双点遥控', 'Accept double command', 'C_DC_NA_1', 'Accept double command', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','ACCEPT_CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '被控站接收并处理双点遥控。', 'Controlled station accepts and processes a double command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_SEND_CLOCK_SYNCHRONIZATION', '发送时钟同步', 'Send clock synchronization', 'C_CS_NA_1', 'Send clock synchronization', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','TIME_SYNC'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '控制站发送 CP56Time2a 时钟同步命令。', 'Controlling station sends a CP56Time2a clock synchronization command.'),
(ref_code_id('PROTOCOL','IEC104'), 'IEC104_ACCEPT_CLOCK_SYNCHRONIZATION', '接收时钟同步', 'Accept clock synchronization', 'C_CS_NA_1', 'Accept clock synchronization', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','TIME_SYNC'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC 60870-5-104', '被控站接收并处理时钟同步命令。', 'Controlled station accepts and processes a clock synchronization command.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), 'IEC61850_MMS_MMS_READ', 'MMS read', 'MMS_READ', 'MMS_READ', 'MMS read', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC61850_MMS engineering practice', 'MMS read。', 'MMS read.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), 'IEC61850_MMS_MMS_POLL_READ', 'MMS poll read', 'MMS_POLL_READ', 'MMS_POLL_READ', 'MMS poll read', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC61850_MMS engineering practice', 'MMS poll read。', 'MMS poll read.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), 'IEC61850_MMS_MMS_REPORT', 'MMS report control', 'MMS_REPORT', 'MMS_REPORT', 'MMS report control', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','REPORT'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REPORTING'), 'IEC61850_MMS engineering practice', 'MMS report control。', 'MMS report control.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), 'IEC61850_MMS_MMS_WRITE', 'MMS write', 'MMS_WRITE', 'MMS_WRITE', 'MMS write', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC61850_MMS engineering practice', 'MMS write。', 'MMS write.'),
(ref_code_id('PROTOCOL','IEC61850_MMS'), 'IEC61850_MMS_MMS_CONTROL', 'MMS control', 'MMS_CONTROL', 'MMS_CONTROL', 'MMS control', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'IEC61850_MMS engineering practice', 'MMS control。', 'MMS control.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), 'IEC61850_GOOSE_GOOSE_SUBSCRIBE', 'GOOSE subscribe', 'GOOSE_SUBSCRIBE', 'GOOSE_SUBSCRIBE', 'GOOSE subscribe', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','SUBSCRIBE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'IEC61850_GOOSE engineering practice', 'GOOSE subscribe。', 'GOOSE subscribe.'),
(ref_code_id('PROTOCOL','IEC61850_GOOSE'), 'IEC61850_GOOSE_GOOSE_PUBLISH', 'GOOSE publish', 'GOOSE_PUBLISH', 'GOOSE_PUBLISH', 'GOOSE publish', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','PUBLISH'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'IEC61850_GOOSE engineering practice', 'GOOSE publish。', 'GOOSE publish.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), 'IEC61850_SV_SV_SUBSCRIBE', 'Sampled value subscribe', 'SV_SUBSCRIBE', 'SV_SUBSCRIBE', 'Sampled value subscribe', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','SUBSCRIBE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'IEC61850_SV engineering practice', 'Sampled value subscribe。', 'Sampled value subscribe.'),
(ref_code_id('PROTOCOL','IEC61850_SV'), 'IEC61850_SV_SV_PUBLISH', 'Sampled value publish', 'SV_PUBLISH', 'SV_PUBLISH', 'Sampled value publish', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','PUBLISH'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'IEC61850_SV engineering practice', 'Sampled value publish。', 'Sampled value publish.'),
(ref_code_id('PROTOCOL','MQTT'), 'MQTT_MQTT_SUBSCRIBE', 'MQTT subscribe', 'MQTT_SUBSCRIBE', 'MQTT_SUBSCRIBE', 'MQTT subscribe', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','SUBSCRIBE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','REMOTE_TO_LOCAL'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'MQTT engineering practice', 'MQTT subscribe。', 'MQTT subscribe.'),
(ref_code_id('PROTOCOL','MQTT'), 'MQTT_MQTT_PUBLISH', 'MQTT publish', 'MQTT_PUBLISH', 'MQTT_PUBLISH', 'MQTT publish', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','PUBLISH'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','PUBLISH_SUBSCRIBE'), 'MQTT engineering practice', 'MQTT publish。', 'MQTT publish.'),
(ref_code_id('PROTOCOL','HTTP_REST'), 'HTTP_REST_HTTP_GET', 'HTTP GET', 'HTTP_GET', 'HTTP_GET', 'HTTP GET', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'HTTP_REST engineering practice', 'HTTP GET。', 'HTTP GET.'),
(ref_code_id('PROTOCOL','HTTP_REST'), 'HTTP_REST_HTTP_POLL_GET', 'HTTP scheduled GET', 'HTTP_POLL_GET', 'HTTP_POLL_GET', 'HTTP scheduled GET', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','READ'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'HTTP_REST engineering practice', 'HTTP scheduled GET。', 'HTTP scheduled GET.'),
(ref_code_id('PROTOCOL','HTTP_REST'), 'HTTP_REST_HTTP_POST', 'HTTP POST', 'HTTP_POST', 'HTTP_POST', 'HTTP POST', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','WRITE'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'HTTP_REST engineering practice', 'HTTP POST。', 'HTTP POST.'),
(ref_code_id('PROTOCOL','HTTP_REST'), 'HTTP_REST_HTTP_CONTROL', 'HTTP control API', 'HTTP_CONTROL', 'HTTP_CONTROL', 'HTTP control API', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','CONTROL'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_TO_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'HTTP_REST engineering practice', 'HTTP control API。', 'HTTP control API.'),
(ref_code_id('PROTOCOL','HTTP_REST'), 'HTTP_REST_HTTP_PUBLISH', 'HTTP callback/publish', 'HTTP_PUBLISH', 'HTTP_PUBLISH', 'HTTP callback/publish', ref_code_id('PROTOCOL_OPERATION_SEMANTIC','PUBLISH'), ref_code_id('PROTOCOL_OPERATION_DIRECTION','LOCAL_REPORT_REMOTE'), ref_code_id('REQUEST_RESPONSE_MODE','REQUEST_RESPONSE'), 'HTTP_REST engineering practice', 'HTTP callback/publish。', 'HTTP callback/publish.');
INSERT INTO cfg_protocol_operation_role(protocol_operation_def_id, protocol_role_ref_id, point_table_usage_ref_id, requires_point_table, requires_write_value, requires_response_mapping, requires_confirm, description_zh, description_en) VALUES
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MODBUS') AND operation_identifier='MODBUS_MODBUS_READ'), ref_code_id('PROTOCOL_ROLE','MODBUS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'MODBUS READ_ONCE 组合。', 'MODBUS READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MODBUS') AND operation_identifier='MODBUS_MODBUS_POLL_READ'), ref_code_id('PROTOCOL_ROLE','MODBUS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'MODBUS POLL_READ 组合。', 'MODBUS POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MODBUS') AND operation_identifier='MODBUS_MODBUS_WRITE'), ref_code_id('PROTOCOL_ROLE','MODBUS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'MODBUS WRITE_ONCE 组合。', 'MODBUS WRITE_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MODBUS') AND operation_identifier='MODBUS_MODBUS_CONTROL'), ref_code_id('PROTOCOL_ROLE','MODBUS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'MODBUS CONTROL 组合。', 'MODBUS CONTROL combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_READ'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'OPCUA READ_ONCE 组合。', 'OPCUA READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_POLL_READ'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'OPCUA POLL_READ 组合。', 'OPCUA POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_SUBSCRIBE'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'OPCUA SUBSCRIBE 组合。', 'OPCUA SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_WRITE'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'OPCUA WRITE_ONCE 组合。', 'OPCUA WRITE_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_CONTROL'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'OPCUA CONTROL 组合。', 'OPCUA CONTROL combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','OPCUA') AND operation_identifier='OPCUA_OPCUA_CALL_METHOD'), ref_code_id('PROTOCOL_ROLE','OPCUA_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, false, 'OPCUA CALL_METHOD 组合。', 'OPCUA CALL_METHOD combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','ADS') AND operation_identifier='ADS_ADS_READ'), ref_code_id('PROTOCOL_ROLE','ADS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'ADS READ_ONCE 组合。', 'ADS READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','ADS') AND operation_identifier='ADS_ADS_POLL_READ'), ref_code_id('PROTOCOL_ROLE','ADS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'ADS POLL_READ 组合。', 'ADS POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','ADS') AND operation_identifier='ADS_ADS_NOTIFICATION'), ref_code_id('PROTOCOL_ROLE','ADS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'ADS SUBSCRIBE 组合。', 'ADS SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','ADS') AND operation_identifier='ADS_ADS_WRITE'), ref_code_id('PROTOCOL_ROLE','ADS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'ADS WRITE_ONCE 组合。', 'ADS WRITE_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','ADS') AND operation_identifier='ADS_ADS_CONTROL'), ref_code_id('PROTOCOL_ROLE','ADS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'ADS CONTROL 组合。', 'ADS CONTROL combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_INTERROGATION_MASTER'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'IEC101 READ_ONCE 组合。', 'IEC101 READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_PERIODIC_READ'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'IEC101 POLL_READ 组合。', 'IEC101 POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_RESPOND_INTERROGATION'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','SERVE_RESPONSE_SET'), true, false, true, false, 'IEC101 RESPOND_READ 组合。', 'IEC101 RESPOND_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_SERVE_REPORT'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','REPORT_DATASET'), true, false, true, false, 'IEC101 SERVE_REPORT 组合。', 'IEC101 SERVE_REPORT combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_CLOCK_SYNC_ACCEPT'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'IEC101 WRITE_ONCE 服务端写入处理组合。', 'IEC101 WRITE_ONCE server-side write handler combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC101') AND operation_identifier='IEC101_IEC101_ACCEPT_CONTROL'), ref_code_id('PROTOCOL_ROLE','IEC101_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC101 CONTROL 服务端控制处理组合。', 'IEC101 CONTROL server-side control handler combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_GENERAL_INTERROGATION'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'IEC104 发送站总召组合。', 'IEC104 send-general-interrogation combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_RECEIVE_MONITOR_DATA'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'IEC104 接收监视数据组合。', 'IEC104 receive-monitor-data combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_SETPOINT_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'IEC104 发送设点命令组合。', 'IEC104 send-setpoint-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_SINGLE_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC104 发送单点遥控组合。', 'IEC104 send-single-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_DOUBLE_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC104 发送双点遥控组合。', 'IEC104 send-double-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_CLOCK_SYNCHRONIZATION'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLING_STATION'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), false, false, false, true, 'IEC104 发送时钟同步组合。', 'IEC104 send-clock-synchronization combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_RESPOND_GENERAL_INTERROGATION'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','SERVE_RESPONSE_SET'), true, false, true, false, 'IEC104 响应站总召组合。', 'IEC104 respond-general-interrogation combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_CYCLIC_DATA'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','REPORT_DATASET'), true, false, true, false, 'IEC104 周期上送组合。', 'IEC104 cyclic-data combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_SPONTANEOUS_DATA'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','REPORT_DATASET'), true, false, true, false, 'IEC104 变化上送组合。', 'IEC104 spontaneous-data combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_SEND_BACKGROUND_DATA'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','REPORT_DATASET'), true, false, true, false, 'IEC104 背景上送组合。', 'IEC104 background-data combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_ACCEPT_SETPOINT_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'IEC104 接收设点命令组合。', 'IEC104 accept-setpoint-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_ACCEPT_SINGLE_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC104 接收单点遥控组合。', 'IEC104 accept-single-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_ACCEPT_DOUBLE_COMMAND'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC104 接收双点遥控组合。', 'IEC104 accept-double-command combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC104') AND operation_identifier='IEC104_ACCEPT_CLOCK_SYNCHRONIZATION'), ref_code_id('PROTOCOL_ROLE','IEC104_CONTROLLED_STATION'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), false, false, false, true, 'IEC104 接收时钟同步组合。', 'IEC104 accept-clock-synchronization combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_MMS') AND operation_identifier='IEC61850_MMS_MMS_READ'), ref_code_id('PROTOCOL_ROLE','IEC61850_MMS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'IEC61850_MMS READ_ONCE 组合。', 'IEC61850_MMS READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_MMS') AND operation_identifier='IEC61850_MMS_MMS_POLL_READ'), ref_code_id('PROTOCOL_ROLE','IEC61850_MMS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'IEC61850_MMS POLL_READ 组合。', 'IEC61850_MMS POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_MMS') AND operation_identifier='IEC61850_MMS_MMS_REPORT'), ref_code_id('PROTOCOL_ROLE','IEC61850_MMS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'IEC61850_MMS SUBSCRIBE 组合。', 'IEC61850_MMS SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_MMS') AND operation_identifier='IEC61850_MMS_MMS_WRITE'), ref_code_id('PROTOCOL_ROLE','IEC61850_MMS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'IEC61850_MMS WRITE_ONCE 组合。', 'IEC61850_MMS WRITE_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_MMS') AND operation_identifier='IEC61850_MMS_MMS_CONTROL'), ref_code_id('PROTOCOL_ROLE','IEC61850_MMS_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'IEC61850_MMS CONTROL 组合。', 'IEC61850_MMS CONTROL combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_GOOSE') AND operation_identifier='IEC61850_GOOSE_GOOSE_SUBSCRIBE'), ref_code_id('PROTOCOL_ROLE','IEC61850_GOOSE_SUBSCRIBER'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'IEC61850_GOOSE SUBSCRIBE 组合。', 'IEC61850_GOOSE SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_GOOSE') AND operation_identifier='IEC61850_GOOSE_GOOSE_PUBLISH'), ref_code_id('PROTOCOL_ROLE','IEC61850_GOOSE_PUBLISHER'), ref_code_id('POINT_TABLE_USAGE','PUBLISH_PAYLOAD_SET'), true, false, false, false, 'IEC61850_GOOSE PUBLISH 组合。', 'IEC61850_GOOSE PUBLISH combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_SV') AND operation_identifier='IEC61850_SV_SV_SUBSCRIBE'), ref_code_id('PROTOCOL_ROLE','IEC61850_SV_SUBSCRIBER'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'IEC61850_SV SUBSCRIBE 组合。', 'IEC61850_SV SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','IEC61850_SV') AND operation_identifier='IEC61850_SV_SV_PUBLISH'), ref_code_id('PROTOCOL_ROLE','IEC61850_SV_PUBLISHER'), ref_code_id('POINT_TABLE_USAGE','PUBLISH_PAYLOAD_SET'), true, false, false, false, 'IEC61850_SV PUBLISH 组合。', 'IEC61850_SV PUBLISH combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MQTT') AND operation_identifier='MQTT_MQTT_SUBSCRIBE'), ref_code_id('PROTOCOL_ROLE','MQTT_SUBSCRIBER'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, true, false, 'MQTT SUBSCRIBE 组合。', 'MQTT SUBSCRIBE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','MQTT') AND operation_identifier='MQTT_MQTT_PUBLISH'), ref_code_id('PROTOCOL_ROLE','MQTT_PUBLISHER'), ref_code_id('POINT_TABLE_USAGE','PUBLISH_PAYLOAD_SET'), true, false, false, false, 'MQTT PUBLISH 组合。', 'MQTT PUBLISH combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','HTTP_REST') AND operation_identifier='HTTP_REST_HTTP_GET'), ref_code_id('PROTOCOL_ROLE','HTTP_REST_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'HTTP_REST READ_ONCE 组合。', 'HTTP_REST READ_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','HTTP_REST') AND operation_identifier='HTTP_REST_HTTP_POLL_GET'), ref_code_id('PROTOCOL_ROLE','HTTP_REST_CLIENT'), ref_code_id('POINT_TABLE_USAGE','ACQUIRE_POINT_SET'), true, false, false, false, 'HTTP_REST POLL_READ 组合。', 'HTTP_REST POLL_READ combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','HTTP_REST') AND operation_identifier='HTTP_REST_HTTP_POST'), ref_code_id('PROTOCOL_ROLE','HTTP_REST_CLIENT'), ref_code_id('POINT_TABLE_USAGE','COMMAND_TARGET_SET'), true, true, false, true, 'HTTP_REST WRITE_ONCE 组合。', 'HTTP_REST WRITE_ONCE combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','HTTP_REST') AND operation_identifier='HTTP_REST_HTTP_CONTROL'), ref_code_id('PROTOCOL_ROLE','HTTP_REST_CLIENT'), ref_code_id('POINT_TABLE_USAGE','CONTROL_TARGET_SET'), true, true, false, true, 'HTTP_REST CONTROL 组合。', 'HTTP_REST CONTROL combination.'),
((SELECT cfg_protocol_operation_def_id FROM cfg_protocol_operation_def WHERE protocol_ref_id=ref_code_id('PROTOCOL','HTTP_REST') AND operation_identifier='HTTP_REST_HTTP_PUBLISH'), ref_code_id('PROTOCOL_ROLE','HTTP_REST_CLIENT'), ref_code_id('POINT_TABLE_USAGE','PUBLISH_PAYLOAD_SET'), true, false, false, false, 'HTTP_REST PUBLISH 组合。', 'HTTP_REST PUBLISH combination.');

-- 11. Centralized value domains
INSERT INTO cfg_value_domain(domain_identifier,name_zh,name_en,data_type_ref_id,ref_code_type,description_zh,description_en) VALUES
('TRIGGER_EVENT_ONLY','仅事件触发','Event only',ref_code_id('DATA_TYPE','STRING'),'TRIGGER_MODE','只允许 EVENT。','Allows EVENT only.'),
('TRIGGER_SCHEDULED_ONLY','仅调度触发','Scheduled only',ref_code_id('DATA_TYPE','STRING'),'TRIGGER_MODE','只允许 SCHEDULED。','Allows SCHEDULED only.'),
('TRIGGER_MANUAL_EVENT','手动或事件触发','Manual or event',ref_code_id('DATA_TYPE','STRING'),'TRIGGER_MODE','允许 MANUAL 或 EVENT。','Allows MANUAL or EVENT.'),
('TRIGGER_ALL','全部任务触发方式','All task triggers',ref_code_id('DATA_TYPE','STRING'),'TRIGGER_MODE','允许 MANUAL、EVENT、SCHEDULED。','Allows MANUAL, EVENT, and SCHEDULED.'),
('POINT_ROLE_READ','读取源点角色','Read-source role',ref_code_id('DATA_TYPE','STRING'),'TASK_POINT_ROLE','只允许 READ_SOURCE。','Allows READ_SOURCE only.'),
('POINT_ROLE_WRITE','写入目标角色','Write-target role',ref_code_id('DATA_TYPE','STRING'),'TASK_POINT_ROLE','只允许 WRITE_TARGET。','Allows WRITE_TARGET only.'),
('POINT_ROLE_CONTROL','控制目标角色','Control-target role',ref_code_id('DATA_TYPE','STRING'),'TASK_POINT_ROLE','只允许 CONTROL_TARGET。','Allows CONTROL_TARGET only.'),
('POINT_ROLE_PUBLISH','发布字段角色','Publish-field role',ref_code_id('DATA_TYPE','STRING'),'TASK_POINT_ROLE','只允许 PUBLISH_FIELD。','Allows PUBLISH_FIELD only.'),
('POINT_ROLE_REPORT','报告字段角色','Report-field role',ref_code_id('DATA_TYPE','STRING'),'TASK_POINT_ROLE','只允许 REPORT_FIELD。','Allows REPORT_FIELD only.'),
('SAMPLE_EVENT_ONLY','仅事件采样','Event sample only',ref_code_id('DATA_TYPE','STRING'),'SAMPLE_MODE','只允许 EVENT。','Allows EVENT only.'),
('SAMPLE_CYCLIC_ONLY','仅周期采样','Cyclic sample only',ref_code_id('DATA_TYPE','STRING'),'SAMPLE_MODE','只允许 CYCLIC。','Allows CYCLIC only.'),
('SAMPLE_MANUAL_EVENT','手动或事件采样','Manual or event sample',ref_code_id('DATA_TYPE','STRING'),'SAMPLE_MODE','允许 MANUAL 或 EVENT。','Allows MANUAL or EVENT.'),
('SAMPLE_ALL','全部采样方式','All sample modes',ref_code_id('DATA_TYPE','STRING'),'SAMPLE_MODE','允许 MANUAL、EVENT、CYCLIC。','Allows MANUAL, EVENT, and CYCLIC.'),
('IEC104_MONITOR_TYPE_ID','IEC104监视类型','IEC104 monitor Type IDs',ref_code_id('DATA_TYPE','STRING'),'IEC104_TYPE_ID','允许任务使用的 IEC104 M_* 监视类型。','IEC104 M_* monitor Type IDs allowed in tasks.'),
('IEC104_SETPOINT_TYPE_ID','IEC104设点类型','IEC104 setpoint Type IDs',ref_code_id('DATA_TYPE','STRING'),'IEC104_TYPE_ID','允许 C_SE_NA/NB/NC_1。','Allows C_SE_NA/NB/NC_1.'),
('IEC104_SINGLE_COMMAND_TYPE_ID','IEC104单点命令类型','IEC104 single-command Type ID',ref_code_id('DATA_TYPE','STRING'),'IEC104_TYPE_ID','只允许 C_SC_NA_1。','Allows C_SC_NA_1 only.'),
('IEC104_DOUBLE_COMMAND_TYPE_ID','IEC104双点命令类型','IEC104 double-command Type ID',ref_code_id('DATA_TYPE','STRING'),'IEC104_TYPE_ID','只允许 C_DC_NA_1。','Allows C_DC_NA_1 only.'),
('ASDU_SEQUENCE_MODE','ASDU顺序地址模式','ASDU sequence mode',ref_code_id('DATA_TYPE','STRING'),NULL,'AUTO、SQ0、SQ1。','AUTO, SQ0, and SQ1.'),
('QUALITY_HANDLING_MODE','质量处理方式','Quality handling mode',ref_code_id('DATA_TYPE','STRING'),NULL,'接收质量位处理方式。','Quality handling modes for received data.');

INSERT INTO cfg_value_domain_item(cfg_value_domain_id,value_code,ref_code_id,name_zh,name_en,sort_order,description_zh,description_en)
SELECT d.cfg_value_domain_id,r.code,r.ref_code_id,r.name_zh,r.name_en,r.sort_order,r.description_zh,r.description_en
FROM cfg_value_domain d JOIN ref_code r ON
 (d.domain_identifier='TRIGGER_EVENT_ONLY' AND r.ref_type='TRIGGER_MODE' AND r.code='EVENT') OR
 (d.domain_identifier='TRIGGER_SCHEDULED_ONLY' AND r.ref_type='TRIGGER_MODE' AND r.code='SCHEDULED') OR
 (d.domain_identifier='TRIGGER_MANUAL_EVENT' AND r.ref_type='TRIGGER_MODE' AND r.code IN ('MANUAL','EVENT')) OR
 (d.domain_identifier='TRIGGER_ALL' AND r.ref_type='TRIGGER_MODE') OR
 (d.domain_identifier='POINT_ROLE_READ' AND r.ref_type='TASK_POINT_ROLE' AND r.code='READ_SOURCE') OR
 (d.domain_identifier='POINT_ROLE_WRITE' AND r.ref_type='TASK_POINT_ROLE' AND r.code='WRITE_TARGET') OR
 (d.domain_identifier='POINT_ROLE_CONTROL' AND r.ref_type='TASK_POINT_ROLE' AND r.code='CONTROL_TARGET') OR
 (d.domain_identifier='POINT_ROLE_PUBLISH' AND r.ref_type='TASK_POINT_ROLE' AND r.code='PUBLISH_FIELD') OR
 (d.domain_identifier='POINT_ROLE_REPORT' AND r.ref_type='TASK_POINT_ROLE' AND r.code='REPORT_FIELD') OR
 (d.domain_identifier='SAMPLE_EVENT_ONLY' AND r.ref_type='SAMPLE_MODE' AND r.code='EVENT') OR
 (d.domain_identifier='SAMPLE_CYCLIC_ONLY' AND r.ref_type='SAMPLE_MODE' AND r.code='CYCLIC') OR
 (d.domain_identifier='SAMPLE_MANUAL_EVENT' AND r.ref_type='SAMPLE_MODE' AND r.code IN ('MANUAL','EVENT')) OR
 (d.domain_identifier='SAMPLE_ALL' AND r.ref_type='SAMPLE_MODE') OR
 (d.domain_identifier='IEC104_MONITOR_TYPE_ID' AND r.ref_type='IEC104_TYPE_ID' AND EXISTS (SELECT 1 FROM cfg_iec104_type_def td JOIN ref_code tc ON tc.ref_code_id=td.type_category_ref_id WHERE td.type_id_ref_id=r.ref_code_id AND tc.code IN ('PROCESS_MONITOR','COUNTER_MONITOR','PROTECTION_MONITOR') AND td.point_registration_supported)) OR
 (d.domain_identifier='IEC104_SETPOINT_TYPE_ID' AND r.ref_type='IEC104_TYPE_ID' AND r.code IN ('C_SE_NA_1','C_SE_NB_1','C_SE_NC_1')) OR
 (d.domain_identifier='IEC104_SINGLE_COMMAND_TYPE_ID' AND r.ref_type='IEC104_TYPE_ID' AND r.code='C_SC_NA_1') OR
 (d.domain_identifier='IEC104_DOUBLE_COMMAND_TYPE_ID' AND r.ref_type='IEC104_TYPE_ID' AND r.code='C_DC_NA_1');

INSERT INTO cfg_value_domain_item(cfg_value_domain_id,value_code,name_zh,name_en,sort_order,description_zh,description_en)
SELECT d.cfg_value_domain_id,v.value_code,v.name_zh,v.name_en,v.sort_order,v.description_zh,v.description_en
FROM cfg_value_domain d JOIN (VALUES
 ('ASDU_SEQUENCE_MODE','AUTO','自动','Auto',1,'驱动自动选择 SQ=0 或 SQ=1。','Driver selects SQ=0 or SQ=1.'),
 ('ASDU_SEQUENCE_MODE','SQ0','显式地址','Explicit addresses',2,'每个信息对象携带 IOA。','Each information object carries an IOA.'),
 ('ASDU_SEQUENCE_MODE','SQ1','顺序地址','Sequential addresses',3,'仅首个对象携带 IOA，后续地址连续递增。','Only the first object carries an IOA; later addresses are sequential.'),
 ('QUALITY_HANDLING_MODE','ACCEPT_ALL','接受全部','Accept all',1,'接受全部质量状态并透传。','Accept and propagate all quality states.'),
 ('QUALITY_HANDLING_MODE','REJECT_INVALID','拒绝无效质量','Reject invalid',2,'拒绝 invalid 数据。','Reject invalid data.'),
 ('QUALITY_HANDLING_MODE','MARK_INVALID','标记无效质量','Mark invalid',3,'保留数据并标记为无效。','Keep data and mark it invalid.')
) v(domain_identifier,value_code,name_zh,name_en,sort_order,description_zh,description_en)
ON d.domain_identifier=v.domain_identifier;

-- 12. Core field constraints for every mapping
INSERT INTO cfg_task_field_constraint(cfg_protocol_operation_role_id,constrained_field_ref_id,cfg_value_domain_id,default_value_code,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,
       ref_code_id('TASK_CONSTRAINT_FIELD','TRIGGER_MODE'),
       d.cfg_value_domain_id,
       CASE
         WHEN op.operation_identifier='IEC104_SEND_BACKGROUND_DATA' THEN 'SCHEDULED'
         WHEN op.operation_identifier IN (
              'IEC104_RESPOND_GENERAL_INTERROGATION','IEC104_RECEIVE_MONITOR_DATA',
              'IEC104_SEND_CYCLIC_DATA','IEC104_SEND_SPONTANEOUS_DATA',
              'IEC104_ACCEPT_SETPOINT_COMMAND','IEC104_ACCEPT_SINGLE_COMMAND',
              'IEC104_ACCEPT_DOUBLE_COMMAND','IEC104_ACCEPT_CLOCK_SYNCHRONIZATION'
         ) THEN 'EVENT'
         WHEN op.operation_identifier IN (
              'IEC104_SEND_SETPOINT_COMMAND','IEC104_SEND_SINGLE_COMMAND','IEC104_SEND_DOUBLE_COMMAND'
         ) THEN 'MANUAL'
         WHEN op.operation_identifier IN (
              'IEC104_SEND_GENERAL_INTERROGATION','IEC104_SEND_CLOCK_SYNCHRONIZATION'
         ) THEN 'EVENT'
         WHEN op.operation_identifier LIKE '%POLL%'
           OR op.operation_identifier LIKE '%PUBLISH%' THEN 'SCHEDULED'
         WHEN op.operation_identifier LIKE '%SUBSCRIBE%'
           OR op.operation_identifier LIKE '%REPORT%'
           OR op.operation_identifier LIKE '%NOTIFICATION%'
           OR op.operation_identifier LIKE '%RESPOND%'
           OR op.operation_identifier LIKE '%RECEIVE%'
           OR op.operation_identifier LIKE '%ACCEPT%' THEN 'EVENT'
         ELSE 'MANUAL'
       END,
       '该协议原生操作—协议角色组合允许的触发方式。',
       'Allowed trigger mode for this protocol-operation and protocol-role combination.'
FROM cfg_protocol_operation_role m
JOIN cfg_protocol_operation_def op
  ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
JOIN cfg_value_domain d
  ON d.domain_identifier=CASE
       WHEN op.operation_identifier='IEC104_SEND_BACKGROUND_DATA' THEN 'TRIGGER_SCHEDULED_ONLY'
       WHEN op.operation_identifier IN (
            'IEC104_RESPOND_GENERAL_INTERROGATION','IEC104_RECEIVE_MONITOR_DATA',
            'IEC104_SEND_CYCLIC_DATA','IEC104_SEND_SPONTANEOUS_DATA',
            'IEC104_ACCEPT_SETPOINT_COMMAND','IEC104_ACCEPT_SINGLE_COMMAND',
            'IEC104_ACCEPT_DOUBLE_COMMAND','IEC104_ACCEPT_CLOCK_SYNCHRONIZATION'
       ) THEN 'TRIGGER_EVENT_ONLY'
       WHEN op.operation_identifier IN (
            'IEC104_SEND_SETPOINT_COMMAND','IEC104_SEND_SINGLE_COMMAND','IEC104_SEND_DOUBLE_COMMAND'
       ) THEN 'TRIGGER_MANUAL_EVENT'
       WHEN op.operation_identifier IN (
            'IEC104_SEND_GENERAL_INTERROGATION','IEC104_SEND_CLOCK_SYNCHRONIZATION'
       ) THEN 'TRIGGER_ALL'
       WHEN op.operation_identifier LIKE '%POLL%'
         OR op.operation_identifier LIKE '%PUBLISH%' THEN 'TRIGGER_SCHEDULED_ONLY'
       WHEN op.operation_identifier LIKE '%SUBSCRIBE%'
         OR op.operation_identifier LIKE '%REPORT%'
         OR op.operation_identifier LIKE '%NOTIFICATION%'
         OR op.operation_identifier LIKE '%RESPOND%'
         OR op.operation_identifier LIKE '%RECEIVE%'
         OR op.operation_identifier LIKE '%ACCEPT%' THEN 'TRIGGER_EVENT_ONLY'
       WHEN op.operation_identifier LIKE '%WRITE%'
         OR op.operation_identifier LIKE '%CONTROL%'
         OR op.operation_identifier LIKE '%COMMAND%'
         OR op.operation_identifier LIKE '%METHOD%' THEN 'TRIGGER_MANUAL_EVENT'
       ELSE 'TRIGGER_ALL'
     END;

INSERT INTO cfg_task_field_constraint(cfg_protocol_operation_role_id,constrained_field_ref_id,cfg_value_domain_id,default_value_code,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,ref_code_id('TASK_CONSTRAINT_FIELD','POINT_ROLE'),d.cfg_value_domain_id,
       CASE u.code WHEN 'ACQUIRE_POINT_SET' THEN 'READ_SOURCE' WHEN 'COMMAND_TARGET_SET' THEN 'WRITE_TARGET' WHEN 'CONTROL_TARGET_SET' THEN 'CONTROL_TARGET' WHEN 'PUBLISH_PAYLOAD_SET' THEN 'PUBLISH_FIELD' ELSE 'REPORT_FIELD' END,
       '该协议操作映射允许的任务点角色。','Allowed task-point roles for this protocol-operation mapping.'
FROM cfg_protocol_operation_role m JOIN ref_code u ON u.ref_code_id=m.point_table_usage_ref_id
JOIN cfg_value_domain d ON d.domain_identifier=CASE u.code WHEN 'ACQUIRE_POINT_SET' THEN 'POINT_ROLE_READ' WHEN 'COMMAND_TARGET_SET' THEN 'POINT_ROLE_WRITE' WHEN 'CONTROL_TARGET_SET' THEN 'POINT_ROLE_CONTROL' WHEN 'PUBLISH_PAYLOAD_SET' THEN 'POINT_ROLE_PUBLISH' ELSE 'POINT_ROLE_REPORT' END;

INSERT INTO cfg_task_field_constraint(cfg_protocol_operation_role_id,constrained_field_ref_id,cfg_value_domain_id,default_value_code,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,ref_code_id('TASK_CONSTRAINT_FIELD','SAMPLE_MODE'),d.cfg_value_domain_id,
       CASE td.domain_identifier WHEN 'TRIGGER_SCHEDULED_ONLY' THEN 'CYCLIC' WHEN 'TRIGGER_EVENT_ONLY' THEN 'EVENT' WHEN 'TRIGGER_MANUAL_EVENT' THEN 'MANUAL' ELSE 'MANUAL' END,
       '该协议操作映射允许的任务点采样方式。','Allowed task-point sample modes for this protocol-operation mapping.'
FROM cfg_protocol_operation_role m
JOIN cfg_task_field_constraint tc ON tc.cfg_protocol_operation_role_id=m.cfg_protocol_operation_role_id
JOIN ref_code f ON f.ref_code_id=tc.constrained_field_ref_id AND f.code='TRIGGER_MODE'
JOIN cfg_value_domain td ON td.cfg_value_domain_id=tc.cfg_value_domain_id
JOIN cfg_value_domain d ON d.domain_identifier=CASE td.domain_identifier WHEN 'TRIGGER_SCHEDULED_ONLY' THEN 'SAMPLE_CYCLIC_ONLY' WHEN 'TRIGGER_EVENT_ONLY' THEN 'SAMPLE_EVENT_ONLY' WHEN 'TRIGGER_MANUAL_EVENT' THEN 'SAMPLE_MANUAL_EVENT' ELSE 'SAMPLE_ALL' END;

INSERT INTO cfg_task_field_constraint(cfg_protocol_operation_role_id,constrained_field_ref_id,cfg_value_domain_id,default_value_code,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,ref_code_id('TASK_CONSTRAINT_FIELD','PROTOCOL_TYPE_ID'),d.cfg_value_domain_id,
       (SELECT value_code FROM cfg_value_domain_item WHERE cfg_value_domain_id=d.cfg_value_domain_id ORDER BY sort_order,value_code LIMIT 1),
       'IEC104 操作允许的 Type ID。','IEC104 Type IDs allowed by the operation.'
FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
JOIN cfg_value_domain d ON d.domain_identifier=CASE
 WHEN op.operation_identifier IN ('IEC104_SEND_SETPOINT_COMMAND','IEC104_ACCEPT_SETPOINT_COMMAND') THEN 'IEC104_SETPOINT_TYPE_ID'
 WHEN op.operation_identifier IN ('IEC104_SEND_SINGLE_COMMAND','IEC104_ACCEPT_SINGLE_COMMAND') THEN 'IEC104_SINGLE_COMMAND_TYPE_ID'
 WHEN op.operation_identifier IN ('IEC104_SEND_DOUBLE_COMMAND','IEC104_ACCEPT_DOUBLE_COMMAND') THEN 'IEC104_DOUBLE_COMMAND_TYPE_ID'
 ELSE 'IEC104_MONITOR_TYPE_ID' END
WHERE op.protocol_ref_id=ref_code_id('PROTOCOL','IEC104')
  AND op.operation_identifier NOT IN ('IEC104_SEND_CLOCK_SYNCHRONIZATION','IEC104_ACCEPT_CLOCK_SYNCHRONIZATION');

-- 13. Task parameter definitions
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,text_pattern,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,'schedule_expression','调度表达式','Schedule expression',ref_code_id('DATA_TYPE','STRING'),NULL,NULL,false,NULL,NULL,NULL,'^(rate[(][1-9][0-9]*(ms|s|m|h)[)]|cron[(].+[)])$','仅 SCHEDULED 任务必填；支持 rate(5s) 或 cron(...)。','Required only for SCHEDULED tasks; supports rate(5s) or cron(...).'
FROM cfg_protocol_operation_role m
JOIN cfg_task_field_constraint fc ON fc.cfg_protocol_operation_role_id=m.cfg_protocol_operation_role_id
JOIN ref_code f ON f.ref_code_id=fc.constrained_field_ref_id AND f.code='TRIGGER_MODE'
WHERE m.enabled
  AND EXISTS (
      SELECT 1 FROM cfg_value_domain_item di
      WHERE di.cfg_value_domain_id=fc.cfg_value_domain_id
        AND di.value_code='SCHEDULED'
        AND di.enabled=TRUE AND di.valid_to IS NULL
  );

INSERT INTO cfg_task_param_dependency_rule(target_task_param_def_id,condition_field_ref_id,condition_operator_ref_id,condition_value_code,rule_action_ref_id,description_zh,description_en)
SELECT d.task_param_def_id,ref_code_id('TASK_CONSTRAINT_FIELD','TRIGGER_MODE'),ref_code_id('VALIDATION_OPERATOR','EQUALS'),'SCHEDULED',ref_code_id('PARAM_RULE_ACTION','REQUIRED'),'调度任务必须配置 schedule_expression。','Scheduled tasks require schedule_expression.'
FROM task_param_def d WHERE d.param_identifier='schedule_expression';

-- IEC104 common ASDU batching parameters for server responses and active transmissions
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.param_identifier,v.name_zh,v.name_en,v.data_type_ref_id,v.unit_id,v.domain_id,v.required,v.default_value,v.numeric_min,v.numeric_max,v.description_zh,v.description_en
FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN LATERAL (VALUES
 ('max_objects_per_asdu','每ASDU最大对象数','Maximum objects per ASDU',ref_code_id('DATA_TYPE','INT32'),NULL::BIGINT,NULL::BIGINT,false,'40',1::NUMERIC,127::NUMERIC,'单个 ASDU 最大信息对象数。','Maximum information objects in one ASDU.'),
 ('sequence_mode','顺序地址模式','Sequence address mode',ref_code_id('DATA_TYPE','STRING'),NULL,(SELECT cfg_value_domain_id FROM cfg_value_domain WHERE domain_identifier='ASDU_SEQUENCE_MODE'),false,'AUTO',NULL,NULL,'AUTO、SQ0 或 SQ1。','AUTO, SQ0, or SQ1.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,unit_id,domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
WHERE op.operation_identifier IN ('IEC104_RESPOND_GENERAL_INTERROGATION','IEC104_SEND_CYCLIC_DATA','IEC104_SEND_SPONTANEOUS_DATA','IEC104_SEND_BACKGROUND_DATA');

-- Station interrogation parameters
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.* FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN (VALUES
 ('startdt_required','执行前要求STARTDT','Require STARTDT',ref_code_id('DATA_TYPE','BOOL'),NULL::BIGINT,NULL::BIGINT,false,'true',NULL::NUMERIC,NULL::NUMERIC,'执行召唤前要求数据传输已启动。','Require STARTDT before interrogation.'),
 ('wait_activation_confirmation','等待激活确认','Wait activation confirmation',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'等待 activation confirmation。','Wait for activation confirmation.'),
 ('wait_activation_termination','等待激活终止','Wait activation termination',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'等待 activation termination；总流程超时使用 task.timeout_ms。','Wait for activation termination; the overall timeout is task.timeout_ms.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
WHERE op.operation_identifier IN ('IEC104_SEND_GENERAL_INTERROGATION');


INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,required,default_value,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.* FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN (VALUES
 ('send_activation_confirmation','发送激活确认','Send activation confirmation',ref_code_id('DATA_TYPE','BOOL'),false,'true','数据发送前返回激活确认。','Send activation confirmation before data.'),
 ('send_activation_termination','发送激活终止','Send activation termination',ref_code_id('DATA_TYPE','BOOL'),false,'true','响应结束后返回激活终止。','Send activation termination after data.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,required,default_value,description_zh,description_en)
WHERE op.operation_identifier IN ('IEC104_RESPOND_GENERAL_INTERROGATION');

-- Controlled-station monitor-data tasks
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,'period_ms','背景刷新间隔','Background transmission period',ref_code_id('DATA_TYPE','INT32'),ref_code_id('UNIT','MS'),true,'60000',1,NULL,'背景上送间隔。','Background transmission interval.'
FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id WHERE op.operation_identifier='IEC104_SEND_BACKGROUND_DATA';

-- Controlling-station receive parameters
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.* FROM cfg_protocol_operation_role m JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN (VALUES
 ('accept_cyclic','接收周期数据','Accept cyclic data',ref_code_id('DATA_TYPE','BOOL'),NULL::BIGINT,NULL::BIGINT,false,'true',NULL::NUMERIC,NULL::NUMERIC,'是否接收 COT=CYCLIC 的监视数据。','Whether to accept monitor data with COT=CYCLIC.'),
 ('accept_spontaneous','接收变化数据','Accept spontaneous data',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'是否接收 COT=SPONTANEOUS 的监视数据。','Whether to accept monitor data with COT=SPONTANEOUS.'),
 ('accept_background','接收背景数据','Accept background data',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'是否接收 COT=BACKGROUND 的监视数据。','Whether to accept monitor data with COT=BACKGROUND.'),
 ('accept_interrogated','接收召唤响应数据','Accept interrogation-response data',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'是否接收站总召和组召响应监视数据。','Whether to accept station/group interrogation-response monitor data.'),
 ('deduplicate','去重','Deduplicate',ref_code_id('DATA_TYPE','BOOL'),NULL,NULL,false,'true',NULL,NULL,'按 CA、IOA、Type ID、时标和值去重。','Deduplicate by CA, IOA, Type ID, timestamp, and value.'),
 ('stale_timeout_ms','数据陈旧超时','Stale timeout',ref_code_id('DATA_TYPE','INT32'),ref_code_id('UNIT','MS'),NULL,false,'60000',1,NULL,'未刷新超过此时间标记陈旧。','Mark data stale after this interval.'),
 ('quality_handling','质量处理策略','Quality handling',ref_code_id('DATA_TYPE','STRING'),NULL,(SELECT cfg_value_domain_id FROM cfg_value_domain WHERE domain_identifier='QUALITY_HANDLING_MODE'),false,'MARK_INVALID',NULL,NULL,'质量描述符处理策略。','Quality-descriptor handling policy.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,cfg_value_domain_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
WHERE op.operation_identifier='IEC104_RECEIVE_MONITOR_DATA';

-- Command parameters: controlling-station send and controlled-station accept semantics are defined separately.
INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.*
FROM cfg_protocol_operation_role m
JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN (VALUES
 ('select_before_operate','选择后执行','Select before operate',ref_code_id('DATA_TYPE','BOOL'),NULL::BIGINT,false,'false',NULL::NUMERIC,NULL::NUMERIC,'是否采用选择后执行；命令总超时使用 task.timeout_ms。','Whether to use select-before-operate; command timeout is task.timeout_ms.'),
 ('wait_activation_confirmation','等待激活确认','Wait activation confirmation',ref_code_id('DATA_TYPE','BOOL'),NULL,false,'true',NULL,NULL,'是否等待对端激活确认。','Whether to wait for peer activation confirmation.'),
 ('wait_activation_termination','等待激活终止','Wait activation termination',ref_code_id('DATA_TYPE','BOOL'),NULL,false,'true',NULL,NULL,'是否等待对端激活终止。','Whether to wait for peer activation termination.'),
 ('readback_verify','回读校验','Readback verification',ref_code_id('DATA_TYPE','BOOL'),NULL,false,'false',NULL,NULL,'是否执行显式反馈点回读；默认关闭。','Whether to verify an explicitly mapped feedback point; disabled by default.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,engineering_unit_ref_id,required,default_value,numeric_min,numeric_max,description_zh,description_en)
WHERE op.operation_identifier IN ('IEC104_SEND_SETPOINT_COMMAND','IEC104_SEND_SINGLE_COMMAND','IEC104_SEND_DOUBLE_COMMAND');

INSERT INTO task_param_def(cfg_protocol_operation_role_id,param_identifier,name_zh,name_en,data_type_ref_id,required,default_value,description_zh,description_en)
SELECT m.cfg_protocol_operation_role_id,v.*
FROM cfg_protocol_operation_role m
JOIN cfg_protocol_operation_def op ON op.cfg_protocol_operation_def_id=m.protocol_operation_def_id
CROSS JOIN (VALUES
 ('require_select_before_operate','要求选择后执行','Require select before operate',ref_code_id('DATA_TYPE','BOOL'),false,'false','是否拒绝未经过选择阶段的执行命令。','Whether to reject execute commands without a preceding select phase.'),
 ('send_activation_confirmation','发送激活确认','Send activation confirmation',ref_code_id('DATA_TYPE','BOOL'),false,'true','是否向控制站返回激活确认。','Whether to send activation confirmation to the controlling station.'),
 ('send_activation_termination','发送激活终止','Send activation termination',ref_code_id('DATA_TYPE','BOOL'),false,'true','是否在命令处理完成后返回激活终止。','Whether to send activation termination after command processing.')
) v(param_identifier,name_zh,name_en,data_type_ref_id,required,default_value,description_zh,description_en)
WHERE op.operation_identifier IN ('IEC104_ACCEPT_SETPOINT_COMMAND','IEC104_ACCEPT_SINGLE_COMMAND','IEC104_ACCEPT_DOUBLE_COMMAND');

COMMIT;
