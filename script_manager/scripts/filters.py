import django_filters
from .models import ExecutionRecord

class ExecutionRecordFilter(django_filters.FilterSet):
    # Filtrar por nombre del script (contiene)
    script_name = django_filters.CharFilter(field_name='script_name', lookup_expr='icontains', label='Script')
    # Filtrar por rango de fecha de ejecución
    execution_date = django_filters.DateFromToRangeFilter(label="Fecha (desde - hasta)")

    class Meta:
        model = ExecutionRecord
        fields = ['script_name', 'execution_date']
