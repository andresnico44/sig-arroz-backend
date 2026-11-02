from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# 1. Perfil de Usuario para Roles (RF06, RF07)
class Perfil(models.Model):
    """Perfil de extensión de usuario para control de acceso basado en roles (RBAC).

    Extiende el modelo estándar de autenticación de Django (User) asociando un rol
    operativo específico dentro del sistema arrocero (ADMIN, PRODUCTOR o TECNICO)
    y canales de contacto directo.

    Attributes:
        user (OneToOneField): Referencia uno a uno con el usuario del sistema Django.
        rol (CharField): Rol funcional que define permisos ('ADMIN', 'PRODUCTOR', 'TECNICO').
        telefono (CharField): Número de teléfono de contacto móvil o fijo.
    """
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
        """Retorna la representación legible del perfil con su usuario y rol."""
        return f"{self.user.username} - {self.get_rol_display()}"

# 2. Entidad Finca (RF08)
class Finca(models.Model):
    """Unidad productiva agropecuaria principal donde se desarrollan los cultivos.

    Representa la propiedad rural o predio arrocero perteneciente a un productor.
    Actúa como nodo raíz geográfico y administrativo que agrupa uno o varios lotes
    de cultivo.

    Attributes:
        productor (ForeignKey): Usuario con rol PRODUCTOR propietario o titular del predio.
        nombre (CharField): Nombre o denominación comercial de la finca (ej. La Esmeralda).
        ubicacion_departamento (CharField): Departamento de ubicación geográfica.
        ubicacion_municipio (CharField): Municipio o jurisdicción local del predio.
        area_total_ha (DecimalField): Extensión superficial total en hectáreas (ha).
    """
    productor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fincas')
    nombre = models.CharField(max_length=150)
    ubicacion_departamento = models.CharField(max_length=100)
    ubicacion_municipio = models.CharField(max_length=100)
    area_total_ha = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fincas'

    def __str__(self):
        """Retorna el nombre comercial asignado a la finca."""
        return self.nombre

# 3. Entidad Lote (RF09, RF12)
class Lote(models.Model):
    """Subdivisión territorial o parcela operativa dentro de una finca arrocera.

    Constituye la unidad mínima de manejo agronómico e hídrico donde se planifican
    y ejecutan los ciclos productivos de arroz de manera homogénea.

    Attributes:
        finca (ForeignKey): Finca madre a la que pertenece la parcela.
        nombre (CharField): Identificador o código del lote (ej. Lote A1).
        area_hectareas (DecimalField): Área neta cultivable en hectáreas.
        tipo_suelo (CharField): Clasificación edafológica ('ARCILLOSO', 'FRANCO', 'ARENOSO').
        sistema_produccion (CharField): Modalidad hídrica ('RIEGO' o 'SECANO').
        latitud (DecimalField): Coordenada geográfica de latitud en grados decimales.
        longitud (DecimalField): Coordenada geográfica de longitud en grados decimales.
        estado (CharField): Estado operativo actual ('ACTIVO', 'PREPARACION', 'EN_CICLO',
            'COSECHADO', 'DESCANSO').
    """
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
        """Retorna el nombre del lote junto al nombre de su finca contenedora."""
        return f"{self.nombre} - {self.finca.nombre}"

# 4. Entidad Análisis de Suelo (RF14)
class AnalisisSuelo(models.Model):
    """Registro de caracterización física y química edafológica de un lote.

    Contiene los parámetros analíticos de laboratorio requeridos para formular planes
    de fertilización y enmiendas calizas previas al establecimiento del cultivo de arroz.

    Attributes:
        lote (ForeignKey): Lote evaluado en el muestreo de suelo.
        fecha_muestreo (DateField): Fecha en que se recolectaron las submuestras en campo.
        ph (DecimalField): Potencial de hidrógeno del suelo (rango analítico 0 a 14).
        materia_organica_porcentaje (DecimalField): Contenido de materia orgánica (%).
        fosforo_ppm (DecimalField): Concentración de fósforo asimilable en partes por millón (ppm).
        potasio_meq (DecimalField): Potasio intercambiable en meq/100g de suelo.
        textura (CharField): Clase textural determinada en laboratorio (ej. Franco Arcilloso).
        laboratorio (CharField): Razón social del laboratorio que emitió el informe.
        observaciones (TextField): Comentarios técnicos o recomendaciones del agrólogo.
    """
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
        """Retorna la fecha de muestreo y el lote correspondiente."""
        return f"Análisis {self.fecha_muestreo} - {self.lote.nombre}"

