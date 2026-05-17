from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import CustomTokenObtainPairSerializer, RegistroUsuarioSerializer, FincaSerializer, LoteSerializer
from .models import Finca, Lote
from .permissions import IsProductorDueñoOrReadOnly

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

# =========================================================================
# SPRINT 2: CONTROLADORES DE GESTIÓN DE CULTIVO (FINCAS Y LOTES)
# =========================================================================

class FincaViewSet(viewsets.ModelViewSet):
    serializer_class = FincaSerializer
    permission_classes = [IsAuthenticated, IsProductorDueñoOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Técnicos y Administradores pueden visualizar todas las fincas
        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            return Finca.objects.all().order_by('-id')
        
        # Un PRODUCTOR solo puede listar sus propias fincas (Privacidad de datos)
        return Finca.objects.filter(productor=user).order_by('-id')

    def perform_create(self, serializer):
        # Asignación segura del dueño: Se inyecta el productor desde el Token JWT
        serializer.save(productor=self.request.user)


class LoteViewSet(viewsets.ModelViewSet):
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, IsProductorDueñoOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Soporte para filtrar lotes visualizando una finca específica en el frontend
        finca_id = self.request.query_params.get('finca_id', None)
        
        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = Lote.objects.all().order_by('-id')
        else:
            # Privacidad: El PRODUCTOR solo ve los lotes de las fincas que le pertenecen
            queryset = Lote.objects.filter(finca__productor=user).order_by('-id')
            
        if finca_id:
            queryset = queryset.filter(finca_id=finca_id)
            
        return queryset

    def perform_create(self, serializer):
        finca = serializer.validated_data['finca']
        # Medida de Ciberseguridad Definitiva: 
        # Evitar que un productor malicioso con conocimientos de API inserte un lote en la finca de un competidor
        if finca.productor != self.request.user and self.request.user.perfil.rol != 'ADMIN':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción denegada: No tienes permiso para agregar lotes a una finca que no es de tu propiedad.")
        
        serializer.save()
