import re
import time
import ftfy
from pydantic import BaseModel, Field
from typing import List, Optional
from .absa_model import ABSAModel

class AspectResult(BaseModel):
    aspect_category: str
    polarity: str
    confidence: float
    aspect_term: Optional[str] = None

class ABSAResult(BaseModel):
    aspects: List[AspectResult]
    overall_sentiment: str
    processing_time_ms: int

class ABSAPipeline:
    def __init__(self, model: ABSAModel):
        self._model = model

    def _normalize_text(self, text: str) -> str:
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Fix unicode issues (ftfy)
        text = ftfy.fix_text(text)
        # Lowercase
        text = text.lower().strip()
        return text

    def compute_overall_sentiment(self, aspects: List[AspectResult]) -> str:
        if not aspects:
            return "neutral"
            
        # Weighted majority polarity based on confidence
        scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        for aspect in aspects:
            scores[aspect.polarity] += aspect.confidence
            
        return max(scores, key=scores.get)

    def process_review(self, review_text: str) -> ABSAResult:
        start_time = time.time()
        
        # Normalize
        clean_text = self._normalize_text(review_text)
        
        # Run extraction
        raw_aspects = self._model.extract_aspects(clean_text)
        
        # Convert to Pydantic models
        aspect_results = [AspectResult(**a) for a in raw_aspects]
        
        # Compute overall sentiment
        overall_sentiment = self.compute_overall_sentiment(aspect_results)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return ABSAResult(
            aspects=aspect_results,
            overall_sentiment=overall_sentiment,
            processing_time_ms=processing_time_ms
        )

    def batch_process(self, texts: List[str]) -> List[ABSAResult]:
        # Pre-normalize all
        clean_texts = [self._normalize_text(t) for t in texts]
        
        start_time = time.time()
        # ABSAModel.batch_extract handles the batching logic internally
        all_raw_aspects = self._model.batch_extract(clean_texts)
        
        results = []
        for i, raw_aspects in enumerate(all_raw_aspects):
            aspect_results = [AspectResult(**a) for a in raw_aspects]
            overall_sentiment = self.compute_overall_sentiment(aspect_results)
            
            # Note: overall processing time for batch is divided by count for estimate?
            # Or just use total time per request? Let's just use per-request if possible.
            # But process_review is more granular.
            results.append(ABSAResult(
                aspects=aspect_results,
                overall_sentiment=overall_sentiment,
                processing_time_ms=0 # Batch doesn't track per-item fine-grained perfectly here
            ))
            
        return results
