import os
import subprocess
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import ExecutionRecord
from .filters import ExecutionRecordFilter

def lista_scripts(request):
    """
    Lista los archivos .sh de la carpeta:
    script_manager/script_manager/scripts_files
    """
    # Ajusta la ruta según tu estructura
    scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
    scripts_list = []
    if os.path.exists(scripts_dir):
        for filename in os.listdir(scripts_dir):
            if filename.endswith(".sh"):
                scripts_list.append({"nombre": filename})
    else:
        print("El directorio no existe:", scripts_dir)
    return render(request, "scripts/index.html", {"scripts": scripts_list})

def ejecutar_script(request, script_name):
    if request.method == "POST":
        scripts_dir = os.path.join(settings.BASE_DIR, "script_manager", "scripts_files")
        file_path = os.path.join(scripts_dir, script_name)
        if os.path.exists(file_path):
            try:
                result = subprocess.run(['bash', file_path], capture_output=True, text=True)
                mensaje = (
                    f"Script '{script_name}' ejecutado (código {result.returncode}). "
                    f"Salida: {result.stdout.strip()}"
                )
                # Guardar el registro de ejecución
                ExecutionRecord.objects.create(
                    script_name=script_name,
                    return_code=result.returncode,
                    output=result.stdout.strip()
                )
                return JsonResponse({"mensaje": mensaje})
            except Exception as e:
                return JsonResponse({"mensaje": f"Error al ejecutar el script: {str(e)}"})
        else:
            return JsonResponse({"mensaje": "Script no encontrado."}, status=404)
    else:
        return JsonResponse({"mensaje": "Método no permitido."}, status=405)

def historial_ejecuciones(request):
    """
    Muestra el historial de ejecuciones con filtro y paginación.
    """
    queryset = ExecutionRecord.objects.order_by("-execution_date")
    # Aplicar el filtro usando django-filter
    record_filter = ExecutionRecordFilter(request.GET, queryset=queryset)
    filtered_qs = record_filter.qs

    # Paginación (por ejemplo, 20 registros por página)
    paginator = Paginator(filtered_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': record_filter,
        'page_obj': page_obj,
    }
    return render(request, "scripts/historial.html", context)

@require_POST
def borrar_registros(request):
    """
    Borra registros anteriores a una fecha dada (YYYY-MM-DD) recibida vía POST.
    """
    date_limit = request.POST.get('date_limit')
    if date_limit:
        try:
            date_limit_parsed = datetime.datetime.strptime(date_limit, '%Y-%m-%d').date()
            # Borrar registros cuyo execution_date sea anterior a la fecha límite
            deleted_count, _ = ExecutionRecord.objects.filter(execution_date__lt=date_limit_parsed).delete()
            messages.success(request, f"Se borraron {deleted_count} registros anteriores a {date_limit}.")
        except Exception as e:
            messages.error(request, f"Error al borrar registros: {str(e)}")
    else:
        messages.error(request, "Debe proporcionar una fecha.")
    return redirect('historial_ejecuciones')
