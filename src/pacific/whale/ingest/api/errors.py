"""API 错误定义。

定义 ingest API 的统一异常类（denied、not_found、conflict 等）
和对应的 HTTP 状态码映射。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ApiError(Exception):
    """异常处理器使用的结构化 API 错误。"""

    code: str
    message: str
    http_status: int
    action: str
    resource_type: str
    resource_id: str | None = None
    decision: str = "DENY"
    result: str = "FAILED"
    reason_code: str | None = None
    changed_fields: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        """to_payload 方法。"""
        
        return {
            "error": self.code,
                """将 ApiError 转换为 HTTP 响应 payload 字典。"""
            "message": self.message,
        }


def not_found(*, action: str, resource_type: str, resource_id: str) -> ApiError:
    """构造 404 Not Found 异常。"""
    return ApiError(
        code="NOT_FOUND",
        message=f"{resource_type} `{resource_id}` was not found.",
        http_status=404,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="NOT_FOUND",
        reason_code="NOT_FOUND",
    )


def conflict(
    *,
    action: str,
    
    resource_type: str,
    resource_id: str | None,
    message: str,
    changed_fields: list[str] | None = None,
) -> ApiError:
    """构造 409 Conflict 异常。用于版本冲突、资源重复等并发冲突场景。"""
    return ApiError(
        code="CONFLICT",
        message=message,
        http_status=409,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="CONFLICT",
        reason_code="VERSION_CONFLICT",
        changed_fields=changed_fields or [],
    )


def denied(*, action: str, resource_type: str, resource_id: str | None = None) -> ApiError:
    """构造 403 Forbidden 异常。用于权限不足拒绝访问。"""
    
    return ApiError(
        code="DENIED",
        message="Access denied.",
        http_status=403,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="DENIED",
        reason_code="ACCESS_DENIED",
    )