# 5. Entidad Ciclo Productivo (RF20, RF21, CU-08)
class CicloProductivo(models.Model):
    """Ciclo agronómico estacional y financiero del cultivo de arroz en un lote.

    Controla el ciclo de vida completo del cultivo en una campaña agrícola, desde su
    planificación temporal y presupuestal, pasando por la ejecución operativa de labores,
    hasta el corte de cosecha y la liquidación comercial con el molino.

    Attributes:
        lote (ForeignKey): Lote asignado donde se efectúa la campaña arrocera.
        nombre_ciclo (CharField): Nombre descriptivo del ciclo (ej. Ciclo Arroz 2026-A).
        anio (IntegerField): Año calendario correspondiente a la campaña agrícola.
        semestre (CharField): Semestre agronómico ('1' para A, '2' para B).
        variedad_arroz (CharField): Variedad botánica sembrada (ej. FEDEARROZ 67).
        presupuesto_estimado (DecimalField): Techo presupuestal estimado en pesos COP.
        estado (CharField): Estado del ciclo ('PLANIFICADO', 'EJECUCION', 'COSECHADO', 'FINALIZADO').
        fecha_preparacion_estimada (DateField): Fecha estimada de labores mecánicas.
        fecha_siembra_estimada (DateField): Fecha estimada de siembra.
        fecha_macollamiento_estimada (DateField): Fecha estimada de macollamiento.
        fecha_panicula_estimada (DateField): Fecha estimada de emisión de panícula.
        fecha_cosecha_estimada (DateField): Fecha estimada de recolección en campo.
        fecha_inicio_real (DateField): Fecha real de inicio (asignada al sembrar).
        fecha_fin_real (DateField): Fecha real de término (asignada al cosechar).
    """
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
        """Retorna la denominación del ciclo, año y semestre agronómico."""
        return f"{self.nombre_ciclo} ({self.anio}-{self.semestre})"

    def clean(self):
        """Valida que el lote seleccionado no tenga un ciclo actualmente activo.

        Raises:
            ValidationError: Si el lote se encuentra en estado 'PREPARACION' o 'EN_CICLO'.
        """
        super().clean()
        if not self.pk: # Si es un nuevo ciclo
            # Validar si el lote ya tiene un ciclo activo
            if self.lote.estado in ['PREPARACION', 'EN_CICLO']:
                raise ValidationError("El lote seleccionado ya posee un ciclo en ejecución. Debe cerrar el ciclo actual antes de iniciar uno nuevo.")

    def save(self, *args, **kwargs):
        """Persiste el ciclo productivo y transiciona el lote a 'PREPARACION' al planificar.

        Garantiza consistencia transaccional atómica al crear un ciclo nuevo.
        """
        # Lógica de Validación y Cambio de Estado del Lote (CU-08 / HU-05)
        with transaction.atomic():
            if not self.pk: # Si es un nuevo ciclo
                # Cambiar automáticamente el estado del lote a "En Preparación" al planificar el ciclo
                self.lote.estado = 'PREPARACION'
                self.lote.save()
                
            super().save(*args, **kwargs)

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

