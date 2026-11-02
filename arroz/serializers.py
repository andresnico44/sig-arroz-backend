from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import (Perfil, Finca, Lote, AnalisisSuelo, CicloProductivo, PreparacionMaquinaria, Siembra, 
                     SeguimientoFenologico, RegistroCosto, MonitoreoFitosanitario, Fertilizacion, 
                     AplicacionAgroquimico, RegistroHidrico, Cosecha, Liquidacion)
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializador personalizado para autenticación JWT con inyección de metadatos.

    Extiende el serializador base de SimpleJWT para incluir en el payload del token
    el nombre completo del usuario y su rol funcional en el sistema SIG-ARROZ,
    permitiendo al frontend renderizar vistas acordes al perfil sin peticiones adicionales.
    """
    @classmethod
    def get_token(cls, user):
        """Genera el token JWT enriquecido con datos del perfil del usuario.

        Args:
            user (User): Instancia del usuario autenticado.

        Returns:
            Token: Token JWT con los claims 'username' (nombre completo) y 'rol'.
        """
        token = super().get_token(user)

        # Inyectar el Nombre Completo real al token JWT (permite espacios, tildes, ñ)
        full_name = f"{user.first_name} {user.last_name}".strip()
        token['username'] = full_name if full_name else user.username
        
        # Intentar obtener el rol del usuario para enviarlo al frontend
        try:
            token['rol'] = user.perfil.rol
        except Perfil.DoesNotExist:
            token['rol'] = 'SIN_ROL'

        return token

# Serializador para el Registro de Usuarios (RF05 extendido para self-registration)
class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """Serializador para el autoregistro público de usuarios y asignación de perfil inicial.

    Permite a nuevos usuarios registrarse en la plataforma capturando su nombre completo,
    correo electrónico, contraseña y rol inicial (ADMIN, PRODUCTOR, TECNICO).
    """
    nombre_completo = serializers.CharField(write_only=True, required=True)
    rol = serializers.ChoiceField(choices=Perfil.ROLES, write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('nombre_completo', 'email', 'password', 'rol')

    def validate_email(self, value):
        """Valida que el correo electrónico no se encuentre previamente registrado en el sistema.

        Args:
            value (str): Dirección de correo electrónico enviada por el usuario.

        Returns:
            str: Correo electrónico validado.

        Raises:
            serializers.ValidationError: Si ya existe un usuario activo con dicho correo.
        """
        # Validar duplicados de correo electrónico
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value

    def create(self, validated_data):
        """Crea el usuario Django base y su correspondiente entidad Perfil con el rol asignado.

        Args:
            validated_data (dict): Diccionario de datos validados.

        Returns:
            User: Instancia del nuevo usuario creado.
        """
        nombre_completo = validated_data.pop('nombre_completo').strip()
        email = validated_data['email']
        rol = validated_data.pop('rol')
        
        # Dividir nombre y apellido de manera inteligente
        parts = nombre_completo.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        # Crear usuario base de Django (usando el email como username único interno)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name
        )
        
        # Asociarle su perfil y rol
        Perfil.objects.create(user=user, rol=rol)
        return user

# =========================================================================
# SPRINT 2: GESTIÓN DE CULTIVO (FINCAS Y LOTES)
# =========================================================================

class FincaSerializer(serializers.ModelSerializer):
    """Serializador para la administración y consulta de unidades productivas (Fincas).

    Incluye el campo computado 'productor_nombre' para simplificar la visualización
    en interfaces de usuario y valida que la extensión territorial sea positiva.
    """
    # Campo de solo lectura para facilitar el renderizado en React
    productor_nombre = serializers.SerializerMethodField()
    productor_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Finca
        fields = ('id', 'productor', 'productor_nombre', 'productor_id', 'nombre', 'ubicacion_departamento', 'ubicacion_municipio', 'area_total_ha')
        # El productor se asigna automáticamente en el View, nadie puede falsificar este ID en el JSON
        read_only_fields = ('productor',)

    def get_productor_nombre(self, obj):
        """Obtiene el nombre completo formateado del productor propietario de la finca.

        Args:
            obj (Finca): Instancia del modelo Finca.

        Returns:
            str: Nombre y apellido concatenados del productor.
        """
        return f"{obj.productor.first_name} {obj.productor.last_name}".strip()

    def validate_area_total_ha(self, value):
        """Valida que el área total de la finca sea estrictamente mayor a 0 hectáreas.

        Args:
            value (Decimal): Extensión total ingresada en hectáreas.

        Returns:
            Decimal: Valor del área validado.

        Raises:
            serializers.ValidationError: Si el área es menor o igual a 0.
        """
        if value <= 0:
            raise serializers.ValidationError("El área de la finca debe ser mayor a 0 hectáreas.")
        return value

class LoteSerializer(serializers.ModelSerializer):
    """Serializador para la gestión territorial de parcelas o lotes arroceros.

    Valida la coherencia espacial del predio, asegurando que el área del lote no exceda
    la extensión total de la finca madre (RF12).
    """
    # Campo de solo lectura para que React sepa el nombre de la finca madre sin hacer otra petición
    finca_nombre = serializers.ReadOnlyField(source='finca.nombre')

    class Meta:
        model = Lote
        fields = ('id', 'finca', 'finca_nombre', 'nombre', 'area_hectareas', 'tipo_suelo', 'sistema_produccion', 'latitud', 'longitud', 'estado')

    def validate_area_hectareas(self, value):
        """Valida que el área neta del lote sea un valor positivo mayor a 0.

        Args:
            value (Decimal): Extensión de la parcela en hectáreas.

        Returns:
            Decimal: Área validada.

        Raises:
            serializers.ValidationError: Si el área es menor o igual a cero.
        """
        if value <= 0:
            raise serializers.ValidationError("El área del lote debe ser mayor a 0 hectáreas.")
        return value

    def validate(self, data):
        """Aplica la regla de negocio cruzada RF12: Área del Lote <= Área Total de la Finca.

        Args:
            data (dict): Diccionario de atributos del lote a validar.

        Returns:
            dict: Datos validados.

        Raises:
            serializers.ValidationError: Si el área del lote supera el área total de la finca.
        """
        # Validar lógica de negocio cruzada (RF12)
        # Un lote no puede ser más grande que la propia finca.
        finca = data.get('finca')
        area_lote = data.get('area_hectareas')
        
        # En caso de actualización parcial (PATCH), si no viene finca o área, omitir validación cruzada estricta
        if finca and area_lote:
            if area_lote > finca.area_total_ha:
                raise serializers.ValidationError({
                    "area_hectareas": f"El área del lote ({area_lote} ha) no puede superar el área total de la finca '{finca.nombre}' ({finca.area_total_ha} ha)."
                })
        return data

# =========================================================================
# SPRINT 2: GESTIÓN DE ANÁLISIS DE SUELO Y CICLOS PRODUCTIVOS
# =========================================================================

class AnalisisSueloSerializer(serializers.ModelSerializer):
    """Serializador para el registro y diagnóstico agronómico de análisis de suelos.

    Calcula automáticamente la interpretación cualitativa de acidez según la escala
    oficial de pH para arroz y valida el rango físico admisible de 0 a 14.
    """
    # Campo calculado para que el frontend no tenga que procesar la acidez en React
    interpretacion_ph = serializers.SerializerMethodField()
    lote_nombre = serializers.ReadOnlyField(source='lote.nombre')
    laboratorio = serializers.CharField(required=False, allow_blank=True, default='Laboratorio General')

    class Meta:
        model = AnalisisSuelo
        fields = ('id', 'lote', 'lote_nombre', 'fecha_muestreo', 'ph', 'materia_organica_porcentaje', 'fosforo_ppm', 'potasio_meq', 'textura', 'laboratorio', 'interpretacion_ph')

    def get_interpretacion_ph(self, obj):
        """Clasifica agronómicamente el nivel de acidez del suelo para el cultivo de arroz.

        Args:
            obj (AnalisisSuelo): Instancia del modelo con el valor de pH.

        Returns:
            str: Diagnóstico agronómico ('Fuerte Ácido', 'Moderadamente Ácido', 'Neutro', 'Alcalino').
        """
        ph = float(obj.ph)
        if ph < 5.5:
            return "Fuerte Ácido (Requiere enmienda caliza)"
        elif 5.5 <= ph < 6.0:
            return "Moderadamente Ácido"
        elif 6.0 <= ph <= 7.0:
            return "Neutro (Óptimo para arroz)"
        else:
            return "Alcalino"

    def validate_ph(self, value):
        """Valida que el valor de pH se encuentre en la escala físico-química estándar [0.0, 14.0].

        Args:
            value (Decimal): Valor de pH medido.

        Returns:
            Decimal: Valor de pH validado.

        Raises:
            serializers.ValidationError: Si el pH es menor que 0 o mayor que 14.
        """
        if value < 0 or value > 14:
            raise serializers.ValidationError("El nivel de pH debe estar en el rango de 0 a 14.")
        return value


class CicloProductivoSerializer(serializers.ModelSerializer):
    """Serializador para la planificación y seguimiento operativo de ciclos productivos.

    Expone datos agregados del lote y la finca contenedora en formato de lectura directa,
    y verifica la no negatividad de los presupuestos estimados.
    """
    lote_nombre = serializers.ReadOnlyField(source='lote.nombre')
    finca_nombre = serializers.ReadOnlyField(source='lote.finca.nombre')

    class Meta:
        model = CicloProductivo
        fields = ('id', 'lote', 'lote_nombre', 'finca_nombre', 'nombre_ciclo', 'anio', 'semestre', 'variedad_arroz', 'presupuesto_estimado', 'estado', 'fecha_inicio_real', 'fecha_fin_real')

    def validate_presupuesto_estimado(self, value):
        """Valida que el presupuesto estimado del ciclo sea mayor o igual a cero.

        Args:
            value (Decimal): Techo presupuestal propuesto en COP.

        Returns:
            Decimal: Presupuesto validado.

        Raises:
            serializers.ValidationError: Si el presupuesto estimado es negativo.
        """
        if value < 0:
            raise serializers.ValidationError("El presupuesto estimado no puede ser un valor negativo.")
        return value

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

class PreparacionMaquinariaSerializer(serializers.ModelSerializer):
    """Serializador para el registro de horas y labores mecánicas de tractores.

    Controla el cálculo automático de costos totales de maquinaria e impide la entrada
    de horas de trabajo negativas.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = PreparacionMaquinaria
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'labor', 'condicion_humedad', 'horas_maquina', 'combustible_galones', 'costo_hora', 'costo_total', 'observaciones')
        read_only_fields = ('costo_total',)

    def validate_horas_maquina(self, value):
        """Valida que las horas de tractor registradas no sean valores negativos.

        Args:
            value (Decimal): Cantidad de horas reportadas.

        Returns:
            Decimal: Horas validadas.

        Raises:
            serializers.ValidationError: Si las horas son menores a 0.
        """
        if value < 0:
            raise serializers.ValidationError("Las horas de máquina no pueden ser negativas.")
        return value


