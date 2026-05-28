"""
Sentiment Agent - Analyzes sentiment of news headlines
Uses HuggingFace DistilBERT model
"""

from transformers import pipeline


class SentimentAgent:
    """Analyzes sentiment of text using DistilBERT"""
    
    def __init__(self):
        print("🔄 Loading sentiment model...")
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        print("✅ Sentiment model loaded")
    
    def analyze(self, text):
        """
        Analyze sentiment of a single text
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with sentiment label and score
        """
        try:
            # Truncate text to model's max length
            text = text[:512]
            
            result = self.analyzer(text)[0]
            
            # Map to simple labels
            label = result["label"].lower()  # POSITIVE or NEGATIVE
            score = result["score"]
            
            # Add neutral for low confidence scores
            if score < 0.6:
                label = "neutral"
            
            return {
                "sentiment": label,
                "confidence": round(score, 2)
            }
        
        except Exception as e:
            print(f"⚠️ Sentiment error: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    def analyze_batch(self, texts):
        """
        Analyze sentiment of multiple texts
        
        Args:
            texts: List of texts to analyze
        
        Returns:
            List of sentiment dictionaries
        """
        results = []
        for text in texts:
            results.append(self.analyze(text))
        return results


# Test
if __name__ == "__main__":
    agent = SentimentAgent()
    
    test_texts = [
        "India wins the World Cup! Amazing performance!",
        "Terrible defeat for the team. Very disappointing.",
        "Match scheduled for tomorrow at 2 PM."
    ]
    
    for text in test_texts:
        result = agent.analyze(text)
        print(f"'{text[:40]}...' → {result['sentiment']} ({result['confidence']})")