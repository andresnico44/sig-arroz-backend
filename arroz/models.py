from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User # Usaremos el usuario base de Django por ahora

# 1. Entidad Finca
class Finca(models.Model):
    productor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fincas')
    nombre = models.CharField(max_length=150)
    ubicacion_departamento = models.CharField(max_length=100)
    ubicacion_municipio = models.CharField(max_length=100)
    area_total_ha = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fincas'

    def __str__(self):
        return self.nombre

# 2. Entidad Lote
class Lote(models.Model):
    ESTADOS_LOTE = [
        ('INACTIVO', 'Inactivo'),
        ('PREPARACION', 'En Preparación'),
        ('EJECUCION', 'En Ejecución'),
        ('COSECHADO', 'Cosechado'),
    ]
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='lotes')
    nombre = models.CharField(max_length=100)
    area_hectareas = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_LOTE, default='INACTIVO')

    class Meta:
        db_table = 'lotes'

    def __str__(self):
        return f"{self.nombre} - {self.finca.nombre}"

# 3. Entidad Análisis de Suelo
class AnalisisSuelo(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='analisis_suelos')
    fecha_muestreo = models.DateField()
    ph = models.DecimalField(max_digits=4, decimal_places=2)
    materia_organica_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    textura = models.CharField(max_length=100)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'analisis_suelos'

# 4. Entidad Ciclo Productivo (Eje Central)
class CicloProductivo(models.Model):
    ESTADOS_CICLO = [
        ('PLANIFICADO', 'Planificado'),
        ('EJECUCION', 'En Ejecución'),
        ('COSECHADO', 'Cosechado'),
        ('FINALIZADO', 'Finalizado'),
    ]
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='ciclos')
    variedad_arroz = models.CharField(max_length=100)
    fecha_siembra_estimada = models.DateField()
    fecha_inicio_real = models.DateField(null=True, blank=True)
    presupuesto_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_CICLO, default='PLANIFICADO')

    class Meta:
        db_table = 'ciclos_productivos'