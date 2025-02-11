# scripts/views.py
import os
import subprocess
import time
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from .models import ExecutionRecord
from django.views.decorators.http import require_POST
from django.contrib import messages
from datetime import datetime
from django.core.paginator import Paginator


def lista_scripts(request):
    """
    Lista los archivos .sh de la carpeta:
    script_manager/script_manager/scripts_files/
    Se utiliza para la página principal.
    """
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    scripts_list = []
    if os.path.exists(scripts_dir):
        for filename in os.listdir(scripts_dir):
            if filename.endswith(".sh"):
                # Conservamos la información de programación para usarla en Programación,
                # pero en la página principal solo mostraremos el nombre y el botón de ejecutar.
                task_name = f"cron_{filename}"
                auto = PeriodicTask.objects.filter(name=task_name).exists()
                scripts_list.append({"nombre": filename, "auto": auto})
    else:
        print("El directorio no existe:", scripts_dir)
    return render(request, "scripts/index.html", {"scripts": scripts_list})

@require_POST
def ejecutar_script(request, script_name):
    """
    Ejecuta el script de forma inmediata y guarda un registro con duración.
    """
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    file_path = os.path.join(scripts_dir, script_name)
    if os.path.exists(file_path):
        try:
            start_time = time.time()
            result = subprocess.run(['bash', file_path], capture_output=True, text=True)
            duration = time.time() - start_time
            mensaje = (
                f"Script '{script_name}' ejecutado (código {result.returncode}) en {duration:.2f} s. "
                f"Salida: {result.stdout.strip()}"
            )
            # Guardar registro de ejecución
            ExecutionRecord.objects.create(
                script_name=script_name,
                return_code=result.returncode,
                output=result.stdout.strip(),
                duration=duration
            )
            return JsonResponse({"mensaje": mensaje})
        except Exception as e:
            return JsonResponse({"mensaje": f"Error al ejecutar el script: {str(e)}"})
    else:
        return JsonResponse({"mensaje": "Script no encontrado."}, status=404)

@require_POST
def programar_auto(request, script_name):
    """
    Programa la ejecución automática del script a una hora específica.
    Se espera recibir un campo 'hora' en formato HH:MM.
    Se crea o actualiza una tarea periódica usando CrontabSchedule.
    """
    hora = request.POST.get("hora")
    if not hora:
        return JsonResponse({"mensaje": "No se proporcionó hora."}, status=400)
    try:
        hour_str, minute_str = hora.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(minute),
            hour=str(hour),
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        task_name = f"cron_{script_name}"
        periodic_task = PeriodicTask.objects.filter(name=task_name).first()
        if periodic_task:
            periodic_task.crontab = schedule
            periodic_task.save()
            mensaje = f"Programación actualizada para {script_name} a las {hora}."
        else:
            periodic_task = PeriodicTask.objects.create(
                crontab=schedule,
                name=task_name,
                task="scripts.tasks.execute_script_task",
                args=json.dumps([script_name]),
                one_off=False,
            )
            mensaje = f"Ejecución automática programada para {script_name} a las {hora}."
        return JsonResponse({"mensaje": mensaje})
    except Exception as e:
        return JsonResponse({"mensaje": f"Error al programar: {str(e)}"}, status=500)

@require_POST
def desactivar_programacion(request, script_name):
    """
    Desactiva la programación automática eliminando la tarea periódica correspondiente.
    """
    task_name = f"cron_{script_name}"
    periodic_task = PeriodicTask.objects.filter(name=task_name).first()
    if periodic_task:
        periodic_task.delete()
        mensaje = f"Programación desactivada para {script_name}."
    else:
        mensaje = f"No hay programación activa para {script_name}."
    return JsonResponse({"mensaje": mensaje})

def ver_programacion(request):
    """
    Muestra la lista de tareas periódicas creadas para los scripts (con nombre que comienzan con 'cron_').
    """
    tasks = PeriodicTask.objects.filter(name__startswith="cron_").order_by("name")
    return render(request, "scripts/programacion.html", {"tasks": tasks})

def historial_ejecuciones(request):
    """
    Muestra el historial de ejecuciones de scripts.
    """
    registros = ExecutionRecord.objects.order_by("-execution_date")
    return render(request, "scripts/historial.html", {"registros": registros})

def borrar_historial(request):
    """
    Borra todos los registros del historial de ejecuciones.
    """
    count, _ = ExecutionRecord.objects.all().delete()
    messages.success(request, f"Se han borrado {count} registros del historial.")
    return redirect('historial_ejecuciones')

@require_POST
def ejecutar_script(request, script_name):
    """
    Ejecuta el script de forma inmediata y guarda un registro con duración.
    """
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    file_path = os.path.join(scripts_dir, script_name)
    if os.path.exists(file_path):
        try:
            start_time = time.time()
            result = subprocess.run(['bash', file_path], capture_output=True, text=True)
            duration = time.time() - start_time
            mensaje = (
                f"Script '{script_name}' ejecutado (código {result.returncode}) en {duration:.2f} s. "
                f"Salida: {result.stdout.strip()}"
            )
            # Guardar registro de ejecución como manual
            ExecutionRecord.objects.create(
                script_name=script_name,
                return_code=result.returncode,
                output=result.stdout.strip(),
                duration=duration,
                tipo="manual"
            )
            return JsonResponse({"mensaje": mensaje})
        except Exception as e:
            return JsonResponse({"mensaje": f"Error al ejecutar el script: {str(e)}"})
    else:
        return JsonResponse({"mensaje": "Script no encontrado."}, status=404)




def historial_ejecuciones(request):
    """
    Muestra el historial de ejecuciones de scripts con paginación.
    """
    registros = ExecutionRecord.objects.order_by("-execution_date")
    paginator = Paginator(registros, 20)  # 20 registros por página (ajusta según necesites)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "scripts/historial.html", {"page_obj": page_obj})

@require_POST
def borrar_historial_por_fecha(request):
    """
    Borra los registros del historial cuyas fechas y horas estén dentro del rango especificado.
    Se esperan 4 campos en POST: 'fecha_inicio', 'hora_inicio', 'fecha_fin' y 'hora_fin' (formato YYYY-MM-DD y HH:MM).
    """
    fecha_inicio = request.POST.get("fecha_inicio")
    hora_inicio = request.POST.get("hora_inicio")
    fecha_fin = request.POST.get("fecha_fin")
    hora_fin = request.POST.get("hora_fin")
    
    if not (fecha_inicio and fecha_fin and hora_inicio and hora_fin):
        return JsonResponse({"mensaje": "Debe proporcionar fecha y hora de inicio y fin."}, status=400)
    
    try:
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        start_time = datetime.strptime(hora_inicio, '%H:%M').time()
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        end_time = datetime.strptime(hora_fin, '%H:%M').time()
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        deleted_count, _ = ExecutionRecord.objects.filter(
            execution_date__gte=start_datetime,
            execution_date__lte=end_datetime
        ).delete()
        return JsonResponse({"mensaje": f"Se han borrado {deleted_count} registros entre {start_datetime} y {end_datetime}."})
    except Exception as e:
        return JsonResponse({"mensaje": f"Error al borrar registros: {str(e)}"}, status=500)
