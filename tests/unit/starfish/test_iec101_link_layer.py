"""Starfish IEC 60870-5-101 链路层 skeleton 测试。

验证：
1. LinkLayerMode 枚举定义。
2. LinkState 枚举定义（IDLE / WAIT_ACK / SEND / RECEIVE / ERROR）。
3. LinkEvent dataclass 字段。
4. LinkControlHelper 构造 ack / nack / reset / reset_ack / user_data 帧。
5. LinkLayer 状态转移：
   - 初始 state=IDLE
   - user data 不改变 state（UNBALANCED 模式）
   - WAIT_ACK -> IDLE on ACK
   - WAIT_ACK -> ERROR on NACK
   - 任意 state -> IDLE on RESET
   - 任意 state -> IDLE on RESET_ACK
   - 收到未识别 control 保持 state
6. LinkLayer 计数：send_sequence / receive_sequence / retry_count /
   user_data_received / fcb / fcv。
7. LinkLayer reset() 行为。
8. LinkLayer snapshot() 行为。
9. LinkLayer.feed_frame 支持 FixedFrame / VariableFrame / bytes 三种入参。
10. 明确 skeleton 行为（无 IO、无重试定时器）。
11. FCB/FCV 控制位 helper（build_fcb_fcv / parse_fcb_fcv）。
12. t1/t2/t3 协议计时器常量（LinkLayerTimers）。
13. sequence flip / retry 逻辑（flip_fcb / bump_retry / max_retries）。
14. balanced / unbalanced 模式差异化 skeleton 行为：
    - balanced 模式 user data 触发 RECEIVE 中间态
    - balanced 模式 ACK/NACK 在 SEND 状态回 IDLE
    - unbalanced 模式 NACK 仅在 WAIT_ACK 触发 ERROR

测试阶段：开发期验证 (P1)。
使用的替身：无（纯 codec 状态机测试）。
不能证明：真实 IEC101 server 链路层能力、串口收发、t1/t2/t3 定时器。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

import pytest

from starfish.domain.protocols.iec101 import (
    T1_DEFAULT_MS,
    T2_DEFAULT_MS,
    T3_DEFAULT_MS,
    FixedFrame,
    LinkControlHelper,
    LinkEvent,
    LinkLayer,
    LinkLayerMode,
    LinkLayerTimers,
    LinkState,
    VariableFrame,
)
from starfish.domain.protocols.iec101.frame import (
    END_CHAR,
    START_CHAR_FIXED,
)


# ── 枚举 / 数据类基础测试 ──────────────────────────────────────────────────────


class TestLinkLayerMode:
    """LinkLayerMode 枚举测试。"""

    def test_modes(self) -> None:
        """BALANCED / UNBALANCED 两种模式。"""
        assert LinkLayerMode.BALANCED.value == "balanced"
        assert LinkLayerMode.UNBALANCED.value == "unbalanced"


class TestLinkState:
    """LinkState 枚举测试。"""

    def test_states(self) -> None:
        """IDLE / WAIT_ACK / SEND / RECEIVE / ERROR 五种状态。"""
        assert LinkState.IDLE.value == "idle"
        assert LinkState.WAIT_ACK.value == "wait_ack"
        assert LinkState.SEND.value == "send"
        assert LinkState.RECEIVE.value == "receive"
        assert LinkState.ERROR.value == "error"


class TestLinkEvent:
    """LinkEvent 数据类测试。"""

    def test_event_defaults(self) -> None:
        """LinkEvent 默认字段值。"""
        ev = LinkEvent(
            previous_state=LinkState.IDLE,
            current_state=LinkState.IDLE,
            frame_kind="unknown",
        )
        assert ev.previous_state == LinkState.IDLE
        assert ev.current_state == LinkState.IDLE
        assert ev.frame_kind == "unknown"
        assert ev.control is None
        assert ev.is_ack is False
        assert ev.is_nack is False
        assert ev.is_reset is False
        assert ev.is_user_data is False
        assert ev.note == ""


# ── LinkControlHelper 构造测试 ──────────────────────────────────────────────────


class TestLinkControlHelper:
    """LinkControlHelper 构造工具测试。"""

    def test_build_ack(self) -> None:
        """build_ack 构造 SUPERVISORY 固定帧。"""
        ack = LinkControlHelper.build_ack()
        assert isinstance(ack, FixedFrame)
        assert ack.control == 0x01  # SUPERVISORY

    def test_build_nack(self) -> None:
        """build_nack 构造 0x02 固定帧。"""
        nack = LinkControlHelper.build_nack()
        assert isinstance(nack, FixedFrame)
        assert nack.control == 0x02

    def test_build_reset(self) -> None:
        """build_reset 构造 RESET 固定帧。"""
        reset = LinkControlHelper.build_reset()
        assert isinstance(reset, FixedFrame)
        assert reset.control == 0x40  # RESET

    def test_build_reset_ack(self) -> None:
        """build_reset_ack 构造 RESET_ACK 固定帧。"""
        reset_ack = LinkControlHelper.build_reset_ack()
        assert isinstance(reset_ack, FixedFrame)
        assert reset_ack.control == 0x20  # RESET_ACK

    def test_build_user_data_variable(self) -> None:
        """build_user_data 构造可变帧。"""
        user_data = LinkControlHelper.build_user_data(b"\x01\x02\x03")
        assert isinstance(user_data, VariableFrame)
        assert user_data.data == b"\x01\x02\x03"

    def test_build_user_data_empty_raises(self) -> None:
        """build_user_data 空数据应抛出 FrameError。"""
        with pytest.raises(Exception):
            LinkControlHelper.build_user_data(b"")


# ── LinkLayer 基础测试 ────────────────────────────────────────────────────────


class TestLinkLayerBasic:
    """LinkLayer 基础状态与计数测试。"""

    def test_initial_state(self) -> None:
        """初始 state=IDLE，计数为 0。"""
        ll = LinkLayer()
        assert ll.state == LinkState.IDLE
        assert ll.send_sequence == 0
        assert ll.receive_sequence == 0
        assert ll.retry_count == 0
        assert ll.user_data_received == 0
        assert ll.events == []

    def test_default_mode(self) -> None:
        """默认 mode=UNBALANCED。"""
        ll = LinkLayer()
        assert ll.mode == LinkLayerMode.UNBALANCED

    def test_explicit_mode(self) -> None:
        """可显式指定 mode=BALANCED。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        assert ll.mode == LinkLayerMode.BALANCED

    def test_reset_method(self) -> None:
        """reset() 复位 state 与全部计数。"""
        ll = LinkLayer()
        ll.state = LinkState.WAIT_ACK
        ll.send_sequence = 5
        ll.receive_sequence = 10
        ll.retry_count = 3
        ll.user_data_received = 7
        ll.events.append(
            LinkEvent(
                previous_state=LinkState.IDLE,
                current_state=LinkState.WAIT_ACK,
                frame_kind="fixed",
            )
        )
        ll.reset()
        assert ll.state == LinkState.IDLE
        assert ll.send_sequence == 0
        assert ll.receive_sequence == 0
        assert ll.retry_count == 0
        assert ll.user_data_received == 0
        assert ll.events == []

    def test_snapshot(self) -> None:
        """snapshot() 返回当前状态快照。"""
        ll = LinkLayer()
        snap = ll.snapshot()
        assert snap["mode"] == "unbalanced"
        assert snap["state"] == "idle"
        assert snap["send_sequence"] == 0
        assert snap["receive_sequence"] == 0
        assert snap["retry_count"] == 0
        assert snap["user_data_received"] == 0
        assert snap["event_count"] == 0

    def test_bump_send_sequence(self) -> None:
        """bump_send_sequence 递增并返回旧值。"""
        ll = LinkLayer()
        old = ll.bump_send_sequence()
        assert old == 0
        assert ll.send_sequence == 1
        old2 = ll.bump_send_sequence()
        assert old2 == 1
        assert ll.send_sequence == 2

    def test_mark_waiting_ack(self) -> None:
        """mark_waiting_ack 把 state 设为 WAIT_ACK。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        assert ll.state == LinkState.WAIT_ACK


# ── LinkLayer feed_frame 状态转移测试 ──────────────────────────────────────────


class TestLinkLayerFeedFrameStateTransitions:
    """LinkLayer.feed_frame 状态机行为测试。"""

    def test_user_data_no_state_change(self) -> None:
        """user data（variable）不应改变 state，仅计数。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02"))
        assert ev.is_user_data is True
        assert ev.current_state == LinkState.IDLE
        assert ev.previous_state == LinkState.IDLE
        assert ll.state == LinkState.IDLE
        assert ll.user_data_received == 1

    def test_user_data_fixed_no_state_change(self) -> None:
        """user data（fixed, control=0x07/0x0B）不应改变 state。"""
        ll = LinkLayer()
        # USER_DATA_NOREPLY = 0x07
        frame = FixedFrame(control=0x07)
        ev = ll.feed_frame(frame)
        assert ev.is_user_data is True
        assert ll.state == LinkState.IDLE
        assert ll.user_data_received == 1

    def test_ack_transitions_wait_ack_to_idle(self) -> None:
        """WAIT_ACK + ACK -> IDLE。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        assert ll.state == LinkState.WAIT_ACK
        ev = ll.feed_frame(LinkControlHelper.build_ack())
        assert ev.is_ack is True
        assert ev.current_state == LinkState.IDLE
        assert ll.state == LinkState.IDLE

    def test_ack_does_not_change_from_idle(self) -> None:
        """IDLE + ACK 保持 IDLE（不在 WAIT_ACK 时不应影响 state）。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_ack())
        assert ev.is_ack is True
        assert ll.state == LinkState.IDLE

    def test_nack_transitions_wait_ack_to_error(self) -> None:
        """WAIT_ACK + NACK -> ERROR。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        ev = ll.feed_frame(LinkControlHelper.build_nack())
        assert ev.is_nack is True
        assert ev.current_state == LinkState.ERROR
        assert ll.state == LinkState.ERROR

    def test_nack_does_not_change_from_idle(self) -> None:
        """IDLE + NACK 保持 IDLE。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_nack())
        assert ev.is_nack is True
        assert ll.state == LinkState.IDLE

    def test_reset_from_idle(self) -> None:
        """IDLE + RESET -> IDLE。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_reset())
        assert ev.is_reset is True
        assert ll.state == LinkState.IDLE

    def test_reset_from_wait_ack(self) -> None:
        """WAIT_ACK + RESET -> IDLE。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        ev = ll.feed_frame(LinkControlHelper.build_reset())
        assert ev.is_reset is True
        assert ll.state == LinkState.IDLE

    def test_reset_from_error(self) -> None:
        """ERROR + RESET -> IDLE。"""
        ll = LinkLayer()
        ll.state = LinkState.ERROR
        ev = ll.feed_frame(LinkControlHelper.build_reset())
        assert ev.is_reset is True
        assert ll.state == LinkState.IDLE

    def test_reset_ack_from_any_state(self) -> None:
        """任意 state + RESET_ACK -> IDLE。"""
        for start_state in (LinkState.IDLE, LinkState.WAIT_ACK, LinkState.ERROR):
            ll = LinkLayer()
            ll.state = start_state
            ev = ll.feed_frame(LinkControlHelper.build_reset_ack())
            assert ev.is_reset is True
            assert ll.state == LinkState.IDLE

    def test_unknown_control_keeps_state(self) -> None:
        """未识别 control 保持当前 state。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        frame = FixedFrame(control=0x55)  # 未识别 control
        ev = ll.feed_frame(frame)
        assert ev.control == 0x55
        assert ll.state == LinkState.WAIT_ACK  # 保持


# ── LinkLayer feed_frame 入参类型测试 ──────────────────────────────────────────


class TestLinkLayerFeedFrameInputs:
    """LinkLayer.feed_frame 支持多种入参类型测试。"""

    def test_feed_frame_fixed(self) -> None:
        """feed_frame 接受 FixedFrame。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_ack())
        assert ev.is_ack is True

    def test_feed_frame_variable(self) -> None:
        """feed_frame 接受 VariableFrame。"""
        ll = LinkLayer()
        ev = ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02\x03"))
        assert ev.is_user_data is True
        assert ev.frame_kind == "variable"

    def test_feed_frame_bytes_fixed(self) -> None:
        """feed_frame 接受 raw bytes（FixedFrame）。"""
        ll = LinkLayer()
        # 构造 raw bytes: 0x10 + control(0x40) + checksum + 0x16
        fixed_bytes = bytes([START_CHAR_FIXED, 0x40, 0xBF, END_CHAR])
        ev = ll.feed_frame(fixed_bytes)
        assert ev.is_reset is True
        assert ev.frame_kind == "fixed"

    def test_feed_frame_bytes_variable(self) -> None:
        """feed_frame 接受 raw bytes（VariableFrame）。"""
        ll = LinkLayer()
        var = LinkControlHelper.build_user_data(b"\x01\x02\x03")
        ev = ll.feed_frame(var.encode())
        assert ev.is_user_data is True
        assert ev.frame_kind == "variable"

    def test_feed_frame_empty_bytes(self) -> None:
        """feed_frame 空 bytes 产生 unknown 事件。"""
        ll = LinkLayer()
        ev = ll.feed_frame(b"")
        assert ev.frame_kind == "unknown"
        assert ll.state == LinkState.IDLE

    def test_feed_frame_unsupported_type(self) -> None:
        """feed_frame 不支持类型产生 unknown 事件。"""
        ll = LinkLayer()
        ev = ll.feed_frame("not a frame")  # type: ignore[arg-type]
        assert ev.frame_kind == "unknown"
        assert ll.state == LinkState.IDLE

    def test_feed_frame_invalid_bytes(self) -> None:
        """feed_frame 无效 raw bytes（仅 END_CHAR）产生 unknown 事件。"""
        ll = LinkLayer()
        ev = ll.feed_frame(bytes([END_CHAR]))
        assert ev.frame_kind == "unknown"


