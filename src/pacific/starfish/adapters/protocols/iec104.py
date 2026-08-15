

from pacific.starfish.core import ServerDefinition, ServerStatus


class IEC104Server():

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""

    def init(self) -> None:
        """初始化 server 内部资源；重复调用应安全。"""

    def start(self) -> None:
        """启动 server；重复调用应安全。"""

    def stop(self) -> None:
        """停止 server 并释放运行资源；重复调用应安全。"""

    def status(self) -> ServerStatus:
        """返回 server 当前运行状态。"""
