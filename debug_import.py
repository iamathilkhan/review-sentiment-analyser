import sys
import os
sys.path.append(os.getcwd())
try:
    from app import create_app
    print("Success: app.create_app imported")
    app = create_app('development')
    print("Success: app created")
except Exception as e:
    import traceback
    traceback.print_exc()
