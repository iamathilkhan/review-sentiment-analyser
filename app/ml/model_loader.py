import logging
from .absa_model import ABSAModel
from .pipeline import ABSAPipeline

# Singleton instance
_pipeline = None

logger = logging.getLogger(__name__)

def get_pipeline() -> ABSAPipeline:
    """
    Singleton loader for the ABSA Pipeline.
    Loads model once and performs warm-up inference.
    """
    global _pipeline
    
    if _pipeline is None:
        try:
            print("Initializing ABSA Pipeline (this may take a while if downloading weights)...")
            model = ABSAModel()
            _pipeline = ABSAPipeline(model)
            
            # Warm-up inference
            print("Performing warm-up inference...")
            warmup_text = "Great product with amazing battery life"
            _pipeline.process_review(warmup_text)
            print("ABSA Pipeline loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load ABSA Pipeline: {e}")
            # We return None so the caller can decide to use fallback.py
            _pipeline = None
            raise e
            
    return _pipeline

def is_pipeline_available() -> bool:
    """Check if the pipeline has been successfully initialized."""
    return _pipeline is not None
