from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.config import settings
from app.utils.logger import get_logger
from app.core.exceptions import HoneypotException

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description="Agentic Honeypot for Scam Detection & Intelligence Extraction",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


# Exception handlers
@app.exception_handler(HoneypotException)
async def honeypot_exception_handler(request: Request, exc: HoneypotException):
    """Handle custom honeypot exceptions."""
    logger.error(f"Honeypot exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error", "message": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal server error"}
    )


# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response


# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint - API information.
    """
    return {
        "status": "running",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze-message",
            "session": "/api/session/{session_id}"
        },
        "authentication": "Requires x-api-key header"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"🚀 {settings.API_TITLE} v{settings.API_VERSION} starting...")
    logger.info(f"API Key configured: {'*' * 10}...")
    logger.info(f"GUVI Callback endpoint: {settings.GUVI_ENDPOINT}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info("🛑 Shutting down API...")
