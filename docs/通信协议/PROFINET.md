# PROFINET 工程说明文档 v2

## 1. 协议定位

PROFINET 是 PI（PROFIBUS & PROFINET International）维护的工业以太网协议，主要用于 **PLC / IO Controller 与现场 IO Device 之间的实时 I/O 数据交换**。

它常见于：

```text
PLC / IO Controller
  └── 工业以太网
        ├── 远程 I/O
        ├── 变频器
        ├── 伺服驱动
        ├── 机器人控制柜
        ├── 阀岛
        ├── 传感器网关
        └── 视觉/扫码/称重设备
```

PROFINET 的重点不是像 Modbus 那样按寄存器地址读写，也不是像 IEC104 那样按 CA/IOA 上送遥测遥信，而是围绕 **设备名、模块、子模块、输入/输出过程数据区、实时通信关系** 建立控制网络。

一句话理解：

```text
PROFINET 解决 PLC 如何实时控制现场设备；
OPC UA / IEC104 / MQTT 等更常用于把数据向 SCADA、集控、调度或平台暴露。
```

---

## 2. 核心角色

| 角色 | 含义 | 典型设备 |
|------|------|----------|
| **IO Controller** | 控制器，负责配置、参数化并周期读写 IO Device | PLC、运动控制器、工业 PC |
| **IO Device** | 被控制的现场设备，提供输入数据、接收输出数据 | 远程 I/O、驱动器、阀岛、机器人 |
| **IO Supervisor** | 工程、诊断、调试角色 | TIA Portal、TwinCAT、CODESYS、诊断工具 |

### 2.1 IO Controller

IO Controller 负责：

- 按工程配置查找 IO Device；
- 给设备分配或确认 Device Name / IP；
- 根据 GSDML 和工程配置检查模块、子模块是否匹配；
- 建立 AR / CR 通信关系；
- 周期读取 Input Data；
- 周期写入 Output Data；
- 接收报警和诊断；
- 读写非周期参数记录。

### 2.2 IO Device

IO Device 负责：

- 按 GSDML 暴露设备能力；
- 提供模块、子模块、输入区、输出区；
- 向 IO Controller 提供 Input Data；
- 接收 IO Controller 写入的 Output Data；
- 上报告警、诊断、模块状态；
- 接收参数化数据。

注意 input/output 的方向是从 **IO Device 视角** 定义的：

```text
Input  = IO Device -> IO Controller
Output = IO Controller -> IO Device
```

所以远程 I/O 模块中的 DI 状态是 `Input`，DO 命令是 `Output`。

---

## 3. PROFINET 与 TCP/IP 的关系

PROFINET 基于 Ethernet，但不能简单理解成“跑在 TCP/IP 上的协议”。它有三类通信通道：

| 通道 | 是否经过 TCP/IP | 典型用途 | 实时性 |
|------|----------------|----------|--------|
| TCP/IP / UDP/IP | 是 | 工程配置、参数化、诊断、非实时数据 | 非实时 |
| RT，Real-Time | 通常不走 TCP/IP，直接使用 Ethernet 实时帧 | 周期 I/O 数据 | 实时 |
| IRT，Isochronous Real-Time | 不走普通 TCP/IP，使用时间同步和调度时间片 | 高同步运动控制 | 等时实时 |

所以：

```text
PROFINET 可以同时使用 TCP/IP、RT、IRT；
但周期 I/O 数据通常不是普通 TCP socket 数据。
```

这也是为什么纯 Python `socket` 不能直接实现一个完整生产级 PROFINET Controller / Device。

---

## 4. RT / IRT 使用什么物理接口

RT 和 IRT 都使用 **Ethernet 物理接口**。它们不是两种不同线缆标准，而是不同实时通信机制。

常见物理接口包括：

| 物理接口 | 常见场合 |
|----------|----------|
| RJ45 | 控制柜、普通工业以太网设备 |
| M12 D-coded | 100 Mbps 现场设备，防护等级较高 |
| M12 X-coded | 1 Gbps 现场设备 |
| 光纤 | 长距离、强干扰、主干网络、环网 |
| 工业交换机端口 | 星型、线型、树型、环网拓扑 |

RT 与 IRT 的区别：

