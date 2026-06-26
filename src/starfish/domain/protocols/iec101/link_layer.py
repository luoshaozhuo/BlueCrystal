"""IEC 60870-5-101 链路层最小状态机骨架（skeleton）。

本模块提供 IEC 60870-5-101 链路层（FT1.2 + balanced/unbalanced
传输模式）的**最小纯状态机/codec 辅助**。它是 ``codec-only`` 骨架，
**不是 server**，**不实现真实串口收发、字节流解析、PTX 超时、重试
定时器**等生产行为。

能力边界（Round 17 skeleton 范围 + Round 20 计时器/翻转/序列
增量）:

    - 定义 ``LinkLayerMode`` 枚举：BALANCED / UNBALANCED。
    - 定义 ``LinkState`` 枚举：IDLE / WAIT_ACK / SEND / RECEIVE / ERROR。
    - 提供 ``LinkControlHelper`` 构造工具：
        ``build_ack`` / ``build_nack`` / ``build_reset`` /
        ``build_user_data`` / ``build_fcb_fcv`` 等返回 ``FixedFrame`` /
        ``VariableFrame`` 的辅助方法，便于测试时构造链路层控制帧。
    - 提供 ``LinkLayerTimers`` 数据类：t1 / t2 / t3 协议计时器常量
        （**仅占位**；skeleton 不实现真实定时器线程）。
    - 提供 ``FCB / FCV`` helper：构造与解析 FCB/FCV 控制位字段。
    - 提供 ``LinkLayer`` 类：维护当前 mode / state / sequence / retry
        计数；``feed_frame(frame) -> LinkEvent`` 在不连接任何真实
        串口的情况下按协议状态机驱动转移；不重试、不起线程。
    - sequence flip / retry 逻辑骨架（``flip_fcb()`` / ``bump_retry()``）。
    - balanced / unbalanced 模式下的差异化 skeleton 行为：
        UNBALANCED 收到 NACK 不自动重试；BALANCED 收到 ACK 可继续发
        下一帧（state -> IDLE）。
    - 转移事件以 ``LinkEvent`` dataclass 暴露，便于调用方观测。

Round 20 增量（计时器/翻转/序列骨架；仍是 skeleton）:

    - ``LinkLayerTimerService`` 抽象接口：``start_timer / cancel_timer /
      cancel_all``。生产实现 ``DefaultLinkLayerTimerService`` 用
      ``threading.Timer``；测试可用 ``FakeLinkLayerTimerService`` 注入
      确定性触发回调。**默认不启用**（``LinkLayer(enable_timers=
      False)``），保持 Round 17 行为完全一致；测试可显式开启以验证
      计时器调度 + 超时回调路径。
    - ``LinkLayer.start_timer(name, ms, callback)`` /
      ``cancel_timer(name)``：基于注入 timer_service 的薄封装。
      ``on_timeout(name)`` 默认实现 = ``bump_retry()`` + state ->
      ERROR（超限后）。
    - retry 超限 → ERROR：``bump_retry()`` 已有"超 max_retries 置
      ERROR"行为；Round 20 在 ``_apply_nack`` 路径上**显式**调用
      ``bump_retry()`` 一次后再做 ERROR 转移，使得 retry_count 与
      状态机同步，测试可断言 ``retry_count == n`` + ``state ==
      ERROR``。
    - balanced FCB auto flip：``receive_ack()``（Round 20 新增）
      收到 ACK 时若 ``fcv==1``（FCV enabled）自动 ``flip_fcb()``。
      ``receive_nack()`` 与 ``on_timeout`` **不**触发 flip（避免
      失败帧错误翻转）。
    - sequence 状态机：``send_user_data()`` IDLE/SEND -> WAIT_ACK；
      ``receive_ack()`` WAIT_ACK -> IDLE + 成功 flip（balanced 模式）
      / ACK-only state change（unbalanced 模式）；``receive_nack()``
      WAIT_ACK -> ERROR；``reset()`` 任意状态 -> IDLE。
    - ``FakeLinkLayerTimerService`` 测试替身：记录每次
      ``start_timer / cancel_timer`` 调用并允许测试主动 ``fire(name)``
      触发 on_timeout。**禁止** sleep / real threading 计时器。

不负责（明确 deferred）:

    - 真实 RS-232 / RS-485 / PTY 串口收发、字节流分帧。
    - 真实超时、重试定时器、t1/t2/t3 等协议计时器线程（Round 20 提供
      可注入 timer_service，但 LinkLayer 默认不启用任何计时器线程）。
    - 完整 balanced 模式的发送/接收序列、FCB/FCV 翻转细节（仅
      状态机骨架，不做完整协议状态机）。
    - 任何 persistent session / 跨调用状态保留（每次 ``LinkLayer`` 实例
      独立维护本地状态，不连接外部资源）。
    - 这是 **skeleton**，不是 server。Iec101Facade 必须继续返回
      ``supports_server=false``，probe/profile/capacity 必须继续返回
      ``NOT_RUN / CODEC_ONLY`` + reason，不得写 PASS。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from starfish.domain.protocols.iec101.frame import (
    END_CHAR,
    FixedFrame,
    LinkControl,
    START_CHAR_FIXED,
    VariableFrame,
    compute_checksum,
)


# ── 枚举 ──────────────────────────────────────────────────────────────────────


class LinkLayerMode(str, Enum):
    """链路层传输模式（IEC 60870-5-101）。"""

    BALANCED = "balanced"  # 对等模式（双方均可发起）
    UNBALANCED = "unbalanced"  # 非平衡模式（主站发起）


class LinkState(str, Enum):
    """链路层最小状态机状态。

    skeleton 包含五个核心状态（Round 17 扩展）：
    - IDLE: 空闲，可发起新请求。
    - WAIT_ACK: 等待对端确认。
    - SEND: 正在发送用户数据帧（balanced 模式专用中间态）。
    - RECEIVE: 正在接收用户数据帧（balanced 模式专用中间态）。
    - ERROR: 检测到错误或非法转移，停留在 ERROR 等待外部恢复。
    """

    IDLE = "idle"
    WAIT_ACK = "wait_ack"
    SEND = "send"
    RECEIVE = "receive"
    ERROR = "error"


# ── 事件 / 结果 ───────────────────────────────────────────────────────────────


@dataclass
class LinkEvent:
    """链路层状态机事件。

    每次 ``feed_frame`` 调用产生一个 ``LinkEvent``，描述状态转移与
    接收帧的语义。调用方通过观察事件序列即可验证状态机行为。

    Attributes:
        previous_state: 转移前状态。
        current_state: 转移后状态。
        frame_kind: 接收帧类型："fixed" / "variable" / "unknown"。
        control: 接收帧的链路层 control 字节（如有）。
        is_ack: True 表示该帧被识别为 ACK（肯定确认）。
        is_nack: True 表示该帧被识别为 NACK（否定确认）。
        is_reset: True 表示该帧被识别为 RESET。
        is_user_data: True 表示该帧被识别为 user data。
        note: 解释性文本，便于测试断言。
    """

    previous_state: LinkState
    current_state: LinkState
    frame_kind: str
    control: int | None = None
    is_ack: bool = False
    is_nack: bool = False
    is_reset: bool = False
    is_user_data: bool = False
    note: str = ""


# ── LinkControl 辅助构造 ──────────────────────────────────────────────────────


class LinkControlHelper:
    """FT1.2 链路层控制帧 / 数据帧构造辅助。

    封装 ``FixedFrame`` / ``VariableFrame`` 的常用组装方式，便于测试
    与上层协议栈直接构造链路层报文。本类**不发起任何 IO**，只构造字节。

    本类提供的方法：
        - ``build_ack``: 构造 ACK（肯定确认）固定帧。
        - ``build_nack``: 构造 NACK（否定确认）固定帧。
        - ``build_reset``: 构造 RESET 固定帧。
        - ``build_reset_ack``: 构造 RESET ACK 固定帧。
        - ``build_user_data``: 构造 user data 可变帧。
    """

    @staticmethod
    def _fixed(control: int) -> FixedFrame:
        """构造单字节 control 固定帧（不验签）。"""
        return FixedFrame(control=control)

    @staticmethod
    def build_ack() -> FixedFrame:
        """构造 ACK（肯定确认）固定帧。

        IEC 60870-5-1 / FT1.2 中 SUPERVISORY 位 + ack data pattern;
        本实现采用 ``LinkControl.SUPERVISORY`` (0x01) 作为通用 ACK
        control 值。
        """
        return LinkControlHelper._fixed(int(LinkControl.SUPERVISORY))

    @staticmethod
    def build_nack() -> FixedFrame:
        """构造 NACK（否定确认）固定帧。

        在 IEC 60870-5-1 中 NACK 无标准 control 字段值；本实现沿用
        0x02 作为 NEGATIVE_ACK 约定值（不在 LinkControl 枚举中，
        避免污染已有枚举语义）。
        """
        return LinkControlHelper._fixed(0x02)

    @staticmethod
    def build_reset() -> FixedFrame:
        """构造 RESET 链路层重置固定帧。"""
        return LinkControlHelper._fixed(int(LinkControl.RESET))

    @staticmethod
    def build_reset_ack() -> FixedFrame:
        """构造 RESET ACK（重置确认）固定帧。"""
        return LinkControlHelper._fixed(int(LinkControl.RESET_ACK))

    @staticmethod
    def build_user_data(payload: bytes) -> VariableFrame:
        """构造 user data 可变帧。

        Args:
            payload: 链路层用户数据（如 ASDU 字节），长度 1..255。

        Returns:
            VariableFrame 实例。
        """
        return VariableFrame(data=bytes(payload))

    @staticmethod
    def build_fcb_fcv(
        fcb: bool = False,
        fcv: bool = False,
        function: int | None = None,
    ) -> "FixedFrame":
        """构造带 FCB/FCV 位的固定帧（用于 user data 方向控制）。

        FCB (Frame Count Bit, bit 4) 与 FCV (Frame Count Valid, bit 5)
        控制位用于有序帧传输与接收方去重。常用 function code：
            0x03 = USER_DATA_NOREPLY (FCB/FCV 启用)
            0x0B = USER_DATA_REPLY (FCB/FCV 启用)
            0x01 = SUPERVISORY (无 FCB/FCV)
        本方法只负责把 FCB/FCV 编码到 control 字节的低 6 位
        （bit 4 = FCB、bit 5 = FCV），其它位保留。

        Args:
            fcb: FCB 位值。
            fcv: FCV 位值。
            function: function code 低 4 位（0..15）；None 时
                使用 USER_DATA_REPLY (0x0B)。

        Returns:
            FixedFrame 实例。
        """
        fn = int(LinkControl.USER_DATA_REPLY) if function is None else function
        fn &= 0x0F
        control = fn
        if fcb:
            control |= 0x10
        if fcv:
            control |= 0x20
        return FixedFrame(control=control & 0xFF)

    @staticmethod
    def parse_fcb_fcv(control: int) -> tuple[bool, bool, int]:
        """从控制字段解析 FCB / FCV 位与 function code。

        Args:
            control: 控制字段字节（0..0xFF）。

        Returns:
            ``(fcb, fcv, function)`` 三元组。
                - fcb: FCB 位（bit 4）。
                - fcv: FCV 位（bit 5）。
                - function: function code 低 4 位（0..15）。
        """
        return (
            bool(control & 0x10),
            bool(control & 0x20),
            control & 0x0F,
        )


# ── 协议计时器服务接口（Round 20 增量，skeleton）─────────────────────────────────

# Timer 回调签名：``Callable[[str], None]``，name 为 timer 标识。
TimerCallback = Callable[[str], None]


class LinkLayerTimerService:
    """链路层 timer service 抽象接口（Round 20 新增，skeleton）。

    链路层计时器（t1/t2/t3）的实际执行需要根据运行时环境选择
    ``threading.Timer`` / ``asyncio`` / 真实硬件定时器等不同实现。
    本类定义统一接口，``LinkLayer`` 在 ``enable_timers=True`` 时通过
    注入的 service 调度计时器。

    **默认禁用**：``LinkLayer.__init__`` 默认
    ``enable_timers=False``，保持 Round 17 行为完全一致；测试可在
    构造时显式开启以验证调度路径。

    关键不变量：

    - ``start_timer(name, ms, cb)`` 同一 name 已存在时应**取消旧
      timer**再调度新 timer（避免重叠）。
    - ``cancel_timer(name)`` 对未启动的 name 必须**安全幂等**。
    - ``cancel_all()`` 必须停止所有未触发的 timer。
    - 实际触发回调由具体实现负责（threading.Timer 用后台线程，Fake
      实现由测试主动 ``fire(name)`` 触发）。
    """

    def start_timer(self, name: str, ms: int, callback: TimerCallback) -> None:
        """启动一次性 timer；name 已存在则取消旧 timer 重新调度。

        Args:
            name: timer 标识（必须非空）。
            ms: 延时（毫秒）；必须 >= 0。
            callback: 触发时调用的回调函数。
        """
        raise NotImplementedError

    def cancel_timer(self, name: str) -> None:
        """取消指定 name 的 timer；未启动的 name 幂等。"""
        raise NotImplementedError

    def cancel_all(self) -> None:
        """取消所有已注册 timer。"""
        raise NotImplementedError

    def active_names(self) -> list[str]:
        """返回当前活跃的 timer 名称列表（便于测试断言）。"""
        raise NotImplementedError


class DefaultLinkLayerTimerService(LinkLayerTimerService):
    """基于 ``threading.Timer`` 的默认 timer service（skeleton）。

    每个 timer 启动一个 ``threading.Timer`` 后台线程，到期后调用
    回调。本实现**仅在显式注入并启用时**启动线程；默认 LinkLayer
    不启用计时器。生产环境应替换为基于 asyncio / 真实硬件的实现。

    线程安全：内部用 ``threading.Lock`` 保护 ``_timers`` 字典。
    """

    def __init__(self) -> None:
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def start_timer(self, name: str, ms: int, callback: TimerCallback) -> None:
        """启动 ``threading.Timer``。name 已存在则取消旧 timer。"""
        if not name:
            raise ValueError("timer name 不能为空")
        if ms < 0:
            raise ValueError(f"timer 延时不能为负，实际 {ms} ms")
        with self._lock:
            existing = self._timers.pop(name, None)
            if existing is not None:
                existing.cancel()
            t = threading.Timer(
                ms / 1000.0,
                self._safe_invoke,
                args=(name, callback),
            )
            t.daemon = True
            self._timers[name] = t
            t.start()

    def _safe_invoke(self, name: str, callback: TimerCallback) -> None:
        """在 timer 线程中调用回调，并清理 ``_timers``。"""
        try:
            callback(name)
        finally:
            with self._lock:
                self._timers.pop(name, None)

    def cancel_timer(self, name: str) -> None:
        """取消指定 timer。"""
        with self._lock:
            t = self._timers.pop(name, None)
            if t is not None:
                t.cancel()

    def cancel_all(self) -> None:
        """取消所有 timer。"""
        with self._lock:
            timers = list(self._timers.values())
            self._timers.clear()
        for t in timers:
            t.cancel()

    def active_names(self) -> list[str]:
        """返回当前活跃 timer 名称列表（线程安全快照）。"""
        with self._lock:
            return list(self._timers.keys())


class FakeLinkLayerTimerService(LinkLayerTimerService):
    """测试用 fake timer service（不启动任何线程，纯记录 + 主动触发）。

    测试场景：
    - 调用 ``start_timer(name, ms, cb)`` 记录调用（不启动实际线程）。
    - 测试可调用 ``fire(name)`` 主动触发回调，模拟"时间到了"。
    - ``elapsed_ms(name)`` 返回自 start 以来累计"虚拟时间"（便于
      断言是否在 t1 窗口内触发）。
    - ``cancel_timer / cancel_all`` 正常生效（从记录中移除）。

    禁止引入 ``time.sleep`` / 真实线程。
    """

    def __init__(self) -> None:
        self._timers: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.start_calls: list[tuple[str, int]] = []
        self.cancel_calls: list[str] = []

    def start_timer(self, name: str, ms: int, callback: TimerCallback) -> None:
        """记录 timer 启动（不实际调度线程）。"""
        if not name:
            raise ValueError("timer name 不能为空")
        if ms < 0:
            raise ValueError(f"timer 延时不能为负，实际 {ms} ms")
        with self._lock:
            self._timers[name] = {
                "ms": ms,
                "callback": callback,
                "elapsed": 0,
                "fired": False,
                "cancelled": False,
            }
            self.start_calls.append((name, ms))

    def fire(self, name: str) -> None:
        """主动触发指定 timer 的回调（模拟"时间到了"）。

        Args:
            name: timer 标识。

        Raises:
            KeyError: 未启动的 timer。
        """
        with self._lock:
            entry = self._timers.get(name)
            if entry is None:
                raise KeyError(f"timer {name!r} 不存在或已被取消")
            if entry["fired"] or entry["cancelled"]:
                raise RuntimeError(f"timer {name!r} 已触发或已取消，不能再次 fire")
            entry["fired"] = True
            callback = entry["callback"]
        callback(name)

    def advance(self, name: str, delta_ms: int) -> None:
        """累加虚拟时间，便于测试断言"在 t1 窗口内 / 外"。"""
        with self._lock:
            entry = self._timers.get(name)
            if entry is None:
                raise KeyError(f"timer {name!r} 不存在")
            entry["elapsed"] += delta_ms

    def elapsed_ms(self, name: str) -> int:
        """返回自 start 以来累计虚拟时间（ms）。"""
        with self._lock:
            entry = self._timers.get(name)
            if entry is None:
                raise KeyError(f"timer {name!r} 不存在")
            return int(entry["elapsed"])

    def cancel_timer(self, name: str) -> None:
        """取消指定 timer（标记 cancelled，从活跃列表移除）。"""
        with self._lock:
            entry = self._timers.pop(name, None)
            if entry is not None:
                entry["cancelled"] = True
                self.cancel_calls.append(name)

    def cancel_all(self) -> None:
        """取消所有 timer。"""
        with self._lock:
            names = list(self._timers.keys())
            self._timers.clear()
        for n in names:
            self.cancel_calls.append(n)

    def active_names(self) -> list[str]:
        """返回当前活跃 timer 名称列表。"""
        with self._lock:
            return list(self._timers.keys())

    def is_fired(self, name: str) -> bool:
        """返回指定 timer 是否已触发。"""
        with self._lock:
            entry = self._timers.get(name)
            return bool(entry and entry["fired"])

    def is_cancelled(self, name: str) -> bool:
        """返回指定 timer 是否已取消。"""
        with self._lock:
            entry = self._timers.get(name)
            if entry is None:
                return True  # 已从列表移除视为已取消
            return bool(entry["cancelled"])


# ── 协议计时器常量（skeleton 占位）─────────────────────────────────────────────


# IEC 60870-5-1 / -2 协议计时器典型默认值（毫秒）。
# 本实现只暴露常量，不实现真实定时器线程（明确 deferred）。
T1_DEFAULT_MS = 1500  # 发送方等待 ACK 超时
T2_DEFAULT_MS = 1000  # 接收方响应超时（用于回答帧）
T3_DEFAULT_MS = 20000  # 空闲链路空闲超时（用于链路保活）


@dataclass
class LinkLayerTimers:
    """链路层协议计时器常量集合（skeleton 占位）。

    字段：t1 / t2 / t3（毫秒）。``LinkLayer`` 实例化时默认使用
    协议标准默认值；测试可通过替换字段值模拟不同时间预算场景。
    **不实现真实定时器线程**（不发起 sleep / threading.Timer），
    计时器仅作为字段记录 + 测试观察使用。

    Attributes:
        t1_ms: 发送方等待 ACK 超时（毫秒）。
        t2_ms: 接收方响应超时（毫秒）。
        t3_ms: 空闲链路超时（毫秒）。
    """

    t1_ms: int = T1_DEFAULT_MS
    t2_ms: int = T2_DEFAULT_MS
    t3_ms: int = T3_DEFAULT_MS

    def snapshot(self) -> dict[str, int]:
        """返回计时器快照（便于测试断言）。"""
        return {
            "t1_ms": self.t1_ms,
            "t2_ms": self.t2_ms,
            "t3_ms": self.t3_ms,
        }


# ── LinkLayer skeleton ───────────────────────────────────────────────────────


@dataclass
class LinkLayer:
    """IEC 60870-5-101 链路层最小状态机骨架。

    本类**不连接任何真实串口**，只维护本地 mode / state / sequence /
    retry / FCB / FCV / timers 计数，并通过 ``feed_frame`` 接收已解码
    的 ``FixedFrame`` / ``VariableFrame`` 进行状态转移。每次
    ``feed_frame`` 返回 ``LinkEvent``，调用方基于事件序列验证状态机
    行为。

    skeleton 行为约定:
        - 初始 state = ``IDLE``。
        - 收到 ``user data``（VariableFrame 或 fixed 0x07/0x0B）：
          IDLE -> IDLE（计数 user_data_received，不进入 WAIT_ACK）。
        - 收到 ``ACK``（SUPERVISORY 0x01）：WAIT_ACK -> IDLE。
        - 收到 ``NACK``（0x02）：WAIT_ACK -> ERROR。
        - 收到 ``RESET``（0x40）：任意状态 -> IDLE。
        - 收到 ``RESET_ACK``（0x20）：任意状态 -> IDLE。
        - 收到未识别 control：保持当前状态，note 标注。

    balanced / unbalanced 模式差异化（Round 17 新增）:
        - UNBALANCED：仅主站可发起命令；NACK 触发 ERROR 等待外部恢复。
        - BALANCED：双方均可发起命令；ACK 回到 IDLE 之后可继续发
          下一帧（``mark_sending()`` 显式把 state 设为 SEND）。
        - FCB/FCV 翻转与 retry 计数器在 BALANCED 模式才有意义；
          UNBALANCED 模式下 FCB/FCV 由主站硬性管控，skeleton 不做
          翻转策略，仅暴露 ``flip_fcb()`` 供调用方手动控制。

    Round 20 增量（计时器 / 翻转 / 序列）:
        - ``enable_timers`` 默认 False（**不**启动任何线程，保持
          Round 17 行为完全一致）；构造时显式开启并注入
          ``timer_service`` 后可调度 t1 / t2 / t3 计时器。
        - ``send_user_data()``：IDLE/SEND -> WAIT_ACK，并启动 t1 计时器
          （若启用）。
        - ``receive_ack()``：WAIT_ACK -> IDLE；balanced 模式下若
          ``fcv==1`` 自动 ``flip_fcb()``（ACK 后翻 FCB），unbalanced
          模式下 FCB 不翻（主站硬性管控）。
        - ``receive_nack()``：WAIT_ACK -> ERROR，并 ``bump_retry()``；
          retry_count > max_retries 时 state 保持 ERROR（不再回到 IDLE）。
        - ``on_timeout(name)``：默认 ``bump_retry()`` + state -> ERROR
          （超限后）；**不**触发 FCB 翻转（避免超时错误翻 FCB）。
        - ``reset()`` 自动 ``cancel_all()`` 所有 timer。

    Attributes:
        mode: 链路层模式（BALANCED / UNBALANCED）。
        state: 当前状态（可读写，便于测试强制设置）。
        send_sequence: 发送序号计数器（int，初始 0）。
        receive_sequence: 接收序号计数器（int，初始 0）。
        retry_count: 重试次数计数器（int，初始 0；skeleton 不会自动重试）。
        max_retries: 重试上限（int，默认 3；达到后 NACK 自动置 ERROR）。
        fcb: Frame Count Bit（int, 0/1；skeleton 不自动翻转，
            由 ``flip_fcb()`` 显式控制）。
        fcv: Frame Count Valid（int, 0/1）。
        timers: 协议计时器常量集合（``LinkLayerTimers`` 实例）。
        user_data_received: 已接收 user data 帧计数（仅 skeleton 观测用）。
        events: 历史 LinkEvent 列表（便于测试断言）。
        enable_timers: 是否启用 timer_service 调度（默认 False；启
            用后 ``send_user_data()`` 会自动调度 t1 timer）。
        timer_service: 已注册的 timer_service 实例（仅在
            ``enable_timers=True`` 时使用；默认 None）。
    """

    mode: LinkLayerMode = LinkLayerMode.UNBALANCED
    state: LinkState = LinkState.IDLE
    send_sequence: int = 0
    receive_sequence: int = 0
    retry_count: int = 0
    max_retries: int = 3
    fcb: int = 0
    fcv: int = 0
    timers: LinkLayerTimers = field(default_factory=LinkLayerTimers)
    user_data_received: int = 0
    events: list[LinkEvent] = field(default_factory=list)
    enable_timers: bool = False
    timer_service: LinkLayerTimerService | None = None
    timeout_events: list[dict[str, Any]] = field(default_factory=list)

    # ── 工具方法 ──────────────────────────────────────────────────────────

    def reset(self) -> None:
        """重置状态机至 IDLE，并清空所有计数与 timer。"""
        if self.enable_timers and self.timer_service is not None:
            try:
                self.timer_service.cancel_all()
            except Exception:
                # 计时器取消失败不应阻塞 reset
                pass
        self.state = LinkState.IDLE
        self.send_sequence = 0
        self.receive_sequence = 0
        self.retry_count = 0
        self.fcb = 0
        self.fcv = 0
        self.user_data_received = 0
        self.events.clear()
        self.timeout_events.clear()

    def snapshot(self) -> dict[str, Any]:
        """返回当前状态快照，便于测试断言。"""
        return {
            "mode": self.mode.value,
            "state": self.state.value,
            "send_sequence": self.send_sequence,
            "receive_sequence": self.receive_sequence,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "fcb": self.fcb,
            "fcv": self.fcv,
            "user_data_received": self.user_data_received,
            "event_count": len(self.events),
            "timers": self.timers.snapshot(),
            "enable_timers": self.enable_timers,
            "timeout_event_count": len(self.timeout_events),
        }

    def flip_fcb(self) -> int:
        """翻转 FCB 位（0 -> 1, 1 -> 0），并返回翻转后的值。

        skeleton 行为：仅翻转当前 fcb 字段，不影响 state 转移。
        调用方在发送一帧成功后才调用本方法。

        Returns:
            翻转后的 fcb 值（0 或 1）。
        """
        self.fcb = 1 - self.fcb
        return self.fcb

    def bump_retry(self) -> int:
        """递增 retry_count；超过 ``max_retries`` 时把 state 置为 ERROR。

        Returns:
            递增后的 retry_count。
        """
        self.retry_count += 1
        if self.retry_count > self.max_retries:
            self.state = LinkState.ERROR
        return self.retry_count

    def mark_sending(self) -> None:
        """测试 / 上层调用方：把 state 置为 SEND（balanced 模式专用）。"""
        self.state = LinkState.SEND

    def mark_receiving(self) -> None:
        """测试 / 上层调用方：把 state 置为 RECEIVE（balanced 模式专用）。"""
        self.state = LinkState.RECEIVE

    # ── Timer 调度辅助（Round 20 新增）─────────────────────────────────────

    def start_timer(self, name: str, ms: int, callback: TimerCallback) -> None:
        """通过 ``timer_service`` 启动一次性 timer。

        行为：
        - 若 ``enable_timers=False`` 或 ``timer_service is None``，
          本方法**静默跳过**（与 Round 17 行为一致）。
        - 若 ``enable_timers=True`` 且 service 已注册，则把回调透传
          给 ``timer_service.start_timer``。

        Args:
            name: timer 标识。
            ms: 延时（毫秒）。
            callback: 触发时调用的回调。
        """
        if not self.enable_timers or self.timer_service is None:
            return
        self.timer_service.start_timer(name, ms, callback)

    def cancel_timer(self, name: str) -> None:
        """取消指定 name 的 timer（仅在 ``enable_timers=True`` 时生效）。"""
        if not self.enable_timers or self.timer_service is None:
            return
        self.timer_service.cancel_timer(name)

    def cancel_all_timers(self) -> None:
        """取消所有 timer。"""
        if not self.enable_timers or self.timer_service is None:
            return
        self.timer_service.cancel_all()

    def on_timeout(self, name: str) -> None:
        """默认 timer 触发回调（Round 20 新增，skeleton）。

        行为：
        - 取消同名 timer（避免回调重复触发）。
        - ``bump_retry()``：retry_count + 1；超 max_retries 时 state
          置 ERROR。
        - **不**触发 FCB 翻转（避免超时错误翻 FCB；这是协议规范要求）。
        - 记录 ``timeout_events`` 列表，便于测试断言。

        Args:
            name: 触发的 timer 名称（默认实现不区分 name，调用方可
                在重写时区分 t1 / t2 / t3）。
        """
        self.cancel_timer(name)
        new_retry = self.bump_retry()
        prev_state = self.state
        # 记录 timeout 事件便于测试观察
        self.timeout_events.append({
            "name": name,
            "retry_count": new_retry,
            "state_after": self.state.value,
            "previous_state": prev_state.value,
        })

    # ── Sequence 状态机（Round 20 新增）────────────────────────────────────

    def send_user_data(self) -> None:
        """发送 user data 入口：state -> WAIT_ACK，启动 t1 计时器。

        行为：
        - 任意非 ERROR 状态可调用；ERROR 状态保持。
        - 启动 t1 计时器（仅当 ``enable_timers=True``）；cancel 旧
          t1 timer（避免重叠）。
        - 递增 ``send_sequence`` 计数。

        状态转移：
        - IDLE -> WAIT_ACK
        - SEND (balanced) -> WAIT_ACK
        - WAIT_ACK -> WAIT_ACK（保持，便于测试连续发送）
        - RECEIVE (balanced) -> WAIT_ACK
        - ERROR -> ERROR（保持）
        """
        if self.state == LinkState.ERROR:
            return
        self.bump_send_sequence()
        self.state = LinkState.WAIT_ACK
        if self.enable_timers and self.timer_service is not None:
            self.timer_service.start_timer("t1", self.timers.t1_ms, self.on_timeout)

    def receive_ack(self) -> tuple[LinkState, bool]:
        """处理 ACK 到达：state -> IDLE + balanced 模式下 auto-flip FCB。

        行为：
        - 取消 t1 计时器（ACK 到达，不再需要超时重试）。
        - 任意 WAIT_ACK 状态回到 IDLE；其它状态保持。
        - balanced 模式 + FCV enabled（``fcv==1``）时自动
          ``flip_fcb()``；unbalanced 模式或 FCV disabled 时不翻。
        - 记录 LinkEvent 便于观察。

        Returns:
            (previous_state, flipped) 元组，便于 feed_frame 构造
            LinkEvent 时引用。
        """
        self.cancel_timer("t1")
        previous_state = self.state
        if self.state == LinkState.WAIT_ACK:
            self.state = LinkState.IDLE
        elif self.state == LinkState.SEND and self.mode == LinkLayerMode.BALANCED:
            self.state = LinkState.IDLE
        # balanced + FCV enabled 时自动翻 FCB
        flipped = False
        if (
            self.mode == LinkLayerMode.BALANCED
            and self.fcv == 1
            and previous_state in (LinkState.WAIT_ACK, LinkState.SEND)
        ):
            self.flip_fcb()
            flipped = True
        return previous_state, flipped

    def receive_nack(self) -> LinkState:
        """处理 NACK 到达：state -> ERROR（若 WAIT_ACK）+ ``bump_retry()``。

        行为：
        - 取消 t1 计时器。
        - WAIT_ACK 状态进入 ERROR；其它状态保持。
        - ``bump_retry()`` 一次，使 retry_count 与状态机同步。
        - **不**触发 FCB 翻转（NACK 不应错误翻 FCB）。

        Returns:
            转移前的 previous_state，便于 feed_frame 构造 LinkEvent。
        """
        self.cancel_timer("t1")
        previous_state = self.state
        if self.state == LinkState.WAIT_ACK:
            self.state = LinkState.ERROR
        elif self.state == LinkState.SEND and self.mode == LinkLayerMode.BALANCED:
            self.state = LinkState.IDLE
        # retry 计数与 NACK 同步
        self.bump_retry()
        return previous_state

    # ── 核心 feed_frame 接口 ──────────────────────────────────────────────

    def feed_frame(self, frame: FixedFrame | VariableFrame | bytes) -> LinkEvent:
        """喂入一帧并产生 ``LinkEvent``，按 skeleton 约定更新状态。

        Args:
            frame: 已解码的 ``FixedFrame`` / ``VariableFrame``，或裸
                字节（自动通过 ``decode_frame`` 解析）。

        Returns:
            本次喂入产生的 ``LinkEvent``（同时已追加到 ``self.events``）。
        """
        previous_state = self.state

        # 归一化为已解码帧
        if isinstance(frame, (FixedFrame, VariableFrame)):
            decoded = frame
            kind = "fixed" if isinstance(frame, FixedFrame) else "variable"
        elif isinstance(frame, (bytes, bytearray)):
            bytes_data = bytes(frame)
            if not bytes_data:
                ev = LinkEvent(
                    previous_state=previous_state,
                    current_state=previous_state,
                    frame_kind="unknown",
                    note="空数据，无法识别 frame 类型",
                )
                self.events.append(ev)
                return ev
            if bytes_data[0] == START_CHAR_FIXED:
                kind = "fixed"
            elif bytes_data[0] == END_CHAR:  # 0x16 同时也是可变的结尾字符
                # 0x16 单独出现不是有效帧
                ev = LinkEvent(
                    previous_state=previous_state,
                    current_state=previous_state,
                    frame_kind="unknown",
                    control=None,
                    note=f"仅 END_CHAR (0x{END_CHAR:02X})，无 start，无法解析",
                )
                self.events.append(ev)
                return ev
            else:
                # 走 VariableFrame 解码路径（start 0x68）
                kind = "variable"
            try:
                from starfish.domain.protocols.iec101.frame import (
                    FixedFrame as _FF,
                    VariableFrame as _VF,
                )
                if kind == "fixed":
                    decoded = _FF.decode(bytes_data)
                else:
                    decoded = _VF.decode(bytes_data)
            except Exception as exc:
                ev = LinkEvent(
                    previous_state=previous_state,
                    current_state=previous_state,
                    frame_kind=kind,
                    note=f"frame 解码失败: {exc}",
                )
                self.events.append(ev)
                return ev
        else:
            ev = LinkEvent(
                previous_state=previous_state,
                current_state=previous_state,
                frame_kind="unknown",
                note=f"不支持的 frame 类型 {type(frame).__name__}",
            )
            self.events.append(ev)
            return ev

        # 分类处理
        is_ack = False
        is_nack = False
        is_reset = False
        is_user_data = False
        control: int | None = None
        note = ""

        if isinstance(decoded, FixedFrame):
            control = decoded.control
            if control == int(LinkControl.SUPERVISORY):
                is_ack = True
                # ACK 到达：t1 取消 + balanced FCV auto-flip（Round 20 增强）
                ack_prev_state, _flipped = self.receive_ack()
                # 使用 receive_ack 记录的 previous_state（可能与
                # 外层 previous_state 不同，但本场景下二者一致）。
                _ = ack_prev_state
                note = "ACK 到达"
            elif control == 0x02:
                is_nack = True
                # NACK 到达：t1 取消 + bump_retry（Round 20 增强）
                _nack_prev_state = self.receive_nack()
                note = "NACK 到达"
            elif control == int(LinkControl.RESET):
                is_reset = True
                self.cancel_timer("t1")
                self.state = LinkState.IDLE
                note = "RESET 到达，重置至 IDLE"
            elif control == int(LinkControl.RESET_ACK):
                is_reset = True
                self.cancel_timer("t1")
                self.state = LinkState.IDLE
                note = "RESET_ACK 到达，重置至 IDLE"
            elif control in (
                int(LinkControl.USER_DATA_NOREPLY),
                int(LinkControl.USER_DATA_REPLY),
            ):
                is_user_data = True
                self.user_data_received += 1
                # balanced 模式下 user data 到达 RECEIVE 中间态
                if self.mode == LinkLayerMode.BALANCED:
                    self.state = LinkState.RECEIVE
                note = "user data (fixed) 到达"
            else:
                note = f"未识别的 control=0x{control:02X}，保持状态"
        else:  # VariableFrame
            is_user_data = True
            self.user_data_received += 1
            if self.mode == LinkLayerMode.BALANCED:
                self.state = LinkState.RECEIVE
            note = "user data (variable) 到达"

        # 维护 sequence 计数
        self.receive_sequence = (self.receive_sequence + 1) & 0xFFFF

        ev = LinkEvent(
            previous_state=previous_state,
            current_state=self.state,
            frame_kind=kind,
            control=control,
            is_ack=is_ack,
            is_nack=is_nack,
            is_reset=is_reset,
            is_user_data=is_user_data,
            note=note,
        )
        self.events.append(ev)
        return ev

    # ── 发送计数器辅助（仅供测试）─────────────────────────────────────────

    def bump_send_sequence(self) -> int:
        """测试 / 上层调用方在发送一帧后调用：递增 send_sequence。

        Returns:
            递增前的 send_sequence 值。
        """
        old = self.send_sequence
        self.send_sequence = (self.send_sequence + 1) & 0xFFFF
        return old

    def mark_waiting_ack(self) -> None:
        """测试 / 上层调用方：把状态置为 WAIT_ACK（期望下一帧是 ACK）。"""
        self.state = LinkState.WAIT_ACK


# ── 状态转移辅助 ──────────────────────────────────────────────────────────────


def _apply_ack(state: LinkState, mode: LinkLayerMode) -> LinkState:
    """ACK 状态转移：WAIT_ACK -> IDLE；其它状态保持。

    balanced 模式下 SEND 收到 ACK 视为完成（回到 IDLE）；
    UNBALANCED 模式下 SEND 仅作主站使用，不应出现 ACK 应答。
    """
    if state == LinkState.WAIT_ACK:
        return LinkState.IDLE
    if state == LinkState.SEND and mode == LinkLayerMode.BALANCED:
        return LinkState.IDLE
    return state


def _apply_nack(state: LinkState, mode: LinkLayerMode) -> LinkState:
    """NACK 状态转移：WAIT_ACK -> ERROR；其它状态保持。

    balanced 模式下 SEND 收到 NACK 也回到 IDLE（skeleton 不做自动
    重试，由调用方根据 retry_count 决定是否 ``mark_sending()`` 重新发）。
    """
    if state == LinkState.WAIT_ACK:
        return LinkState.ERROR
    if state == LinkState.SEND and mode == LinkLayerMode.BALANCED:
        return LinkState.IDLE
    return state


# ── 便捷导出 helper ──────────────────────────────────────────────────────────


def compute_checksum_for_link(data: bytes) -> int:
    """对链路层用户数据计算 FT1.2 校验和（仅 skeleton 辅助）。"""
    return compute_checksum(data)


__all__ = [
    "LinkLayerMode",
    "LinkState",
    "LinkEvent",
    "LinkControlHelper",
    "LinkLayerTimers",
    "T1_DEFAULT_MS",
    "T2_DEFAULT_MS",
    "T3_DEFAULT_MS",
    "LinkLayerTimerService",
    "DefaultLinkLayerTimerService",
    "FakeLinkLayerTimerService",
    "LinkLayer",
    "compute_checksum_for_link",
]
