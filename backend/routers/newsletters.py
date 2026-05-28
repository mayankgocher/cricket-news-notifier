"""
Newsletters Router - Handles newsletter archive endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_db
from backend.models import Newsletter, NewsItem
from backend.schemas import NewsletterResponse, NewsItemResponse

router = APIRouter(
    prefix="/newsletters",
    tags=["newsletters"]
)


@router.get("/", response_model=List[NewsletterResponse])
def get_newsletters(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Get list of past newsletters (archive)
    """
    newsletters = db.query(Newsletter)\
        .order_by(Newsletter.sent_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return newsletters


@router.get("/{newsletter_id}")
def get_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    """
    Get single newsletter by ID
    """
    newsletter = db.query(Newsletter).filter(Newsletter.id == newsletter_id).first()
    
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    
    return {
        "id": newsletter.id,
        "content": newsletter.content,
        "headlines_count": newsletter.headlines_count,
        "subscriber_count": newsletter.subscriber_count,
        "sent_at": newsletter.sent_at
    }


@router.get("/latest/one")
def get_latest_newsletter(db: Session = Depends(get_db)):
    """
    Get the most recent newsletter
    """
    newsletter = db.query(Newsletter)\
        .order_by(Newsletter.sent_at.desc())\
        .first()
    
    if not newsletter:
        raise HTTPException(status_code=404, detail="No newsletters found")
    
    return {
        "id": newsletter.id,
        "content": newsletter.content,
        "headlines_count": newsletter.headlines_count,
        "subscriber_count": newsletter.subscriber_count,
        "sent_at": newsletter.sent_at
    }


@router.get("/news/items", response_model=List[NewsItemResponse])
def get_news_items(skip: int = 0, limit: int = 30, db: Session = Depends(get_db)):
    """
    Get individual news items (for archive display)
    """
    items = db.query(NewsItem)\
        .order_by(NewsItem.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return items


@router.get("/news/items/{item_id}", response_model=NewsItemResponse)
def get_news_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get single news item by ID
    """
    item = db.query(NewsItem).filter(NewsItem.id == item_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="News item not found")
    
    return item