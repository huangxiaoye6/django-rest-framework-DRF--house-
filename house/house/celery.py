import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "house.settings")

app = Celery('proj')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
# 项目路径下启动worker:   celery -A house worker -l info -P eventlet
