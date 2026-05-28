"""
Run Pipeline - Manual pipeline trigger
Run with: python run_pipeline.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline.graph import run_pipeline


def main():
    """
    Run the complete pipeline manually
    """
    print("\n" + "="*60)
    print("🏏 CRICKET NEWS NOTIFIER - Manual Pipeline Run")
    print("="*60)
    
    try:
        result = run_pipeline()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        print(f"  ✅ News items: {len(result.get('news_items', []))}")
        print(f"  📧 Emails sent: {result.get('email_sent', 0)}")
        print(f"  📱 Telegram sent: {result.get('telegram_sent', 0)}")
        print(f"  💾 Enrichment: {'Complete' if result.get('enrichment_complete') else 'Skipped'}")
        print("="*60)
        
        return result
    
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()