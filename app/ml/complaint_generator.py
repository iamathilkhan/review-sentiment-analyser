from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

# Singleton for the generator
_generator = None

def get_complaint_generator():
    """
    Loads a summarization/generation pipeline to create complaint content from negative reviews.
    Using a small model for speed and efficiency.
    """
    global _generator
    if _generator is None:
        try:
            # DistilBART is great for summarization (generating 'complaint content' from review text)
            print("Loading Complaint Generator AI...")
            _generator = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6", device=-1) # CPU
            print("Complaint Generator loaded.")
        except Exception as e:
            logger.error(f"Failed to load generator: {e}")
            _generator = None
    return _generator

def generate_complaint_text(review_text: str) -> str:
    """
    Generates a formal complaint description from a raw review text.
    """
    gen = get_complaint_generator()
    if not gen:
        return f"Automatic Complaint: Review flagged due to negative sentiment. Content: {review_text[:100]}..."

    try:
        # Generate summary that sounds like a complaint report
        result = gen(review_text, max_length=50, min_length=10, do_sample=False)
        summary = result[0]['summary_text']
        return f"AI Generated Complaint: {summary}"
    except Exception as e:
        logger.warn(f"Generation failed: {e}")
        return f"Automatic Complaint: Negative feedback detected. Review: {review_text[:100]}..."
