import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

# Use 'production' by default if FLASK_ENV is not set
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == "__main__":
    app.run()