# 6. Entidad Preparación y Uso de Maquinaria (HU-06)
class PreparacionMaquinaria(models.Model):
    """Registro de labores mecánicas de adecuación de suelos y uso de maquinaria agrícola.

    Controla el trabajo de tractores e implementos (rastra, pulidor, caballoneo, nivelación,
    zanjeo), calculando el costo total derivado de horas máquina y sincronizándolo en la
    billetera de costos del ciclo.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo beneficiario de las labores mecanizadas.
        fecha (DateField): Fecha en que se ejecutó la labor en lote.
        labor (CharField): Tipo de pase de maquinaria ('RASTRA', 'PULIDOR', 'CABALLONEO',
            'NIVELACION', 'ZANJEO', 'OTRO').
        condicion_humedad (CharField): Estado de humedad edáfica ('SECO', 'CAPACIDAD_CAMPO', 'SATURADO').
        horas_maquina (DecimalField): Tiempo de trabajo del tractor en horas.
        combustible_galones (DecimalField): Galones de combustible consumidos durante la labor.
        costo_hora (DecimalField): Tarifa unitaria por hora de tractor en pesos COP.
        costo_total (DecimalField): Monto económico total (horas_maquina * costo_hora).
        observaciones (TextField): Notas del operario sobre implementos o condiciones del terreno.
    """
    LABORES = [
        ('RASTRA', 'Pase de Rastra'),
        ('PULIDOR', 'Pase de Pulidor'),
        ('CABALLONEO', 'Caballoneo'),
        ('NIVELACION', 'Nivelación (Laser/Taipa)'),
        ('ZANJEO', 'Zanjeo/Drenajes'),
        ('OTRO', 'Otro'),
    ]
    CONDICIONES_HUMEDAD = [
        ('SECO', 'Suelo Seco'),
        ('CAPACIDAD_CAMPO', 'Capacidad de Campo (Ideal)'),
        ('SATURADO', 'Saturado / Lodo'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='preparaciones')
    fecha = models.DateField()
    labor = models.CharField(max_length=20, choices=LABORES)
    condicion_humedad = models.CharField(max_length=20, choices=CONDICIONES_HUMEDAD, default='CAPACIDAD_CAMPO')
    horas_maquina = models.DecimalField(max_digits=5, decimal_places=2, help_text="Horas de uso del tractor")
    combustible_galones = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    costo_hora = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'preparacion_maquinaria'

    def __str__(self):
        """Retorna la labor mecánica, nombre del ciclo y fecha de ejecución."""
        return f"{self.get_labor_display()} - {self.ciclo.nombre_ciclo} ({self.fecha})"

    def save(self, *args, **kwargs):
        """Calcula el costo total e inyecta atómicamente el gasto en RegistroCosto.

        Actualiza costo_total multiplicando horas_maquina por costo_hora y sincroniza
        el registro contable bajo la categoría 'MAQUINARIA'.
        """
        self.costo_total = self.horas_maquina * self.costo_hora
        with transaction.atomic():
            super().save(*args, **kwargs)
            
            # Inyectar/Actualizar en RegistroCosto
            from .models import RegistroCosto
            desc = f"Labores mecánicas de {self.get_labor_display()} (Fecha: {self.fecha})"
            costo_obj, created = RegistroCosto.objects.get_or_create(
                preparacion=self,
                defaults={
                    'ciclo': self.ciclo,
                    'categoria': 'MAQUINARIA',
                    'descripcion': desc,
                    'fecha': self.fecha,
                    'monto_total': self.costo_total
                }
            )
            if not created:
                costo_obj.descripcion = desc
                costo_obj.monto_total = self.costo_total
                costo_obj.fecha = self.fecha
                costo_obj.save()


# 7. Entidad Siembra (HU-07)
class Siembra(models.Model):
    """Registro del establecimiento físico y biológico de la semilla en el lote.

    Marca el inicio operativo del cultivo en campo, definiendo el método de dispersión,
    variedad botánica, densidad por hectárea y porcentaje de germinación comprobado.

    Attributes:
        ciclo (OneToOneField): Ciclo productivo único al cual se vincula la siembra.
        fecha (DateField): Fecha de realización de la labor de siembra.
        metodo (CharField): Modalidad de siembra ('VOLEO', 'MECANIZADA', 'TRANSPLANTE').
        variedad (CharField): Variedad o cultivar de semilla certificada sembrada.
        dosis_kg_ha (DecimalField): Densidad de semilla empleada en kilogramos por hectárea.
        tratamiento_semilla (CharField): Productos agroquímicos o biológicos inoculados a la semilla.
        germinacion_porcentaje (DecimalField): Porcentaje de germinación comprobado en prueba de vigor (0-100%).
    """
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
        """Retorna la variedad sembrada y el nombre del ciclo."""
        return f"Siembra {self.variedad} - {self.ciclo.nombre_ciclo}"

    def save(self, *args, **kwargs):
        """Transiciona de forma atómica el estado del ciclo a 'EJECUCION' y el lote a 'EN_CICLO'.

        Garantiza que al asentar la siembra física, la fecha de inicio real del ciclo
        quede fijada con la fecha de la siembra.
        """
        # Lógica de Cambio Automático de Estados (HU-07)
        # Al sembrar, el ciclo entra en EJECUCION y el lote EN_CICLO
        with transaction.atomic():
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
    """Registro cronológico de las fases fenológicas y vigor agronómico del arroz.

    Permite monitorear el desarrollo biológico del cultivo a través de sus fases
    vegetativas, reproductivas y de maduración, computando automáticamente los días
    transcurridos y soportando registro fotográfico.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo en observación.
        fecha (DateField): Fecha de la inspección agronómica en campo.
        fase (CharField): Fase fenológica actual ('GERMINACION', 'PLANTULA', 'MACOLLAMIENTO',
            'PRIMORDIO', 'EMBUCHAMIENTO', 'FLORACION', 'GRANO_LECHOSO', 'GRANO_PASTOSO', 'MADUREZ_COSECHA').
        estado_general (CharField): Evaluación de vigor ('EXCELENTE', 'BUENO', 'REGULAR', 'MALO').
        dias_transcurridos_calculados (IntegerField): Días calculados automáticamente desde la siembra.
        observaciones (TextField): Notas del técnico sobre macollamiento, vigor o anomalías.
        fotografia (ImageField): Evidencia fotográfica del dosel vegetal en campo.
    """
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
    ESTADOS = [
        ('EXCELENTE', 'Excelente Vigor'),
        ('BUENO', 'Buen Desarrollo'),
        ('REGULAR', 'Desarrollo Regular / Atraso'),
        ('MALO', 'Deficiente / Estrés Severo'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='seguimientos_fenologicos')
    fecha = models.DateField()
    fase = models.CharField(max_length=30, choices=FASES)
    estado_general = models.CharField(max_length=20, choices=ESTADOS, default='BUENO', help_text="Vigor y estado general del cultivo")
    dias_transcurridos_calculados = models.IntegerField(null=True, blank=True, help_text="Días transcurridos desde la siembra (auto calculado)")
    observaciones = models.TextField(null=True, blank=True)
    fotografia = models.ImageField(upload_to='fenologia/', null=True, blank=True)

    class Meta:
        db_table = 'seguimiento_fenologico'

    def __str__(self):
        """Retorna la fase fenológica y el nombre del ciclo."""
        return f"{self.get_fase_display()} - {self.ciclo.nombre_ciclo}"

    def save(self, *args, **kwargs):
        """Calcula de forma automática los días transcurridos desde la fecha de siembra."""
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
    """Libro contable y centralizador de costos operativos del ciclo productivo.

    Almacena los egresos directos originados automáticamente por labores agronómicas
    (preparación de maquinaria, fertilización, aplicaciones fitosanitarias, bombeo de riego)
    y egresos manuales (mano de obra, transporte, arrendamiento de tierra, otros).

    Attributes:
        ciclo (ForeignKey): Ciclo productivo al cual se carga el costo.
        preparacion (OneToOneField): Enlace uno a uno opcional con la labor de maquinaria origen.
        fertilizacion (OneToOneField): Enlace uno a uno opcional con la fertilización origen.
        aplicacion (OneToOneField): Enlace uno a uno opcional con la aplicación fitosanitaria origen.
        riego (OneToOneField): Enlace uno a uno opcional con el registro de riego origen.
        fecha (DateField): Fecha de realización del gasto o labor.
        categoria (CharField): Rubro presupuestal ('MANO_DE_OBRA', 'INSUMOS_AGROQUIMICOS',
            'MAQUINARIA', 'ARRENDAMIENTO_TIERRA', 'TRANSPORTE', 'OTROS').
        descripcion (TextField): Concepto detallado del egreso.
        monto_total (DecimalField): Valor monetario del costo en pesos COP.
    """
    CATEGORIAS = [
        ('MANO_DE_OBRA', 'Mano de Obra'),
        ('INSUMOS_AGROQUIMICOS', 'Insumos Agroquímicos'),
        ('MAQUINARIA', 'Maquinaria'),
        ('ARRENDAMIENTO_TIERRA', 'Arrendamiento de Tierra'),
        ('TRANSPORTE', 'Transporte'),
        ('OTROS', 'Otros'),
    ]
    ciclo = models.ForeignKey(CicloProductivo, on_delete=models.CASCADE, related_name='costos')
    preparacion = models.OneToOneField('PreparacionMaquinaria', on_delete=models.CASCADE, null=True, blank=True, related_name='costo_asociado')
    fertilizacion = models.OneToOneField('Fertilizacion', on_delete=models.CASCADE, null=True, blank=True, related_name='costo_asociado')
    aplicacion = models.OneToOneField('AplicacionAgroquimico', on_delete=models.CASCADE, null=True, blank=True, related_name='costo_asociado')
    riego = models.OneToOneField('RegistroHidrico', on_delete=models.CASCADE, null=True, blank=True, related_name='costo_asociado')
    fecha = models.DateField()
    categoria = models.CharField(max_length=30, choices=CATEGORIAS)
    descripcion = models.TextField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'registro_costo'

    def __str__(self):
        """Retorna la categoría, descripción y monto total del egreso."""
        return f"{self.get_categoria_display()} - {self.descripcion} ({self.monto_total})"


# 10. Entidad Monitoreo Fitosanitario (HU-15)
class MonitoreoFitosanitario(models.Model):
    """Inspección técnica de sanidad vegetal en el lote (plagas, enfermedades y malezas).

    Registra el diagnóstico en campo de factores bióticos perjudiciales, evaluando el
    nivel de daño porcentual observado para orientar decisiones agronómicas de control
    y registrar opcionalmente coordenadas satelitales del punto de muestreo.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo monitoreado.
        fecha (DateField): Fecha de toma de datos en campo.
        tipo_problema (CharField): Tipo de agente dañino ('PLAGA', 'ENFERMEDAD', 'MALEZA').
        nombre_comun (CharField): Nombre común del organismo o síntoma (ej. Sogata, Pyricularia).
        umbral_danio_porcentaje (DecimalField): Porcentaje de daño o incidencia observada (0-100%).
        decision_tecnica (TextField): Justificación y recomendación agronómica (ej. no aplicar, control químico).
        latitud (DecimalField): Coordenada GPS de latitud en grados decimales.
        longitud (DecimalField): Coordenada GPS de longitud en grados decimales.
    """
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
        """Retorna el tipo de problema, nombre común del agente y fecha."""
        return f"{self.get_tipo_problema_display()}: {self.nombre_comun} ({self.fecha})"


# 11. Entidad Fertilización (HU-16)
class Fertilizacion(models.Model):
    """Registro de fertilización edáfica y nutricional foliar del cultivo de arroz.

    Controla los planes de aporte de nutrientes (NPK y elementos menores), las fuentes
    comerciales empleadas, dosis aplicadas y los costos incurridos en insumos y mano de obra.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo receptor de los nutrientes.
        fecha (DateField): Fecha de realización de la fertilización en campo.
        etapa_fenologica (CharField): Fase fenológica del arroz (ej. Macollamiento, Primordio).
        tipo_fertilizante (CharField): Composición o tipo (ej. NPK 15-15-15, Urea).
        fuente_comercial (CharField): Marca o denominación comercial de la fuente (ej. DAP, KCl).
        dosis_kg_ha (DecimalField): Dosis dosificada en kilogramos por hectárea (kg/ha).
        costo_producto (DecimalField): Costo de compra del fertilizante en pesos COP.
        costo_mano_obra (DecimalField): Costo de aplicación pagado a operarios en pesos COP.
    """
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
        """Retorna el tipo de fertilizante, fuente comercial y fecha de aplicación."""
        return f"Fertilización {self.tipo_fertilizante} - {self.fuente_comercial} ({self.fecha})"

    def save(self, *args, **kwargs):
        """Persiste la fertilización y crea/actualiza el egreso en RegistroCosto.

        Suma costo_producto y costo_mano_obra e inserta de forma atómica el registro en
        RegistroCosto bajo la categoría 'INSUMOS_AGROQUIMICOS'.
        """
        with transaction.atomic():
            super().save(*args, **kwargs)
            from .models import RegistroCosto
            desc = f"Fertilización {self.tipo_fertilizante} - {self.fuente_comercial} ({self.dosis_kg_ha} kg/ha)"
            monto = self.costo_producto + self.costo_mano_obra
            costo_obj, created = RegistroCosto.objects.get_or_create(
                fertilizacion=self,
                defaults={
                    'ciclo': self.ciclo,
                    'categoria': 'INSUMOS_AGROQUIMICOS',
                    'descripcion': desc,
                    'fecha': self.fecha,
                    'monto_total': monto
                }
            )
            if not created:
                costo_obj.descripcion = desc
                costo_obj.monto_total = monto
                costo_obj.fecha = self.fecha
                costo_obj.save()


# 12. Entidad Aplicación de Agroquímicos (HU-17)
class AplicacionAgroquimico(models.Model):
    """Registro de aplicaciones fitoterapéuticas de protección vegetal.

    Almacena las aspersiones de insecticidas, fungicidas, herbicidas y bactericidas,
    controlando parámetros climáticos, periodo de carencia previa a cosecha y trazabilidad
    hacia el monitoreo fitosanitario origen.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo donde se aplica el plaguicida.
        monitoreo (ForeignKey): Monitoreo fitosanitario opcional que justificó la aplicación.
        fecha (DateField): Fecha de realización de la aspersión.
        nombre_comercial (CharField): Marca comercial del producto formulado.
        ingrediente_activo (CharField): Molécula química o ingrediente activo del producto.
        dosis_por_ha (DecimalField): Cantidad de producto dosificado por hectárea.
        equipo_aspersion (CharField): Maquinaria o equipo (ej. Bomba espalda, Dron, Tractor).
        temperatura_c (DecimalField): Temperatura ambiental en grados Celsius al momento de aplicar.
        velocidad_viento_kmh (DecimalField): Velocidad del viento en km/h durante la aspersión.
        periodo_carencia_dias (IntegerField): Días requeridos de retiro antes de recolectar el grano.
        costo_producto (DecimalField): Valor monetario del insumo químico en COP.
        costo_mano_obra (DecimalField): Valor pagado por el servicio de aspersión en COP.
    """
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
        """Retorna el nombre comercial del agroquímico y la fecha de aspersión."""
        return f"Aplicación {self.nombre_comercial} ({self.fecha})"

    def save(self, *args, **kwargs):
        """Persiste la aplicación fitosanitaria e integra el costo total en RegistroCosto.

        Calcula monto = costo_producto + costo_mano_obra e inserta o actualiza el registro
        bajo 'INSUMOS_AGROQUIMICOS' en una transacción atómica.
        """
        with transaction.atomic():
            super().save(*args, **kwargs)
            from .models import RegistroCosto
            desc = f"Aplicación Agroquímico {self.nombre_comercial} ({self.ingrediente_activo})"
            monto = self.costo_producto + self.costo_mano_obra
            costo_obj, created = RegistroCosto.objects.get_or_create(
                aplicacion=self,
                defaults={
                    'ciclo': self.ciclo,
                    'categoria': 'INSUMOS_AGROQUIMICOS',
                    'descripcion': desc,
                    'fecha': self.fecha,
                    'monto_total': monto
                }
            )
            if not created:
                costo_obj.descripcion = desc
                costo_obj.monto_total = monto
                costo_obj.fecha = self.fecha
                costo_obj.save()


# 13. Entidad Manejo Hídrico y Control de Riego (HU-18)
class RegistroHidrico(models.Model):
    """Control cuantitativo de riego, lámina de agua y compuertas de drenaje.

    Registra el volumen de agua ingresado o recirculado en el lote arrocero, la fuente
    de abastecimiento, costos de bombeo asociados, la altura de lámina y el estado de drenaje.

    Attributes:
        ciclo (ForeignKey): Ciclo productivo beneficiario del recurso hídrico.
        fecha (DateField): Fecha de suministro o medición del agua.
        volumen_agua_m3 (DecimalField): Cantidad de agua suministrada en metros cúbicos.
        fuente_hidrica (CharField): Procedencia del agua ('CANAL', 'RIO', 'POZO').
        costo_bombeo (DecimalField): Costo asociado a combustible o energía de motobombas en COP.
        dias_inundacion (IntegerField): Días acumulados de permanencia continua de la lámina de agua.
        lamina_agua_cm (DecimalField): Espesor o altura de la lámina de agua en centímetros.
        estado_drenaje (CharField): Estado operativo de compuertas ('ABIERTO', 'CERRADO').
    """
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
        """Retorna la fuente hídrica, espesor de lámina en cm y la fecha de registro."""
        return f"Riego {self.fuente_hidrica} - L: {self.lamina_agua_cm}cm ({self.fecha})"

    def save(self, *args, **kwargs):
        """Persiste el evento hídrico y sincroniza el costo de bombeo en RegistroCosto.

        Crea o actualiza de manera transaccional el egreso en RegistroCosto bajo la
        categoría 'OTROS' por el valor de costo_bombeo.
        """
        with transaction.atomic():
            super().save(*args, **kwargs)
            from .models import RegistroCosto
            desc = f"Manejo Hídrico / Riego desde {self.get_fuente_hidrica_display()}"
            costo_obj, created = RegistroCosto.objects.get_or_create(
                riego=self,
                defaults={
                    'ciclo': self.ciclo,
                    'categoria': 'OTROS',
                    'descripcion': desc,
                    'fecha': self.fecha,
                    'monto_total': self.costo_bombeo
                }
            )
            if not created:
                costo_obj.descripcion = desc
                costo_obj.monto_total = self.costo_bombeo
                costo_obj.fecha = self.fecha
                costo_obj.save()

# =========================================================================
# SPRINT 4: COSECHA Y CIERRE ECONÓMICO
# =========================================================================

# 14. Entidad Cosecha (HU-013)
class Cosecha(models.Model):
    """Registro físico de recolección y rendimiento bruto de arroz paddy en campo.

    Representa la labor de corte con cosechadora combinada, registrando la producción
    en verde obtenida en kilogramos y variables de calidad física al corte.

    Attributes:
        ciclo (OneToOneField): Ciclo productivo único que finaliza su fase de cultivo.
        fecha (DateField): Fecha en que se realizó el corte y recolección.
        produccion_obtenida_kg (DecimalField): Producción bruta en campo en kilogramos.
        humedad_grano_porcentaje (DecimalField): Humedad relativa del grano al corte (%).
        impurezas_porcentaje (DecimalField): Contenido de impurezas físicas (% cascabillo, tamo).
        condiciones_cosecha (TextField): Circunstancias agronómicas o climáticas al momento del corte.
    """
    ciclo = models.OneToOneField(CicloProductivo, on_delete=models.CASCADE, related_name='cosecha')
    fecha = models.DateField()
    produccion_obtenida_kg = models.DecimalField(max_digits=12, decimal_places=2, help_text="Producción total obtenida en Kilogramos")
    humedad_grano_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de humedad del grano al corte")
    impurezas_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Porcentaje de impurezas")
    condiciones_cosecha = models.TextField(null=True, blank=True, help_text="Condiciones generales durante la cosecha (ej. lluvia, acame)")

    class Meta:
        db_table = 'cosecha'

    def __str__(self):
        """Retorna la fecha de cosecha y el nombre del ciclo."""
        return f"Cosecha {self.fecha} - {self.ciclo.nombre_ciclo}"

    def save(self, *args, **kwargs):
        """Transiciona atómicamente el estado del ciclo y del lote a 'COSECHADO'.

        Fija la fecha_fin_real del CicloProductivo con la fecha de la labor de corte.
        """
        with transaction.atomic():
            if not self.pk:
                # Lógica de cierre al registrar la cosecha
                self.ciclo.estado = 'COSECHADO'
                self.ciclo.fecha_fin_real = self.fecha
                self.ciclo.save()
                
                self.ciclo.lote.estado = 'COSECHADO'
                self.ciclo.lote.save()
                
            super().save(*args, **kwargs)

# 15. Entidad Liquidación del Molino (HU-014)
class Liquidacion(models.Model):
    """Liquidación comercial y cierre económico final de la cosecha en el molino.

    Registra los parámetros industriales de secamiento y trilla (grano entero vs. quebrado),
    precio pagado por tonelada, descuentos por humedad o impurezas y la liquidación neta final.

    Attributes:
        ciclo (OneToOneField): Ciclo productivo que culmina su liquidación financiera.
        fecha (DateField): Fecha de emisión de la liquidación expedida por el molino.
        humedad_final_porcentaje (DecimalField): Porcentaje final de humedad tras secamiento (14% ideal).
        porcentaje_grano_entero (DecimalField): Rendimiento de trilla de arroz blanco entero (%).
        porcentaje_grano_quebrado (DecimalField): Porcentaje de grano quebrado o partido (%).
        precio_tonelada_cop (DecimalField): Precio comercial pagado por tonelada de arroz en COP.
        descuentos_aplicados_cop (DecimalField): Deducciones monetarias por humedad o impureza en COP.
        ingreso_neto_cop (DecimalField): Monto neto liquidado y transferido al productor en COP.
        observaciones (TextField): Notas sobre la calidad molinera o conceptos del pago.
    """
    ciclo = models.OneToOneField(CicloProductivo, on_delete=models.CASCADE, related_name='liquidacion')
    fecha = models.DateField()
    humedad_final_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de humedad final logrado en secamiento")
    porcentaje_grano_entero = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de granos enteros logrados en trilla")
    porcentaje_grano_quebrado = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de granos quebrados logrados en trilla")
    precio_tonelada_cop = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio pagado por tonelada en pesos COP")
    descuentos_aplicados_cop = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="Descuentos aplicados por humedad o impurezas en pesos COP")
    ingreso_neto_cop = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto neto final recibido del molino en pesos COP")
    observaciones = models.TextField(null=True, blank=True, help_text="Observaciones generales sobre la trilla o liquidación")

    class Meta:
        db_table = 'liquidacion'

    def __str__(self):
        """Retorna la fecha de liquidación, nombre del ciclo e ingreso neto liquidado."""
        return f"Liquidación {self.fecha} - {self.ciclo.nombre_ciclo} (${self.ingreso_neto_cop})"

    def save(self, *args, **kwargs):
        """Finaliza el ciclo productivo y pasa el lote a descanso biológico.

        En una transacción atómica:
        1. Transiciona CicloProductivo a estado 'FINALIZADO'.
        2. Transiciona Lote a estado 'DESCANSO' para permitir la recuperación edáfica del suelo.
        """
        with transaction.atomic():
            if not self.pk:
                # Lógica de cierre al registrar la liquidación
                self.ciclo.estado = 'FINALIZADO'
                self.ciclo.save()
                
                # Cambiar el lote a "En Descanso" para el reposo biológico de la tierra (Sprint 4)
                self.ciclo.lote.estado = 'DESCANSO'
                self.ciclo.lote.save()
                
            super().save(*args, **kwargs)
