from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """Validation error - 400 Bad Request"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthenticationError(HTTPException):
    """Authentication error - 401 Unauthorized"""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization error - 403 Forbidden"""
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    """Not found error - 404"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """Conflict error - 409 (e.g., duplicate email)"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InternalServerError(HTTPException):
    """Internal server error - 500"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
