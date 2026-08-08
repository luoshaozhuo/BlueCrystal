-- BlueCrystal Whale 基础元数据 DML v2.14.0
-- 与 02_bluecrystal_schema_ddl_v2_14_0.sql 配套。
-- 当前协议范围：IEC104、ADS；comm_* 仅描述外部 Remote Connection。
-- Meta 数据按二级职责前缀组织，新增 meta_topo_elec_ / meta_topo_mech_ / meta_topo_comm_；运行时 View 仅输出 Meta 实际值，不暴露 Meta ID。

BEGIN;
SET search_path TO whale, public;

INSERT INTO whale.meta_org_organization_type (code, description_zh, sort_order, enabled) VALUES
('GROUP', '集团级组织，管理多个区域公司或项目公司。', 1, TRUE),
('REGIONAL_COMPANY', '区域公司，负责一定地理区域内多个场站或项目公司的经营管理。', 2, TRUE),
('PROJECT_COMPANY', '项目公司或电场公司，承担具体风光储项目运营责任。', 3, TRUE),
('DEPARTMENT', '公司内部职能部门，例如运行管理、设备维保、控制通信和安全管理。', 4, TRUE);

INSERT INTO whale.meta_org_site_type (code, description_zh, sort_order, enabled) VALUES
('WIND_PLANT', '以风力发电为主体的并网场站。', 1, TRUE),
('PV_PLANT', '以光伏发电为主体的并网场站。', 2, TRUE),
('STORAGE_PLANT', '以电化学储能为主体的并网场站。', 3, TRUE),
('HYBRID_PLANT', '同时包含风电、光伏、储能中两类及以上资源的并网场站。', 4, TRUE);

INSERT INTO whale.meta_org_responsibility_category (code, description_zh, sort_order, enabled) VALUES
('OPERATIONS', '负责场站日常运行、监盘、调度联系和运行方式执行。', 1, TRUE),
('MAINTENANCE', '负责设备检修、缺陷处理和维护计划执行。', 2, TRUE),
('CONTROL_COMMUNICATION', '负责自动化、通信、网络、控制系统和调度数据链路。', 3, TRUE),
('SAFETY', '负责安全生产、作业许可和安全监督。', 4, TRUE);

INSERT INTO whale.meta_equ_equipment_status (code, description_zh, sort_order, enabled) VALUES
('IN_SERVICE', '设备已投运并处于可参与生产或通信的状态。', 1, TRUE),
('STANDBY', '设备具备投入条件，但当前作为备用或待机设备。', 2, TRUE),
('MAINTENANCE', '设备处于计划检修或故障检修状态。', 3, TRUE),
('OUT_OF_SERVICE', '设备已停运或不再具备正常服务能力。', 4, TRUE);

INSERT INTO whale.meta_topo_elec_interface_type (code, description_zh, sort_order, enabled) VALUES
('ELECTRICAL_TERMINAL', '一次电气设备的电缆头、母线侧端子或其他电气连接界面。', 1, TRUE);

INSERT INTO whale.meta_topo_elec_connection_type (code, description_zh, sort_order, enabled) VALUES
('ELECTRICAL_CABLE', '一次交流或直流电力电缆连接。', 1, TRUE),
('BUSBAR', '一次电气母线连接。', 2, TRUE),
('OVERHEAD_LINE', '架空输电或集电线路连接。', 3, TRUE);

INSERT INTO whale.meta_topo_mech_interface_type (code, description_zh, sort_order, enabled) VALUES
('SHAFT_END', '旋转机械轴端连接界面。', 1, TRUE),
('FLANGE', '机械法兰连接界面。', 2, TRUE),
('STRUCTURAL_MOUNT', '结构安装或支撑连接界面。', 3, TRUE);

INSERT INTO whale.meta_topo_mech_connection_type (code, description_zh, sort_order, enabled) VALUES
('SHAFT', '两个轴端之间的轴系连接。', 1, TRUE),
('COUPLING', '通过联轴器建立的机械连接。', 2, TRUE),
('FLANGE_CONNECTION', '通过法兰建立的机械连接。', 3, TRUE),
('STRUCTURAL_CONNECTION', '设备或结构件之间的结构安装连接。', 4, TRUE);

