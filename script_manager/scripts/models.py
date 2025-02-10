from django.db import models

class Script(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    ruta = models.CharField(max_length=500)  # Ruta al archivo .sh o .py
    programado = models.BooleanField(default=False)
    horario_ejecucion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Ejecucion(models.Model):
    script = models.ForeignKey(Script, on_delete=models.CASCADE)
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('Ejecutando', 'Ejecutando'),
            ('Completado', 'Completado'),
            ('Fallido', 'Fallido'),
        ],
        default='Ejecutando'
    )
    resultado = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.script.nombre} - {self.fecha_ejecucion}"
from django.db import models

class ExecutionRecord(models.Model):
    script_name = models.CharField(max_length=255)
    execution_date = models.DateTimeField(auto_now_add=True)
    return_code = models.IntegerField()
    output = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.script_name} - {self.execution_date}"