# scripts/views.py
import os
import subprocess
import time
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from .models import ExecutionRecord
from django.views.decorators.http import require_POST
from django.contrib import messages
from datetime import datetime
from django.core.paginator import Paginator
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import csv
from django.shortcuts import render


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
    Programa la ejecución automática continua del script usando un intervalo en minutos.
    Se espera recibir un campo 'intervalo' en minutos (valor entero). Si no se proporciona, se usará 60.
    """
    intervalo = request.POST.get("intervalo")
    try:
        intervalo = int(intervalo) if intervalo else 60
    except ValueError:
        return JsonResponse({"mensaje": "Intervalo inválido."}, status=400)
    try:
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=intervalo,
            period=IntervalSchedule.MINUTES,
        )
        task_name = f"cron_{script_name}"
        periodic_task = PeriodicTask.objects.filter(name=task_name).first()
        if periodic_task:
            periodic_task.interval = schedule
            periodic_task.save()
            mensaje = f"Programación actualizada para {script_name} con intervalo de {intervalo} minutos."
        else:
            periodic_task = PeriodicTask.objects.create(
                interval=schedule,
                name=task_name,
                task="scripts.tasks.execute_script_task",
                args=json.dumps([script_name]),
                one_off=False,
            )
            mensaje = f"Ejecución automática programada para {script_name} con intervalo de {intervalo} minutos."
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
    # Obtener las tareas programadas existentes
    tasks = PeriodicTask.objects.filter(name__startswith="cron_").order_by("name")
    
    # Definir el directorio donde se encuentran los scripts
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    available_scripts = []
    if os.path.exists(scripts_dir):
        for filename in os.listdir(scripts_dir):
            if filename.endswith(".sh"):
                available_scripts.append(filename)
    else:
        print("El directorio de scripts no existe:", scripts_dir)
    
    context = {
        'tasks': tasks,
        'available_scripts': available_scripts,
    }
    return render(request, "scripts/programacion.html", context)


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

def dashboard(request):
    """
    Renderiza la página del dashboard con indicadores y gráficos.
    """
    total_executions = ExecutionRecord.objects.count()
    manual_count = ExecutionRecord.objects.filter(tipo='manual').count()
    programado_count = ExecutionRecord.objects.filter(tipo='programado').count()
    avg_duration = ExecutionRecord.objects.aggregate(avg=Avg('duration'))['avg'] or 0

    context = {
        'total_executions': total_executions,
        'manual_count': manual_count,
        'programado_count': programado_count,
        'avg_duration': round(avg_duration, 2),
    }
    return render(request, "scripts/dashboard.html", context)

def dashboard_data(request):
    """
    Devuelve datos en formato JSON para el gráfico de ejecuciones diarias de los últimos 7 días.
    """
    now = timezone.now()
    data = []
    for i in range(7):
        day = now - timedelta(days=i)
        count = ExecutionRecord.objects.filter(execution_date__date=day.date()).count()
        data.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count,
        })
    data.reverse()  # Para que las fechas vayan de la más antigua a la más reciente
    return JsonResponse(data, safe=False)

def exportar_historial(request):
    """
    Exporta todo el historial de ejecuciones a un archivo CSV.
    """
    registros = ExecutionRecord.objects.order_by("-execution_date")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="historial_ejecuciones.csv"'
    
    writer = csv.writer(response)
    # Escribir la cabecera
    writer.writerow(['Script', 'Fecha de Ejecución', 'Código', 'Duración (s)', 'Salida', 'Tipo'])
    
    # Escribir cada registro
    for registro in registros:
        writer.writerow([
            registro.script_name,
            registro.execution_date,
            registro.return_code,
            registro.duration,
            registro.output,
            registro.tipo
        ])
    
    return response