INSERT INTO whale.meta_topo_comm_interface_type (code, description_zh, sort_order, enabled) VALUES
('ETHERNET_PORT', '铜缆以太网端口，例如 RJ45 电口。', 1, TRUE),
('FIBER_PORT', '光纤通信端口，例如 SFP/SFP+ 光口。', 2, TRUE),
('SERIAL_PORT', '串行通信端口，例如 RS-485/RS-232 端口。', 3, TRUE),
('TIME_SYNC_PORT', '专用于 IRIG-B、PPS、PTP 等时钟同步信号的接口。', 4, TRUE);

INSERT INTO whale.meta_topo_comm_connection_type (code, description_zh, sort_order, enabled) VALUES
('FIBER', '光纤链路或光缆纤芯。', 1, TRUE),
('COPPER_ETHERNET', '双绞线以太网链路。', 2, TRUE),
('RS485_BUS', 'RS-485 串行通信链路。', 3, TRUE),
('TIME_SYNC_LINK', '专用时钟同步传输链路。', 4, TRUE);

INSERT INTO whale.meta_point_data_type (code, description_zh, sort_order, enabled) VALUES
('BOOLEAN', '布尔值，适用于开关状态、启停命令等二值语义。', 1, TRUE),
('INT32', '32 位有符号整数。', 2, TRUE),
('INT64', '64 位有符号整数。', 3, TRUE),
('FLOAT32', '32 位 IEEE 754 浮点数。', 4, TRUE),
('FLOAT64', '64 位 IEEE 754 浮点数。', 5, TRUE),
('STRING', 'UTF-8 字符串。', 6, TRUE);

INSERT INTO whale.meta_point_unit (code, description_zh, sort_order, enabled) VALUES
('MW', '兆瓦，有功功率单位。', 1, TRUE),
('MVAR', '兆乏，无功功率单位。', 2, TRUE),
('KV', '千伏，电压单位。', 3, TRUE),
('A', '安培，电流单位。', 4, TRUE),
('HZ', '赫兹，频率单位。', 5, TRUE),
('MPS', '米每秒，风速等速度量单位。', 6, TRUE),
('RPM', '转每分钟，旋转机械转速单位。', 7, TRUE),
('DEG_C', '摄氏度，温度单位。', 8, TRUE),
('PERCENT', '百分比单位。', 9, TRUE);

INSERT INTO whale.meta_point_physical_quantity_category (code, description_zh, sort_order, enabled) VALUES
('ACTIVE_POWER', '有功功率及其设定值。', 1, TRUE),
('REACTIVE_POWER', '无功功率及其设定值。', 2, TRUE),
('VOLTAGE', '交流或直流电压。', 3, TRUE),
('CURRENT', '交流或直流电流。', 4, TRUE),
('FREQUENCY', '电网频率或其他频率量。', 5, TRUE),
('WIND_SPEED', '风速。', 6, TRUE),
('ROTATIONAL_SPEED', '转子、发电机等旋转部件转速。', 7, TRUE),
('TEMPERATURE', '温度。', 8, TRUE),
('STATUS', '设备运行、告警、开关等离散状态。', 9, TRUE),
('COMMAND', '启停、复位等离散控制命令。', 10, TRUE);


INSERT INTO whale.meta_task_operation_semantic (code, description_zh, sort_order, enabled) VALUES
('INTERROGATION', '召唤或读取一组远端信息对象。', 1, TRUE),
('REPORT', '向对端上送一组信息对象。', 2, TRUE),
('CONTROL', '向对端下发控制或设点。', 3, TRUE),
('RECEIVE_CONTROL', '接收并处理对端下发的控制或设点。', 4, TRUE),
('SUBSCRIBE', '持续接收对端的事件或变化上送。', 5, TRUE),
('READ', '主动读取远端点值。', 6, TRUE),
('WRITE', '主动向远端写入数据、设点、参数或命令值。', 7, TRUE);

