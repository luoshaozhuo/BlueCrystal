"""采集角色实现。

定义轮询和订阅等不同采集模式的具体执行逻辑。
"""

from pacific.whale.ingest.usecases.roles.polling_acquisition_role import (
    PollingAcquisitionRole,
    PollingAcquisitionSession,
)
from pacific.whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
    SubscriptionAcquisitionSession,
)

__all__ = [
    "PollingAcquisitionRole",
    "PollingAcquisitionSession",
    "SubscriptionAcquisitionRole",
    "SubscriptionAcquisitionSession",
]
