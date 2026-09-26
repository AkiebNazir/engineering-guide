from celery import Celery
from celery.signals import task_postrun
from prometheus_client import Counter, start_http_server

app = Celery('tasks', broker='redis://localhost:6379/0')

TASK_COUNTER = Counter('celery_task_status_total', 'Total task count', ['task_name', 'state'])

@task_postrun.connect
def on_task_postrun(task_id, task, args, kwargs, retval, state, **kw):
    TASK_COUNTER.labels(task_name=task.name, state=state).inc()

@app.task
def divide(x, y):
    return x / y

if __name__ == '__main__':
    start_http_server(9090)
    app.worker_main(['worker', '--loglevel=info'])