# ── LinkLayer sequence / 计数累计测试 ──────────────────────────────────────────


class TestLinkLayerCounters:
    """LinkLayer 计数累计测试。"""

    def test_receive_sequence_increments(self) -> None:
        """每次 feed_frame 接收序号递增 1。"""
        ll = LinkLayer()
        for i in range(5):
            ll.feed_frame(LinkControlHelper.build_user_data(b"\x01"))
        assert ll.receive_sequence == 5

    def test_user_data_received_accumulates(self) -> None:
        """user_data_received 累计所有 user data 帧。"""
        ll = LinkLayer()
        for _ in range(3):
            ll.feed_frame(LinkControlHelper.build_user_data(b"\x01"))
        for _ in range(2):
            ll.feed_frame(FixedFrame(control=0x07))  # USER_DATA_NOREPLY
        assert ll.user_data_received == 5

    def test_events_appended(self) -> None:
        """每次 feed_frame 都会追加一个 event。"""
        ll = LinkLayer()
        ll.feed_frame(LinkControlHelper.build_ack())
        ll.feed_frame(LinkControlHelper.build_reset())
        ll.feed_frame(LinkControlHelper.build_user_data(b"\x01"))
        assert len(ll.events) == 3
        assert ll.events[0].is_ack is True
        assert ll.events[1].is_reset is True
        assert ll.events[2].is_user_data is True