class SiembraSerializer(serializers.ModelSerializer):
    """Serializador para el registro del establecimiento inicial de la siembra en campo.

    Valida parámetros biológicos esenciales como el porcentaje de viabilidad y germinación,
    además de exigir una densidad de siembra positiva.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = Siembra
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'metodo', 'variedad', 'dosis_kg_ha', 'tratamiento_semilla', 'germinacion_porcentaje')

    def validate_germinacion_porcentaje(self, value):
        """Valida que el porcentaje de germinación se encuentre en el rango físico [0, 100].

        Args:
            value (Decimal): Porcentaje de germinación de la semilla.

        Returns:
            Decimal: Porcentaje validado.

        Raises:
            serializers.ValidationError: Si el valor es menor a 0 o mayor a 100.
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de germinación debe estar entre 0 y 100.")
        return value

    def validate_dosis_kg_ha(self, value):
        """Valida que la cantidad de semilla sembrada por hectárea sea estrictamente mayor a 0.

        Args:
            value (Decimal): Densidad de semilla en kg/ha.

        Returns:
            Decimal: Dosis validada.

        Raises:
            serializers.ValidationError: Si la dosis es menor o igual a 0.
        """
        if value <= 0:
            raise serializers.ValidationError("La dosis de siembra debe ser mayor a 0.")
        return value


