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
    task_queues={
        'celery': {
            'exchange': 'celery',
            'routing_key': 'celery',
        },
        'dead_letter': {
            'exchange': 'dead_letter',
            'routing_key': 'dead_letter',
        },
    },
    task_routes={
        'workers.review_tasks.process_review_task': {'queue': 'celery'},
    },
)

# Optional: DLQ handling - tasks that fail too many times can be sent here manually
# or via specific queue configuration if using RabbitMQ. For Redis, we manage retries.

if __name__ == '__main__':
    celery.start()