| 对比项 | RT | IRT |
|--------|----|-----|
| 物理层 | Ethernet | Ethernet |
| 常见接口 | RJ45 / M12 / 光纤 | RJ45 / M12 / 光纤，但设备和交换机必须支持 IRT |
| 通信机制 | 实时 Ethernet 帧、优先级处理 | 时间同步、带宽预留、调度时间片 |
| 设备要求 | 普通 PROFINET RT 设备 | IRT-capable Controller、Device、Switch |
| 典型场景 | 远程 I/O、阀岛、普通变频器 | 高同步伺服、机器人、多轴运动控制 |

可以这样理解：

```text
RT / IRT 的线可能一样，接口形态也可能一样；
区别在于网卡、交换芯片、设备协议栈、控制器和工程配置是否支持确定性调度。
```

---

## 5. GSDML、PLC 工程配置、点表的边界

这是 PROFINET 最容易混淆的部分。

### 5.1 GSDML 不是点表

GSDML 是设备厂商提供的 **设备描述文件**。它描述设备能力，不直接描述项目业务变量。

GSDML 主要说明：

```text
这个设备是谁；
支持哪些模块；
每个模块有哪些子模块；
子模块有多少 Input bytes / Output bytes；
支持哪些参数记录；
支持哪些诊断和报警；
支持哪些实时等级；
工程工具应该如何显示它。
```

GSDML 通常不会直接定义这些业务变量名：

```text
wind_speed
active_power
motor_running
nacelle_temperature
```

这些属于项目点表、PLC 变量表或 SCADA 标签。

### 5.2 PLC 工程配置

PLC 工程配置是在 GSDML 能力基础上，选择本项目实际使用哪些模块、槽位、子槽位和参数。

例如 GSDML 说设备支持：

```text
16DI
8DO
4AI
2AO
```

但本项目工程可能只使用：

```text
Slot 1 = 16DI
Slot 2 = 8DO
Slot 3 = 4AI
```

PLC 工程还会把这些输入/输出映射到 PLC 地址区或过程映像区，例如：

```text
I100.0 ~ I101.7   Slot 1 16DI
Q100.0 ~ Q100.7   Slot 2 8DO
IW102  ~ IW108     Slot 3 4AI
```

### 5.3 点表

点表是项目侧的业务映射文件。它把 PROFINET 的设备、槽位、子槽位、字节偏移、bit 偏移映射为业务点名。

例如：

```yaml
- name: wind_speed
  device_name: remote-io-01
  slot: 3
  subslot: 1
  direction: input
  byte_offset: 0
  data_type: int16
  scale: 0.1
  unit: m/s
```

关系总结：

```text
GSDML：设备厂家给的“设备能力说明书”
PLC 工程：本项目实际选择了哪些模块和参数
点表：把实际 I/O 字节映射成业务变量
```

不能只靠 GSDML 自动生成完整业务点表，因为 GSDML 不知道项目业务命名和语义。

---

## 6. GSDML 到底规定哪些东西

GSDML 的核心内容如下：

| 内容 | 典型 Tag | 说明 |
|------|----------|------|
| 文件 Profile 信息 | `ProfileHeader` | GSDML 文件类型、Profile 版本 |
| 文件主体 | `ProfileBody` | 设备描述主体 |
| 设备身份 | `DeviceIdentity` | VendorID、DeviceID、厂家名、设备说明 |
| 设备访问点 | `DeviceAccessPointList` / `DeviceAccessPointItem` | DAP，设备根入口，通常对应 Slot 0 |
| 系统子模块 | `SystemDefinedSubmoduleList` | 接口、端口等系统级子模块 |
| 接口子模块 | `InterfaceSubmoduleItem` | 网络接口能力，如支持 RT_CLASS_1 / RT_CLASS_3 |
| 端口子模块 | `PortSubmoduleItem` | 物理端口，用于拓扑、LLDP、端口诊断 |
| 模块列表 | `ModuleList` | 设备支持的模块类型列表 |
| 模块项 | `ModuleItem` | 一个模块类型，如 16DI、8DO、4AI |
| 子模块列表 | `VirtualSubmoduleList` | 某模块下可用的子模块 |
| 子模块项 | `VirtualSubmoduleItem` | 一个子模块类型，通常携带实际 IOData |
| 周期数据 | `IOData` | 周期 I/O 数据定义 |
| 输入数据 | `Input` | Device -> Controller 的数据 |
| 输出数据 | `Output` | Controller -> Device 的数据 |
| 数据项 | `DataItem` | 一个 I/O 数据项，如 `Unsigned16`、`Integer16` |
| 参数记录 | `RecordDataList` / `ParameterRecordDataItem` | 非周期参数记录 |
| 文本资源 | `ExternalTextList` / `Text` | 多语言显示文本 |
| 诊断 | 诊断相关 List / Item | 通道、模块、设备诊断能力 |

