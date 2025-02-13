from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_scripts, name="lista_scripts"),
    path("ejecutar/<str:script_name>/", views.ejecutar_script, name="ejecutar_script"),
    path("programar_auto/<str:script_name>/", views.programar_auto, name="programar_auto"),
    path("desactivar_programacion/<str:script_name>/", views.desactivar_programacion, name="desactivar_programacion"),
    path("ver_programacion/", views.ver_programacion, name="ver_programacion"),
    path("historial/", views.historial_ejecuciones, name="historial_ejecuciones"),
    path("borrar_historial_por_fecha/", views.borrar_historial_por_fecha, name="borrar_historial_por_fecha"),
    path("exportar_historial/", views.exportar_historial, name="exportar_historial"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard_data/", views.dashboard_data, name="dashboard_data"),
]
