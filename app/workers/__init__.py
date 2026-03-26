# Celery workers package
# Define tasks here or import them from submodules

from celery_app import celery

@celery.task
def example_task(arg):
    return f"Task result: {arg}"
