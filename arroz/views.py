from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import (CustomTokenObtainPairSerializer, RegistroUsuarioSerializer, 
                          FincaSerializer, LoteSerializer, AnalisisSueloSerializer, CicloProductivoSerializer,
                          PreparacionMaquinariaSerializer, SiembraSerializer, SeguimientoFenologicoSerializer,
                          RegistroCostoSerializer, MonitoreoFitosanitarioSerializer, FertilizacionSerializer,
                          AplicacionAgroquimicoSerializer, RegistroHidricoSerializer, UserGestionSerializer, CosechaSerializer)
from .models import (Finca, Lote, AnalisisSuelo, CicloProductivo, Perfil, PreparacionMaquinaria, Siembra, 
                     SeguimientoFenologico, RegistroCosto, MonitoreoFitosanitario, Fertilizacion, 
                     AplicacionAgroquimico, RegistroHidrico, Cosecha)
from .permissions import IsProductorDueñoOrReadOnly, IsProductorOrAdminOnlyForCiclos, IsProductorOrTecnicoOrAdminForAnalisis, IsProductorOrTecnicoOrAdminForLabores, IsAdminUserOnly

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

    def perform_update(self, serializer):
        user = self.request.user
        productor_id = self.request.data.get('productor_id', None)
        
        # Si es Administrador y selecciona un Productor desde el Frontend
        if user.perfil.rol == 'ADMIN' and productor_id:
            try:
                productor_real = User.objects.get(id=productor_id, perfil__rol='PRODUCTOR')
                serializer.save(productor=productor_real)
                return
            except User.DoesNotExist:
                pass # Si falla, se actualizará conservando el actual
                
        serializer.save()


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
            queryset = AnalisisSuelo.objects.all().order_by('-fecha_muestreo', '-id')
        else:
            # Privacidad estricta: Solo ver análisis de lotes que pertenecen al productor
            queryset = AnalisisSuelo.objects.filter(lote__finca__productor=user).order_by('-fecha_muestreo', '-id')

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

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

class PreparacionMaquinariaViewSet(viewsets.ModelViewSet):
    serializer_class = PreparacionMaquinariaSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = PreparacionMaquinaria.objects.all().order_by('-fecha', '-id')
        else:
            # Privacidad: El productor solo ve labores de sus propios ciclos
            queryset = PreparacionMaquinaria.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        # Seguridad: El productor solo puede añadir labores a sus propios ciclos
        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas agregar labores no te pertenece.")

        serializer.save()


class SiembraViewSet(viewsets.ModelViewSet):
    serializer_class = SiembraSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = Siembra.objects.all().order_by('-fecha', '-id')
        else:
            queryset = Siembra.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas agregar siembra no te pertenece.")

        serializer.save()


class SeguimientoFenologicoViewSet(viewsets.ModelViewSet):
    serializer_class = SeguimientoFenologicoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = SeguimientoFenologico.objects.all().order_by('-fecha', '-id')
        else:
            queryset = SeguimientoFenologico.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas agregar fenología no te pertenece.")

        serializer.save()


# =========================================================================
# SPRINT 3: GESTIÓN DE SANIDAD, NUTRICIÓN, MANEJO HÍDRICO Y BILLETERA
# =========================================================================

class RegistroCostoViewSet(viewsets.ModelViewSet):
    serializer_class = RegistroCostoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = RegistroCosto.objects.all().order_by('-fecha', '-id')
        else:
            queryset = RegistroCosto.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas registrar un costo no te pertenece.")

        serializer.save()


class MonitoreoFitosanitarioViewSet(viewsets.ModelViewSet):
    serializer_class = MonitoreoFitosanitarioSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = MonitoreoFitosanitario.objects.all().order_by('-fecha', '-id')
        else:
            queryset = MonitoreoFitosanitario.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas agregar monitoreo fitosanitario no te pertenece.")

        serializer.save()


class FertilizacionViewSet(viewsets.ModelViewSet):
    serializer_class = FertilizacionSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = Fertilizacion.objects.all().order_by('-fecha', '-id')
        else:
            queryset = Fertilizacion.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas registrar fertilización no te pertenece.")

        serializer.save()


class AplicacionAgroquimicoViewSet(viewsets.ModelViewSet):
    serializer_class = AplicacionAgroquimicoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = AplicacionAgroquimico.objects.all().order_by('-fecha', '-id')
        else:
            queryset = AplicacionAgroquimico.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas registrar aplicación de agroquímicos no te pertenece.")

        serializer.save()


class RegistroHidricoViewSet(viewsets.ModelViewSet):
    serializer_class = RegistroHidricoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = RegistroHidrico.objects.all().order_by('-fecha', '-id')
        else:
            queryset = RegistroHidrico.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas registrar riego no te pertenece.")

        serializer.save()

class CosechaViewSet(viewsets.ModelViewSet):
    serializer_class = CosechaSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)
        finca_id = self.request.query_params.get('finca_id', None)
        lote_id = self.request.query_params.get('lote_id', None)

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = Cosecha.objects.all().order_by('-fecha', '-id')
        else:
            queryset = Cosecha.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)
        if finca_id:
            queryset = queryset.filter(ciclo__lote__finca_id=finca_id)
        if lote_id:
            queryset = queryset.filter(ciclo__lote_id=lote_id)

        return queryset

    def perform_create(self, serializer):
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas registrar cosecha no te pertenece.")

        serializer.save()

class UserGestionViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserGestionSerializer
    permission_classes = [IsAdminUserOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response({"error": "No puedes eliminar tu propio usuario administrador."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

class AdminMetricsView(APIView):
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        total_usuarios = User.objects.count()
        admins = Perfil.objects.filter(rol='ADMIN').count()
        productores = Perfil.objects.filter(rol='PRODUCTOR').count()
        tecnicos = Perfil.objects.filter(rol='TECNICO').count()
        
        total_fincas = Finca.objects.count()
        total_lotes = Lote.objects.count()
        total_ciclos = CicloProductivo.objects.count()
        ciclos_activos = CicloProductivo.objects.filter(estado='EJECUCION').count()
        
        return Response({
            'total_usuarios': total_usuarios,
            'roles': {
                'ADMIN': admins,
                'PRODUCTOR': productores,
                'TECNICO': tecnicos
            },
            'total_fincas': total_fincas,
            'total_lotes': total_lotes,
            'total_ciclos': total_ciclos,
            'ciclos_activos': ciclos_activos
        }, status=status.HTTP_200_OK)

