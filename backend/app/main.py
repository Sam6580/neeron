# app/main.py

import logging
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger("neeron")


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware generating X-Request-ID for tracing, audit, and debug support.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


from contextlib import asynccontextmanager
from app.core.mqtt import start_mqtt_client
from app.ml.psi_engine import psi_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload ML models
    psi_engine.load_model()
    
    # Start MQTT client
    import asyncio
    start_mqtt_client(asyncio.get_running_loop())
    yield
    # Shutdown logic if any

# OpenAPI metadata definition
app = FastAPI(
    title="NEERON API",
    description="Precision Aquaculture Intelligence Platform",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration. A wildcard origin cannot be combined with credentials
# per the CORS spec, so credentials are only enabled for explicit origins.
_cors_origins = settings.cors_origin_list
_allow_credentials = "*" not in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Mount the consolidated API v1 router
app.include_router(api_router, prefix="/api/v1")

# Mount WebSocket router
from app.websocket.endpoints import router as ws_router
app.include_router(ws_router, tags=["WebSockets"])

# Custom Exception Handlers for official JSON response compliance
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field_errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"][1:]) if len(err["loc"]) > 1 else str(err["loc"][0])
        field_errors.append({
            "field": field,
            "message": err["msg"],
        })
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "One or more validation checks failed on the payload.",
                "fieldErrors": field_errors,
            },
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "error": {
                "code": "HTTP_EXCEPTION",
                "message": exc.detail,
                "details": {},
            },
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "error": {
                "code": "BAD_REQUEST",
                "message": str(exc),
                "details": {},
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the full detail server-side; never leak internals to the client.
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled error (request_id=%s): %s", request_id, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal error occurred.",
                "details": {},
            },
        },
    )
