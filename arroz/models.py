from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# 1. Perfil de Usuario para Roles (RF06, RF07)
class Perfil(models.Model):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('PRODUCTOR', 'Productor'),
        ('TECNICO', 'Técnico'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='TECNICO')
    telefono = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'perfiles'

    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"

# 2. Entidad Finca (RF08)
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

# 3. Entidad Lote (RF09, RF12)
class Lote(models.Model):
    ESTADOS_LOTE = [
        ('ACTIVO', 'Activo'),
        ('PREPARACION', 'En Preparación'),
        ('EN_CICLO', 'En Ciclo'),
        ('COSECHADO', 'Cosechado'),
        ('DESCANSO', 'En Descanso'),
    ]
    TIPOS_SUELO = [
        ('ARCILLOSO', 'Arcilloso'),
        ('FRANCO', 'Franco'),
        ('ARENOSO', 'Arenoso'),
    ]
    SISTEMAS_PRODUCCION = [
        ('RIEGO', 'Riego'),
        ('SECANO', 'Secano'),
    ]
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='lotes')
    nombre = models.CharField(max_length=100)
    area_hectareas = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_suelo = models.CharField(max_length=20, choices=TIPOS_SUELO, default='FRANCO')
    sistema_produccion = models.CharField(max_length=20, choices=SISTEMAS_PRODUCCION, default='RIEGO')
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_LOTE, default='ACTIVO')

    class Meta:
        db_table = 'lotes'

    def __str__(self):
        return f"{self.nombre} - {self.finca.nombre}"

# 4. Entidad Análisis de Suelo (RF14)
class AnalisisSuelo(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='analisis_suelos')
    fecha_muestreo = models.DateField()
    ph = models.DecimalField(max_digits=4, decimal_places=2)
    materia_organica_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    fosforo_ppm = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    potasio_meq = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    textura = models.CharField(max_length=100)
    laboratorio = models.CharField(max_length=150, default='Laboratorio General')
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'analisis_suelos'

    def __str__(self):
        return f"Análisis {self.fecha_muestreo} - {self.lote.nombre}"

# 5. Entidad Ciclo Productivo (RF20, RF21, CU-08)
class CicloProductivo(models.Model):
    ESTADOS_CICLO = [
        ('PLANIFICADO', 'Planificado'),
        ('EJECUCION', 'En Ejecución'),
        ('COSECHADO', 'Cosechado'),
        ('FINALIZADO', 'Finalizado'),
    ]
    SEMESTRES = [
        ('1', 'Primer Semestre (A)'),
        ('2', 'Segundo Semestre (B)'),
    ]
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name='ciclos')
    nombre_ciclo = models.CharField(max_length=100, default='Ciclo sin nombre')
    anio = models.IntegerField(default=2026)
    semestre = models.CharField(max_length=1, choices=SEMESTRES, default='1')
    variedad_arroz = models.CharField(max_length=100)
    presupuesto_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_CICLO, default='PLANIFICADO')
    
    # Cronograma Estimado de Etapas (RF21)
    fecha_preparacion_estimada = models.DateField(null=True, blank=True)
    fecha_siembra_estimada = models.DateField(null=True, blank=True)
    fecha_macollamiento_estimada = models.DateField(null=True, blank=True)
    fecha_panicula_estimada = models.DateField(null=True, blank=True)
    fecha_cosecha_estimada = models.DateField(null=True, blank=True)
    
    # Fechas reales
    fecha_inicio_real = models.DateField(null=True, blank=True)
    fecha_fin_real = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'ciclos_productivos'

    def __str__(self):
        return f"{self.nombre_ciclo} ({self.anio}-{self.semestre})"

    def save(self, *args, **kwargs):
        # Lógica de Validación y Cambio de Estado del Lote (CU-08 / HU-05)
        if not self.pk: # Si es un nuevo ciclo
            # Validar si el lote ya tiene un ciclo activo
            if self.lote.estado in ['PREPARACION', 'EN_CICLO']:
                raise ValidationError(
                    "El lote seleccionado posee un ciclo en ejecución. Debe cerrar el ciclo actual antes de iniciar uno nuevo."
                )
            
            # Cambiar automáticamente el estado del lote a "En Preparación" al planificar el ciclo
            self.lote.estado = 'PREPARACION'
            self.lote.save()
            
        super().save(*args, **kwargs)