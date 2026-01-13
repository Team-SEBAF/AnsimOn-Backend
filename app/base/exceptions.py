class BaseException(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CodeException(BaseException):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message, status_code)
        self.code = code


class BadRequestException(BaseException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class UnauthorizedException(BaseException):
    def __init__(self, message: str):
        super().__init__(message, 401)


class ForbiddenException(BaseException):
    def __init__(self, message: str):
        super().__init__(message, 403)


class NotFoundException(BaseException):
    def __init__(self, message: str):
        super().__init__(message, 404)


class InternalServerErrorException(BaseException):
    def __init__(self, message: str):
        super().__init__(message, 500)


__all__ = [
    "BaseException",
    "CodeException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "InternalServerErrorException",
]