class SeguimientoFenologicoSerializer(serializers.ModelSerializer):
    """Serializador para las evaluaciones periódicas de desarrollo vegetal y fenología.

    Maneja la serialización de fases fenológicas, vigor agronómico, imágenes fotográficas
    y expone los días de desarrollo calculados por el modelo de forma protegida.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    
    class Meta:
        model = SeguimientoFenologico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'fase', 'estado_general', 'dias_transcurridos_calculados', 'observaciones', 'fotografia')
        read_only_fields = ('dias_transcurridos_calculados',)


# =========================================================================
# SPRINT 3: GESTIÓN DE SANIDAD, NUTRICIÓN, MANEJO HÍDRICO Y BILLETERA
# =========================================================================

class RegistroCostoSerializer(serializers.ModelSerializer):
    """Serializador para la consulta y registro contable de egresos en la billetera del ciclo.

    Provee la descripción legible de la categoría presupuestal e impide el ingreso
    de importes económicos negativos.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = RegistroCosto
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'categoria', 'categoria_display', 'descripcion', 'monto_total')

    def validate_monto_total(self, value):
        """Valida que el valor económico del egreso no sea negativo.

        Args:
            value (Decimal): Importe monetario del costo en COP.

        Returns:
            Decimal: Monto validado.

        Raises:
            serializers.ValidationError: Si el monto es menor a 0.
        """
        if value < 0:
            raise serializers.ValidationError("El monto total del costo no puede ser negativo.")
        return value


