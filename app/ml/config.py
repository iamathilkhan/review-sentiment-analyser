import os

# Aspect categories for detection and mapping
ASPECT_CATEGORIES = [
    "product_quality", 
    "battery_life", 
    "camera", 
    "display", 
    "performance",
    "delivery", 
    "packaging", 
    "customer_service", 
    "price_value", 
    "build_quality"
]

# HuggingFace Pre-trained Model ID
ABSA_MODEL_NAME = "yangheng/deberta-v3-base-absa-v1.1"

# Local cache directory for downloaded weights
# Using absolute path relative to project root is safer for various execution contexts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_CACHE_DIR = os.path.join(BASE_DIR, "models")

# Extraction configuration
CONFIDENCE_THRESHOLD = 0.25
BATCH_SIZE = 8
