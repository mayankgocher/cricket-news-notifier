"""
Pipeline Router - Handles pipeline trigger endpoints
"""

from fastapi import APIRouter, BackgroundTasks

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.schemas import PipelineResponse

router = APIRouter(
    prefix="/pipeline",
    tags=["pipeline"]
)

# Track pipeline status
pipeline_status = {
    "running": False,
    "last_run": None,
    "last_result": None
}


def run_pipeline_task():
    """Background task to run pipeline"""
    global pipeline_status
    
    try:
        pipeline_status["running"] = True
        
        from src.pipeline.graph import run_pipeline
        result = run_pipeline()
        
        from datetime import datetime
        pipeline_status["last_run"] = datetime.now().isoformat()
        pipeline_status["last_result"] = {
            "news_count": len(result.get("news_items", [])),
            "emails_sent": result.get("email_sent", 0),
            "telegram_sent": result.get("telegram_sent", 0),
            "success": True
        }
    
    except Exception as e:
        pipeline_status["last_result"] = {
            "success": False,
            "error": str(e)
        }
    
    finally:
        pipeline_status["running"] = False


@router.post("/run", response_model=PipelineResponse)
def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the news pipeline (runs in background)
    """
    global pipeline_status
    
    if pipeline_status["running"]:
        return PipelineResponse(
            status="already_running",
            message="Pipeline is already running. Please wait."
        )
    
    # Run in background
    background_tasks.add_task(run_pipeline_task)
    
    return PipelineResponse(
        status="started",
        message="Pipeline started in background"
    )


@router.get("/status")
def get_pipeline_status():
    """
    Get current pipeline status
    """
    return {
        "running": pipeline_status["running"],
        "last_run": pipeline_status["last_run"],
        "last_result": pipeline_status["last_result"]
    }


@router.post("/run-sync", response_model=PipelineResponse)
def trigger_pipeline_sync():
    """
    Trigger pipeline and wait for completion (for testing)
    WARNING: This blocks the request until pipeline completes
    """
    global pipeline_status
    
    if pipeline_status["running"]:
        return PipelineResponse(
            status="already_running",
            message="Pipeline is already running"
        )
    
    try:
        from src.pipeline.graph import run_pipeline
        
        pipeline_status["running"] = True
        result = run_pipeline()
        pipeline_status["running"] = False
        
        news_count = len(result.get("news_items", []))
        
        return PipelineResponse(
            status="completed",
            message=f"Pipeline completed successfully",
            news_count=news_count
        )
    
    except Exception as e:
        pipeline_status["running"] = False
        return PipelineResponse(
            status="error",
            message=f"Pipeline failed: {str(e)}"
        )