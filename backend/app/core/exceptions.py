from fastapi import HTTPException, status
from typing import Optional, Dict, Any, List


class NotFoundError(HTTPException):
    """Resource not found exception"""
    def __init__(
        self, 
        detail: str = "Resource not found", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )


class BadRequestError(HTTPException):
    """Bad request exception"""
    def __init__(
        self, 
        detail: str = "Bad request", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers
        )


class UnauthorizedError(HTTPException):
    """Unauthorized exception"""
    def __init__(
        self, 
        detail: str = "Not authenticated", 
        headers: Optional[Dict[str, Any]] = None
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers
        )


class ForbiddenError(HTTPException):
    """Forbidden exception"""
    def __init__(
        self, 
        detail: str = "Not authorized to perform this action", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers
        )


class ServiceUnavailableError(HTTPException):
    """Service unavailable exception"""
    def __init__(
        self, 
        detail: str = "Service unavailable", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers
        )


class ConfigurationError(HTTPException):
    """Configuration error exception"""
    def __init__(
        self, 
        detail: str = "System not properly configured", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )


class PluginError(Exception):
    """Base plugin exception"""
    def __init__(
        self, 
        detail: str = "Plugin exception", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )



class PluginNotFoundError(PluginError):
    """Plugin not found exception"""
    def __init__(
        self, 
        detail: str = "Plugin not found exception", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )



class PluginInitializationError(PluginError):
    """Plugin initialization exception"""
    def __init__(
        self, 
        detail: str = "Plugin initialization exception", 
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )