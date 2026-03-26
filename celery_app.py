import os
from celery import Celery
from config import config_by_name

env = os.environ.get('FLASK_ENV', 'development')
config = config_by_name[env]

def make_celery(app_name=__name__):
    return Celery(
        app_name,
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
        include=['app.workers']
    )

celery = make_celery()

# Optional: Configuration updates
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == '__main__':
    celery.start()
