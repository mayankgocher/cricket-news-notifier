"""
Scheduler - Runs the pipeline daily at 8 AM IST
Uses APScheduler
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime

from src.config.settings import SCHEDULER_HOUR, SCHEDULER_MINUTE, TIMEZONE


def run_daily_pipeline():
    """
    Job function - runs the complete pipeline
    """
    print("\n" + "="*60)
    print(f"⏰ SCHEDULED JOB - {datetime.now()}")
    print("="*60)
    
    try:
        from src.pipeline.graph import run_pipeline
        result = run_pipeline()
        
        news_count = len(result.get("news_items", []))
        print(f"\n✅ Scheduled pipeline completed - {news_count} news items processed")
    
    except Exception as e:
        print(f"\n❌ Scheduled pipeline failed: {e}")


def create_scheduler():
    """
    Create and configure the scheduler
    """
    scheduler = BackgroundScheduler()
    
    # Get timezone
    tz = pytz.timezone(TIMEZONE)
    
    # Add daily job at configured time
    scheduler.add_job(
        run_daily_pipeline,
        trigger=CronTrigger(
            hour=SCHEDULER_HOUR,
            minute=SCHEDULER_MINUTE,
            timezone=tz
        ),
        id="daily_newsletter",
        name="Daily Cricket Newsletter",
        replace_existing=True
    )
    
    return scheduler


def start_scheduler():
    """
    Start the scheduler
    """
    scheduler = create_scheduler()
    scheduler.start()
    
    print("\n" + "="*60)
    print("🕐 SCHEDULER STARTED")
    print("="*60)
    print(f"📅 Job: Daily Cricket Newsletter")
    print(f"⏰ Time: {SCHEDULER_HOUR}:{SCHEDULER_MINUTE:02d} {TIMEZONE}")
    print(f"🔄 Status: Running")
    print("="*60)
    print("\nPress Ctrl+C to stop\n")
    
    return scheduler


# Run standalone
if __name__ == "__main__":
    import time
    
    scheduler = start_scheduler()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        scheduler.shutdown()
        print("✅ Scheduler stopped")