---

## 7. 带注释的 GSDML 示例

下面是一个简化但更容易读懂的 GSDML 示例。真实 GSDML 会更长，并带 namespace、schemaLocation、更多约束和诊断定义。

```xml
<?xml version="1.0" encoding="UTF-8"?>

<!--
  GSDML 根节点。
  它描述一个 PROFINET IO Device 的能力。
  注意：GSDML 不是业务点表。
-->
<GSDML>

  <!--
    ProfileHeader：文件 Profile 信息。
    工程工具用它判断这是 PROFINET Device Profile 的设备描述。
  -->
  <ProfileHeader>
    <ProfileIdentification>PROFINET Device Profile</ProfileIdentification>
    <ProfileRevision>2.43</ProfileRevision>
  </ProfileHeader>

  <!-- ProfileBody：设备描述主体。 -->
  <ProfileBody>

    <!--
      DeviceIdentity：设备身份。
      VendorID 由 PI 分配给厂家。
      DeviceID 由厂家分配给某个设备型号或设备系列。
      工程工具用 VendorID + DeviceID 识别设备类型。
    -->
    <DeviceIdentity VendorID="0x1234" DeviceID="0x0001">
      <VendorName Value="DemoVendor"/>
      <InfoText TextId="TXT_DEVICE_INFO"/>
    </DeviceIdentity>

    <!--
      DeviceAccessPointList：设备访问点列表。
      DAP 是 Device Access Point，通常位于 Slot 0。
      它是整个 IO Device 的根模块入口。
    -->
    <DeviceAccessPointList>

      <!--
        DeviceAccessPointItem：一个 DAP 定义。
        PhysicalSlots="0..3" 表示该设备允许使用 Slot 0 到 Slot 3。
        ModuleIdentNumber 是厂家定义的模块标识号。
      -->
      <DeviceAccessPointItem
          ID="DAP_1"
          PhysicalSlots="0..3"
          ModuleIdentNumber="0x00000001">

        <!-- ModuleInfo：工程工具中显示的模块名称和说明。 -->
        <ModuleInfo>
          <Name TextId="TXT_DAP_NAME"/>
          <InfoText TextId="TXT_DAP_INFO"/>
        </ModuleInfo>

        <!--
          SystemDefinedSubmoduleList：系统定义子模块。
          通常包含接口子模块和端口子模块。
        -->
        <SystemDefinedSubmoduleList>

          <!--
            InterfaceSubmoduleItem：接口子模块。
            SubslotNumber="0x8000" 是接口子模块常见位置。
            SupportedRT_Classes 声明实时等级能力：
              RT_CLASS_1 通常对应 PROFINET RT；
              RT_CLASS_3 通常对应 PROFINET IRT。
            SupportedProtocols 声明支持 SNMP、LLDP 等辅助协议。
          -->
          <InterfaceSubmoduleItem
              ID="IF_1"
              SubslotNumber="0x8000"
              SubmoduleIdentNumber="0x00008000"
              SupportedRT_Classes="RT_CLASS_1;RT_CLASS_3"
              SupportedProtocols="SNMP;LLDP"/>

          <!--
            PortSubmoduleItem：物理端口子模块。
            多端口设备会有多个端口子模块。
            它用于拓扑识别、LLDP、端口诊断等。
          -->
          <PortSubmoduleItem
              ID="PORT_1"
              SubslotNumber="0x8001"
              SubmoduleIdentNumber="0x00008001"/>
        </SystemDefinedSubmoduleList>
      </DeviceAccessPointItem>
    </DeviceAccessPointList>

    <!--
      ModuleList：设备支持的模块类型列表。
      这里只说明“设备支持什么模块”，不代表本项目实际插入了这些模块。
      实际选择哪个模块由 PLC 工程配置决定。
    -->
    <ModuleList>

      <!--
        ModuleItem：一个模块类型。
        这里定义 16DI 模块。
      -->
      <ModuleItem ID="MOD_16DI" ModuleIdentNumber="0x00000011">
        <ModuleInfo>
          <Name TextId="TXT_MOD_16DI"/>
        </ModuleInfo>

        <!-- VirtualSubmoduleList：该模块下可用的子模块。 -->
        <VirtualSubmoduleList>

          <!--
            VirtualSubmoduleItem：一个子模块类型。
            子模块通常真正定义 Input / Output 数据。
          -->
          <VirtualSubmoduleItem
              ID="SUB_16DI"
              SubmoduleIdentNumber="0x00000012">

            <!-- IOData：周期过程数据定义。 -->
            <IOData>

              <!--
                Input：Device -> Controller 的输入数据。
                对 16DI 模块来说，16 路数字量状态由设备输入给控制器。
              -->
              <Input>

                <!--
                  DataItem：一个数据项。
                  Unsigned16 表示 16 位无符号数据。
                  它可以承载 16 个 DI bit。
                  TXT_DI_STATUS 是显示文本，不是业务变量名。
                -->
                <DataItem
                    DataType="Unsigned16"
                    TextId="TXT_DI_STATUS"/>
              </Input>
            </IOData>
          </VirtualSubmoduleItem>
        </VirtualSubmoduleList>
      </ModuleItem>

      <!-- 8DO 输出模块 -->
      <ModuleItem ID="MOD_8DO" ModuleIdentNumber="0x00000021">
        <ModuleInfo>
          <Name TextId="TXT_MOD_8DO"/>
        </ModuleInfo>

        <VirtualSubmoduleList>
          <VirtualSubmoduleItem
              ID="SUB_8DO"
              SubmoduleIdentNumber="0x00000022">

            <IOData>
              <!--
                Output：Controller -> Device 的输出数据。
                对 8DO 模块来说，控制器输出 8 路 DO 命令给设备。
              -->
              <Output>
                <DataItem
                    DataType="Unsigned8"
                    TextId="TXT_DO_COMMAND"/>
              </Output>
            </IOData>
          </VirtualSubmoduleItem>
        </VirtualSubmoduleList>
      </ModuleItem>

      <!-- 4AI 模拟量输入模块 -->
      <ModuleItem ID="MOD_4AI" ModuleIdentNumber="0x00000031">
        <ModuleInfo>
          <Name TextId="TXT_MOD_4AI"/>
        </ModuleInfo>

        <VirtualSubmoduleList>
          <VirtualSubmoduleItem
              ID="SUB_4AI"
              SubmoduleIdentNumber="0x00000032">

            <IOData>
              <Input>
                <!--
                  4 个 Integer16 输入数据项。
                  它们只是通道数据项。
                  业务上到底叫 wind_speed、temperature 还是 pressure，
                  需要由 PLC 工程和点表进一步映射。
                -->
                <DataItem DataType="Integer16" TextId="TXT_AI_CH1"/>
                <DataItem DataType="Integer16" TextId="TXT_AI_CH2"/>
                <DataItem DataType="Integer16" TextId="TXT_AI_CH3"/>
                <DataItem DataType="Integer16" TextId="TXT_AI_CH4"/>
              </Input>
            </IOData>

            <!--
              RecordDataList：非周期参数记录。
              控制器启动时可以通过 Record Data CR 下发或读取这些参数。
              例如量程、滤波时间、诊断使能等。
            -->
            <RecordDataList>
              <ParameterRecordDataItem
                  Index="0x8000"
                  Length="4"
                  TextId="TXT_AI_PARAMETER_RECORD"/>
            </RecordDataList>
          </VirtualSubmoduleItem>
        </VirtualSubmoduleList>
      </ModuleItem>
    </ModuleList>

    <!--
      ExternalTextList：文本资源表。
      上面的 TextId 都在这里解析成工程工具显示文本。
    -->
    <ExternalTextList>
      <PrimaryLanguage>
        <Text TextId="TXT_DEVICE_INFO" Value="Demo PROFINET IO Device"/>
        <Text TextId="TXT_DAP_NAME" Value="Device Access Point"/>
        <Text TextId="TXT_DAP_INFO" Value="Main access point of the device"/>
        <Text TextId="TXT_MOD_16DI" Value="16 Digital Inputs"/>
        <Text TextId="TXT_MOD_8DO" Value="8 Digital Outputs"/>
        <Text TextId="TXT_MOD_4AI" Value="4 Analog Inputs"/>
        <Text TextId="TXT_DI_STATUS" Value="Digital input status word"/>
        <Text TextId="TXT_DO_COMMAND" Value="Digital output command byte"/>
        <Text TextId="TXT_AI_CH1" Value="Analog input channel 1"/>
        <Text TextId="TXT_AI_CH2" Value="Analog input channel 2"/>
        <Text TextId="TXT_AI_CH3" Value="Analog input channel 3"/>
        <Text TextId="TXT_AI_CH4" Value="Analog input channel 4"/>
        <Text TextId="TXT_AI_PARAMETER_RECORD" Value="Analog input parameter record"/>
      </PrimaryLanguage>
    </ExternalTextList>

  </ProfileBody>
</GSDML>
```

