"""Beckhoff ADS source_lab 协议实现。

导出两类 facade：
- BeckhoffAdsSimulatorFacade: backend_kind=in_process，进程内 lightweight ADS simulator；
- BeckhoffDotnetAdsSimulatorFacade: backend_kind=beckhoff_dotnet，真实 .NET server + client。
"""

from tools.source_lab.protocols.beckhoff_ads.simulator import (
    BeckhoffAdsSimulatorFacade,
    BeckhoffDotnetAdsSimulatorFacade,
)

__all__ = ["BeckhoffAdsSimulatorFacade", "BeckhoffDotnetAdsSimulatorFacade"]
