"""
AIVOA Complaint Management System - Backend API Entrypoint
Pharmaceutical Manufacturing (API & FDF QA Module)
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import complaints_router

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="AIVOA Complaint Management System API",
    description="AI-powered Customer Complaint Management System for pharmaceutical manufacturing (API & FDF QA module)",
    version="0.1.0",
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    else:
        headers["Access-Control-Allow-Origin"] = "*"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal Server Error: {str(exc)}",
            "type": exc.__class__.__name__,
        },
        headers=headers,
    )

# Allowed origins for frontend integration
ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(complaints_router)


@app.get("/")
async def root():
    """Root endpoint providing service metadata."""
    return {
        "app": "AIVOA Complaint Management System",
        "description": "Pharmaceutical Manufacturing Customer Complaint QA Module (API & FDF)",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend service readiness."""
    return {
        "status": "healthy",
        "service": "aivoa-complaint-system-backend",
        "modules": {
            "api_qa": "ready",
            "fdf_qa": "ready",
            "ai_agent": "ready",
            "complaints_api": "ready",
        },
        "version": "0.1.0",
    }
