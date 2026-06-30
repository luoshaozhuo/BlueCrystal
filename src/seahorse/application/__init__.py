"""Seahorse 应用层。

应用层负责用例编排、端口契约和运行时状态骨架。它只能依赖
``seahorse.domain`` 与本层端口，不创建 driver、repository、socket
或 SDK client。
"""