INSERT INTO whale.meta_task_interaction_mode (code, description_zh, sort_order, enabled) VALUES
('REQUEST_RESPONSE', '由一方发起明确请求，另一方针对该请求返回响应；适用于总召等有请求—响应对应关系的操作。', 1, TRUE),
('PERIODIC_PUSH', '无需每次请求，由发送方按固定周期主动发送数据。', 2, TRUE),
('SPONTANEOUS_PUSH', '数据变化或事件发生后，由发送方主动上送。', 3, TRUE),
('COMMAND_CONFIRM', '控制命令下发后按协议完成激活确认、执行确认或其他命令确认流程。', 4, TRUE),
('SUBSCRIPTION', '建立持续订阅关系，由协议在订阅存续期间持续推送变化或周期数据。', 5, TRUE);

INSERT INTO whale.meta_task_trigger_mode (code, description_zh, sort_order, enabled) VALUES
('MANUAL', '由人工或上层 API 显式触发任务。', 1, TRUE),
('CYCLIC', '由调度器按固定周期触发任务。', 2, TRUE),
('EVENT', '由数据变化、内部事件或业务条件触发任务。', 3, TRUE),
('PROTOCOL_REQUEST', '由通信对端发来的协议请求触发响应任务，例如 IEC104 总召请求。', 4, TRUE);

INSERT INTO whale.meta_task_status (code, description_zh, sort_order, enabled) VALUES
('SCHEDULED', '任务配置已发布并允许调度执行。', 1, TRUE),
('STOPPED', '任务已正常停止，不再主动执行。', 2, TRUE),
('FAILED', '任务因不可恢复错误进入失败状态。', 3, TRUE),
('DISABLED', '任务配置被禁用。', 4, TRUE);

INSERT INTO whale.meta_task_retry_backoff_strategy (code, description_zh, sort_order, enabled) VALUES
('FIXED', '每次重试均使用固定时间间隔。', 1, TRUE);

INSERT INTO whale.meta_task_failure_action (code, description_zh, sort_order, enabled) VALUES
('SUSPEND', '连续失败达到阈值后暂停任务，等待人工或上层运行管理恢复。', 1, TRUE);

INSERT INTO whale.meta_task_concurrency_policy (code, description_zh, sort_order, enabled) VALUES
('FORBID', '同一任务已有实例运行时禁止再次启动新实例。', 1, TRUE),
('ALLOW', '允许同一任务在最大实例数约束内并发运行。', 2, TRUE);

INSERT INTO whale.meta_task_misfire_policy (code, description_zh, sort_order, enabled) VALUES
('SKIP', '错过计划触发时跳过该次执行，等待下一次合法触发。', 1, TRUE);

INSERT INTO whale.meta_point_source_value_update_mode (code, description_zh, sort_order, enabled) VALUES
('PERIODIC', '数据源自身按固定周期刷新值；value_update_interval_ms 必填。', 1, TRUE),
('ON_CHANGE', '数据源值在内部状态变化时刷新，不要求固定刷新周期。', 2, TRUE),
('ON_DEMAND', '仅在读取或其他外部请求发生时生成或刷新当前值。', 3, TRUE);

INSERT INTO whale.meta_ads_data_type (code, byte_size, description_zh, sort_order, enabled) VALUES
('BOOL', 1, 'ADS BOOL。', 1, TRUE),
('INT', 2, 'ADS 16 位有符号整数。', 2, TRUE),
('DINT', 4, 'ADS 32 位有符号整数。', 3, TRUE),
('REAL', 4, 'ADS 32 位 IEEE 754 浮点数。', 4, TRUE),
('LREAL', 8, 'ADS 64 位 IEEE 754 浮点数。', 5, TRUE),
('STRING', NULL, 'ADS STRING；实际长度由 PLC 符号定义决定。', 6, TRUE);

INSERT INTO whale.meta_ads_addressing_mode (code, description_zh, sort_order, enabled) VALUES
('SYMBOL', '按 TwinCAT/PLC 符号名寻址。', 1, TRUE),
('INDEX', '按 IndexGroup + IndexOffset 直接寻址。', 2, TRUE);

