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
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"detail": "El lote seleccionado ya posee un ciclo en ejecución. Debe cerrar el ciclo actual antes de iniciar uno nuevo."})
            
            # Cambiar automáticamente el estado del lote a "En Preparación" al planificar el ciclo
            self.lote.estado = 'PREPARACION'
            self.lote.save()
            
        super().save(*args, **kwargs)

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

# 6. Entidad Preparación y Uso de Maquinaria (HU-06)
class PreparacionMaquinaria(models.Model):
    LABORES = [
        ('RASTRA', 'Pase de Rastra'),
        ('PULIDOR', 'Pase de Pulidor'),
        ('CABALLONEO', 'Caballoneo'),
        ('NIVELACION', 'Nivelación (Laser/Taipa)'),
        ('ZANJEO', 'Zanjeo/Drenajes'),
        ('OTRO', 'Otro'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='preparaciones')
    fecha = models.DateField()
    labor = models.CharField(max_length=20, choices=LABORES)
    horas_maquina = models.DecimalField(max_digits=5, decimal_places=2, help_text="Horas de uso del tractor")
    combustible_galones = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    costo_hora = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'preparacion_maquinaria'

    def __str__(self):
        return f"{self.get_labor_display()} - {self.ciclo.nombre_ciclo} ({self.fecha})"

    def save(self, *args, **kwargs):
        self.costo_total = self.horas_maquina * self.costo_hora
        super().save(*args, **kwargs)
        
        # Inyectar/Actualizar en RegistroCosto
        from .models import RegistroCosto
        desc = f"Labores mecánicas de {self.get_labor_display()} (Fecha: {self.fecha})"
        costo_obj, created = RegistroCosto.objects.get_or_create(
            ciclo=self.ciclo,
            categoria='MAQUINARIA',
            descripcion=desc,
            defaults={'fecha': self.fecha, 'monto_total': self.costo_total}
        )
        if not created:
            costo_obj.monto_total = self.costo_total
            costo_obj.fecha = self.fecha
            costo_obj.save()

    def delete(self, *args, **kwargs):
        from .models import RegistroCosto
        desc = f"Labores mecánicas de {self.get_labor_display()} (Fecha: {self.fecha})"
        RegistroCosto.objects.filter(ciclo=self.ciclo, categoria='MAQUINARIA', descripcion=desc).delete()
        super().delete(*args, **kwargs)


# 7. Entidad Siembra (HU-07)
class Siembra(models.Model):
    METODOS = [
        ('VOLEO', 'Al Voleo'),
        ('MECANIZADA', 'Sembradora Mecanizada'),
        ('TRANSPLANTE', 'Transplante'),
    ]
    ciclo = models.OneToOneField(CicloProductivo, on_delete=models.CASCADE, related_name='siembra')
    fecha = models.DateField()
    metodo = models.CharField(max_length=20, choices=METODOS, default='VOLEO')
    variedad = models.CharField(max_length=100)
    dosis_kg_ha = models.DecimalField(max_digits=5, decimal_places=2, help_text="Kilogramos de semilla por Hectárea")
    tratamiento_semilla = models.CharField(max_length=150, null=True, blank=True, help_text="Fungicidas o insecticidas aplicados a la semilla")
    germinacion_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'siembra'

    def __str__(self):
        return f"Siembra {self.variedad} - {self.ciclo.nombre_ciclo}"

    def save(self, *args, **kwargs):
        # Lógica de Cambio Automático de Estados (HU-07)
        # Al sembrar, el ciclo entra en EJECUCION y el lote EN_CICLO
        if not self.pk: # Solo en la creación
            self.ciclo.estado = 'EJECUCION'
            if not self.ciclo.fecha_inicio_real:
                self.ciclo.fecha_inicio_real = self.fecha
            self.ciclo.save()
            
            self.ciclo.lote.estado = 'EN_CICLO'
            self.ciclo.lote.save()
            
        super().save(*args, **kwargs)


# 8. Entidad Seguimiento Fenológico (HU-08)
class SeguimientoFenologico(models.Model):
    FASES = [
        ('GERMINACION', 'Germinación / Emergencia'),
        ('PLANTULA', 'Plántula'),
        ('MACOLLAMIENTO', 'Macollamiento (Inicio/Máximo)'),
        ('PRIMORDIO', 'Diferenciación de Primordio Floral'),
        ('EMBUCHAMIENTO', 'Embuchamiento'),
        ('FLORACION', 'Floración (Antesis)'),
        ('GRANO_LECHOSO', 'Grano Lechoso'),
        ('GRANO_PASTOSO', 'Grano Pastoso'),
        ('MADUREZ_COSECHA', 'Madurez de Cosecha'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='seguimientos_fenologicos')
    fecha = models.DateField()
    fase = models.CharField(max_length=30, choices=FASES)
    dias_transcurridos_calculados = models.IntegerField(null=True, blank=True, help_text="Días transcurridos desde la siembra (auto calculado)")
    observaciones = models.TextField(null=True, blank=True)
    fotografia = models.ImageField(upload_to='fenologia/', null=True, blank=True)

    class Meta:
        db_table = 'seguimiento_fenologico'

    def __str__(self):
        return f"{self.get_fase_display()} - {self.ciclo.nombre_ciclo}"

    def save(self, *args, **kwargs):
        # Calcular automáticamente los días transcurridos si hay una siembra registrada
        if hasattr(self.ciclo, 'siembra') and self.ciclo.siembra:
            delta = self.fecha - self.ciclo.siembra.fecha
            self.dias_transcurridos_calculados = delta.days
            
        super().save(*args, **kwargs)


# =========================================================================
# SPRINT 3: GESTIÓN DE SANIDAD, NUTRICIÓN, MANEJO HÍDRICO Y BILLETERA
# =========================================================================

# 9. Entidad Billetera Central de Costos (HU-22)
class RegistroCosto(models.Model):
    CATEGORIAS = [
        ('MANO_DE_OBRA', 'Mano de Obra'),
        ('INSUMOS_AGROQUIMICOS', 'Insumos Agroquímicos'),
        ('MAQUINARIA', 'Maquinaria'),
        ('ARRENDAMIENTO_TIERRA', 'Arrendamiento de Tierra'),
        ('TRANSPORTE', 'Transporte'),
        ('OTROS', 'Otros'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='costos')
    fecha = models.DateField()
    categoria = models.CharField(max_length=30, choices=CATEGORIAS)
    descripcion = models.TextField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'registro_costo'

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.descripcion} ({self.monto_total})"


# 10. Entidad Monitoreo Fitosanitario (HU-15)
class MonitoreoFitosanitario(models.Model):
    TIPOS = [
        ('PLAGA', 'Plaga'),
        ('ENFERMEDAD', 'Enfermedad'),
        ('MALEZA', 'Maleza'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='monitoreos')
    fecha = models.DateField()
    tipo_problema = models.CharField(max_length=20, choices=TIPOS)
    nombre_comun = models.CharField(max_length=150) # Ej: Sogata, Pyricularia
    umbral_danio_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de umbral de daño observado")
    decision_tecnica = models.TextField()
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'monitoreo_fitosanitario'

    def __str__(self):
        return f"{self.get_tipo_problema_display()}: {self.nombre_comun} ({self.fecha})"


# 11. Entidad Fertilización (HU-16)
class Fertilizacion(models.Model):
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='fertilizaciones')
    fecha = models.DateField()
    etapa_fenologica = models.CharField(max_length=50) # Ej: Macollamiento
    tipo_fertilizante = models.CharField(max_length=100) # Ej: NPK 15-15-15
    fuente_comercial = models.CharField(max_length=100) # Ej: Urea, DAP, KCl
    dosis_kg_ha = models.DecimalField(max_digits=7, decimal_places=2)
    costo_producto = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    costo_mano_obra = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'fertilizacion'

    def __str__(self):
        return f"Fertilización {self.tipo_fertilizante} - {self.fuente_comercial} ({self.fecha})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .models import RegistroCosto
        desc = f"Fertilización {self.tipo_fertilizante} - {self.fuente_comercial} ({self.dosis_kg_ha} kg/ha)"
        monto = self.costo_producto + self.costo_mano_obra
        costo_obj, created = RegistroCosto.objects.get_or_create(
            ciclo=self.ciclo,
            categoria='INSUMOS_AGROQUIMICOS',
            descripcion=desc,
            defaults={'fecha': self.fecha, 'monto_total': monto}
        )
        if not created:
            costo_obj.monto_total = monto
            costo_obj.fecha = self.fecha
            costo_obj.save()

    def delete(self, *args, **kwargs):
        from .models import RegistroCosto
        desc = f"Fertilización {self.tipo_fertilizante} - {self.fuente_comercial} ({self.dosis_kg_ha} kg/ha)"
        RegistroCosto.objects.filter(ciclo=self.ciclo, categoria='INSUMOS_AGROQUIMICOS', descripcion=desc).delete()
        super().delete(*args, **kwargs)


# 12. Entidad Aplicación de Agroquímicos (HU-17)
class AplicacionAgroquimico(models.Model):
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='aplicaciones_agroquimicos')
    monitoreo = models.ForeignKey(MonitoreoFitosanitario, on_delete=models.SET_NULL, null=True, blank=True, related_name='aplicaciones')
    fecha = models.DateField()
    nombre_comercial = models.CharField(max_length=150)
    ingrediente_activo = models.CharField(max_length=150)
    dosis_por_ha = models.DecimalField(max_digits=7, decimal_places=2)
    equipo_aspersion = models.CharField(max_length=100) # Ej: Bomba espalda, Dron, Tractor
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    velocidad_viento_kmh = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    periodo_carencia_dias = models.IntegerField(help_text="Días de retiro antes de cosechar")
    costo_producto = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    costo_mano_obra = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'aplicacion_agroquimico'

    def __str__(self):
        return f"Aplicación {self.nombre_comercial} ({self.fecha})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .models import RegistroCosto
        desc = f"Aplicación Agroquímico {self.nombre_comercial} ({self.ingrediente_activo})"
        monto = self.costo_producto + self.costo_mano_obra
        costo_obj, created = RegistroCosto.objects.get_or_create(
            ciclo=self.ciclo,
            categoria='INSUMOS_AGROQUIMICOS',
            descripcion=desc,
            defaults={'fecha': self.fecha, 'monto_total': monto}
        )
        if not created:
            costo_obj.monto_total = monto
            costo_obj.fecha = self.fecha
            costo_obj.save()

    def delete(self, *args, **kwargs):
        from .models import RegistroCosto
        desc = f"Aplicación Agroquímico {self.nombre_comercial} ({self.ingrediente_activo})"
        RegistroCosto.objects.filter(ciclo=self.ciclo, categoria='INSUMOS_AGROQUIMICOS', descripcion=desc).delete()
        super().delete(*args, **kwargs)


# 13. Entidad Manejo Hídrico y Control de Riego (HU-18)
class RegistroHidrico(models.Model):
    FUENTES = [
        ('CANAL', 'Canal de Riego'),
        ('RIO', 'Río'),
        ('POZO', 'Pozo Profundo'),
    ]
    DRENAJES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='riegos')
    fecha = models.DateField()
    volumen_agua_m3 = models.DecimalField(max_digits=10, decimal_places=2)
    fuente_hidrica = models.CharField(max_length=20, choices=FUENTES)
    costo_bombeo = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    dias_inundacion = models.IntegerField()
    lamina_agua_cm = models.DecimalField(max_digits=5, decimal_places=2)
    estado_drenaje = models.CharField(max_length=20, choices=DRENAJES)

    class Meta:
        db_table = 'registro_hidrico'

    def __str__(self):
        return f"Riego {self.fuente_hidrica} - L: {self.lamina_agua_cm}cm ({self.fecha})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .models import RegistroCosto
        desc = f"Manejo Hídrico / Riego desde {self.get_fuente_hidrica_display()}"
        costo_obj, created = RegistroCosto.objects.get_or_create(
            ciclo=self.ciclo,
            categoria='OTROS',
            descripcion=desc,
            defaults={'fecha': self.fecha, 'monto_total': self.costo_bombeo}
        )
        if not created:
            costo_obj.monto_total = self.costo_bombeo
            costo_obj.fecha = self.fecha
            costo_obj.save()

    def delete(self, *args, **kwargs):
        from .models import RegistroCosto
        desc = f"Manejo Hídrico / Riego desde {self.get_fuente_hidrica_display()}"
        RegistroCosto.objects.filter(ciclo=self.ciclo, categoria='OTROS', descripcion=desc).delete()
        super().delete(*args, **kwargs)