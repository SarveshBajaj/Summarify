from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
from typing import Optional, Dict, Any, List
import uvicorn
import time
import os

# For extensibility
from .providers import get_provider, ProviderType, ContentProvider
from .schemas import SummaryRequest, SummaryResponse, UserCreate, Token, User, QueryRecord
from .auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_active_user, get_current_user_id, register_user
)
from .database import log_query, get_user_queries, get_query_stats, get_user

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Summarify API",
    description="API for summarizing YouTube videos and other content",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for frontend and Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "chrome-extension://*"],  # Allow requests from any origin and Chrome extensions
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type", "Authorization"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
log_path = os.path.join("logs", "app.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logger.add(log_path, rotation="1 MB", retention="30 days", level="INFO")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Summarify API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    """Register a new user and return an access token"""
    try:
        user_data = register_user(user)
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        # Re-raise the exception from register_user
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return an access token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: str = Depends(get_current_active_user)):
    """Get current user information"""
    user_data = get_user(current_user)
    return User(
        username=user_data.get("username", ""),
        email=user_data.get("email"),
        disabled=user_data.get("disabled", False)
    )

@app.post("/summarize", response_model=SummaryResponse)
@limiter.limit("5/second")
async def summarize(
    request: Request,
    req: SummaryRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_active_user),
    user_id: int = Depends(get_current_user_id)
):
    """Summarize content from the provided URL"""
    start_time = time.time()
    logger.info(f"Summarization requested by {current_user} (ID: {user_id}) for {req.url}")

    try:
        # Get the appropriate provider based on the request
        provider_type = req.provider_type or ProviderType.youtube
        provider = get_provider(provider_type)

        # Get transcript
        transcript = provider.get_transcript(req.url)

        # Generate summary
        summary, is_okay = provider.summarize_and_validate(transcript, req.url)

        # Calculate metadata
        word_count = len(summary.split())
        processing_time = time.time() - start_time

        # Log the query in the database
        query_id = log_query(
            user_id=user_id,
            url=req.url,
            provider_type=provider_type,
            summary_length=word_count,
            valid=is_okay,
            processing_time=processing_time
        )

        # Log completion in the background to avoid delaying the response
        background_tasks.add_task(
            logger.info,
            f"Summary generated for {req.url} by {current_user} in {processing_time:.2f}s (Query ID: {query_id})"
        )

        # Always return the summary even if validation fails
        # This allows the user to see the summary and decide for themselves
        return SummaryResponse(
            summary=summary,
            valid=is_okay,
            metadata={
                "word_count": word_count,
                "source_type": provider_type,
                "processing_time_seconds": round(processing_time, 2),
                "query_id": query_id,
                # Add validation info to help users understand why a summary might be invalid
                "validation_info": "The summary may contain irrelevant content or not cover key topics from the video."
                                  "You can still use it, but we recommend reviewing it for accuracy."
            }
        )
    except ValueError as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during summarization"
        )

@app.get("/queries/me", response_model=List[QueryRecord])
async def get_my_queries(
    limit: int = 10,
    user_id: int = Depends(get_current_user_id)
):
    """Get recent queries for the current user"""
    queries = get_user_queries(user_id, limit)
    return queries

@app.get("/queries/stats")
async def get_queries_statistics(
    _: str = Depends(get_current_active_user)  # Ensure user is authenticated
):
    """Get overall query statistics"""
    stats = get_query_stats()
    return stats

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
