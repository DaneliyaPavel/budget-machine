from fastapi import HTTPException


def api_error(status_code: int, detail: str, code: str) -> HTTPException:
    """Helper to create HTTP errors with code."""
    return HTTPException(
        status_code=status_code, detail={"detail": detail, "code": code}
    )