# ── LinkLayer skeleton 边界测试 ────────────────────────────────────────────────


class TestLinkLayerSkeletonBoundaries:
    """LinkLayer skeleton 边界 / 状态机一致性测试。"""

    def test_no_retry_automatically(self) -> None:
        """skeleton 不会自动重发 frame，但 NACK 路径上 bump_retry 计数。

        Round 20 强化：NACK 路径显式 ``bump_retry()``，使 ``retry_count``
        与状态机同步。**不**等价于"自动重发"：skeleton 不主动重新
        调度 ``send_user_data()``，仅记录 NACK 次数供调用方决策。
        """
        ll = LinkLayer()
        ll.feed_frame(LinkControlHelper.build_nack())  # 触发 receive_nack
        # Round 20：NACK 路径显式 bump_retry，retry_count == 1
        assert ll.retry_count == 1
        # IDLE 状态 + NACK 不会进 ERROR（仅 WAIT_ACK 触发）
        assert ll.state == LinkState.IDLE  # IDLE 时 NACK 不进 ERROR

    def test_nack_in_idle_bumps_retry_but_keeps_state(self) -> None:
        """Round 20：IDLE 状态 NACK 仍 bump_retry，但 state 保持 IDLE。"""
        ll = LinkLayer()
        assert ll.retry_count == 0
        ll.feed_frame(LinkControlHelper.build_nack())
        # receive_nack 路径：bump_retry 一次，state 保持 IDLE
        assert ll.retry_count == 1
        assert ll.state == LinkState.IDLE

    def test_state_machine_consistency(self) -> None:
        """状态机：NACK (in WAIT_ACK) -> ERROR 之后需 RESET 才能回 IDLE。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        ll.feed_frame(LinkControlHelper.build_nack())
        assert ll.state == LinkState.ERROR
        # 再次 NACK 仍保持 ERROR
        ll.mark_waiting_ack()
        ll.feed_frame(LinkControlHelper.build_nack())
        assert ll.state == LinkState.ERROR
        # RESET 恢复 IDLE
        ll.feed_frame(LinkControlHelper.build_reset())
        assert ll.state == LinkState.IDLE

    def test_no_io_side_effects(self) -> None:
        """skeleton 不进行任何 IO，feed_frame 不会影响文件系统或网络。"""
        ll = LinkLayer()
        for _ in range(10):
            ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02\x03"))
        # 仍能正常工作且无 IO 副作用
        assert ll.user_data_received == 10


# ── LinkLayerTimers 测试（Round 17 新增）──────────────────────────────────────


class TestLinkLayerTimers:
    """LinkLayerTimers 协议计时器测试。"""

    def test_default_values(self) -> None:
        """LinkLayerTimers 默认值与协议标准一致。"""
        t = LinkLayerTimers()
        assert t.t1_ms == 1500
        assert t.t2_ms == 1000
        assert t.t3_ms == 20000

    def test_module_level_constants(self) -> None:
        """模块级默认常量。"""
        assert T1_DEFAULT_MS == 1500
        assert T2_DEFAULT_MS == 1000
        assert T3_DEFAULT_MS == 20000

    def test_snapshot(self) -> None:
        """snapshot() 返回 dict。"""
        t = LinkLayerTimers()
        snap = t.snapshot()
        assert snap == {"t1_ms": 1500, "t2_ms": 1000, "t3_ms": 20000}

    def test_custom_values(self) -> None:
        """可显式设置计时器值。"""
        t = LinkLayerTimers(t1_ms=500, t2_ms=200, t3_ms=1000)
        assert t.t1_ms == 500
        assert t.t2_ms == 200
        assert t.t3_ms == 1000


# ── LinkControlHelper FCB/FCV helper 测试（Round 17 新增）─────────────────────


class TestLinkControlHelperFcbFcv:
    """LinkControlHelper.build_fcb_fcv / parse_fcb_fcv 测试。"""

    def test_build_fcb_fcv_default(self) -> None:
        """build_fcb_fcv 默认参数：FCB=0, FCV=0, function=USER_DATA_REPLY (0x0B)。"""
        frame = LinkControlHelper.build_fcb_fcv()
        assert isinstance(frame, FixedFrame)
        assert frame.control == int(0x0B)  # 0x0B = USER_DATA_REPLY

    def test_build_fcb_set(self) -> None:
        """FCB=True 时 bit 4 置 1。"""
        frame = LinkControlHelper.build_fcb_fcv(fcb=True)
        assert frame.control & 0x10

    def test_build_fcv_set(self) -> None:
        """FCV=True 时 bit 5 置 1。"""
        frame = LinkControlHelper.build_fcb_fcv(fcv=True)
        assert frame.control & 0x20

    def test_build_fcb_fcv_both(self) -> None:
        """FCB=FCV=True 时 bit 4 + bit 5 = 0x30。"""
        frame = LinkControlHelper.build_fcb_fcv(fcb=True, fcv=True)
        assert frame.control & 0x30 == 0x30

    def test_build_with_function(self) -> None:
        """自定义 function code。"""
        frame = LinkControlHelper.build_fcb_fcv(
            fcb=True, fcv=True, function=0x03,  # USER_DATA_NOREPLY
        )
        assert frame.control & 0x0F == 0x03
        assert frame.control & 0x30 == 0x30

    def test_parse_fcb_fcv_zero(self) -> None:
        """parse_fcb_fcv(0) -> (False, False, 0)。"""
        fcb, fcv, fn = LinkControlHelper.parse_fcb_fcv(0)
        assert fcb is False
        assert fcv is False
        assert fn == 0

    def test_parse_fcb_fcv_full(self) -> None:
        """parse_fcb_fcv(0x3F) -> (True, True, 0x0F)。"""
        fcb, fcv, fn = LinkControlHelper.parse_fcb_fcv(0x3F)
        assert fcb is True
        assert fcv is True
        assert fn == 0x0F

    def test_parse_fcb_only(self) -> None:
        """parse_fcb_fcv(0x10) -> (True, False, 0)。"""
        fcb, fcv, fn = LinkControlHelper.parse_fcb_fcv(0x10)
        assert fcb is True
        assert fcv is False
        assert fn == 0

    def test_parse_fcv_only(self) -> None:
        """parse_fcb_fcv(0x20) -> (False, True, 0)。"""
        fcb, fcv, fn = LinkControlHelper.parse_fcb_fcv(0x20)
        assert fcb is False
        assert fcv is True
        assert fn == 0

    def test_build_parse_roundtrip(self) -> None:
        """build + parse roundtrip。"""
        for fcb in (False, True):
            for fcv in (False, True):
                frame = LinkControlHelper.build_fcb_fcv(fcb=fcb, fcv=fcv)
                pfcb, pfcv, _ = LinkControlHelper.parse_fcb_fcv(frame.control)
                assert pfcb == fcb
                assert pfcv == fcv


# ── LinkLayer FCB / retry / timers / balanced mode 测试（Round 17 新增）─────


class TestLinkLayerFcbRetryTimers:
    """LinkLayer FCB / retry / timers 字段测试。"""

    def test_initial_fcb_fcv(self) -> None:
        """LinkLayer 初始 fcb=0 / fcv=0。"""
        ll = LinkLayer()
        assert ll.fcb == 0
        assert ll.fcv == 0

    def test_initial_max_retries(self) -> None:
        """LinkLayer 默认 max_retries=3。"""
        ll = LinkLayer()
        assert ll.max_retries == 3

    def test_initial_timers(self) -> None:
        """LinkLayer 默认 timers 为 LinkLayerTimers 默认值。"""
        ll = LinkLayer()
        assert ll.timers.t1_ms == 1500
        assert ll.timers.t2_ms == 1000
        assert ll.timers.t3_ms == 20000

    def test_snapshot_includes_fcb_timers(self) -> None:
        """snapshot() 应包含 fcb / fcv / max_retries / timers。"""
        ll = LinkLayer()
        snap = ll.snapshot()
        assert snap["fcb"] == 0
        assert snap["fcv"] == 0
        assert snap["max_retries"] == 3
        assert snap["timers"]["t1_ms"] == 1500

    def test_flip_fcb_toggles(self) -> None:
        """flip_fcb 应翻转 fcb 位 0/1。"""
        ll = LinkLayer()
        assert ll.flip_fcb() == 1
        assert ll.fcb == 1
        assert ll.flip_fcb() == 0
        assert ll.fcb == 0

    def test_flip_fcb_does_not_change_state(self) -> None:
        """flip_fcb 不应改变 state。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        state_before = ll.state
        ll.flip_fcb()
        assert ll.state == state_before

    def test_bump_retry_increments(self) -> None:
        """bump_retry 递增 retry_count。"""
        ll = LinkLayer()
        assert ll.retry_count == 0
        ll.bump_retry()
        assert ll.retry_count == 1
        ll.bump_retry()
        assert ll.retry_count == 2

    def test_bump_retry_exceeds_max(self) -> None:
        """bump_retry 超过 max_retries 时 state 置 ERROR。"""
        ll = LinkLayer()
        ll.max_retries = 2
        ll.bump_retry()  # 1
        assert ll.state != LinkState.ERROR
        ll.bump_retry()  # 2
        assert ll.state != LinkState.ERROR
        ll.bump_retry()  # 3 > 2
        assert ll.state == LinkState.ERROR

    def test_reset_clears_fcb(self) -> None:
        """reset() 应清零 fcb。"""
        ll = LinkLayer()
        ll.flip_fcb()
        assert ll.fcb == 1
        ll.reset()
        assert ll.fcb == 0

    def test_reset_clears_retry_count(self) -> None:
        """reset() 应清零 retry_count。"""
        ll = LinkLayer()
        ll.bump_retry()
        ll.bump_retry()
        assert ll.retry_count == 2
        ll.reset()
        assert ll.retry_count == 0

    def test_mark_sending_sets_state(self) -> None:
        """mark_sending 把 state 置为 SEND。"""
        ll = LinkLayer()
        ll.mark_sending()
        assert ll.state == LinkState.SEND

    def test_mark_receiving_sets_state(self) -> None:
        """mark_receiving 把 state 置为 RECEIVE。"""
        ll = LinkLayer()
        ll.mark_receiving()
        assert ll.state == LinkState.RECEIVE


