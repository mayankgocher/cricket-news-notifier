"""
Cleanup SQLite - Remove old newsletters from database
Run manually: python scripts/cleanup_sqlite.py --days 30
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import Newsletter, NewsItem


def cleanup_sqlite(days_to_keep=30):
    """
    Delete newsletters older than specified days
    
    Args:
        days_to_keep: Keep data from last N days
    """
    print("\n" + "="*50)
    print("🗑️  SQLite Cleanup")
    print("="*50)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    print(f"📅 Deleting data older than: {cutoff_date.strftime('%Y-%m-%d')}")
    
    db = SessionLocal()
    
    try:
        # Count before deletion
        newsletter_count_before = db.query(Newsletter).count()
        newsitem_count_before = db.query(NewsItem).count()
        
        # Delete old newsletters
        deleted_newsletters = db.query(Newsletter).filter(
            Newsletter.sent_at < cutoff_date
        ).delete()
        
        # Delete old news items
        deleted_items = db.query(NewsItem).filter(
            NewsItem.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        # Count after deletion
        newsletter_count_after = db.query(Newsletter).count()
        newsitem_count_after = db.query(NewsItem).count()
        
        print(f"\n✅ Cleanup complete!")
        print(f"   Newsletters: {newsletter_count_before} → {newsletter_count_after} (deleted {deleted_newsletters})")
        print(f"   News items: {newsitem_count_before} → {newsitem_count_after} (deleted {deleted_items})")
    
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        db.rollback()
    
    finally:
        db.close()
    
    print("="*50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup old SQLite data")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Keep data from last N days (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Confirmation
    confirm = input(f"Delete data older than {args.days} days? (yes/no): ")
    
    if confirm.lower() == "yes":
        cleanup_sqlite(args.days)
    else:
        print("Cleanup cancelled")