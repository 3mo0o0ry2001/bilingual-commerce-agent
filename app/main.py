"""
main.py

FastAPI application entry point.
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter
from app.api.routes import router
from app.api.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("main")

app = FastAPI(
    title="Bilingual Commerce Agent",
    description="Arabic/English customer service agent for UAE perfume e-commerce",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exception anywhere in the app. Logs the full
    traceback for debugging, but returns a generic safe message to the
    client — never leak internal details (stack traces, DB errors, etc).
    """
    log.error(f"Unhandled exception on {request.url.path}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "حصل خطأ غير متوقع. حاول تاني بعد شوية."},
    )


app.include_router(router)
app.include_router(webhook_router)


@app.get("/")
def root():
    return {"service": "bilingual-commerce-agent", "status": "running"}