class TestLinkLayerBalancedMode:
    """LinkLayer balanced 模式差异化 skeleton 行为测试。"""

    def test_balanced_user_data_triggers_receive(self) -> None:
        """balanced 模式 user data 触发 RECEIVE 中间态。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ev = ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02"))
        assert ev.is_user_data is True
        assert ll.state == LinkState.RECEIVE

    def test_unbalanced_user_data_keeps_idle(self) -> None:
        """unbalanced 模式 user data 保持 IDLE。"""
        ll = LinkLayer(mode=LinkLayerMode.UNBALANCED)
        ev = ll.feed_frame(LinkControlHelper.build_user_data(b"\x01\x02"))
        assert ev.is_user_data is True
        assert ll.state == LinkState.IDLE

    def test_balanced_ack_in_send_returns_idle(self) -> None:
        """balanced 模式 ACK 在 SEND 状态回 IDLE。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.mark_sending()
        assert ll.state == LinkState.SEND
        ev = ll.feed_frame(LinkControlHelper.build_ack())
        assert ev.is_ack is True
        assert ll.state == LinkState.IDLE

    def test_unbalanced_ack_in_send_stays_send(self) -> None:
        """unbalanced 模式 ACK 在 SEND 状态保持 SEND（无应答）。"""
        ll = LinkLayer(mode=LinkLayerMode.UNBALANCED)
        ll.mark_sending()
        ev = ll.feed_frame(LinkControlHelper.build_ack())
        assert ev.is_ack is True
        assert ll.state == LinkState.SEND  # 不变

    def test_balanced_nack_in_send_returns_idle(self) -> None:
        """balanced 模式 NACK 在 SEND 状态回 IDLE。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.mark_sending()
        ev = ll.feed_frame(LinkControlHelper.build_nack())
        assert ev.is_nack is True
        assert ll.state == LinkState.IDLE

    def test_unbalanced_nack_in_wait_ack_triggers_error(self) -> None:
        """unbalanced 模式 NACK 在 WAIT_ACK 触发 ERROR。"""
        ll = LinkLayer(mode=LinkLayerMode.UNBALANCED)
        ll.mark_waiting_ack()
        ev = ll.feed_frame(LinkControlHelper.build_nack())
        assert ev.is_nack is True
        assert ll.state == LinkState.ERROR

    def test_balanced_nack_in_wait_ack_triggers_error(self) -> None:
        """balanced 模式 NACK 在 WAIT_ACK 也触发 ERROR（与 unbalanced 一致）。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.mark_waiting_ack()
        ll.feed_frame(LinkControlHelper.build_nack())
        assert ll.state == LinkState.ERROR

    def test_balanced_user_data_fixed_triggers_receive(self) -> None:
        """balanced 模式 fixed user data (0x07/0x0B) 触发 RECEIVE。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.feed_frame(FixedFrame(control=0x0B))
        assert ll.state == LinkState.RECEIVE


class TestLinkLayerImports:
    """LinkLayer 模块导入边界测试。"""

    def test_link_layer_timers_default_import(self) -> None:
        """LinkLayerTimers / T1/T2/T3 常量可从 starfish.domain.protocols.iec101 导入。"""
        from starfish.domain.protocols.iec101 import (
            T1_DEFAULT_MS as t1,
            T2_DEFAULT_MS as t2,
            T3_DEFAULT_MS as t3,
            LinkLayerTimers as Timers,
        )
        assert t1 == 1500
        assert t2 == 1000
        assert t3 == 20000
        assert Timers is LinkLayerTimers

    def test_link_state_includes_send_receive(self) -> None:
        """LinkState 枚举含 SEND / RECEIVE。"""
        assert hasattr(LinkState, "SEND")
        assert hasattr(LinkState, "RECEIVE")


# ── Round 20 LinkLayer timer / FCB auto flip / sequence 测试 ──────────────


class TestLinkLayerTimerService:
    """LinkLayerTimerService 抽象 + Default / Fake 实现测试。"""

    def test_fake_service_start_records(self) -> None:
        """FakeLinkLayerTimerService.start_timer 记录调用不启动线程。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        callback_calls: list[str] = []
        svc.start_timer("t1", 100, lambda n: callback_calls.append(n))
        assert svc.active_names() == ["t1"]
        assert ("t1", 100) in svc.start_calls
        # 尚未触发
        assert callback_calls == []

    def test_fake_service_fire_invokes_callback(self) -> None:
        """FakeLinkLayerTimerService.fire 主动触发回调。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        callback_calls: list[str] = []
        svc.start_timer("t1", 100, lambda n: callback_calls.append(n))
        svc.fire("t1")
        assert callback_calls == ["t1"]
        assert svc.is_fired("t1")

    def test_fake_service_cancel(self) -> None:
        """FakeLinkLayerTimerService.cancel_timer 取消活跃 timer。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        svc.start_timer("t1", 100, lambda n: None)
        svc.cancel_timer("t1")
        assert "t1" not in svc.active_names()
        assert svc.is_cancelled("t1")

    def test_fake_service_cancel_unknown_safe(self) -> None:
        """FakeLinkLayerTimerService.cancel_timer 对未知 name 幂等。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        svc.cancel_timer("nonexistent")  # 不应抛

    def test_fake_service_cancel_all(self) -> None:
        """FakeLinkLayerTimerService.cancel_all 清空所有 timer。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        svc.start_timer("t1", 100, lambda n: None)
        svc.start_timer("t2", 200, lambda n: None)
        svc.cancel_all()
        assert svc.active_names() == []

    def test_fake_service_start_replaces_existing(self) -> None:
        """同一 name 重复 start_timer 取消旧 timer。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        svc.start_timer("t1", 100, lambda n: None)
        svc.start_timer("t1", 200, lambda n: None)
        assert svc.active_names() == ["t1"]
        # 第二次的 ms 应被记录
        assert ("t1", 200) in svc.start_calls

    def test_fake_service_advance_elapsed(self) -> None:
        """FakeLinkLayerTimerService.advance 累加虚拟时间。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        svc.start_timer("t1", 100, lambda n: None)
        assert svc.elapsed_ms("t1") == 0
        svc.advance("t1", 50)
        assert svc.elapsed_ms("t1") == 50

    def test_fake_service_start_validates(self) -> None:
        """FakeLinkLayerTimerService.start_timer 校验 name 非空 + ms >= 0。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        import pytest
        with pytest.raises(ValueError):
            svc.start_timer("", 100, lambda n: None)
        with pytest.raises(ValueError):
            svc.start_timer("t1", -1, lambda n: None)

    def test_default_service_can_be_instantiated(self) -> None:
        """DefaultLinkLayerTimerService 可实例化。"""
        from starfish.domain.protocols.iec101 import DefaultLinkLayerTimerService
        svc = DefaultLinkLayerTimerService()
        assert svc.active_names() == []

    def test_default_service_cancel_all_safe_when_empty(self) -> None:
        """DefaultLinkLayerTimerService.cancel_all 空时安全。"""
        from starfish.domain.protocols.iec101 import DefaultLinkLayerTimerService
        svc = DefaultLinkLayerTimerService()
        svc.cancel_all()  # 不应抛


class TestLinkLayerEnableTimers:
    """LinkLayer enable_timers 开关 + 与 timer_service 协作测试。"""

    def test_default_disable_timers(self) -> None:
        """LinkLayer 默认 enable_timers=False，timer_service=None。"""
        ll = LinkLayer()
        assert ll.enable_timers is False
        assert ll.timer_service is None

    def test_disable_timers_start_is_noop(self) -> None:
        """LinkLayer 默认 start_timer 静默跳过。"""
        ll = LinkLayer()
        # 不应抛
        ll.start_timer("t1", 100, lambda n: None)
        ll.cancel_timer("t1")
        ll.cancel_all_timers()

    def test_enable_timers_uses_service(self) -> None:
        """LinkLayer 启用 timer_service 时 start_timer 透传到 service。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.start_timer("t1", 100, lambda n: None)
        assert "t1" in svc.active_names()

    def test_send_user_data_starts_t1_when_enabled(self) -> None:
        """send_user_data 启用 timers 时启动 t1。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.send_user_data()
        assert ll.state == LinkState.WAIT_ACK
        assert "t1" in svc.active_names()
        # 计时器 ms 应为 LinkLayerTimers 默认 t1_ms
        assert ("t1", ll.timers.t1_ms) in svc.start_calls

    def test_send_user_data_no_t1_when_disabled(self) -> None:
        """send_user_data 默认（disable_timers）不启动 t1。"""
        ll = LinkLayer()
        ll.send_user_data()
        assert ll.state == LinkState.WAIT_ACK
        # 无 timer_service，无 start_calls 记录
        assert ll.timeout_events == []

    def test_receive_ack_cancels_t1(self) -> None:
        """receive_ack 取消 t1 计时器。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.send_user_data()  # 启动 t1
        assert "t1" in svc.active_names()
        ll.receive_ack()  # ACK 取消 t1
        assert "t1" not in svc.active_names()

    def test_receive_nack_cancels_t1(self) -> None:
        """receive_nack 取消 t1 计时器。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.send_user_data()
        ll.receive_nack()
        assert "t1" not in svc.active_names()

    def test_reset_cancels_all_timers(self) -> None:
        """LinkLayer.reset() 取消所有 timer。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.start_timer("t1", 100, lambda n: None)
        ll.start_timer("t2", 200, lambda n: None)
        ll.reset()
        assert svc.active_names() == []
        assert ll.timeout_events == []