INSERT INTO whale.meta_ads_notification_mode (code, description_zh, sort_order, enabled) VALUES
('NONE', '不配置 ADS Device Notification；通过主动读取获取值。', 1, TRUE),
('CYCLIC', 'ADS Device Notification 按周期发送。', 2, TRUE),
('ON_CHANGE', 'ADS Device Notification 在值变化时发送。', 3, TRUE);

INSERT INTO whale.meta_iec104_type
(type_id_value, code, description_zh, sort_order, enabled) VALUES
(1, 'M_SP_NA_1', '单点信息，不带时标。', 1, TRUE),
(9, 'M_ME_NA_1', '测量值，归一化值，不带时标。', 2, TRUE),
(11, 'M_ME_NB_1', '测量值，标度化值，不带时标。', 3, TRUE),
(13, 'M_ME_NC_1', '测量值，短浮点数，不带时标。', 4, TRUE),
(30, 'M_SP_TB_1', '单点信息，带 CP56Time2a 时标。', 5, TRUE),
(34, 'M_ME_TD_1', '测量值，归一化值，带 CP56Time2a 时标。', 6, TRUE),
(35, 'M_ME_TE_1', '测量值，标度化值，带 CP56Time2a 时标。', 7, TRUE),
(36, 'M_ME_TF_1', '测量值，短浮点数，带 CP56Time2a 时标。', 8, TRUE),
(45, 'C_SC_NA_1', '单命令，用于开/停等二态控制。', 9, TRUE),
(50, 'C_SE_NC_1', '设定值命令，短浮点数。', 10, TRUE),
(100, 'C_IC_NA_1', '总召唤命令。', 11, TRUE);

INSERT INTO whale.meta_iec104_type_category (code, description_zh, sort_order, enabled) VALUES
('MONITOR', '监视方向信息，包括遥信、遥测、电度等信息对象。', 1, TRUE),
('CONTROL', '控制方向信息，包括遥控和设点命令。', 2, TRUE),
('SYSTEM', '系统命令，例如总召、时钟同步等。', 3, TRUE);

INSERT INTO whale.meta_iec104_information_value_type (code, description_zh, sort_order, enabled) VALUES
('SINGLE_POINT', '单点状态值。', 1, TRUE),
('NORMALIZED', '归一化测量值。', 2, TRUE),
('SCALED', '标度化整数测量值。', 3, TRUE),
('SHORT_FLOAT', '32 位短浮点测量值。', 4, TRUE),
('COMMAND', '控制命令值。', 5, TRUE);

INSERT INTO whale.meta_iec104_time_tag_type (code, description_zh, sort_order, enabled) VALUES
('NONE', '信息对象不携带时标。', 1, TRUE),
('CP24TIME2A', '三字节短时标，表达毫秒和分钟范围内的时间信息。', 2, TRUE),
('CP56TIME2A', '七字节绝对时标，包含毫秒、分钟、小时、日、月和年，可表达完整日期时间。', 3, TRUE);

INSERT INTO whale.meta_iec104_cause_of_transmission (code, description_zh, sort_order, enabled) VALUES
('PERIODIC', '周期传送，由周期机制触发的数据上送。', 1, TRUE),
('BACKGROUND', '背景扫描传送。', 2, TRUE),
('SPONTANEOUS', '自发传送，由值变化或事件触发。', 3, TRUE),
('INTERROGATED_BY_STATION', '响应站总召唤而发送的数据。', 4, TRUE),
('ACTIVATION', '命令或请求的激活。', 5, TRUE),
('ACTIVATION_CONFIRMATION', '对激活请求的确认。', 6, TRUE),
('ACTIVATION_TERMINATION', '激活过程结束。', 7, TRUE);

INSERT INTO whale.meta_iec104_command_mode (code, description_zh, sort_order, enabled) VALUES
('DIRECT', '直接执行命令，不先进行选择阶段。', 1, TRUE),
('SELECT_EXECUTE', '先选择目标并等待确认，再发送执行命令；用于需要选择后执行语义的控制。', 2, TRUE);

INSERT INTO whale.meta_comm_protocol
(protocol_identifier, standard_source, enabled) VALUES
('IEC104', 'IEC 60870-5-104', TRUE),
('ADS', 'Beckhoff ADS', TRUE);

