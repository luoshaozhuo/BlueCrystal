# ADR-20260524-006: Source Lab 协议目录统一治理

## 状态

Accepted

## 背景

source_lab 存在历史目录分叉：

```text
tools/source_lab/opcua/          ← OPC UA 协议资源在顶层
tools/source_lab/protocols/      ← 其他所有协议资源在下层
```

这种不一致导致：
1. OPC UA 的 address_space、simulator、templates、docs 与其他协议不共用同一目录结构。
2. import 路径混乱（`tools.source_lab.opcua.*` vs `tools.source_lab.protocols.*`）。
3. 新增协议开发者不清楚协议资源应放在哪里。
4. factory/registry 需要特殊判断 OPC UA 与非 OPC UA 协议。

## 决策

统一为 `tools/source_lab/protocols/{protocol}` 作为所有协议资源的唯一位置：

```text
tools/source_lab/protocols/
├── common/                      ← 协议公共逻辑（simulators、point_mapping）
├── http_rest/
├── iec101/
├── iec104/
├── iec61850/
├── modbus/
├── mqtt/
└── opcua/                       ← 迁移后统一位置
    ├── __init__.py
    ├── address_space.py
    ├── open62541_source_simulator.py
    ├── docs/
    └── templates/
```

## 影响

### 迁移内容

- `tools/source_lab/opcua/` 整目录迁移到 `tools/source_lab/protocols/opcua/`。
- 所有 import 从 `tools.source_lab.opcua.*` 更新为 `tools.source_lab.protocols.opcua.*`。
- 更新 `tests/support/source_lab_runtime.py` 中 namespace package 注册路径。
- 删除旧 `tools/source_lab/opcua/` 目录。

### 不兼容旧路径

不保留兼容 shim。旧路径 `tools.source_lab.opcua` 的 import 会立即失败。所有集成测试、source_lab 内部模块、provider 的 import 已同步更新。

## 边界条件

| 维度 | 边界 |
|---|---|
| `tools/source_lab/native/` | 保留 C runner/server 源码，不作迁移 |
| `tools/source_lab/access/` | 保留 probe/capacity/profile Task Facade，不移动 |
| `src/whale/shared/source/opcua/` | 生产 client 目录，不受影响 |
| `tools/source_simulation/` | 已删除，无运行引用 |
| `tests/conftest.py` | 死亡 OPC UA fixture（`opcua_server_runtime`, `opcua_sim_fleet`）已清理，`OPCUA_SIM_TEMPLATE_DIR` 已删除。零旧路径残留。 |

## 替代方案

1. **保留旧目录并添加 protocols/opcua facade**：需要维护两套 import，增加混淆。不采用。
2. **不迁移，新增协议也放顶层**：继续助长目录分叉。不采用。

## 后续

- 所有协议资源统一在 `protocols/{protocol}` 下治理。
- 无到期删除条件（本决策为永久性）。