---

## 8. 从 GSDML 到点表的转换示例

上面的 GSDML 定义了：

```text
MOD_4AI / SUB_4AI 有 4 个 Integer16 输入通道
```

PLC 工程配置可能实际选择：

```yaml
io_device:
  device_name: remote-io-01
  modules:
    - slot: 3
      module: MOD_4AI
      subslot: 1
      submodule: SUB_4AI
      input_length: 8
```

项目点表才把这 4 个通道命名为业务变量：

```yaml
points:
  - name: wind_speed
    device_name: remote-io-01
    slot: 3
    subslot: 1
    direction: input
    byte_offset: 0
    data_type: int16
    scale: 0.1
    unit: m/s

  - name: nacelle_temperature
    device_name: remote-io-01
    slot: 3
    subslot: 1
    direction: input
    byte_offset: 2
    data_type: int16
    scale: 0.1
    unit: degC

  - name: active_power
    device_name: remote-io-01
    slot: 3
    subslot: 1
    direction: input
    byte_offset: 4
    data_type: int16
    scale: 1.0
    unit: kW

  - name: reactive_power
    device_name: remote-io-01
    slot: 3
    subslot: 1
    direction: input
    byte_offset: 6
    data_type: int16
    scale: 1.0
    unit: kvar
```

这里的结论是：

