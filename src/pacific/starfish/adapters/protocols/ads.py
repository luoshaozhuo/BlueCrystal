
"""基于 pyads testserver 的 ADS server adapter。"""

import pandas as pd
from pyads.testserver import AdsTestServer, AdvancedHandler, PLCVariable

from pacific.starfish.core import ServerDefinition, ServerStatus
from pacific.starfish.errors import ServerError

class ADSServer():
    def __init__(self, definition: ServerDefinition) -> None:
        """初始化 server worker。

        Args:
            definition: 该 worker 持有的 server definition。
        """
        self._definition = definition
        self._server = None
        self._status = ServerStatus.NOT_CREATED

    @property
    def definition(self) -> ServerDefinition:
        """返回该 worker 持有的 server definition。"""
        return self._definition

    def init(self) -> None:
        """初始化 server 内部资源；重复调用应安全。"""
        if self._status == ServerStatus.RUNNING:
            raise ServerError(f"id = {self.definition.conn['connection_id']} 的 ADS server 正在运行，无法初始化")

        colums = ['symbol_name', 'symbol_type', 'ads_type_value', 'index_group', 'index_offset','byte_size']
        if not (self._definition.src_point_items_df.empty and self._definition.sink_point_items_df.empty):
            point_item_df = pd.concat(
                [self._definition.src_point_items_df[colums], self._definition.sink_point_items_df[colums]], 
                ignore_index=True
                )
            point_item_df = point_item_df.drop_duplicates(subset=["symbol_name"]).reset_index(drop=True)
        else:
            point_item_df = self._definition.src_point_items_df[colums] \
                if not self._definition.src_point_items_df.empty else self._definition.sink_point_items_df[colums]

        handler = AdvancedHandler()
        for _, row in point_item_df.iterrows():
            handler.add_variable(
                PLCVariable(
                    name=row['symbol_name'],
                    value=bytes(row['byte_size']),
                    ads_type=row['ads_type_value'],
                    symbol_type=row['symbol_type'],
                    index_group=row['index_group'],
                    index_offset=row['index_offset'],
                ))
        conn = self._definition.conn
        server = AdsTestServer(
            handler=handler,
            ip_address=str(conn["host"]),
            port=int(conn["port"]),
        )
        self._server = server
        self._status = ServerStatus.INITIALIZED

    def start(self) -> None:
        """启动 server；重复调用应安全。"""
        self.init()
        self._server.start()
        self._status = ServerStatus.RUNNING

    def stop(self) -> None:
        """停止 server 并释放运行资源；重复调用应安全。"""
        if self._status != ServerStatus.RUNNING:
            return
        self._server.stop()
        self._status = ServerStatus.STOPPED

    def status(self) -> ServerStatus:
        """返回 server 当前运行状态。"""
        return self._status


__test__ = {
    "read_write_notification": r"""
    使用 pyads client 验证 testserver 的同步读写与 ON_CHANGE 通知。

    该测试会在本地 ``127.0.0.1:48898`` 创建真实 socket，pyads
    ``AdsTestServer`` 只用于协议联调，不能证明真实 PLC 可用性。

    >>> import threading
    >>> import pyads
    >>> from pyads import constants
    >>> columns = [
    ...     "symbol_name",
    ...     "symbol_type",
    ...     "ads_type_value",
    ...     "index_group",
    ...     "index_offset",
    ...     "byte_size",
    ... ]
    >>> source_points = pd.DataFrame(
    ...     [{
    ...         "symbol_name": "MAIN.counter",
    ...         "symbol_type": "INT",
    ...         "ads_type_value": constants.ADST_INT16,
    ...         "index_group": 0x4020,
    ...         "index_offset": 0,
    ...         "byte_size": 2,
    ...     }],
    ...     columns=columns,
    ... )
    >>> definition = ServerDefinition(
    ...     conn=pd.Series({
    ...         "connection_id": 1,
    ...         "host": "127.0.0.1",
    ...         "port": 48898,
    ...     }),
    ...     src_point_items_df=source_points,
    ...     sink_point_items_df=pd.DataFrame(columns=columns),
    ... )
    >>> server = ADSServer(definition)
    >>> plc = pyads.Connection("127.0.0.1.1.1", 851, "127.0.0.1")
    >>> notification_handle = None
    >>> notification_values = []
    >>> notification_received = threading.Event()
    >>> def on_change(notification, _data):
    ...     _handle, _timestamp, value = plc.parse_notification(
    ...         notification, pyads.PLCTYPE_INT
    ...     )
    ...     notification_values.append(value)
    ...     notification_received.set()
    >>> try:
    ...     server.start()
    ...     plc.open()
    ...     plc.write_by_name("MAIN.counter", 7, pyads.PLCTYPE_INT)
    ...     assert plc.read_by_name("MAIN.counter", pyads.PLCTYPE_INT) == 7
    ...     notification_handle = plc.add_device_notification(
    ...         (0x4020, 0),
    ...         pyads.NotificationAttrib(
    ...             2,
    ...             trans_mode=pyads.ADSTRANS_SERVERONCHA,
    ...             max_delay=0.1,
    ...             cycle_time=0.01,
    ...         ),
    ...         on_change,
    ...     )
    ...     assert notification_handle is not None
    ...     plc.write_by_name("MAIN.counter", 9, pyads.PLCTYPE_INT)
    ...     assert notification_received.wait(2)
    ...     assert notification_values[-1] == 9
    ... finally:
    ...     try:
    ...         if notification_handle is not None and plc.is_open:
    ...             plc.del_device_notification(*notification_handle)
    ...     finally:
    ...         try:
    ...             plc.close()
    ...         finally:
    ...             server.stop()
    >>> assert server.status() is ServerStatus.STOPPED
    """,
}

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
