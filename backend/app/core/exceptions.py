"""
自定义异常类

定义了应用程序中使用的所有自定义异常，用于统一的错误处理和响应。
"""

from typing import Any, Optional


class AppError(Exception):
    """
    应用程序基础异常类

    所有自定义异常都应继承此类，以便统一处理。

    Attributes:
        message: 错误消息
        status_code: HTTP状态码
        details: 额外的错误详情
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化应用程序异常

        Args:
            message: 错误消息
            status_code: HTTP状态码，默认为500
            details: 额外的错误详情字典
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """
        将异常转换为字典格式，便于JSON序列化

        Returns:
            包含错误信息的字典
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class NotFoundError(AppError):
    """
    资源未找到异常

    当请求的资源不存在时抛出此异常。
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化资源未找到异常

        Args:
            resource_type: 资源类型（如 "Organization", "IP", "Domain"）
            resource_id: 资源标识符
            details: 额外的错误详情
        """
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message=message, status_code=404, details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ConflictError(AppError):
    """
    资源冲突异常

    当尝试创建已存在的资源或违反唯一性约束时抛出此异常。
    """

    def __init__(
        self,
        resource_type: str,
        field: str,
        value: str,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化资源冲突异常

        Args:
            resource_type: 资源类型
            field: 冲突的字段名
            value: 冲突的字段值
            details: 额外的错误详情
        """
        message = f"{resource_type} with {field}='{value}' already exists"
        super().__init__(message=message, status_code=409, details=details)
        self.resource_type = resource_type
        self.field = field
        self.value = value


class ValidationError(AppError):
    """
    数据验证异常

    当输入数据不符合验证规则时抛出此异常。
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化数据验证异常

        Args:
            message: 验证错误消息
            field: 验证失败的字段名
            details: 额外的错误详情
        """
        super().__init__(message=message, status_code=422, details=details)
        self.field = field


class DatabaseError(AppError):
    """
    数据库操作异常

    当数据库操作失败时抛出此异常。
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化数据库操作异常

        Args:
            message: 错误消息
            operation: 失败的操作类型（如 "insert", "update", "delete"）
            details: 额外的错误详情
        """
        super().__init__(message=message, status_code=500, details=details)
        self.operation = operation


class AuthenticationError(AppError):
    """
    认证异常

    当用户认证失败时抛出此异常。
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化认证异常

        Args:
            message: 错误消息
            details: 额外的错误详情
        """
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(AppError):
    """
    授权异常

    当用户没有足够权限执行操作时抛出此异常。
    """

    def __init__(
        self,
        message: str = "Not enough permissions",
        required_permission: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ) -> None:
        """
        初始化授权异常

        Args:
            message: 错误消息
            required_permission: 所需的权限
            details: 额外的错误详情
        """
        super().__init__(message=message, status_code=403, details=details)
        self.required_permission = required_permission
