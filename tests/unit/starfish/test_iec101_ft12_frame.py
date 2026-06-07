"""Starfish IEC 60870-5-101 FT1.2 链路层帧测试。

验证：
1. 固定长度帧 encode/decode 往返。
2. 可变长度帧 encode/decode 往返。
3. Checksum 校验和计算与错误检测。
4. 起始字符 / 结束字符校验。
5. 长度字段一致性校验。
6. 自动识别固定 / 可变帧的 decode_frame。
7. 边界：最大 payload、长度不匹配、checksum 失败。

测试阶段：开发期验证 (P1)。
使用的替身：无（纯编解码器测试）。
不能证明：完整 balanced/unbalanced 状态机、真实串口收发、CRC-32 / CRC-16 / FT1.2
       全部子功能。
NOT_RUN 条件：无（所有测试纯 CPU 运算）。
"""

from __future__ import annotations

import pytest

from starfish.protocols.iec101 import (
    END_CHAR,
    FIXED_FRAME_SIZE,
    FixedFrame,
    FrameDecodeResult,
    FrameError,
    LinkControl,
    START_CHAR_FIXED,
    START_CHAR_VARIABLE,
    VARIABLE_FRAME_MAX_PAYLOAD,
    VariableFrame,
    compute_checksum,
    decode_frame,
    verify_checksum,
)


# ── Checksum 测试 ─────────────────────────────────────────────────────────────


class TestChecksum:
    """FT1.2 校验和计算与验证测试。"""

    def test_checksum_empty_data(self) -> None:
        """空数据 checksum 应为 0xFF（保持非 0）。"""
        assert compute_checksum(b"") == 0xFF

    def test_checksum_single_byte_zero(self) -> None:
        """单字节 0x00 的 checksum 为 0xFF。"""
        assert compute_checksum(b"\x00") == 0xFF

    def test_checksum_single_byte_ff(self) -> None:
        """单字节 0xFF 的 checksum 为 0x00。"""
        assert compute_checksum(b"\xFF") == 0x00

    def test_checksum_sum_known_vectors(self) -> None:
        """校验和已知向量。"""
        # sum=0 -> ~0 & 0xFF = 0xFF
        # sum=1 -> ~1 & 0xFF = 0xFE
        # sum=2 -> ~2 & 0xFF = 0xFD
        # sum=255 -> ~255 & 0xFF = 0x00
        # sum=256(=0) -> 0xFF
        # sum=3 -> ~3 & 0xFF = 0xFC
        assert compute_checksum(b"\x01") == 0xFE
        assert compute_checksum(b"\x02") == 0xFD
        assert compute_checksum(b"\x03") == 0xFC
        assert compute_checksum(b"\xFF") == 0x00

    def test_checksum_multi_byte(self) -> None:
        """多字节数据校验和。"""
        # sum=0+0+1=1 -> 0xFE
        assert compute_checksum(b"\x00\x00\x01") == 0xFE
        # sum=0x10+0x40 = 0x50 -> 0xAF
        assert compute_checksum(b"\x10\x40") == 0xAF

    def test_verify_checksum_pass(self) -> None:
        """verify_checksum 应正确识别合法校验和。"""
        data = b"\x01\x02\x03"
        cs = compute_checksum(data)
        assert verify_checksum(data, cs) is True

    def test_verify_checksum_fail(self) -> None:
        """verify_checksum 应正确识别非法校验和。"""
        data = b"\x01\x02\x03"
        assert verify_checksum(data, 0x00) is False
        assert verify_checksum(data, 0xAB) is False


# ── 固定长度帧测试 ───────────────────────────────────────────────────────────


