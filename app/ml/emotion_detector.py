"""
Emotion Detection module using HuggingFace's DistilRoBERTa model.
Model: j-hartmann/emotion-english-distilroberta-base
Detects: anger, disgust, fear, joy, neutral, sadness, surprise

Falls back to VADER-based heuristics if model weights are not available.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Singleton to avoid reloading the model per request
_emotion_pipeline = None

# Map model labels -> friendly display names
EMOTION_LABEL_MAP = {
    "anger": "Angry",
    "disgust": "Disgusted",
    "fear": "Fearful",
    "joy": "Happy",
    "neutral": "Neutral",
    "sadness": "Disappointed",
    "surprise": "Surprised",
}

# Minimum score threshold to surface an emotion suggestion
CONFIDENCE_THRESHOLD = 0.08


def _get_emotion_pipeline():
    """Lazy singleton loader for the HuggingFace emotion pipeline."""
    global _emotion_pipeline
    if _emotion_pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            logger.info("Loading emotion detection model (j-hartmann/emotion-english-distilroberta-base)...")
            _emotion_pipeline = hf_pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,           # Return all emotion scores
                truncation=True,
                max_length=512,
            )
            logger.info("Emotion model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load emotion model: {e}. Falling back to VADER.")
            _emotion_pipeline = "vader_fallback"
    return _emotion_pipeline


def _vader_fallback(text: str) -> List[Dict]:
    """
    Rule-based fallback using VADER sentiment + simple keyword matching.
    Returns same shape as the transformer output but with lower confidence.
    """
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        return [{"label": "Neutral", "score": 1.0}]

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    text_lower = text.lower()

    results = []

    # Map VADER compound score to emotion candidates
    if compound >= 0.4:
        results.append({"label": "Happy", "score": min(0.9, 0.5 + compound)})
    elif compound >= 0.1:
        results.append({"label": "Neutral", "score": 0.6})
    elif compound <= -0.4:
        results.append({"label": "Angry", "score": min(0.9, 0.5 + abs(compound))})
        results.append({"label": "Disappointed", "score": min(0.7, 0.4 + abs(compound))})
    elif compound <= -0.1:
        results.append({"label": "Disappointed", "score": 0.65})
    else:
        results.append({"label": "Neutral", "score": 0.7})

    # Keyword boosters for specific emotions
    if any(w in text_lower for w in ["fear", "scared", "worried", "anxious", "concern"]):
        results.append({"label": "Fearful", "score": 0.5})
    if any(w in text_lower for w in ["wow", "surprised", "unexpected", "unbelievable", "shocked"]):
        results.append({"label": "Surprised", "score": 0.5})
    if any(w in text_lower for w in ["disgusting", "gross", "horrible", "revolting"]):
        results.append({"label": "Disgusted", "score": 0.55})

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["label"] not in seen:
            seen.add(r["label"])
            unique.append(r)

    return unique if unique else [{"label": "Neutral", "score": 0.5}]


def predict_emotions(text: str, top_k: int = 4) -> List[Dict]:
    """
    Main entry point. Returns up to `top_k` emotions with confidence scores.
    Each item: {"label": "Happy", "score": 0.87}
    
    Emotions with score > CONFIDENCE_THRESHOLD are returned, sorted by score descending.
    """
    if not text or len(text.strip()) < 3:
        return []

    pipeline = _get_emotion_pipeline()

    if pipeline == "vader_fallback":
        raw = _vader_fallback(text)
    else:
        try:
            # HuggingFace pipeline returns list of list when top_k=None
            raw_output = pipeline(text[:512])
            # Flatten: pipeline returns [[{label, score}, ...]]
            flat = raw_output[0] if isinstance(raw_output[0], list) else raw_output

            raw = [
                {
                    "label": EMOTION_LABEL_MAP.get(item["label"].lower(), item["label"].capitalize()),
                    "score": round(item["score"], 4)
                }
                for item in flat
            ]
        except Exception as e:
            logger.error(f"Emotion model inference failed: {e}. Using fallback.")
            raw = _vader_fallback(text)

    # Filter by threshold and sort
    filtered = sorted(
        [r for r in raw if r["score"] >= CONFIDENCE_THRESHOLD],
        key=lambda x: x["score"],
        reverse=True
    )

    # Remove duplicate labels (keep highest)
    seen = set()
    deduped = []
    for r in filtered:
        if r["label"] not in seen:
            seen.add(r["label"])
            deduped.append(r)

    return deduped[:top_k]