class MonitoreoFitosanitarioSerializer(serializers.ModelSerializer):
    """Serializador para la captura técnica de censos de plagas, enfermedades y malezas.

    Gestiona los reportes de sanidad vegetal georreferenciados y valida que los umbrales
    de daño se mantengan dentro del rango porcentual válido [0%, 100%].
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    tipo_problema_display = serializers.CharField(source='get_tipo_problema_display', read_only=True)

    class Meta:
        model = MonitoreoFitosanitario
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'tipo_problema', 'tipo_problema_display', 'nombre_comun', 'umbral_danio_porcentaje', 'decision_tecnica', 'latitud', 'longitud')

    def validate_umbral_danio_porcentaje(self, value):
        """Valida que el umbral de daño o severidad observado esté en el rango [0.0, 100.0].

        Args:
            value (Decimal): Nivel de daño porcentual.

        Returns:
            Decimal: Umbral validado.

        Raises:
            serializers.ValidationError: Si el valor es menor a 0% o mayor a 100%.
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El umbral de daño debe estar entre 0% y 100%.")
        return value


class FertilizacionSerializer(serializers.ModelSerializer):
    """Serializador para los registros de nutrición edáfica y aportes de fertilizantes.

    Exige que la dosis nutricional por hectárea sea un valor estrictamente positivo.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = Fertilizacion
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'etapa_fenologica', 'tipo_fertilizante', 'fuente_comercial', 'dosis_kg_ha', 'costo_producto', 'costo_mano_obra')

    def validate_dosis_kg_ha(self, value):
        """Valida que la dosis de fertilizante aplicada sea estrictamente mayor a 0 kg/ha.

        Args:
            value (Decimal): Dosis en kilogramos por hectárea.

        Returns:
            Decimal: Dosis validada.

        Raises:
            serializers.ValidationError: Si la dosis es menor o igual a 0.
        """
        if value <= 0:
            raise serializers.ValidationError("La dosis aplicada debe ser mayor a 0 kg/ha.")
        return value


class AplicacionAgroquimicoSerializer(serializers.ModelSerializer):
    """Serializador para las aspersiones de plaguicidas de protección de cultivos.

    Asocia el evento de control con el monitoreo fitosanitario que lo motivó y valida
    que el periodo de carencia antes de cosecha no sea un valor negativo.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    monitoreo_nombre = serializers.ReadOnlyField(source='monitoreo.nombre_comun')

    class Meta:
        model = AplicacionAgroquimico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'monitoreo', 'monitoreo_nombre', 'fecha', 'nombre_comercial', 'ingrediente_activo', 'dosis_por_ha', 'equipo_aspersion', 'temperatura_c', 'velocidad_viento_kmh', 'periodo_carencia_dias', 'costo_producto', 'costo_mano_obra')

    def validate_periodo_carencia_dias(self, value):
        """Valida que el periodo de carencia (tiempo de espera antes de cosecha) no sea negativo.

        Args:
            value (int): Días de retiro.

        Returns:
            int: Días validados.

        Raises:
            serializers.ValidationError: Si los días son menores a 0.
        """
        if value < 0:
            raise serializers.ValidationError("El periodo de carencia no puede ser negativo.")
        return value


