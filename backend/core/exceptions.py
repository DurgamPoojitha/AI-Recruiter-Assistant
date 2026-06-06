from fastapi import Request
from fastapi.responses import JSONResponse
from backend.core.logging import logger

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"AppError at {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message},
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "An unexpected error occurred. Please try again later."},
    )