```text
GSDML 只能告诉你 Slot 3 / Subslot 1 有 8 个输入字节；
点表才告诉你第 0~1 字节叫 wind_speed，第 2~3 字节叫 nacelle_temperature。
```

---

## 9. 通信关系与数据交换

### 9.1 AR 是什么

AR，全称 Application Relation，是 IO Controller 与 IO Device 之间建立的一组应用通信关系。

可以理解为：

```text
PLC 和某个 PROFINET 设备之间的一次完整运行时连接关系。
```

AR 建立过程中通常包括：

```text
1. 按 Device Name 找到设备；
2. 确认或分配 IP；
3. 建立连接；
4. 参数化设备；
5. 检查模块/子模块配置是否与工程一致；
6. 建立周期 IO、非周期记录、报警诊断等 CR；
7. 进入周期数据交换。
```

### 9.2 CR 是什么

CR，全称 Communication Relation，是 AR 内部的具体通信通道。

| CR 类型 | 作用 | 对应 GSDML / 工程配置 |
|---------|------|----------------------|
| IO Data CR / IOCR | 周期 I/O 数据交换 | `IOData`、`Input`、`Output`、DataItem 长度、slot/subslot 配置 |
| Record Data CR | 非周期参数和记录数据读写 | `RecordDataList`、`ParameterRecordDataItem` |
| Alarm CR | 报警、诊断事件传输 | 诊断能力、通道诊断、模块诊断配置 |

所以“不同关系”的影响是：

```text
IOCR 影响周期过程数据能不能跑起来；
Record Data CR 影响参数能不能读写；
Alarm CR 影响设备诊断和报警能不能上报。
```

### 9.3 为什么 GSDML 例子里没有直接写 AR/CR

GSDML 不是运行时连接文件。它主要描述设备能力。

运行时 AR/CR 由以下内容共同决定：

```text
GSDML 设备能力
+ PLC 工程中实际选择的模块/子模块
+ 控制器配置的周期、实时等级、参数、报警设置
+ 设备当前在线状态
```

也就是说：