class RegistroHidricoSerializer(serializers.ModelSerializer):
    """Serializador para el control de riegos, niveles de lámina de agua y drenajes.

    Provee la interpretación textual de la fuente de agua y del estado de las compuertas,
    facilitando su consumo directo en las interfaces de usuario.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    fuente_hidrica_display = serializers.CharField(source='get_fuente_hidrica_display', read_only=True)
    estado_drenaje_display = serializers.CharField(source='get_estado_drenaje_display', read_only=True)

    class Meta:
        model = RegistroHidrico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'volumen_agua_m3', 'fuente_hidrica', 'fuente_hidrica_display', 'costo_bombeo', 'dias_inundacion', 'lamina_agua_cm', 'estado_drenaje', 'estado_drenaje_display')

class CosechaSerializer(serializers.ModelSerializer):
    """Serializador para el registro de la recolección física del grano en campo.

    Calcula dinámicamente el rendimiento productivo en toneladas por hectárea y valida
    que los kilogramos producidos, porcentaje de humedad e impurezas se encuentren en rangos válidos.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    lote_id = serializers.ReadOnlyField(source='ciclo.lote.id')
    lote_nombre = serializers.ReadOnlyField(source='ciclo.lote.nombre')
    finca_id = serializers.ReadOnlyField(source='ciclo.lote.finca.id')
    finca_nombre = serializers.ReadOnlyField(source='ciclo.lote.finca.nombre')
    variedad_arroz = serializers.ReadOnlyField(source='ciclo.variedad_arroz')
    lote_area = serializers.ReadOnlyField(source='ciclo.lote.area_hectareas')
    estado_ciclo = serializers.ReadOnlyField(source='ciclo.estado')
    rendimiento_ton_ha = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cosecha
        fields = (
            'id', 'ciclo', 'ciclo_nombre', 'lote_id', 'lote_nombre',
            'finca_id', 'finca_nombre', 'fecha', 'produccion_obtenida_kg',
            'humedad_grano_porcentaje', 'impurezas_porcentaje',
            'condiciones_cosecha', 'rendimiento_ton_ha',
            'variedad_arroz', 'lote_area', 'estado_ciclo'
        )

    def get_rendimiento_ton_ha(self, obj):
        """Calcula el rendimiento físico del lote expresado en toneladas métricas por hectárea.

        Fórmula: Rendimiento (ton/ha) = (Producción en kg / 1000) / Área del Lote (ha).

        Args:
            obj (Cosecha): Instancia del modelo Cosecha.

        Returns:
            float: Rendimiento redondeado a 2 decimales, o 0.0 si el área no es válida.
        """
        try:
            # Rendimiento = (Producción en kg / 1000) / Área del lote
            area = obj.ciclo.lote.area_hectareas
            if area and area > 0:
                from decimal import Decimal
                toneladas = obj.produccion_obtenida_kg / Decimal('1000')
                rendimiento = toneladas / area
                return float(round(rendimiento, 2))
            return 0.0
        except Exception:
            return 0.0

    def validate_produccion_obtenida_kg(self, value):
        """Valida que la producción en kilogramos sea estrictamente mayor a 0.

        Args:
            value (Decimal): Kilogramos cosechados.

        Returns:
            Decimal: Producción validada.

        Raises:
            serializers.ValidationError: Si la producción es menor o igual a 0.
        """
        if value <= 0:
            raise serializers.ValidationError("La producción obtenida debe ser mayor a 0 kg.")
        return value
        
    def validate_humedad_grano_porcentaje(self, value):
        """Valida que el porcentaje de humedad del grano al corte se ubique en [0, 100].

        Args:
            value (Decimal): Porcentaje de humedad en verde.

        Returns:
            Decimal: Humedad validada.

        Raises:
            serializers.ValidationError: Si el valor está fuera del rango [0, 100].
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("La humedad debe estar entre 0 y 100.")
        return value

    def validate_impurezas_porcentaje(self, value):
        """Valida que el contenido de impurezas físicas se encuentre en el rango [0, 100].

        Args:
            value (Decimal): Porcentaje de impurezas.

        Returns:
            Decimal: Impurezas validadas.

        Raises:
            serializers.ValidationError: Si el valor está fuera del rango [0, 100].
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de impurezas debe estar entre 0 y 100.")
        return value

