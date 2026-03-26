import logging
from .absa_model import ABSAModel
from .pipeline import ABSAPipeline

# Singleton instance
_pipeline = None

logger = logging.getLogger(__name__)

def get_pipeline() -> ABSAPipeline:
    """
    Singleton loader for the ABSA Pipeline.
    Loads model once; falls back to rule-based logic if dependencies/weights missing.
    """
    global _pipeline
    
    if _pipeline is None:
        try:
            from .absa_model import ABSAModel
            print("Initializing AI Engine (this may take a while)...")
            model = ABSAModel()
            _pipeline = ABSAPipeline(model)
            print("AI Engine loaded successfully.")
        except (Exception, ImportError):
            print("ML weights or dependencies (TensorFlow/Transformers) not found. Falling back to rule-based engine.")
            from .fallback import FallbackPipeline
            # Wrap FallbackPipeline to maintain same interface as ABSAPipeline if needed
            # but FallbackPipeline in the codebase already has process_review
            _pipeline = FallbackPipeline()
            
    return _pipeline

def is_pipeline_available() -> bool:
    """Check if the pipeline has been successfully initialized."""
    return _pipeline is not None