class TestFixedFrame:
    """FT1.2 固定长度帧编解码测试。"""

    def test_fixed_frame_encode_basic(self) -> None:
        """固定帧编码基本结构。"""
        frame = FixedFrame(control=LinkControl.RESET)
        encoded = frame.encode()
        # 0x10 + control(1) + cs(1) + 0x16 = 4 字节
        assert len(encoded) == FIXED_FRAME_SIZE
        assert encoded[0] == START_CHAR_FIXED
        assert encoded[1] == LinkControl.RESET
        assert encoded[3] == END_CHAR

    def test_fixed_frame_encode_checksum(self) -> None:
        """固定帧校验和正确性。"""
        frame = FixedFrame(control=0x40)
        encoded = frame.encode()
        # checksum = ~(control) & 0xFF
        expected_cs = (~0x40) & 0xFF  # 0xBF
        assert encoded[2] == expected_cs

    def test_fixed_frame_decode(self) -> None:
        """固定帧解码。"""
        frame = FixedFrame(control=0x40)
        encoded = frame.encode()
        decoded = FixedFrame.decode(encoded)
        assert decoded.control == 0x40

    def test_fixed_frame_roundtrip(self) -> None:
        """固定帧多种 control 值 roundtrip。"""
        controls = [0x00, 0x01, 0x07, 0x0B, 0x20, 0x40, 0x7F, 0xFF]
        for ctrl in controls:
            frame = FixedFrame(control=ctrl)
            decoded = FixedFrame.decode(frame.encode())
            assert decoded.control == ctrl

    def test_fixed_frame_decode_too_short(self) -> None:
        """固定帧解码数据不足时抛出 FrameError。"""
        with pytest.raises(FrameError):
            FixedFrame.decode(b"\x10\x40\xBF")

    def test_fixed_frame_decode_wrong_start(self) -> None:
        """固定帧起始字符错误时抛出 FrameError。"""
        # 0x68 是可变帧起始字符
        bad = bytes([START_CHAR_VARIABLE, 0x40, 0xBF, 0x16, 0x00])
        with pytest.raises(FrameError):
            FixedFrame.decode(bad)

    def test_fixed_frame_decode_wrong_end(self) -> None:
        """固定帧结束字符错误时抛出 FrameError。"""
        bad = bytes([START_CHAR_FIXED, 0x40, 0xBF, 0x00, 0x00])
        with pytest.raises(FrameError):
            FixedFrame.decode(bad)

    def test_fixed_frame_decode_bad_checksum(self) -> None:
        """固定帧校验和错误时抛出 FrameError。"""
        # 起始 + 数据 + 错误 checksum + 结束
        bad = bytes([START_CHAR_FIXED, 0x40, 0x00, END_CHAR, 0x00])
        with pytest.raises(FrameError):
            FixedFrame.decode(bad)

    def test_fixed_frame_control_out_of_range(self) -> None:
        """固定帧 control 越界应抛出 ValueError。"""
        with pytest.raises(ValueError):
            FixedFrame(control=0x100)
        with pytest.raises(ValueError):
            FixedFrame(control=-1)


# ── 可变长度帧测试 ───────────────────────────────────────────────────────────


