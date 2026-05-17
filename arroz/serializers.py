from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Perfil
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
