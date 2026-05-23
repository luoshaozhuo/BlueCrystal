"""ingest usecase 导出。

本模块集中导出 ingest usecase 公共入口，保持外部 import 稳定。
"""

from whale.ingest.usecases.source_acquisition_use_case import SourceAcquisitionUseCase

__all__ = ["SourceAcquisitionUseCase"]