class TestLinkLayerOnTimeout:
    """LinkLayer.on_timeout 默认行为测试（bump_retry + state -> ERROR）。"""

    def test_on_timeout_bumps_retry(self) -> None:
        """on_timeout 调用 bump_retry，retry_count 递增。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        assert ll.retry_count == 0
        ll.on_timeout("t1")
        assert ll.retry_count == 1

    def test_on_timeout_exceeds_max_goes_to_error(self) -> None:
        """on_timeout 触发 max_retries+1 时 state 置 ERROR。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc, max_retries=2)
        ll.mark_waiting_ack()
        ll.on_timeout("t1")  # 1
        assert ll.state != LinkState.ERROR
        ll.on_timeout("t1")  # 2
        assert ll.state != LinkState.ERROR
        ll.on_timeout("t1")  # 3 > 2
        assert ll.state == LinkState.ERROR

    def test_on_timeout_records_event(self) -> None:
        """on_timeout 记录 timeout_events 列表。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc)
        ll.on_timeout("t1")
        assert len(ll.timeout_events) == 1
        ev = ll.timeout_events[0]
        assert ev["name"] == "t1"
        assert ev["retry_count"] == 1
        assert ev["state_after"] == ll.state.value

    def test_on_timeout_does_not_flip_fcb(self) -> None:
        """on_timeout **不**触发 FCB 翻转（避免错误翻 FCB）。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc, mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.on_timeout("t1")
        assert ll.fcb == 0  # 不翻

    def test_timeout_callback_via_fake_service(self) -> None:
        """完整调度：send_user_data -> fire("t1") -> on_timeout 触发。"""
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc, max_retries=2)
        ll.send_user_data()
        assert ll.retry_count == 0
        # 第一次 fire：retry_count=1
        svc.fire("t1")
        assert ll.retry_count == 1
        # 1 <= max_retries=2 仍不进 ERROR
        assert ll.state != LinkState.ERROR
        # 再次 send + fire
        ll.send_user_data()
        svc.fire("t1")
        assert ll.retry_count == 2
        assert ll.state != LinkState.ERROR
        # 第三次 send + fire -> retry_count=3 > 2 -> ERROR
        ll.send_user_data()
        svc.fire("t1")
        assert ll.retry_count == 3
        assert ll.state == LinkState.ERROR


