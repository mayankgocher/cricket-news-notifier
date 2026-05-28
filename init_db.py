"""
Initialize the database - creates all tables
Run this once: python init_db.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base
from backend.models import Subscriber, Newsletter, NewsItem


def init_database():
    """Create all database tables"""
    print("🗄️  Initializing database...")
    
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print(f"📁 Database location: data/cricket_news.db")
    print("\nTables created:")
    print("  - subscribers")
    print("  - newsletters")
    print("  - news_items")


if __name__ == "__main__":
    init_database()