class UserGestionSerializer(serializers.ModelSerializer):
    """Serializador para el módulo administrativo de gestión y control de usuarios (RBAC).

    Permite a los administradores crear, consultar, modificar roles, teléfonos y estados
    de activación de los usuarios del sistema.
    """
    nombre_completo = serializers.SerializerMethodField(read_only=True)
    nombre_completo_input = serializers.CharField(write_only=True, required=False)
    rol = serializers.CharField(required=False)
    telefono = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'nombre_completo', 'nombre_completo_input', 'email', 'rol', 'telefono', 'is_active', 'password')

    def get_nombre_completo(self, obj):
        """Obtiene el nombre completo formateado o el username si los nombres están vacíos.

        Args:
            obj (User): Instancia del usuario.

        Returns:
            str: Nombre completo formateado.
        """
        return f"{obj.first_name} {obj.last_name}".strip() if (obj.first_name or obj.last_name) else obj.username

    def create(self, validated_data):
        """Crea un nuevo usuario administrativo o técnico junto con su perfil asociado.

        Args:
            validated_data (dict): Datos validados de entrada.

        Returns:
            User: Usuario persistido.
        """
        nombre_completo = validated_data.pop('nombre_completo_input', '').strip()
        email = validated_data.get('email')
        rol = validated_data.pop('rol', 'TECNICO')
        telefono = validated_data.pop('telefono', '')
        
        # Dividir nombre y apellido
        parts = nombre_completo.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=validated_data.get('password', 'Arroz123*')
        )
        # Crear perfil
        Perfil.objects.create(user=user, rol=rol, telefono=telefono)
        return user

    def update(self, instance, validated_data):
        """Actualiza la información personal, credenciales y perfil del usuario existente.

        Args:
            instance (User): Instancia del usuario a modificar.
            validated_data (dict): Nuevos atributos a aplicar.

        Returns:
            User: Usuario actualizado.
        """
        nombre_completo = validated_data.pop('nombre_completo_input', None)
        if nombre_completo is not None:
            parts = nombre_completo.strip().split(' ', 1)
            instance.first_name = parts[0]
            instance.last_name = parts[1] if len(parts) > 1 else ''
            
        instance.email = validated_data.get('email', instance.email)
        instance.username = instance.email # Mantener sincronizado
        
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)
            
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        
        # Perfil
        rol = validated_data.pop('rol', None)
        telefono = validated_data.pop('telefono', None)
        
        perfil = instance.perfil
        if rol is not None:
            perfil.rol = rol
        if telefono is not None:
            perfil.telefono = telefono
        perfil.save()
            
        return instance

    def to_representation(self, instance):
        """Inyecta los campos de perfil ('rol' y 'telefono') a la respuesta serializada.

        Args:
            instance (User): Usuario inspeccionado.

        Returns:
            dict: Representación JSON enriquecida con los atributos de Perfil.
        """
        representation = super().to_representation(instance)
        if hasattr(instance, 'perfil'):
            representation['rol'] = instance.perfil.rol
            representation['telefono'] = instance.perfil.telefono
        else:
            representation['rol'] = 'SIN_ROL'
            representation['telefono'] = ''
        return representation