class TestVariableFrame:
    """FT1.2 可变长度帧编解码测试。"""

    def test_variable_frame_encode_basic(self) -> None:
        """可变帧编码基本结构。"""
        data = b"\x01\x02\x03\x04"
        frame = VariableFrame(data=data)
        encoded = frame.encode()
        # start(1) + length(1) + length(1) + data(4) + cs(1) + end(1) = 9 字节
        assert len(encoded) == 9
        assert encoded[0] == START_CHAR_VARIABLE
        assert encoded[1] == 4
        assert encoded[2] == 4
        assert encoded[3:7] == b"\x01\x02\x03\x04"
        assert encoded[-1] == END_CHAR

    def test_variable_frame_encode_single_byte(self) -> None:
        """可变帧单字节 data 编码。"""
        frame = VariableFrame(data=b"\xAB")
        encoded = frame.encode()
        assert len(encoded) == 6
        assert encoded[0] == START_CHAR_VARIABLE
        assert encoded[1] == 1
        assert encoded[2] == 1
        assert encoded[3] == 0xAB

    def test_variable_frame_encode_max_payload(self) -> None:
        """可变帧最大 payload (255 字节) 编码。"""
        data = bytes(range(255))
        frame = VariableFrame(data=data)
        encoded = frame.encode()
        # start(1) + length(1) + length(1) + data(255) + cs(1) + end(1) = 259 字节
        # (overhead 5 + payload 255 = 260? No: 1+1+1+255+1+1=260. Hmm.
        # 实际 frame 长度: start(1) + length(1) + length(1) + data(N) + cs(1) + end(1) = N + 5
        # 当 N=255 时总长 260。
        assert len(encoded) == 5 + 255
        assert encoded[1] == 255
        assert encoded[2] == 255
        assert encoded[3:258] == data

    def test_variable_frame_decode(self) -> None:
        """可变帧解码。"""
        frame = VariableFrame(data=b"\x01\x02\x03\x04")
        encoded = frame.encode()
        decoded = VariableFrame.decode(encoded)
        assert decoded.data == b"\x01\x02\x03\x04"

    def test_variable_frame_roundtrip(self) -> None:
        """可变帧多种 data roundtrip。"""
        cases = [
            b"\x01",
            b"\x01\x02",
            b"\x01\x02\x03\x04",
            b"\x00" * 100,
            b"\xFF" * 50,
            bytes(range(255)),
        ]
        for data in cases:
            frame = VariableFrame(data=data)
            decoded = VariableFrame.decode(frame.encode())
            assert decoded.data == data

    def test_variable_frame_empty_data_raises(self) -> None:
        """可变帧空 data 应抛出 FrameError。"""
        with pytest.raises(FrameError):
            VariableFrame(data=b"")

    def test_variable_frame_oversize_data_raises(self) -> None:
        """可变帧超长 data 应抛出 FrameError。"""
        with pytest.raises(FrameError):
            VariableFrame(data=b"\x00" * (VARIABLE_FRAME_MAX_PAYLOAD + 1))

    def test_variable_frame_decode_too_short(self) -> None:
        """可变帧解码数据不足时抛出 FrameError。"""
        with pytest.raises(FrameError):
            VariableFrame.decode(b"\x68\x01")

    def test_variable_frame_decode_wrong_start(self) -> None:
        """可变帧起始字符错误时抛出 FrameError。"""
        bad = bytes([0x10, 0x01, 0x01, 0xAB, 0xFF, 0x16])
        with pytest.raises(FrameError):
            VariableFrame.decode(bad)

    def test_variable_frame_decode_wrong_end(self) -> None:
        """可变帧结束字符错误时抛出 FrameError。"""
        # start(1) + len(1) + len(1) + data(1) + cs(1) + bad_end(1) = 6
        bad = bytes([START_CHAR_VARIABLE, 0x01, 0x01, 0xAB, 0xFF, 0x00])
        with pytest.raises(FrameError):
            VariableFrame.decode(bad)

    def test_variable_frame_decode_length_mismatch(self) -> None:
        """可变帧 length 字段不一致时抛出 FrameError。"""
        bad = bytes([START_CHAR_VARIABLE, 0x04, 0x05, 0x01, 0x02, 0x03, 0x04, 0x00, END_CHAR])
        with pytest.raises(FrameError):
            VariableFrame.decode(bad)

    def test_variable_frame_decode_size_mismatch(self) -> None:
        """可变帧声明长度与实际数据长度不匹配时抛出 FrameError。"""
        # 声明 length=5 但实际只有 1 字节 data
        bad = bytes([START_CHAR_VARIABLE, 0x05, 0x05, 0x01, 0x00, END_CHAR])
        with pytest.raises(FrameError):
            VariableFrame.decode(bad)

    def test_variable_frame_decode_bad_checksum(self) -> None:
        """可变帧校验和错误时抛出 FrameError。"""
        # 合法 length + 合法 data + 错误 cs
        bad = bytes([START_CHAR_VARIABLE, 0x01, 0x01, 0xAB, 0x00, END_CHAR])
        with pytest.raises(FrameError):
            VariableFrame.decode(bad)


