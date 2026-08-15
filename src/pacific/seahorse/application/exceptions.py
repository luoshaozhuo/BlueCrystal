"""Seahorse 应用层稳定异常。

当前架构迁移只保留离线生成和 JSON handoff 行为；本文件预留应用层
可稳定捕获的异常类型，不承载运行时引擎实现。
"""


class SeahorseApplicationError(Exception):
    """应用层基础异常。

    用例可抛出该异常或其子类表达稳定失败语义；底层数据库、文件或
    driver 异常应在 adapter/infrastructure 边界转换后再进入应用层。
    """


class WritePlanBuildError(SeahorseApplicationError):
    """WritePlan 构建失败。

    该异常表示 Whale 元数据配置缺失、默认策略无法补齐，或纯内存契约
    校验失败。它不暴露 SQLAlchemy/Whale ORM 细节，供 API/CLI 层稳定捕获。
    """


class DataSourceRuntimeError(SeahorseApplicationError):
    """DataSource runtime 取值失败。

    该异常表示内存数据源配置缺失、函数引用不支持、replay 行不可用，或
    WriteBatch 生成时发现字段引用的 source_id 没有对应值。它不代表真实
    scheduler、Starfish writer 或外部文件流已运行。
    """


class SchedulerRuntimeError(SeahorseApplicationError):
    """Scheduler executor 运行失败。

    该异常表示内存 tick executor 缺少 WritePlan、状态不允许执行，或 batch
    生成失败。它不代表真实 50Hz scheduler、后台线程或 Starfish writer 已运行。
    """
