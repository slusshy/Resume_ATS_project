"""RecruiterMind AI backend entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import jd, candidates, analysis, rankings, predictions, interview_questions
from app.core.config import settings
from app.core.database import init_db
from app.core.logger import logger
from app.core.exceptions import AppException, NotFoundException, ValidationException

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(jd.router, prefix="/upload-jd", tags=["job_descriptions"])
app.include_router(candidates.router, prefix="/upload-candidates", tags=["candidates"])
app.include_router(analysis.router, prefix="/analyze", tags=["analysis"])
app.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
app.include_router(predictions.router, prefix="/prediction", tags=["predictions"])
app.include_router(interview_questions.router, prefix="/interview-questions", tags=["interview_questions"])


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            "resource": exc.details.get("resource"),
            "resource_id": exc.details.get("resource_id"),
        },
    )


@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    logger.info("RecruiterMind AI backend started")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "upload_jd": "/upload-jd/",
            "upload_candidates": "/upload-candidates/",
            "analyze": "/analyze/",
            "rankings": "/rankings/",
            "predictions": "/prediction/{candidate_id}",
            "interview_questions": "/interview-questions/{candidate_id}",
        },
    }