class LiquidacionSerializer(serializers.ModelSerializer):
    """Serializador para el balance económico y liquidación molinera de la cosecha.

    Valida los porcentajes de trilla (grano entero + grano quebrado <= 100%),
    la humedad final comercial y la consistencia de ingresos y precios monetarios.
    """
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    lote_id = serializers.ReadOnlyField(source='ciclo.lote.id')
    lote_nombre = serializers.ReadOnlyField(source='ciclo.lote.nombre')
    finca_id = serializers.ReadOnlyField(source='ciclo.lote.finca.id')
    finca_nombre = serializers.ReadOnlyField(source='ciclo.lote.finca.nombre')

    class Meta:
        model = Liquidacion
        fields = (
            'id', 'ciclo', 'ciclo_nombre', 'lote_id', 'lote_nombre',
            'finca_id', 'finca_nombre', 'fecha', 'humedad_final_porcentaje',
            'porcentaje_grano_entero', 'porcentaje_grano_quebrado',
            'precio_tonelada_cop', 'descuentos_aplicados_cop',
            'ingreso_neto_cop', 'observaciones'
        )

    def validate_humedad_final_porcentaje(self, value):
        """Valida que la humedad final de secado se encuentre en el rango [0, 100].

        Args:
            value (Decimal): Humedad final lograda en el secamiento del molino.

        Returns:
            Decimal: Humedad validada.

        Raises:
            serializers.ValidationError: Si el porcentaje está fuera de [0, 100].
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("La humedad debe estar entre 0% y 100%.")
        return value

    def validate_porcentaje_grano_entero(self, value):
        """Valida que el rendimiento de grano entero se mantenga en el rango [0, 100].

        Args:
            value (Decimal): Porcentaje de arroz blanco entero.

        Returns:
            Decimal: Porcentaje validado.

        Raises:
            serializers.ValidationError: Si el valor está fuera de [0, 100].
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de grano entero debe estar entre 0% y 100%.")
        return value

    def validate_porcentaje_grano_quebrado(self, value):
        """Valida que el porcentaje de grano quebrado o partido esté en el rango [0, 100].

        Args:
            value (Decimal): Porcentaje de arroz quebrado.

        Returns:
            Decimal: Porcentaje validado.

        Raises:
            serializers.ValidationError: Si el valor está fuera de [0, 100].
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de grano quebrado debe estar entre 0% y 100%.")
        return value

    def validate_precio_tonelada_cop(self, value):
        """Valida que el precio comercial pagado por tonelada de arroz no sea negativo.

        Args:
            value (Decimal): Precio por tonelada en pesos COP.

        Returns:
            Decimal: Precio validado.

        Raises:
            serializers.ValidationError: Si el precio es menor a cero.
        """
        if value < 0:
            raise serializers.ValidationError("El precio por tonelada no puede ser negativo.")
        return value

    def validate_ingreso_neto_cop(self, value):
        """Valida que el monto neto liquidado transferido al productor no sea negativo.

        Args:
            value (Decimal): Ingreso neto en COP.

        Returns:
            Decimal: Ingreso validado.

        Raises:
            serializers.ValidationError: Si el ingreso neto es menor a cero.
        """
        if value < 0:
            raise serializers.ValidationError("El ingreso neto no puede ser negativo.")
        return value

    def validate(self, data):
        """Valida que la suma de rendimientos de trilla (grano entero + grano quebrado) no exceda el 100%.

        Args:
            data (dict): Conjunto de datos a validar.

        Returns:
            dict: Datos validados.

        Raises:
            serializers.ValidationError: Si la suma de grano entero y quebrado supera el 100%.
        """
        entero = data.get('porcentaje_grano_entero')
        quebrado = data.get('porcentaje_grano_quebrado')
        if entero is not None and quebrado is not None:
            if entero + quebrado > 100:
                raise serializers.ValidationError("La suma de grano entero y quebrado no puede superar el 100%.")
        return data
