import os
import sys
from huggingface_hub import snapshot_download

# Add the project root to sys.path to import from app.ml.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.config import ABSA_MODEL_NAME, MODEL_CACHE_DIR

def download_absa_model():
    """
    Downloads the DeBERTa ABSA model weights to the local cache directory.
    """
    print(f"Downloading model '{ABSA_MODEL_NAME}' to '{MODEL_CACHE_DIR}'...")
    
    # Ensure cache directory exists
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    
    try:
        path = snapshot_download(
            repo_id=ABSA_MODEL_NAME,
            cache_dir=MODEL_CACHE_DIR,
            local_dir=MODEL_CACHE_DIR,
            local_dir_use_symlinks=False
        )
        print(f"Successfully downloaded to: {path}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_absa_model()
