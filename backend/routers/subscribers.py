"""
Subscribers Router - Handles subscription endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import get_db
from backend.models import Subscriber
from backend.schemas import SubscribeRequest, SubscriberResponse
from src.config.settings import VERIFICATION_ENABLED, SITE_URL
from src.notifiers.email_agent import EmailAgent

router = APIRouter(
    prefix="/subscribers",
    tags=["subscribers"]
)


@router.post("/subscribe")
def subscribe(request: SubscribeRequest, db: Session = Depends(get_db)):
    """
    Subscribe to newsletter (email and/or telegram)
    """
    # Validate - at least one subscription type required
    if not request.email_subscribe and not request.telegram_subscribe:
        raise HTTPException(status_code=400, detail="Select at least one subscription type")
    
    # Check if email subscription requested
    if request.email_subscribe:
        if not request.email:
            raise HTTPException(status_code=400, detail="Email required for email subscription")
        
        # Check if email already exists
        existing = db.query(Subscriber).filter(Subscriber.email == request.email).first()
        
        if existing:
            # Reactivate if inactive
            if not existing.is_active:
                existing.is_active = True
                existing.email_subscribed = True
                db.commit()
                return {"message": "Subscription reactivated", "id": existing.id}
            
            # Update subscription if already exists
            existing.email_subscribed = True
            db.commit()
            return {"message": "Email subscription updated", "id": existing.id}
        
        # Create new subscriber
        token = secrets.token_urlsafe(32) if VERIFICATION_ENABLED else None
        expires = datetime.utcnow() + timedelta(hours=24) if VERIFICATION_ENABLED else None
        
        subscriber = Subscriber(
            email=request.email,
            email_subscribed=True,
            email_verified=not VERIFICATION_ENABLED,  # Auto-verify if disabled
            verification_token=token,
            token_expires_at=expires,
            telegram_subscribed=request.telegram_subscribe,
            is_active=True
        )
        
        db.add(subscriber)
        db.commit()
        db.refresh(subscriber)
        
        # Send verification email if enabled
        if VERIFICATION_ENABLED:
            email_agent = EmailAgent()
            email_agent.send_verification(request.email, token, SITE_URL)
            return {"message": "Verification email sent. Please check your inbox.", "id": subscriber.id}
        
        return {"message": "Subscribed successfully!", "id": subscriber.id}
    
    # Telegram only subscription (handled via bot)
    if request.telegram_subscribe:
        return {"message": "To subscribe via Telegram, message our bot with /subscribe"}


@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify email subscription using token
    """
    subscriber = db.query(Subscriber).filter(
        Subscriber.verification_token == token
    ).first()
    
    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid verification link")
    
    # Check if token expired
    if subscriber.token_expires_at and subscriber.token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification link expired")
    
    # Verify email
    subscriber.email_verified = True
    subscriber.verification_token = None
    subscriber.token_expires_at = None
    db.commit()
    
    return {"message": "Email verified successfully! You will now receive newsletters."}


@router.post("/unsubscribe")
def unsubscribe(email: str = None, telegram_chat_id: str = None, db: Session = Depends(get_db)):
    """
    Unsubscribe from newsletter
    """
    if not email and not telegram_chat_id:
        raise HTTPException(status_code=400, detail="Email or Telegram chat ID required")
    
    subscriber = None
    
    if email:
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
    elif telegram_chat_id:
        subscriber = db.query(Subscriber).filter(Subscriber.telegram_chat_id == telegram_chat_id).first()
    
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    # Deactivate
    subscriber.is_active = False
    subscriber.email_subscribed = False
    subscriber.telegram_subscribed = False
    db.commit()
    
    return {"message": "Unsubscribed successfully"}


@router.get("/count")
def get_subscriber_count(db: Session = Depends(get_db)):
    """
    Get total subscriber count
    """
    total = db.query(Subscriber).filter(Subscriber.is_active == True).count()
    email_count = db.query(Subscriber).filter(
        Subscriber.is_active == True,
        Subscriber.email_subscribed == True,
        Subscriber.email_verified == True
    ).count()
    telegram_count = db.query(Subscriber).filter(
        Subscriber.is_active == True,
        Subscriber.telegram_subscribed == True
    ).count()
    
    return {
        "total": total,
        "email": email_count,
        "telegram": telegram_count
    }


@router.post("/telegram/register")
def register_telegram(chat_id: str, db: Session = Depends(get_db)):
    """
    Register Telegram subscription (called by bot)
    """
    # Check if chat_id already exists
    existing = db.query(Subscriber).filter(Subscriber.telegram_chat_id == chat_id).first()
    
    if existing:
        existing.telegram_subscribed = True
        existing.is_active = True
        db.commit()
        return {"message": "Telegram subscription activated", "id": existing.id}
    
    # Create new subscriber
    subscriber = Subscriber(
        telegram_chat_id=chat_id,
        telegram_subscribed=True,
        is_active=True
    )
    
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    
    return {"message": "Telegram subscription created", "id": subscriber.id}