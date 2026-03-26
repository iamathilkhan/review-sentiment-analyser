import sys
import os
sys.path.append(os.getcwd())
import traceback

print("Trying to import app.api.reviews...")
try:
    from app.api.reviews import reviews_bp
    print("Success")
except ImportError as e:
    print(f"ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"Other Exception: {e}")
    traceback.print_exc()
