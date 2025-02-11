# script_manager/script_manager/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'script_manager.settings')

app = Celery('script_manager')

# Usa una cadena aquí para que el worker no tenga problemas al serializar
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
