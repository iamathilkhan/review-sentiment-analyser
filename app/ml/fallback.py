import re
import time
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .pipeline import ABSAResult, AspectResult
from .config import ASPECT_CATEGORIES

logger = logging.getLogger(__name__)

class FallbackPipeline:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.keywords = {
            "product_quality": ["quality", "premium", "cheap", "good", "bad", "material"],
            "battery_life": ["battery", "charge", "last", "long", "drain", "power"],
            "camera": ["camera", "photo", "lens", "picture", "selfie", "video"],
            "display": ["display", "screen", "amoled", "oled", "brightness", "color"],
            "performance": ["fast", "slow", "lag", "smooth", "gaming", "processor"],
            "delivery": ["delivery", "shipping", "shipped", "arrived", "late", "courier"],
            "packaging": ["packaging", "box", "bubble", "packed", "condition", "damage"],
            "customer_service": ["service", "support", "help", "agent", "return", "refund"],
            "price_value": ["price", "value", "cost", "worth", "money", "expensive", "cheap"],
            "build_quality": ["build", "sturdy", "fragile", "solid", "design", "finish"]
        }
        logger.warning("Using rule-based fallback — install model weights for production")

    def _get_vader_label(self, score: float) -> str:
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"

    def process_review(self, review_text: str) -> ABSAResult:
        start_time = time.time()
        text_lower = review_text.lower()
        
        # Overall sentiment via VADER
        scores = self.analyzer.polarity_scores(review_text)
        overall_sentiment = self._get_vader_label(scores['compound'])
        
        aspects = []
        for category in ASPECT_CATEGORIES:
            # Check for keywords
            found_keywords = [kw for kw in self.keywords.get(category, []) if kw in text_lower]
            
            if found_keywords:
                # Use VADER on sentences containing the keywords for local sentiment?
                # For simplicity, we'll use the overall sentiment for detected aspects too,
                # or just use the compound score. (Prompt says return ABSAResult shape)
                aspects.append(AspectResult(
                    aspect_category=category,
                    polarity=overall_sentiment,
                    confidence=0.5,
                    aspect_term=found_keywords[0] # Use the first found keyword as term
                ))
                
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ABSAResult(
            aspects=aspects,
            overall_sentiment=overall_sentiment,
            processing_time_ms=processing_time_ms
        )

    def batch_process(self, texts: list[str]) -> list[ABSAResult]:
        return [self.process_review(t) for t in texts]