```text
GSDML 负责“能不能这样配置”；
PLC 工程负责“本项目要这样配置”；
IO Controller 启动时负责“按配置建立 AR/CR”。
```

---

## 10. PROFINET 点表建模

### 10.1 IO Controller 侧点表

```yaml
protocol: profinet
role: io_controller

network:
  interface: eth1
  controller_name: plc-controller-01

io_devices:
  - device_name: remote-io-01
    ip: 192.168.10.21
    gsdml: GSDML-V2.43-DemoVendor-RemoteIO-20250601.xml

    configured_modules:
      - slot: 1
        module_id: MOD_16DI
        subslot: 1
        submodule_id: SUB_16DI
        direction: input
        input_length: 2

      - slot: 2
        module_id: MOD_8DO
        subslot: 1
        submodule_id: SUB_8DO
        direction: output
        output_length: 1

      - slot: 3
        module_id: MOD_4AI
        subslot: 1
        submodule_id: SUB_4AI
        direction: input
        input_length: 8

    points:
      - name: emergency_stop
        direction: input
        slot: 1
        subslot: 1
        byte_offset: 0
        bit_offset: 0
        data_type: bool

      - name: motor_running
        direction: input
        slot: 1
        subslot: 1
        byte_offset: 0
        bit_offset: 1
        data_type: bool

      - name: valve_open_command
        direction: output
        slot: 2
        subslot: 1
        byte_offset: 0
        bit_offset: 0
        data_type: bool

      - name: wind_speed
        direction: input
        slot: 3
        subslot: 1
        byte_offset: 0
        data_type: int16
        scale: 0.1
        unit: m/s
```

### 10.2 IO Device 侧点表

如果本系统要模拟或实现一个 PROFINET IO Device，点表应该描述它对外暴露的输入区和接收的输出区。

```yaml
protocol: profinet
role: io_device

device:
  device_name: turbine-io-device-01
  vendor_id: 0x1234
  device_id: 0x0001
  gsdml: GSDML-V2.43-DemoVendor-TurbineIODevice-20250601.xml

modules:
  - slot: 1
    module_id: turbine_status_input
    subslot: 1
    direction: input       # Device -> Controller
    length: 8

  - slot: 2
    module_id: turbine_command_output
    subslot: 1
    direction: output      # Controller -> Device
    length: 4

points:
  - name: turbine_running
    slot: 1
    subslot: 1
    direction: input
    byte_offset: 0
    bit_offset: 0
    data_type: bool

  - name: generator_speed
    slot: 1
    subslot: 1
    direction: input
    byte_offset: 2
    data_type: uint16
    scale: 0.1
    unit: rpm

  - name: start_command
    slot: 2
    subslot: 1
    direction: output
    byte_offset: 0
    bit_offset: 0
    data_type: bool

  - name: active_power_limit
    slot: 2
    subslot: 1
    direction: output
    byte_offset: 2
    data_type: uint16
    scale: 0.1
    unit: percent
```

---

## 11. PROFINET 与其他协议的点表差异

| 协议 | 点定位方式 | 点表核心字段 |
|------|------------|--------------|
| Modbus | 寄存器 / 线圈地址 | unit_id、function、address、data_type |
| IEC104 | ASDU 地址 + IOA + Type ID | common_address、ioa、type_id、cot 策略 |
| OPC UA | Namespace URI + NodeId / BrowsePath | namespace_uri、node_id、browse_path |
| PROFINET | Device + Slot/Subslot + 字节/bit 偏移 | device_name、slot、subslot、byte_offset、bit_offset |

因此，PROFINET 点表不能写成 Modbus 风格的寄存器表，也不能写成 IEC104 风格的 CA/IOA 表。

---

## 12. Python 开发边界

Python 适合：

- 解析 GSDML；
- 生成点表；
- 校验点表与 GSDML/工程配置是否一致；
- 读取 PLC 暴露的 OPC UA、ADS、S7、MQTT、IEC104 数据；
- 调用厂商 SDK 或 C/C++ PROFINET 协议栈封装。

Python 不适合：

- 纯 Python 实现生产级 PROFINET RT / IRT 协议栈；
- 直接用 socket 模拟完整 IO Controller；
- 直接抓 RT 帧作为长期稳定采集方案；
- 在控制网络中绕过 PLC 解释周期 IO 数据。

### 12.1 GSDML 解析示例