class TestLinkLayerReceiveAckNack:
    """LinkLayer.receive_ack / receive_nack 直接调用测试。"""

    def test_receive_ack_in_wait_ack_returns_idle(self) -> None:
        """receive_ack 在 WAIT_ACK 回到 IDLE。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        ll.receive_ack()
        assert ll.state == LinkState.IDLE

    def test_receive_ack_in_idle_keeps_idle(self) -> None:
        """receive_ack 在 IDLE 保持 IDLE。"""
        ll = LinkLayer()
        ll.receive_ack()
        assert ll.state == LinkState.IDLE

    def test_receive_nack_in_wait_ack_returns_error(self) -> None:
        """receive_nack 在 WAIT_ACK 触发 ERROR。"""
        ll = LinkLayer()
        ll.mark_waiting_ack()
        ll.receive_nack()
        assert ll.state == LinkState.ERROR
        # receive_nack 路径显式 bump_retry
        assert ll.retry_count == 1

    def test_receive_nack_in_idle_keeps_idle(self) -> None:
        """receive_nack 在 IDLE 保持 IDLE。"""
        ll = LinkLayer()
        ll.receive_nack()
        assert ll.state == LinkState.IDLE
        assert ll.retry_count == 1

    def test_send_user_data_increments_send_sequence(self) -> None:
        """send_user_data 递增 send_sequence。"""
        ll = LinkLayer()
        assert ll.send_sequence == 0
        ll.send_user_data()
        assert ll.send_sequence == 1
        ll.send_user_data()
        assert ll.send_sequence == 2

    def test_send_user_data_in_error_keeps_error(self) -> None:
        """send_user_data 在 ERROR 状态保持 ERROR。"""
        ll = LinkLayer()
        ll.state = LinkState.ERROR
        ll.send_user_data()
        assert ll.state == LinkState.ERROR


class TestLinkLayerFcbAutoFlip:
    """LinkLayer balanced 模式 FCB auto flip 测试（Round 20 新增）。"""

    def test_balanced_ack_with_fcv_enabled_flips_fcb(self) -> None:
        """balanced 模式 + FCV enabled 时 receive_ack 自动 flip_fcb。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.receive_ack()
        assert ll.fcb == 1  # auto flip

    def test_balanced_ack_with_fcv_enabled_flips_back(self) -> None:
        """balanced 模式 + FCV enabled 时连续 ACK 交替翻 FCB。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        for _ in range(3):
            ll.send_user_data()
            ll.receive_ack()
        # 起始 fcb=0; 第一次 ACK -> 1; 第二次 -> 0; 第三次 -> 1
        assert ll.fcb == 1

    def test_balanced_ack_with_fcv_disabled_no_flip(self) -> None:
        """balanced 模式 + FCV disabled（fcv=0）时不翻 FCB。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 0
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.receive_ack()
        assert ll.fcb == 0  # 不翻

    def test_unbalanced_ack_does_not_flip_fcb(self) -> None:
        """unbalanced 模式 ACK 不翻 FCB（主站硬性管控）。"""
        ll = LinkLayer(mode=LinkLayerMode.UNBALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.receive_ack()
        assert ll.fcb == 0  # 不翻

    def test_nack_does_not_flip_fcb(self) -> None:
        """NACK 不翻 FCB（避免错误翻）。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.receive_nack()
        assert ll.fcb == 0  # NACK 不翻

    def test_feed_frame_nack_does_not_flip_fcb(self) -> None:
        """feed_frame(NACK) 路径不翻 FCB。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.feed_frame(LinkControlHelper.build_nack())
        assert ll.fcb == 0

    def test_feed_frame_ack_balanced_fcv_flips(self) -> None:
        """feed_frame(ACK) 路径在 balanced + fcv=1 时翻 FCB。"""
        ll = LinkLayer(mode=LinkLayerMode.BALANCED)
        ll.fcv = 1
        ll.fcb = 0
        ll.mark_waiting_ack()
        ll.feed_frame(LinkControlHelper.build_ack())
        assert ll.fcb == 1


class TestLinkLayerRetryExceedsMax:
    """LinkLayer retry 超限进入 ERROR 测试。"""

    def test_retry_exceeds_max_goes_to_error(self) -> None:
        """retry_count 超过 max_retries 时（on_timeout 路径）state -> ERROR。

        receive_nack 在 WAIT_ACK 状态直接进 ERROR（与 Round 17 兼容）；
        on_timeout 是另一条 retry 路径，retry_count > max_retries 才置
        ERROR。
        """
        from starfish.domain.protocols.iec101 import FakeLinkLayerTimerService
        svc = FakeLinkLayerTimerService()
        ll = LinkLayer(enable_timers=True, timer_service=svc, max_retries=2)
        # 通过 on_timeout 路径：retry_count=1, 2 都不进 ERROR
        ll.on_timeout("t1")  # 1
        assert ll.retry_count == 1
        assert ll.state != LinkState.ERROR
        ll.on_timeout("t1")  # 2
        assert ll.retry_count == 2
        assert ll.state != LinkState.ERROR
        # retry_count=3 > 2 -> ERROR
        ll.on_timeout("t1")
        assert ll.retry_count == 3
        assert ll.state == LinkState.ERROR

    def test_error_state_persists_after_retry(self) -> None:
        """进入 ERROR 后继续 NACK 不会回到 IDLE。"""
        ll = LinkLayer(max_retries=1)
        ll.mark_waiting_ack()
        ll.receive_nack()  # 1
        ll.receive_nack()  # 2 > 1 -> ERROR
        assert ll.state == LinkState.ERROR
        # 继续 NACK 不会回到 IDLE
        ll.mark_waiting_ack()  # 强制设回 WAIT_ACK
        ll.receive_nack()  # 3
        assert ll.state == LinkState.ERROR  # 仍 ERROR

    def test_reset_clears_error_state(self) -> None:
        """reset() 清除 ERROR 状态回到 IDLE。"""
        ll = LinkLayer(max_retries=0)
        ll.mark_waiting_ack()
        ll.receive_nack()  # 1 > 0 -> ERROR
        assert ll.state == LinkState.ERROR
        ll.reset()
        assert ll.state == LinkState.IDLE
        assert ll.retry_count == 0


class TestLinkLayerSequenceStateMachine:
    """LinkLayer send_user_data / receive_ack / receive_nack 序列状态机测试。"""

    def test_idle_to_wait_ack_on_send(self) -> None:
        """IDLE -> WAIT_ACK on send_user_data。"""
        ll = LinkLayer()
        assert ll.state == LinkState.IDLE
        ll.send_user_data()
        assert ll.state == LinkState.WAIT_ACK

    def test_wait_ack_to_idle_on_ack(self) -> None:
        """WAIT_ACK -> IDLE on receive_ack。"""
        ll = LinkLayer()
        ll.send_user_data()
        assert ll.state == LinkState.WAIT_ACK
        ll.receive_ack()
        assert ll.state == LinkState.IDLE

    def test_wait_ack_to_error_on_nack(self) -> None:
        """WAIT_ACK -> ERROR on receive_nack。"""
        ll = LinkLayer()
        ll.send_user_data()
        ll.receive_nack()
        assert ll.state == LinkState.ERROR

    def test_idle_to_idle_on_ack(self) -> None:
        """IDLE + ACK 保持 IDLE（不在 WAIT_ACK 时不影响 state）。"""
        ll = LinkLayer()
        ll.receive_ack()
        assert ll.state == LinkState.IDLE

    def test_idle_to_idle_on_nack(self) -> None:
        """IDLE + NACK 保持 IDLE（不在 WAIT_ACK 时不影响 state）。"""
        ll = LinkLayer()
        ll.receive_nack()
        assert ll.state == LinkState.IDLE

    def test_send_ack_send_ack_sequence(self) -> None:
        """完整序列：send -> ack -> send -> ack 状态正确。"""
        ll = LinkLayer()
        for i in range(5):
            ll.send_user_data()
            assert ll.state == LinkState.WAIT_ACK
            ll.receive_ack()
            assert ll.state == LinkState.IDLE
        # send_sequence 应递增 5 次
        assert ll.send_sequence == 5

    def test_reset_resets_sequence_counters(self) -> None:
        """reset() 重置所有 sequence / retry / fcb 计数。"""
        ll = LinkLayer()
        ll.send_user_data()
        ll.receive_nack()
        ll.flip_fcb()
        assert ll.send_sequence > 0
        assert ll.retry_count > 0
        assert ll.fcb == 1
        ll.reset()
        assert ll.send_sequence == 0
        assert ll.retry_count == 0
        assert ll.fcb == 0
        assert ll.state == LinkState.IDLE

    def test_snapshot_includes_round20_fields(self) -> None:
        """snapshot() 包含 enable_timers / timeout_event_count。"""
        ll = LinkLayer()
        snap = ll.snapshot()
        assert "enable_timers" in snap
        assert "timeout_event_count" in snap
        assert snap["enable_timers"] is False
        assert snap["timeout_event_count"] == 0

    def test_no_real_threading_when_disabled(self) -> None:
        """默认 enable_timers=False 时不启动任何线程。"""
        import threading
        before = threading.active_count()
        ll = LinkLayer()
        for _ in range(20):
            ll.send_user_data()
            ll.receive_ack()
        after = threading.active_count()
        # 不应有新线程
        assert after == before
