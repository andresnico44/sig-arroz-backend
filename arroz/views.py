from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import CustomTokenObtainPairSerializer, RegistroUsuarioSerializer

# Vista para el Login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Vista para el Registro de Usuario
class RegistroUsuarioView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegistroUsuarioSerializer

# Vista para solicitar Recuperación de Contraseña (RF03)
class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Debe proporcionar un correo electrónico'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(email=email).first()
        if user:
            # En producción, usaríamos send_mail de Django
            print("\n" + "="*50)
            print("✉️ SIMULACIÓN DE ENVÍO DE CORREO")
            print(f"Destinatario: {email}")
            print("Asunto: Recuperación de contraseña SIG-ARROZ")
            print("Cuerpo: Hemos recibido una solicitud para restablecer tu contraseña.")
            print("Haz clic en el siguiente enlace para crear una nueva:")
            print(f"http://localhost:5173/reset-password?token=fake-jwt-token-12345")
            print("="*50 + "\n")
            
        return Response({
            'message': 'Si el correo existe en nuestra base de datos, te enviaremos instrucciones para restablecer tu contraseña.'
        }, status=status.HTTP_200_OK)
