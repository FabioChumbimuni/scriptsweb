# scripts/tasks.py
import os
import subprocess
import time
from celery import shared_task
from django.conf import settings
from .models import ExecutionRecord

@shared_task
def execute_script_task(script_name):
    """
    Tarea que ejecuta el script, mide su tiempo y guarda un registro con tipo 'programado'.
    """
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    file_path = os.path.join(scripts_dir, script_name)
    
    if os.path.exists(file_path):
        start_time = time.time()
        result = subprocess.run(['bash', file_path], capture_output=True, text=True)
        duration = time.time() - start_time
        # Guardar el registro como programado
        ExecutionRecord.objects.create(
            script_name=script_name,
            return_code=result.returncode,
            output=result.stdout.strip(),
            duration=duration,
            tipo="programado"
        )
        return f"Script '{script_name}' ejecutado en {duration:.2f} s, código {result.returncode}."
    else:
        return f"Script '{script_name}' no encontrado."
