# script_manager/script_manager/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'script_manager.settings')

app = Celery('script_manager')

# Cargar la configuración desde settings.py usando el namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks en todas las apps registradas en INSTALLED_APPS
app.autodiscover_tasks()
