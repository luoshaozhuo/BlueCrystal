"""message_pipeline 端口接口契约测试。

验证 MessageSourcePort、MessageSinkPort、SchemaRegistryPort、DeadLetterSinkPort、
ReplayPort 的 ABC 契约：不可直接实例化、abstractmethod 约束等。

被验证对象：
- whale.message_pipeline.ports: 所有端口 ABC

测试阶段：开发期验证 (contract/stub)（接口契约验证，不依赖具体适配器实现）。
"""

from __future__ import annotations

import inspect

import pytest

from whale.message_pipeline.ports import (
    DeadLetterSinkPort,
    MessageSinkPort,
    MessageSourcePort,
    ReplayPort,
    SchemaRegistryPort,
)


class TestPortAbcContracts:
    """端口 ABC 契约测试。"""

    def test_message_source_port_cannot_instantiate(self) -> None:
        """验证 MessageSourcePort 是 ABC，不可直接实例化。"""
        with pytest.raises(TypeError):
            MessageSourcePort()  # type: ignore[abstract]

    def test_message_sink_port_cannot_instantiate(self) -> None:
        """验证 MessageSinkPort 是 ABC，不可直接实例化。"""
        with pytest.raises(TypeError):
            MessageSinkPort()  # type: ignore[abstract]

    def test_schema_registry_port_cannot_instantiate(self) -> None:
        """验证 SchemaRegistryPort 是 ABC，不可直接实例化。"""
        with pytest.raises(TypeError):
            SchemaRegistryPort()  # type: ignore[abstract]

    def test_dead_letter_sink_port_cannot_instantiate(self) -> None:
        """验证 DeadLetterSinkPort 是 ABC，不可直接实例化。"""
        with pytest.raises(TypeError):
            DeadLetterSinkPort()  # type: ignore[abstract]

    def test_replay_port_cannot_instantiate(self) -> None:
        """验证 ReplayPort 是 ABC，不可直接实例化。"""
        with pytest.raises(TypeError):
            ReplayPort()  # type: ignore[abstract]

    def test_all_ports_are_abc(self) -> None:
        """验证所有端口都是 ABC 子类。"""
        ports = [
            MessageSourcePort,
            MessageSinkPort,
            SchemaRegistryPort,
            DeadLetterSinkPort,
            ReplayPort,
        ]
        for port in ports:
            assert inspect.isabstract(port), f"{port.__name__} 应为 ABC"

    def test_message_source_port_has_required_abstracts(self) -> None:
        """验证 MessageSourcePort 定义了 consume/commit/seek 抽象方法。"""
        abstracts = MessageSourcePort.__abstractmethods__
        assert "consume" in abstracts
        assert "commit" in abstracts
        assert "seek" in abstracts

    def test_message_sink_port_has_required_abstracts(self) -> None:
        """验证 MessageSinkPort 定义了 publish/flush 抽象方法。"""
        abstracts = MessageSinkPort.__abstractmethods__
        assert "publish" in abstracts
        assert "flush" in abstracts

    def test_schema_registry_port_has_required_abstracts(self) -> None:
        """验证 SchemaRegistryPort 定义了 register/get_schema 抽象方法。"""
        abstracts = SchemaRegistryPort.__abstractmethods__
        assert "register" in abstracts
        assert "get_schema" in abstracts

    def test_dead_letter_sink_port_has_send_abstract(self) -> None:
        """验证 DeadLetterSinkPort 定义了 send 抽象方法。"""
        assert "send" in DeadLetterSinkPort.__abstractmethods__

    def test_replay_port_has_replay_abstract(self) -> None:
        """验证 ReplayPort 定义了 replay 抽象方法。"""
        assert "replay" in ReplayPort.__abstractmethods__
