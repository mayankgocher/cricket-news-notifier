"""
Chat Router - Handles RAG chat endpoints
session_id is required for conversation history and query rewriting.
UI clients generate a UUID per browser session and pass it in the request.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.schemas import ChatResponse
from src.rag import query_engine
from src.rag import vectordb

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


class ChatRequest(BaseModel):
    """RAG chat request — session_id enables conversation history + query rewriting."""
    question: str
    session_id: Optional[str] = None  # "ui_{uuid}" for web, "telegram_{chat_id}" for bot


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Ask a question about cricket news (RAG with conversation history)."""
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question too short")

    # Prefix ensures UI and Telegram session IDs never collide
    session_id = f"ui_{request.session_id}" if request.session_id else None

    try:
        ans = query_engine.answer(request.question, session_id=session_id)
        return ChatResponse(answer=ans)

    except Exception as e:
        print(f"⚠️ Chat error: {e}")
        raise HTTPException(status_code=500, detail="Error processing question")


@router.post("/with-sources")
def chat_with_sources(request: ChatRequest):
    """Ask a question and get answer with sources."""
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question too short")

    session_id = f"ui_{request.session_id}" if request.session_id else None

    try:
        result = query_engine.answer_with_sources(request.question, session_id=session_id)
        return result

    except Exception as e:
        print(f"⚠️ Chat error: {e}")
        raise HTTPException(status_code=500, detail="Error processing question")


@router.get("/status")
def chat_status():
    """Check RAG system status."""
    try:
        doc_count = vectordb.get_count()
        return {
            "status": "online",
            "documents_indexed": doc_count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
