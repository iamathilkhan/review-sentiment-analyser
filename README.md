# Review Sentiment Analyser

A production-ready product review intelligence platform built with Flask, Celery, and TensorFlow.

## Tech Stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL 15
- **Task Queue**: Redis 7, Celery 5
- **Frontend**: Jinja2, TailwindCSS (CDN), Alpine.js
- **ML**: TensorFlow 2.x, HuggingFace Transformers

## Project Structure
```text
/app
  /api           ← Flask Blueprints (auth, reviews, analytics, admin, seller)
  /core          ← config, security, database, extensions
  /models        ← SQLAlchemy ORM models
  /schemas       ← Marshmallow / Pydantic v2 schemas
  /services      ← business logic
  /workers       ← Celery tasks
  /ml            ← ABSA pipeline code
  /templates     ← Jinja2 HTML templates
  /static        ← Assets (CSS, JS, Images)
/scripts         ← Seed scripts, model downloaders
/migrations      ← Alembic migration files
config.py        ← Configuration classes
celery_app.py    ← Celery instance
requirements.txt ← Dependencies
wsgi.py          ← Production entry point
Makefile         ← Task runner
```

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis

### Setup Instructions
1. **Initialize Environment**:
   ```bash
   python -m venv venv
   # Windows:
   venv/Scripts/activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local database and redis credentials
   ```

4. **Initialize Database**:
   ```bash
   make migrate
   make seed
   ```

5. **Run the Application**:
   ```bash
   make dev
   ```

6. **Start Background Worker**:
   ```bash
   make worker
   ```

7. **Monitor Tasks (Flower)**:
   ```bash
   make flower
   ```

## Development Commands
- `make dev`: Start Flask development server
- `make migrate`: Run database migrations
- `make seed`: Populate database with initial data
- `make test`: Run pytest suite
- `make lint`: Run code style checks (flake8, black)
- `make worker`: Start Celery worker
- `make flower`: Start Celery monitoring dashboard
