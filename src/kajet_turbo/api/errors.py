"""One place for every app-level exception -> HTTP response mapping.

Registered identically on every FastAPI app the project builds (`server.py`'s
production apps and `tests/api/conftest.py`'s test app) via :func:`install_error_handlers`,
so a route's error contract never depends on which harness is exercising it.

`ValueError`, `FileNotFoundError` and `FileExistsError` are deliberately not mapped here:
their meaning is route-specific and stays a local `except` until a route's service layer
raises a typed error (#253/#254).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from kajet_turbo.errors import FolderError, NoteError, RequestError
from kajet_turbo.errors import GitError as GitErrorCode
from kajet_turbo.log import logger
from kajet_turbo.markdown import BrokenWikilinkError
from kajet_turbo.repositories.git import GitError
from kajet_turbo.workspace import InvalidFolderError, TemporalMetadataError


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


async def _request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    # FastAPI raises RequestValidationError with a "json_invalid" entry when the body
    # doesn't parse as JSON at all; every other entry is a field-level validation failure.
    status_code = 400 if first.get("type") == "json_invalid" else 422
    loc = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
    msg = first.get("msg", "Invalid request body")
    detail = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=status_code,
        content={"error": str(RequestError.INVALID_INPUT), "detail": detail},
    )


async def _invalid_folder_handler(request: Request, exc: InvalidFolderError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"error": str(FolderError.INVALID_FOLDER), "detail": str(exc)}
    )


async def _broken_wikilink_handler(request: Request, exc: BrokenWikilinkError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"error": str(NoteError.BROKEN_WIKILINK), "detail": str(exc)}
    )


async def _temporal_metadata_handler(request: Request, exc: TemporalMetadataError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"error": str(NoteError.INVALID_INPUT), "detail": str(exc)}
    )


async def _git_error_handler(request: Request, exc: GitError) -> JSONResponse:
    logger.error(
        "git_error",
        request_id=getattr(request.state, "request_id", None),
        error=str(exc),
    )
    return JSONResponse(status_code=500, content={"error": str(GitErrorCode.GIT_ERROR)})


async def _unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        request_id=getattr(request.state, "request_id", None),
        exc_type=type(exc).__qualname__,
        error=str(exc),
    )
    return JSONResponse(status_code=500, content={"error": "internal_error"})


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _http_exception_handler)  # ty: ignore[invalid-argument-type] — FastAPI accepts narrower exc type at runtime
    app.add_exception_handler(RequestValidationError, _request_validation_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(InvalidFolderError, _invalid_folder_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(BrokenWikilinkError, _broken_wikilink_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(TemporalMetadataError, _temporal_metadata_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(GitError, _git_error_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(Exception, _unexpected_exception_handler)
