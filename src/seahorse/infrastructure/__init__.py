"""Seahorse 基础设施层。

本层隔离数据库、文件系统、driver backend、scheduler 和 telemetry 等
外部资源依赖。领域层和应用层不得 import 本层。
"""
