from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import (CustomTokenObtainPairSerializer, RegistroUsuarioSerializer, 
                          FincaSerializer, LoteSerializer, AnalisisSueloSerializer, CicloProductivoSerializer)
from .models import Finca, Lote, AnalisisSuelo, CicloProductivo
from .permissions import IsProductorDueñoOrReadOnly, IsProductorOrAdminOnlyForCiclos, IsProductorOrTecnicoOrAdminForAnalisis

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

class ProductoresListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Solo el ADMIN debería consultar toda la lista de productores para asignar fincas
        if request.user.perfil.rol != 'ADMIN':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo los administradores pueden listar a los productores.")
            
        productores = User.objects.filter(perfil__rol='PRODUCTOR').values('id', 'first_name', 'last_name', 'email')
        return Response(list(productores), status=status.HTTP_200_OK)

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
        user = self.request.user
        productor_id = self.request.data.get('productor_id', None)
        
        # Si es Administrador y selecciona un Productor desde el Frontend
        if user.perfil.rol == 'ADMIN' and productor_id:
            try:
                productor_real = User.objects.get(id=productor_id, perfil__rol='PRODUCTOR')
                serializer.save(productor=productor_real)
                return
            except User.DoesNotExist:
                pass # Si falla, caerá al comportamiento por defecto abajo
                
        # Comportamiento por defecto (El Productor se la asigna a sí mismo)
        serializer.save(productor=user)


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


class AnalisisSueloViewSet(viewsets.ModelViewSet):
    serializer_class = AnalisisSueloSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForAnalisis]

    def get_queryset(self):
        user = self.request.user
        lote_id = self.request.query_params.get('lote_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = AnalisisSuelo.objects.all().order_by('-fecha_muestreo')
        else:
            # Privacidad estricta: Solo ver análisis de lotes que pertenecen al productor
            queryset = AnalisisSuelo.objects.filter(lote__finca__productor=user).order_by('-fecha_muestreo')

        if lote_id:
            queryset = queryset.filter(lote_id=lote_id)

        return queryset

    def perform_create(self, serializer):
        lote = serializer.validated_data['lote']
        user = self.request.user

        # Seguridad: El productor solo puede añadir análisis a sus propios lotes
        if user.perfil.rol == 'PRODUCTOR' and lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El lote al que intentas agregar el análisis de suelo no te pertenece.")

        serializer.save()


class CicloProductivoViewSet(viewsets.ModelViewSet):
    serializer_class = CicloProductivoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrAdminOnlyForCiclos]

    def get_queryset(self):
        user = self.request.user
        lote_id = self.request.query_params.get('lote_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = CicloProductivo.objects.all().order_by('-id')
        else:
            # Privacidad: El productor solo ve ciclos de sus propios lotes
            queryset = CicloProductivo.objects.filter(lote__finca__productor=user).order_by('-id')

        if lote_id:
            queryset = queryset.filter(lote_id=lote_id)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        lote = serializer.validated_data['lote']

        # Validación 1: Verificar el rol del usuario (Matriz de Permisos)
        if user.perfil.rol == 'TECNICO':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Permiso Denegado: Los asesores técnicos no tienen autorización para iniciar ciclos productivos.")

        # Validación 2: Verificar la propiedad del lote
        if user.perfil.rol == 'PRODUCTOR' and lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El lote seleccionado no pertenece a tus fincas.")

        serializer.save()
