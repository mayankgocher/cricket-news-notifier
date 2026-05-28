"""
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.routers import subscribers, newsletters, chat, pipeline

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Cricket News Notifier API",
    description="API for Cricket Daily Digest - News aggregation and notification service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(subscribers.router)
app.include_router(newsletters.router)
app.include_router(chat.router)
app.include_router(pipeline.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "Cricket News Notifier API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "subscribe": "/subscribers/subscribe",
            "newsletters": "/newsletters/",
            "chat": "/chat/",
            "pipeline": "/pipeline/run"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Run with: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)