```python
from pathlib import Path
import xml.etree.ElementTree as ET


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_gsdml_modules(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    modules = []

    for elem in root.iter():
        if strip_ns(elem.tag) != "ModuleItem":
            continue

        module = {
            "id": elem.attrib.get("ID"),
            "module_ident_number": elem.attrib.get("ModuleIdentNumber"),
            "submodules": [],
        }

        for sub in elem.iter():
            if strip_ns(sub.tag) != "VirtualSubmoduleItem":
                continue

            submodule = {
                "id": sub.attrib.get("ID"),
                "submodule_ident_number": sub.attrib.get("SubmoduleIdentNumber"),
                "input_items": [],
                "output_items": [],
            }

            for node in sub.iter():
                if strip_ns(node.tag) == "Input":
                    for item in node.iter():
                        if strip_ns(item.tag) == "DataItem":
                            submodule["input_items"].append(dict(item.attrib))

                if strip_ns(node.tag) == "Output":
                    for item in node.iter():
                        if strip_ns(item.tag) == "DataItem":
                            submodule["output_items"].append(dict(item.attrib))

            module["submodules"].append(submodule)

        modules.append(module)

    return modules


if __name__ == "__main__":
    for module in parse_gsdml_modules("GSDML-V2.43-DemoVendor-RemoteIO.xml"):
        print(module)
```

这个脚本只能解析 GSDML 中的模块和 I/O 数据项，不能直接得出业务点名。

---

## 13. 风电场中的位置

风电场内，PROFINET 常位于设备控制层：

```text
风机控制柜 / 场站 PLC / 变桨变流控制系统
  ├── PROFINET：远程 I/O、驱动、阀岛、传感器网关
  ├── PROFIBUS：存量老设备
  └── Modbus RTU/TCP：简单仪表或第三方设备

场站网关 / SCADA / 数据平台
  ├── IEC104：对调度/集控
  ├── OPC UA：结构化数据访问
  ├── ADS / S7：PLC 数据访问
  └── MQTT / HTTP：平台集成
```

更推荐的数据链路：

```text
PROFINET IO Device
  ↓ 周期 I/O
PLC / IO Controller
  ↓ OPC UA / ADS / S7 / IEC104 / MQTT
数据平台 / SCADA / 历史库
```

不建议数据平台直接绕过 PLC 抓取 PROFINET RT 帧做长期生产采集。

---

## 14. 工程排查重点

| 现象 | 常见原因 |
|------|----------|
| 设备找不到 | Device Name 未设置、DCP 不通、网络隔离、VLAN 错误 |
| 设备在线但不交换数据 | AR 建立失败、模块/子模块配置不一致 |
| 某模块红灯 | Slot/Subslot 与实际设备不匹配、模块缺失 |
| 数据全 0 | IOCR 未建立、数据状态无效、PLC 工程地址映射错误 |
| 输出无效 | Output 方向理解反了、控制器未进入 Run、设备安全联锁 |
| IRT 不工作 | 控制器、设备、交换机或拓扑不支持 IRT |
| 更换设备失败 | Device Name 不一致、GSDML 版本或设备型号不兼容 |

---

## 15. 文档修正总结

相对上一版，v2 应重点修正以下内容：

```text
1. GSDML 例子必须带逐项注释。
2. 明确 GSDML 不是业务点表，不定义 wind_speed 这类业务变量。
3. 明确 GSDML 规定设备身份、模块、子模块、过程数据、参数、诊断、实时能力。
4. 明确点表由 GSDML + PLC 工程配置 + 业务映射共同产生。
5. 明确 AR / CR 是运行时通信关系，不是 GSDML 里的固定点表。
6. 明确 IOCR、Record Data CR、Alarm CR 分别影响周期数据、参数记录、报警诊断。
7. 明确 RT / IRT 都用 Ethernet 物理接口，区别在实时调度机制和设备能力，不是线缆名称。
8. PROFINET 点表应以 device_name、slot、subslot、byte_offset、bit_offset 建模。
```

---

## 16. 参考资料

- PI：GSDML/GSDX Specification for PROFINET
- PI North America：PROFINET Communication Channels
- PI：PROFINET System Description
- PROFINET University：PROFINET GSD File Basics
- Siemens：GSDML Getting Started
- OPC Foundation OPC 30140：PROFINET Communication Relationships