INSERT INTO whale.meta_comm_protocol_role
(meta_comm_protocol_id, code, description_zh, sort_order, enabled) VALUES
(whale.protocol_id('IEC104'), 'CONTROLLED_STATION',
 '外部 Endpoint 是 IEC104 被控站；Whale 作为控制站主动连接 Remote host/port，执行总召、接收监视信息并下发控制。', 1, TRUE),
(whale.protocol_id('IEC104'), 'CONTROLLING_STATION',
 'IEC104 控制站角色保留为协议标准 Meta；当前 comm_* Remote Connection 不使用该角色，未来由 serv_* 承担对应本地服务场景。', 2, TRUE),
(whale.protocol_id('ADS'), 'SERVER',
 '外部 Endpoint 提供 ADS 服务；Whale 作为 ADS Client 主动连接并读取、订阅或写入变量。', 1, TRUE);

INSERT INTO whale.meta_task_protocol_operation
(meta_comm_protocol_role_id, operation_identifier, meta_task_operation_semantic_id,
 meta_task_interaction_mode_id, requires_acquisition_point_table, requires_delivery_point_table,
 requires_write_value, requires_protocol_confirmation, allowed_trigger_modes, description_zh, enabled)
VALUES
(whale.protocol_role_id('IEC104','CONTROLLED_STATION'), 'GENERAL_INTERROGATION',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='INTERROGATION'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='REQUEST_RESPONSE'),
 TRUE,FALSE,FALSE,TRUE, ARRAY['MANUAL','CYCLIC']::TEXT[],
 'Whale 主动向 Remote IEC104 被控站发起总召；Acquisition 点表指定需要纳入该任务的数据源点。',TRUE),
(whale.protocol_role_id('IEC104','CONTROLLED_STATION'), 'CONTROL_COMMAND',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='CONTROL'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='COMMAND_CONFIRM'),
 FALSE,TRUE,TRUE,TRUE, ARRAY['MANUAL','EVENT']::TEXT[],
 'Whale 向 Remote IEC104 被控站下发遥控或设点；Delivery 点表指定目标 Sink 点。',TRUE),
(whale.protocol_role_id('IEC104','CONTROLLED_STATION'), 'RECEIVE_SPONTANEOUS_REPORT',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='SUBSCRIBE'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='SPONTANEOUS_PUSH'),
 TRUE,FALSE,FALSE,FALSE, ARRAY['EVENT']::TEXT[],
 'Whale 接收 Remote IEC104 被控站自发上送；Acquisition 点表限定本任务关心的 Source 点。',TRUE),
(whale.protocol_role_id('ADS','SERVER'), 'READ',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='READ'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='REQUEST_RESPONSE'),
 TRUE,FALSE,FALSE,TRUE, ARRAY['MANUAL','CYCLIC']::TEXT[],
 'Whale 主动读取 Remote ADS Server 的变量；Acquisition 点表指定读取点。',TRUE),
(whale.protocol_role_id('ADS','SERVER'), 'SUBSCRIBE',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='SUBSCRIBE'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='SUBSCRIPTION'),
 TRUE,FALSE,FALSE,FALSE, ARRAY['MANUAL']::TEXT[],
 'Whale 在 Remote ADS Server 上建立 Device Notification；具体通知模式由 Source ADS 点明细定义。',TRUE),
(whale.protocol_role_id('ADS','SERVER'), 'WRITE',
 (SELECT meta_task_operation_semantic_id FROM whale.meta_task_operation_semantic WHERE code='WRITE'),
 (SELECT meta_task_interaction_mode_id FROM whale.meta_task_interaction_mode WHERE code='REQUEST_RESPONSE'),
 FALSE,TRUE,TRUE,TRUE, ARRAY['MANUAL','EVENT']::TEXT[],
 'Whale 主动写入 Remote ADS Server 变量；Delivery 点表指定目标变量。',TRUE);

INSERT INTO whale.meta_task_operation_parameter_definition
(meta_task_protocol_operation_id, parameter_identifier, meta_point_data_type_id,
 required, default_value, numeric_min, numeric_max, allowed_values, description_zh, enabled)