# ── 自动识别解码测试 ──────────────────────────────────────────────────────────


class TestDecodeFrame:
    """自动识别解码测试。"""

    def test_decode_frame_fixed(self) -> None:
        """decode_frame 应正确识别固定帧。"""
        frame = FixedFrame(control=0x40)
        result = decode_frame(frame.encode())
        assert isinstance(result, FrameDecodeResult)
        assert result.ok is True
        assert result.kind == "fixed"
        assert isinstance(result.frame, FixedFrame)
        assert result.frame.control == 0x40

    def test_decode_frame_variable(self) -> None:
        """decode_frame 应正确识别可变帧。"""
        frame = VariableFrame(data=b"\x01\x02\x03")
        result = decode_frame(frame.encode())
        assert result.ok is True
        assert result.kind == "variable"
        assert isinstance(result.frame, VariableFrame)
        assert result.frame.data == b"\x01\x02\x03"

    def test_decode_frame_empty(self) -> None:
        """空数据应返回失败结果。"""
        result = decode_frame(b"")
        assert result.ok is False
        assert result.kind == "unknown"
        assert "空" in result.reason

    def test_decode_frame_unknown_start_char(self) -> None:
        """未知起始字符应返回 unknown 类型。"""
        result = decode_frame(b"\x00\x01\x02")
        assert result.ok is False
        assert result.kind == "unknown"
        assert "起始字符" in result.reason

    def test_decode_frame_fixed_bad_checksum(self) -> None:
        """固定帧 checksum 错误应返回失败结果（不抛出）。"""
        bad = bytes([START_CHAR_FIXED, 0x40, 0x00, END_CHAR, 0x00])
        result = decode_frame(bad)
        assert result.ok is False
        assert result.kind == "fixed"
        assert result.reason != ""

    def test_decode_frame_variable_bad_length(self) -> None:
        """可变帧 length 错误应返回失败结果（不抛出）。"""
        bad = bytes([START_CHAR_VARIABLE, 0x04, 0x05, 0x01, 0x02, 0x03, 0x04, 0x00, END_CHAR])
        result = decode_frame(bad)
        assert result.ok is False
        assert result.kind == "variable"
        assert result.reason != ""


# ── 与 ASDU 集成测试 ──────────────────────────────────────────────────────────


class TestFrameAsduIntegration:
    """FT1.2 帧承载 ASDU 的集成测试。"""

    def test_variable_frame_carries_asdu(self) -> None:
        """可变帧承载 ASDU：先 encode_asdu，再 encode VariableFrame。"""
        from starfish.protocols.iec101 import (
            Asdu, M_SP_NA_1_Object, SIQ,
            encode_asdu,
        )
        from starfish.protocols.iec101.asdu import ASDUHeader

        asdu = Asdu(
            header=ASDUHeader(
                type_id=1, vsq=0x02, cot=3, ca=1, ioa_count=2, sq=False,
            ),
            ioa_list=[100, 101],
            information_objects=[
                M_SP_NA_1_Object(siq=SIQ(value=True)),
                M_SP_NA_1_Object(siq=SIQ(value=False)),
            ],
        )
        asdu_bytes = encode_asdu(asdu)
        # 包装到 VariableFrame
        frame = VariableFrame(data=asdu_bytes)
        encoded_frame = frame.encode()
        # 解码
        result = decode_frame(encoded_frame)
        assert result.ok is True
        assert isinstance(result.frame, VariableFrame)
        # 从 VariableFrame.data 重新解析 ASDU
        from starfish.protocols.iec101 import decode_asdu
        decoded_asdu = decode_asdu(result.frame.data)
        assert isinstance(decoded_asdu, Asdu)
        assert decoded_asdu.ioa_list == [100, 101]
        assert len(decoded_asdu.information_objects) == 2
