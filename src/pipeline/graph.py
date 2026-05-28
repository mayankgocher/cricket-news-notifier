"""
Pipeline Graph - Orchestrates the entire news pipeline using LangGraph
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

from src.pipeline.nodes.ingestion_node import ingestion_node
from src.pipeline.nodes.deduplication_node import deduplication_node
from src.pipeline.nodes.sentiment_node import sentiment_node
from src.pipeline.nodes.newsletter_node import newsletter_node
from src.pipeline.nodes.notification_node import notification_node
from src.pipeline.nodes.enrichment_node import enrichment_node


class PipelineState(TypedDict):
    """State that flows through the pipeline"""
    news_items: List[dict]
    newsletter_content: Optional[str]
    executive_summary: Optional[str]
    email_sent: Optional[int]
    telegram_sent: Optional[int]
    enrichment_complete: Optional[bool]


def create_pipeline():
    """
    Create the news pipeline graph
    
    Flow:
    ingestion → deduplication → sentiment → newsletter → notification → enrichment → END
    """
    
    # Create graph
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("ingest", ingestion_node)
    workflow.add_node("deduplicate", deduplication_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("newsletter", newsletter_node)
    workflow.add_node("notify", notification_node)
    workflow.add_node("enrich", enrichment_node)
    
    # Set entry point
    workflow.set_entry_point("ingest")
    
    # Add edges (linear flow)
    workflow.add_edge("ingest", "deduplicate")
    workflow.add_edge("deduplicate", "sentiment")
    workflow.add_edge("sentiment", "newsletter")
    workflow.add_edge("newsletter", "notify")
    workflow.add_edge("notify", "enrich")
    workflow.add_edge("enrich", END)
    
    # Compile
    return workflow.compile()


def run_pipeline():
    """
    Run the complete pipeline
    
    Returns:
        Final pipeline state
    """
    print("\n" + "="*60)
    print("🏏 CRICKET NEWS NOTIFIER - Starting Pipeline")
    print("="*60)
    
    # Create and run pipeline
    pipeline = create_pipeline()
    
    # Initial state
    initial_state = {
        "news_items": [],
        "newsletter_content": None,
        "executive_summary": None,
        "email_sent": None,
        "telegram_sent": None,
        "enrichment_complete": None
    }
    
    # Run pipeline
    result = pipeline.invoke(initial_state)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PIPELINE COMPLETE - Summary")
    print("="*60)
    print(f"  📰 News items processed: {len(result.get('news_items', []))}")
    print(f"  📧 Emails sent: {result.get('email_sent', 0)}")
    print(f"  📱 Telegram sent: {result.get('telegram_sent', 0)}")
    print(f"  💾 Enrichment stored: {result.get('enrichment_complete', False)}")
    print("="*60 + "\n")
    
    return result


# Test
if __name__ == "__main__":
    result = run_pipeline()