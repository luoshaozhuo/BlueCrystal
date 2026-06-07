"""Starfish Modbus 共用工具子包。

本子包提供 Modbus TCP / Modbus RTU 共享的寄存器编解码、字节序
/字序组合等工具。这些工具是**纯 CPU 运算**的协议编解码辅助，
不等同于真实设备验证；任何"是否对接到真实 Modbus 设备"的
生产路径仍由 ``facade/modbus_*_facade.py`` 负责。

当前实现（Round 18 新增）：

- ``register_encoding``：寄存器值编解码工具
    - uint16 / int16 / uint32 / int32 / float32
    - byte_order：big / little
    - word_order：big / little（仅 32-bit / float32 有效）
    - 严格 NaN/Inf 策略：拒绝并抛 ``RegisterEncodingValueError``
- ``register_encoding`` 不得被高估为真实设备验证

不负责：
- 真实 Modbus TCP / Modbus RTU 设备 IO、链路层（详见 facade）。
- 多从站 ID 处理、广播地址（0x00）处理、异常码完整矩阵。
- Modbus 协议帧级 IO 业务逻辑（由 facade 负责）。
"""

from starfish.protocols.modbus.register_encoding import (
    INT16_MAX,
    INT16_MIN,
    INT32_MAX,
    INT32_MIN,
    UINT16_MAX,
    UINT32_MAX,
    ByteOrder,
    ModbusRegisterValueType,
    RegisterEncodingError,
    RegisterEncodingLengthError,
    RegisterEncodingRangeError,
    RegisterEncodingValueError,
    WordOrder,
    decode_register_value,
    encode_register_value,
)

__all__ = [
    # 类型与异常
    "ByteOrder",
    "WordOrder",
    "ModbusRegisterValueType",
    "RegisterEncodingError",
    "RegisterEncodingLengthError",
    "RegisterEncodingRangeError",
    "RegisterEncodingValueError",
    # 常量
    "INT16_MIN",
    "INT16_MAX",
    "INT32_MIN",
    "INT32_MAX",
    "UINT16_MAX",
    "UINT32_MAX",
    # 入口
    "encode_register_value",
    "decode_register_value",
]