VALUES
(whale.protocol_operation_id('IEC104','CONTROLLED_STATION','GENERAL_INTERROGATION'),
 'QOI',(SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='INT32'),TRUE,
 '20'::jsonb,0,255,NULL,
 'IEC104 召唤限定词 QOI；20 为站总召，21～36 对应组召 1～16。',TRUE),
(whale.protocol_operation_id('IEC104','CONTROLLED_STATION','CONTROL_COMMAND'),
 'COMMAND_MODE',(SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='STRING'),TRUE,
 '"DIRECT"'::jsonb,NULL,NULL,'["DIRECT", "SELECT_EXECUTE"]'::jsonb,
 '控制命令执行模式；取值使用 meta_iec104_command_mode.code。',TRUE),
(whale.protocol_operation_id('IEC104','CONTROLLED_STATION','CONTROL_COMMAND'),
 'CAUSE_OF_TRANSMISSION',(SELECT meta_point_data_type_id FROM whale.meta_point_data_type WHERE code='STRING'),FALSE,
 '"ACTIVATION"'::jsonb,NULL,NULL,'["ACTIVATION"]'::jsonb,
 '控制命令传送原因；取值语义参考 meta_iec104_cause_of_transmission。',TRUE);

INSERT INTO whale.meta_point_measurement_semantic
(measurement_identifier, name_zh, meta_point_physical_quantity_category_id,
 standard_source, description_zh, enabled)
VALUES
('ACTIVE_POWER','有功功率',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='ACTIVE_POWER'),'PROJECT','以正值表示设备或场站向电网输出有功功率。',TRUE),
('REACTIVE_POWER','无功功率',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='REACTIVE_POWER'),'PROJECT','无功功率；正负号按场站统一约定解释。',TRUE),
('WIND_SPEED','风速',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='WIND_SPEED'),'PROJECT','风机或测风设备测得的风速。',TRUE),
('ROTOR_SPEED','转子转速',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='ROTATIONAL_SPEED'),'PROJECT','风轮或机组转子的机械转速。',TRUE),
('RUNNING_STATUS','运行状态',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='STATUS'),'PROJECT','设备是否处于运行状态的二值业务语义。',TRUE),
('ACTIVE_POWER_SETPOINT','有功功率设点',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='ACTIVE_POWER'),'PROJECT','下发给设备、控制系统或场站的目标有功功率。',TRUE),
('REACTIVE_POWER_SETPOINT','无功功率设点',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='REACTIVE_POWER'),'PROJECT','下发给设备、控制系统或场站的目标无功功率。',TRUE),
('START_COMMAND','启动命令',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='COMMAND'),'PROJECT','命令值为 true 时表示请求设备启动。',TRUE),
('STOP_COMMAND','停机命令',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='COMMAND'),'PROJECT','命令值为 true 时表示请求设备停机。',TRUE),
('POI_VOLTAGE','并网点电压',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='VOLTAGE'),'PROJECT','场站并网点或关口位置的线电压有效值。',TRUE),
('GRID_FREQUENCY','电网频率',(SELECT meta_point_physical_quantity_category_id FROM whale.meta_point_physical_quantity_category WHERE code='FREQUENCY'),'PROJECT','场站并网点测得的系统频率。',TRUE);


-- 兼容既有完整场站样例所需的细分责任类别与工程单位。
INSERT INTO whale.meta_org_responsibility_category (code, description_zh, sort_order, enabled) VALUES
('ELECTRICAL_MAINTENANCE', '负责一次、二次电气设备的检查、维护、检修和缺陷处理。', 20, TRUE),
('MECHANICAL_MAINTENANCE', '负责机械结构、传动和辅助机械系统的维护检修。', 21, TRUE),
('CONTROL_MAINTENANCE', '负责控制器、通信、自动化和相关软件系统的维护与故障处理。', 22, TRUE);

INSERT INTO whale.meta_point_unit (code, description_zh, sort_order, enabled) VALUES
('NONE', '无量纲或不适用工程单位的值。', 100, TRUE),
('MWH', '有功电能单位兆瓦时。', 101, TRUE),
('M', '长度单位米。', 102, TRUE),
('MVA', '视在功率单位兆伏安。', 103, TRUE);

COMMIT;
