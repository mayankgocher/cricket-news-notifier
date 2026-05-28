from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# =========================
# SUBSCRIBER SCHEMAS
# =========================
class SubscribeRequest(BaseModel):
    """Request to subscribe"""
    email: Optional[EmailStr] = None
    email_subscribe: bool = False
    telegram_subscribe: bool = False


class SubscriberResponse(BaseModel):
    """Subscriber info response"""
    id: int
    email: Optional[str] = None
    email_subscribed: bool
    email_verified: bool
    telegram_chat_id: Optional[str] = None
    telegram_subscribed: bool
    is_active: bool
    subscribed_at: datetime

    class Config:
        from_attributes = True


# =========================
# NEWSLETTER SCHEMAS
# =========================
class NewsletterResponse(BaseModel):
    """Newsletter archive response"""
    id: int
    headlines_count: int
    subscriber_count: int
    sent_at: datetime

    class Config:
        from_attributes = True


class NewsItemResponse(BaseModel):
    """Single news item response"""
    id: int
    headline: str
    summary: Optional[str] = None
    source: str
    sentiment: str
    url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# CHAT SCHEMAS
# =========================
class ChatRequest(BaseModel):
    """RAG chat request"""
    question: str


class ChatResponse(BaseModel):
    """RAG chat response"""
    answer: str


# =========================
# PIPELINE SCHEMAS
# =========================
class PipelineResponse(BaseModel):
    """Pipeline run response"""
    status: str
    message: str
    news_count: Optional[int] = None