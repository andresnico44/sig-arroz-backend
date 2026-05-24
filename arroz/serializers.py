from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import (Perfil, Finca, Lote, AnalisisSuelo, CicloProductivo, PreparacionMaquinaria, Siembra, 
                     SeguimientoFenologico, RegistroCosto, MonitoreoFitosanitario, Fertilizacion, 
                     AplicacionAgroquimico, RegistroHidrico)
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
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
    nombre_completo = serializers.CharField(write_only=True, required=True)
    rol = serializers.ChoiceField(choices=Perfil.ROLES, write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('nombre_completo', 'email', 'password', 'rol')

    def validate_email(self, value):
        # Validar duplicados de correo electrónico
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value

    def create(self, validated_data):
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
    # Campo de solo lectura para facilitar el renderizado en React
    productor_nombre = serializers.SerializerMethodField()
    productor_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Finca
        fields = ('id', 'productor', 'productor_nombre', 'productor_id', 'nombre', 'ubicacion_departamento', 'ubicacion_municipio', 'area_total_ha')
        # El productor se asigna automáticamente en el View, nadie puede falsificar este ID en el JSON
        read_only_fields = ('productor',)

    def get_productor_nombre(self, obj):
        return f"{obj.productor.first_name} {obj.productor.last_name}".strip()

    def validate_area_total_ha(self, value):
        if value <= 0:
            raise serializers.ValidationError("El área de la finca debe ser mayor a 0 hectáreas.")
        return value

class LoteSerializer(serializers.ModelSerializer):
    # Campo de solo lectura para que React sepa el nombre de la finca madre sin hacer otra petición
    finca_nombre = serializers.ReadOnlyField(source='finca.nombre')

    class Meta:
        model = Lote
        fields = ('id', 'finca', 'finca_nombre', 'nombre', 'area_hectareas', 'tipo_suelo', 'sistema_produccion', 'latitud', 'longitud', 'estado')

    def validate_area_hectareas(self, value):
        if value <= 0:
            raise serializers.ValidationError("El área del lote debe ser mayor a 0 hectáreas.")
        return value

    def validate(self, data):
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
    # Campo calculado para que el frontend no tenga que procesar la acidez en React
    interpretacion_ph = serializers.SerializerMethodField()
    lote_nombre = serializers.ReadOnlyField(source='lote.nombre')
    laboratorio = serializers.CharField(required=False, allow_blank=True, default='Laboratorio General')

    class Meta:
        model = AnalisisSuelo
        fields = ('id', 'lote', 'lote_nombre', 'fecha_muestreo', 'ph', 'materia_organica_porcentaje', 'fosforo_ppm', 'potasio_meq', 'textura', 'laboratorio', 'interpretacion_ph')

    def get_interpretacion_ph(self, obj):
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
        if value < 0 or value > 14:
            raise serializers.ValidationError("El nivel de pH debe estar en el rango de 0 a 14.")
        return value


class CicloProductivoSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.ReadOnlyField(source='lote.nombre')
    finca_nombre = serializers.ReadOnlyField(source='lote.finca.nombre')

    class Meta:
        model = CicloProductivo
        fields = ('id', 'lote', 'lote_nombre', 'finca_nombre', 'nombre_ciclo', 'anio', 'semestre', 'variedad_arroz', 'presupuesto_estimado', 'estado', 'fecha_inicio_real', 'fecha_fin_real')

    def validate_presupuesto_estimado(self, value):
        if value < 0:
            raise serializers.ValidationError("El presupuesto estimado no puede ser un valor negativo.")
        return value

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

class PreparacionMaquinariaSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = PreparacionMaquinaria
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'labor', 'horas_maquina', 'combustible_galones', 'costo_hora', 'costo_total', 'observaciones')
        read_only_fields = ('costo_total',)

    def validate_horas_maquina(self, value):
        if value < 0:
            raise serializers.ValidationError("Las horas de máquina no pueden ser negativas.")
        return value


class SiembraSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = Siembra
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'metodo', 'variedad', 'dosis_kg_ha', 'tratamiento_semilla', 'germinacion_porcentaje')

    def validate_germinacion_porcentaje(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje de germinación debe estar entre 0 y 100.")
        return value

    def validate_dosis_kg_ha(self, value):
        if value <= 0:
            raise serializers.ValidationError("La dosis de siembra debe ser mayor a 0.")
        return value


class SeguimientoFenologicoSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    
    class Meta:
        model = SeguimientoFenologico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'fase', 'dias_transcurridos_calculados', 'observaciones', 'fotografia')
        read_only_fields = ('dias_transcurridos_calculados',)


# =========================================================================
# SPRINT 3: GESTIÓN DE SANIDAD, NUTRICIÓN, MANEJO HÍDRICO Y BILLETERA
# =========================================================================

class RegistroCostoSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = RegistroCosto
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'categoria', 'categoria_display', 'descripcion', 'monto_total')

    def validate_monto_total(self, value):
        if value < 0:
            raise serializers.ValidationError("El monto total del costo no puede ser negativo.")
        return value


class MonitoreoFitosanitarioSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    tipo_problema_display = serializers.CharField(source='get_tipo_problema_display', read_only=True)

    class Meta:
        model = MonitoreoFitosanitario
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'tipo_problema', 'tipo_problema_display', 'nombre_comun', 'umbral_danio_porcentaje', 'decision_tecnica', 'latitud', 'longitud')

    def validate_umbral_danio_porcentaje(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El umbral de daño debe estar entre 0% y 100%.")
        return value


class FertilizacionSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')

    class Meta:
        model = Fertilizacion
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'etapa_fenologica', 'tipo_fertilizante', 'fuente_comercial', 'dosis_kg_ha', 'costo_producto', 'costo_mano_obra')

    def validate_dosis_kg_ha(self, value):
        if value <= 0:
            raise serializers.ValidationError("La dosis aplicada debe ser mayor a 0 kg/ha.")
        return value


class AplicacionAgroquimicoSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    monitoreo_nombre = serializers.ReadOnlyField(source='monitoreo.nombre_comun')

    class Meta:
        model = AplicacionAgroquimico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'monitoreo', 'monitoreo_nombre', 'fecha', 'nombre_comercial', 'ingrediente_activo', 'dosis_por_ha', 'equipo_aspersion', 'temperatura_c', 'velocidad_viento_kmh', 'periodo_carencia_dias', 'costo_producto', 'costo_mano_obra')

    def validate_periodo_carencia_dias(self, value):
        if value < 0:
            raise serializers.ValidationError("El periodo de carencia no puede ser negativo.")
        return value


class RegistroHidricoSerializer(serializers.ModelSerializer):
    ciclo_nombre = serializers.ReadOnlyField(source='ciclo.nombre_ciclo')
    fuente_hidrica_display = serializers.CharField(source='get_fuente_hidrica_display', read_only=True)
    estado_drenaje_display = serializers.CharField(source='get_estado_drenaje_display', read_only=True)

    class Meta:
        model = RegistroHidrico
        fields = ('id', 'ciclo', 'ciclo_nombre', 'fecha', 'volumen_agua_m3', 'fuente_hidrica', 'fuente_hidrica_display', 'costo_bombeo', 'dias_inundacion', 'lamina_agua_cm', 'estado_drenaje', 'estado_drenaje_display')

class UserGestionSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField(read_only=True)
    nombre_completo_input = serializers.CharField(write_only=True, required=False)
    rol = serializers.CharField(required=False)
    telefono = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'nombre_completo', 'nombre_completo_input', 'email', 'rol', 'telefono', 'is_active', 'password')

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() if (obj.first_name or obj.last_name) else obj.username

    def create(self, validated_data):
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
        representation = super().to_representation(instance)
        if hasattr(instance, 'perfil'):
            representation['rol'] = instance.perfil.rol
            representation['telefono'] = instance.perfil.telefono
        else:
            representation['rol'] = 'SIN_ROL'
            representation['telefono'] = ''
        return representation




