from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_scripts, name="lista_scripts"),
    path("ejecutar/<str:script_name>/", views.ejecutar_script, name="ejecutar_script"),
    path("historial/", views.historial_ejecuciones, name="historial_ejecuciones"),
    path("borrar/", views.borrar_registros, name="borrar_registros"),
]
