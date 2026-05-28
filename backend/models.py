from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base


class Subscriber(Base):
    """Subscriber model - stores email and telegram subscriptions"""
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Email subscription
    email = Column(String, unique=True, nullable=True, index=True)
    email_subscribed = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Telegram subscription
    telegram_chat_id = Column(String, unique=True, nullable=True, index=True)
    telegram_subscribed = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())


class Newsletter(Base):
    """Newsletter archive - stores sent newsletters"""
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    headlines_count = Column(Integer, default=0)
    subscriber_count = Column(Integer, default=0)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())


class NewsItem(Base):
    """Individual news items - for archive display"""
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String)
    summary = Column(Text, nullable=True)
    source = Column(String)  # twitter, reddit, espn
    sentiment = Column(String)  # positive, negative, neutral
    url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())