# project/celery.py
import os
from celery import Celery

# Встановлюємо змінну середовища
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JASU.settings')  # Замініть 'project_name' на ім'я вашого проекту

app = Celery('JASU')

# Завантажуємо налаштування Celery з settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматично знаходить таски у всіх додатках
app.autodiscover_tasks()
