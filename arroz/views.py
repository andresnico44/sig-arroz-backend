from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .serializers import (CustomTokenObtainPairSerializer, RegistroUsuarioSerializer, 
                          FincaSerializer, LoteSerializer, AnalisisSueloSerializer, CicloProductivoSerializer,
                          PreparacionMaquinariaSerializer, SiembraSerializer, SeguimientoFenologicoSerializer,
                          RegistroCostoSerializer, MonitoreoFitosanitarioSerializer, FertilizacionSerializer,
                          AplicacionAgroquimicoSerializer, RegistroHidricoSerializer, UserGestionSerializer, CosechaSerializer, LiquidacionSerializer)
from .models import (Finca, Lote, AnalisisSuelo, CicloProductivo, Perfil, PreparacionMaquinaria, Siembra, 
                     SeguimientoFenologico, RegistroCosto, MonitoreoFitosanitario, Fertilizacion, 
                     AplicacionAgroquimico, RegistroHidrico, Cosecha, Liquidacion)
from .permissions import IsProductorDueñoOrReadOnly, IsProductorOrAdminOnlyForCiclos, IsProductorOrTecnicoOrAdminForAnalisis, IsProductorOrTecnicoOrAdminForLabores, IsAdminUserOnly


# Vista para el Login
class CustomTokenObtainPairView(TokenObtainPairView):
    """Controlador de autenticación mediante JSON Web Tokens (JWT).

    Expide un par de tokens (Access y Refresh) inyectando en el payload
    información personalizada de identidad (nombre real) y rol del usuario.

    Permisos:
        AllowAny: Endpoint público accesible sin credenciales previas.
    """
    serializer_class = CustomTokenObtainPairSerializer

# Vista para el Registro de Usuario
class RegistroUsuarioView(generics.CreateAPIView):
    """Controlador para el autoregistro público de usuarios en la plataforma.

    Permite el registro de nuevos usuarios en el sistema, creando la cuenta
    base en Django y asignándole un perfil operativo inicial (ADMIN, PRODUCTOR, TECNICO).

    Permisos:
        AllowAny: Endpoint público abierto a nuevos aspirantes.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegistroUsuarioSerializer

# Vista para solicitar Recuperación de Contraseña (RF03)
import logging

logger = logging.getLogger('arroz')

from django.db import DatabaseError

class PasswordResetRequestView(APIView):
    """Controlador para la solicitud de restablecimiento de contraseña olvidada.

    Recibe la dirección de correo electrónico del usuario y simula o emite
    un enlace con token temporal de un solo uso para recuperar las credenciales.

    Permisos:
        AllowAny: Endpoint público.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        """Procesa la solicitud de restablecimiento de contraseña.

        Args:
            request (Request): Objeto de solicitud HTTP con el parámetro 'email'.

        Returns:
            Response: Mensaje informativo con código HTTP 200 OK.
        """
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Debe proporcionar un correo electrónico'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.filter(email=email).first()
            if user:
                logger.info("Solicitud de recuperación de contraseña recibida para: %s", email)
                logger.info("Simulación de correo: enlace de recuperación generado para %s (expiración estándar)", email)
                
            return Response({
                'message': 'Si el correo existe en nuestra base de datos, te enviaremos instrucciones para restablecer tu contraseña.'
            }, status=status.HTTP_200_OK)

        except DatabaseError as db_err:
            logger.error("Error de base de datos en PasswordResetRequestView para %s: %s", email, str(db_err), exc_info=True)
            return Response({
                'error': 'Ocurrió un problema de comunicación con el servicio de datos. Intente más tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as ex:
            logger.error("Excepción inesperada en PasswordResetRequestView para %s: %s", email, str(ex), exc_info=True)
            return Response({
                'error': 'Ocurrió un error inesperado al procesar la solicitud. Por favor intente más tarde.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =========================================================================
# SPRINT 2: CONTROLADORES DE GESTIÓN DE CULTIVO (FINCAS Y LOTES)
# =========================================================================

class ProductoresListView(APIView):
    """Controlador para listar los usuarios que poseen el rol de Productor.

    Permite a los administradores obtener el listado depurado de productores para
    la asignación de titularidad de predios y fincas.

    Permisos:
        IsAuthenticated: Requiere sesión activa.
        Restricción de Rol: Exclusivo para usuarios con rol 'ADMIN'.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retorna el listado de productores registrados si el solicitante es Administrador.

        Args:
            request (Request): Objeto de solicitud HTTP.

        Returns:
            Response: Lista JSON de usuarios con rol PRODUCTOR.

        Raises:
            PermissionDenied: Si el usuario solicitante no es ADMIN.
        """
        # Solo el ADMIN debería consultar toda la lista de productores para asignar fincas
        if request.user.perfil.rol != 'ADMIN':
            raise PermissionDenied("Solo los administradores pueden listar a los productores.")
            
        productores = User.objects.filter(perfil__rol='PRODUCTOR').values('id', 'first_name', 'last_name', 'email')
        return Response(list(productores), status=status.HTTP_200_OK)

class FincaViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD para la administración de predios y fincas arroceras.

    Permisos:
        IsAuthenticated: Requiere token JWT válido.
        IsProductorDueñoOrReadOnly: Lectura permitida a Técnicos y Administradores;
            creación, edición y borrado restringido al productor propietario o al Administrador.

    Filtros y Seguridad de Consulta:
        - ADMIN y TECNICO: Visualizan la totalidad de fincas registradas en el sistema.
        - PRODUCTOR: Filtro estricto que solo lista las fincas de su propiedad directa.
    """
    serializer_class = FincaSerializer
    permission_classes = [IsAuthenticated, IsProductorDueñoOrReadOnly]

    def get_queryset(self):
        """Retorna el conjunto de fincas accesible según el rol del usuario autenticado."""
        user = self.request.user
        # Técnicos y Administradores pueden visualizar todas las fincas
        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            return Finca.objects.all().order_by('-id')
        
        # Un PRODUCTOR solo puede listar sus propias fincas (Privacidad de datos)
        return Finca.objects.filter(productor=user).order_by('-id')

    def perform_create(self, serializer):
        """Asigna el productor a la finca creada garantizando aislamiento de datos.

        Si un Administrador envía un 'productor_id', la finca se asigna a dicho usuario;
        de lo contrario, se asigna automáticamente al usuario autenticado.
        """
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
        """Permite a los administradores reasignar el titular de la finca durante la edición."""
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
    """ViewSet CRUD para la gestión de parcelas y lotes productivos.

    Permisos:
        IsAuthenticated: Requiere sesión válida.
        IsProductorDueñoOrReadOnly: Lectura para Técnicos y Admins; modificación solo
            para el productor dueño de la finca madre o Administrador.

    Filtros soportados por Query Parameters:
        - finca_id (int, opcional): Filtra los lotes pertenecientes a una finca específica
          (ej. /api/lotes/?finca_id=3).
    """
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, IsProductorDueñoOrReadOnly]

    def get_queryset(self):
        """Retorna los lotes autorizados, filtrados opcionalmente por finca_id."""
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
        """Valida que el usuario no inserte lotes en fincas de las cuales no es titular.

        Raises:
            PermissionDenied: Si el usuario intenta asociar el lote a una finca ajena.
        """
        finca = serializer.validated_data['finca']
        # Medida de Ciberseguridad Definitiva: 
        # Evitar que un productor malicioso con conocimientos de API inserte un lote en la finca de un competidor
        if finca.productor != self.request.user and self.request.user.perfil.rol != 'ADMIN':
            raise PermissionDenied("Acción denegada: No tienes permiso para agregar lotes a una finca que no es de tu propiedad.")
        
        serializer.save()


class AnalisisSueloViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD para la caracterización química y física de suelos de lotes.

    Permisos:
        IsAuthenticated: Sesión activa obligatoria.
        IsProductorOrTecnicoOrAdminForAnalisis: Admins, Técnicos y Productores dueños
            tienen control completo sobre los análisis de sus predios.

    Filtros soportados por Query Parameters:
        - lote_id (int, opcional): Filtra los análisis correspondientes a un lote específico
          (ej. /api/analisis-suelos/?lote_id=5).
    """
    serializer_class = AnalisisSueloSerializer
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForAnalisis]

    def get_queryset(self):
        """Retorna los análisis de suelo ordenados cronológicamente descendente."""
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
        """Verifica la propiedad del lote antes de persistir el análisis de suelo.

        Raises:
            PermissionDenied: Si un productor intenta registrar un análisis en un lote ajeno.
        """
        lote = serializer.validated_data['lote']
        user = self.request.user

        # Seguridad: El productor solo puede añadir análisis a sus propios lotes
        if user.perfil.rol == 'PRODUCTOR' and lote.finca.productor != user:
            raise PermissionDenied("Acción Denegada: El lote al que intentas agregar el análisis de suelo no te pertenece.")

        serializer.save()


class CicloProductivoViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD para la gestión operativa y financiera de ciclos productivos.

    Permisos:
        IsAuthenticated: Requiere autenticación.
        IsProductorOrAdminOnlyForCiclos: Control integral para ADMIN, TECNICO y el PRODUCTOR
            propietario de la finca asociada al lote.

    Filtros soportados por Query Parameters:
        - lote_id (int, opcional): Filtra ciclos productivos pertenecientes a un lote
          (ej. /api/ciclos/?lote_id=2).

    Acciones Personalizadas:
        - trazabilidad (GET /api/ciclos/{id}/trazabilidad/): Consolida la bitácora integral
          del cultivo (suelo, labores, siembra, fenología, monitoreo, aplicaciones, nutrición,
          riego, costos, cosecha, liquidación y balance de rentabilidad calculado con Decimal).
    """
    serializer_class = CicloProductivoSerializer
    permission_classes = [IsAuthenticated, IsProductorOrAdminOnlyForCiclos]

    def get_queryset(self):
        """Retorna los ciclos productivos autorizados según la pertenencia del lote."""
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
        """Valida la titularidad del lote seleccionado antes de persistir el nuevo ciclo.

        Raises:
            PermissionDenied: Si el lote no pertenece a una finca de su propiedad.
        """
        user = self.request.user
        lote = serializer.validated_data['lote']

        # Validación 1: Verificar la propiedad del lote
        if user.perfil.rol == 'PRODUCTOR' and lote.finca.productor != user:
            raise PermissionDenied("Acción Denegada: El lote seleccionado no pertenece a tus fincas.")

        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def trazabilidad(self, request, pk=None):
        """Consolida la historia agronómica, técnica y balance financiero integral del ciclo.

        Acción personalizada GET /api/ciclos/{id}/trazabilidad/.
        Agrupa y serializa en un único payload:
        - Metadatos de Ciclo, Lote y Finca madre.
        - Análisis de suelo del lote.
        - Labores mecanizadas de preparación de suelos.
        - Datos de siembra y germinación.
        - Línea de tiempo de seguimiento fenológico.
        - Monitoreos fitosanitarios y de plagas/malezas.
        - Aplicaciones agroquímicas realizadas.
        - Planes de fertilización nutricional.
        - Registros y balances de manejo hídrico.
        - Billetera consolidada de costos.
        - Cosecha física en verde y liquidación económica del molino.
        - Resumen financiero de rentabilidad con aritmética Decimal de alta precisión (INSSA-25).

        Args:
            request (Request): Objeto de solicitud HTTP.
            pk (int): Identificador primario del CicloProductivo.

        Returns:
            Response: Estructura JSON consolidada con código HTTP 200 OK.
        """
        ciclo = self.get_object()
        
        # Serializar toda la información asociada
        ciclo_data = CicloProductivoSerializer(ciclo).data
        lote_data = LoteSerializer(ciclo.lote).data
        finca_data = FincaSerializer(ciclo.lote.finca).data
        
        # Análisis de suelo (del lote)
        analisis_suelo = AnalisisSuelo.objects.filter(lote=ciclo.lote).order_by('-fecha_muestreo', '-id')
        analisis_data = AnalisisSueloSerializer(analisis_suelo, many=True).data
        
        # Labores de preparación
        preparaciones = ciclo.preparaciones.all().order_by('fecha', 'id')
        preparaciones_data = PreparacionMaquinariaSerializer(preparaciones, many=True).data
        
        # Siembra
        siembra_data = None
        if hasattr(ciclo, 'siembra') and ciclo.siembra:
            siembra_data = SiembraSerializer(ciclo.siembra).data
            
        # Seguimiento fenológico
        fenologia = ciclo.seguimientos_fenologicos.all().order_by('fecha', 'id')
        fenologia_data = SeguimientoFenologicoSerializer(fenologia, many=True).data
        
        # Monitoreos fitosanitarios
        monitoreos = ciclo.monitoreos.all().order_by('fecha', 'id')
        monitoreos_data = MonitoreoFitosanitarioSerializer(monitoreos, many=True).data
        
        # Aplicaciones de agroquímicos
        aplicaciones = ciclo.aplicaciones_agroquimicos.all().order_by('fecha', 'id')
        aplicaciones_data = AplicacionAgroquimicoSerializer(aplicaciones, many=True).data
        
        # Fertilizaciones
        fertilizaciones = ciclo.fertilizaciones.all().order_by('fecha', 'id')
        fertilizaciones_data = FertilizacionSerializer(fertilizaciones, many=True).data
        
        # Riegos
        riegos = ciclo.riegos.all().order_by('fecha', 'id')
        riegos_data = RegistroHidricoSerializer(riegos, many=True).data
        
        # Costos
        costos = ciclo.costos.all().order_by('fecha', 'id')
        costos_data = RegistroCostoSerializer(costos, many=True).data
        
        # Cosecha
        cosecha_data = None
        if hasattr(ciclo, 'cosecha') and ciclo.cosecha:
            cosecha_data = CosechaSerializer(ciclo.cosecha).data
            
        # Liquidación
        liquidacion_data = None
        if hasattr(ciclo, 'liquidacion') and ciclo.liquidacion:
            liquidacion_data = LiquidacionSerializer(ciclo.liquidacion).data
            
        # Rentabilidad consolidada con aritmética Decimal de alta precisión (INSSA-25)
        from decimal import Decimal
        total_egresos = sum((c.monto_total for c in costos), Decimal('0.00'))
        ingreso_neto = ciclo.liquidacion.ingreso_neto_cop if (hasattr(ciclo, 'liquidacion') and ciclo.liquidacion) else Decimal('0.00')
        balance = ingreso_neto - total_egresos
        area = ciclo.lote.area_hectareas
        
        balance_por_ha = (balance / area) if (area and area > Decimal('0.00')) else Decimal('0.00')
        costo_por_ha = (total_egresos / area) if (area and area > Decimal('0.00')) else Decimal('0.00')
        ingreso_por_ha = (ingreso_neto / area) if (area and area > Decimal('0.00')) else Decimal('0.00')
        
        resumen_financiero = {
            'total_egresos': float(round(total_egresos, 2)),
            'ingreso_neto': float(round(ingreso_neto, 2)),
            'balance_neto': float(round(balance, 2)),
            'costo_por_hectarea': float(round(costo_por_ha, 2)),
            'ingreso_por_hectarea': float(round(ingreso_por_ha, 2)),
            'balance_por_hectarea': float(round(balance_por_ha, 2)),
            'rentable': balance > Decimal('0.00')
        }
        
        return Response({
            'ciclo': ciclo_data,
            'lote': lote_data,
            'finca': finca_data,
            'analisis_suelo': analisis_data,
            'preparaciones': preparaciones_data,
            'siembra': siembra_data,
            'fenologia': fenologia_data,
            'monitoreos': monitoreos_data,
            'aplicaciones': aplicaciones_data,
            'fertilizaciones': fertilizaciones_data,
            'riegos': riegos_data,
            'costos': costos_data,
            'cosecha': cosecha_data,
            'liquidacion': liquidacion_data,
            'resumen_financiero': resumen_financiero
        }, status=status.HTTP_200_OK)

# =========================================================================
# SPRINT 2: OPERACIONES DE ESTABLECIMIENTO DEL CULTIVO
# =========================================================================

class BaseCicloRelacionViewSet(viewsets.ModelViewSet):
    """Clase base para controladores REST vinculados jerárquicamente a un CicloProductivo.

    Provee la lógica reutilizable de autorización, ordenación cronológica y filtros
    multicriterio por Ciclo, Finca o Lote para todas las labores operativas.

    Permisos:
        IsAuthenticated: Requiere sesión activa.
        IsProductorOrTecnicoOrAdminForLabores: Control de acceso para ADMIN, TECNICO
            o PRODUCTOR titular del predio.

    Filtros soportados por Query Parameters:
        - ciclo_id (int, opcional): Filtra registros pertenecientes a un ciclo determinado.
        - finca_id (int, opcional): Filtra registros según la finca de origen.
        - lote_id (int, opcional): Filtra registros pertenecientes a un lote específico.
    """
    permission_classes = [IsAuthenticated, IsProductorOrTecnicoOrAdminForLabores]

    def get_queryset(self):
        """Retorna el queryset del modelo asociado aplicando aislamiento multi-inquilino y filtros."""
        user = self.request.user
        ciclo_id = self.request.query_params.get('ciclo_id', None)
        finca_id = self.request.query_params.get('finca_id', None)
        lote_id = self.request.query_params.get('lote_id', None)
        
        # Obtener el modelo dinámicamente desde el serializer
        model = self.get_serializer_class().Meta.model

        if user.perfil.rol in ['ADMIN', 'TECNICO']:
            queryset = model.objects.all().order_by('-fecha', '-id')
        else:
            queryset = model.objects.filter(ciclo__lote__finca__productor=user).order_by('-fecha', '-id')

        if ciclo_id:
            queryset = queryset.filter(ciclo_id=ciclo_id)
        if finca_id:
            queryset = queryset.filter(ciclo__lote__finca_id=finca_id)
        if lote_id:
            queryset = queryset.filter(ciclo__lote_id=lote_id)

        return queryset

    def perform_create(self, serializer):
        """Verifica que el productor autenticado sea dueño del ciclo antes de persistir la labor.

        Raises:
            PermissionDenied: Si el usuario productor intenta añadir una labor a un ciclo ajeno.
        """
        ciclo = serializer.validated_data['ciclo']
        user = self.request.user

        if user.perfil.rol == 'PRODUCTOR' and ciclo.lote.finca.productor != user:
            raise PermissionDenied("Acción Denegada: El ciclo al que intentas agregar un registro no te pertenece.")

        serializer.save()

class PreparacionMaquinariaViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para labores mecanizadas de preparación de suelos (rastra, zanjeo, nivelación)."""
    serializer_class = PreparacionMaquinariaSerializer

class SiembraViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para el registro del establecimiento inicial de la siembra en campo."""
    serializer_class = SiembraSerializer

class SeguimientoFenologicoViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para la línea de tiempo fenológica, vigor y soporte fotográfico del cultivo."""
    serializer_class = SeguimientoFenologicoSerializer

class RegistroCostoViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para el libro diario de costos y egresos del ciclo productivo."""
    serializer_class = RegistroCostoSerializer

class MonitoreoFitosanitarioViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para reportes de sanidad vegetal, plagas, enfermedades y malezas en lote."""
    serializer_class = MonitoreoFitosanitarioSerializer

class FertilizacionViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para los planes de nutrición vegetal y aportes de fertilizantes."""
    serializer_class = FertilizacionSerializer

class AplicacionAgroquimicoViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para las aplicaciones de plaguicidas y productos fitosanitarios."""
    serializer_class = AplicacionAgroquimicoSerializer

class RegistroHidricoViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para el control de riego, monitoreo de lámina de agua y drenaje."""
    serializer_class = RegistroHidricoSerializer

class CosechaViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para la recolección física del arroz paddy en campo y cálculo de rendimiento."""
    serializer_class = CosechaSerializer

class LiquidacionViewSet(BaseCicloRelacionViewSet):
    """ViewSet CRUD para la liquidación final comercial y financiera en molino."""
    serializer_class = LiquidacionSerializer

class UserGestionViewSet(viewsets.ModelViewSet):
    """ViewSet administrativo exclusivo para la gestión integral de cuentas y roles de usuarios (RBAC).

    Permisos:
        IsAdminUserOnly: Restringido estrictamente a usuarios autenticados con rol 'ADMIN'.
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserGestionSerializer
    permission_classes = [IsAdminUserOnly]

    def destroy(self, request, *args, **kwargs):
        """Impide la auto-eliminación accidental de la propia cuenta del administrador en sesión.

        Args:
            request (Request): Solicitud DELETE.

        Returns:
            Response: 400 Bad Request si intenta borrarse a sí mismo, o 204 No Content en éxito.
        """
        instance = self.get_object()
        if instance == request.user:
            return Response({"error": "No puedes eliminar tu propio usuario administrador."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

class AdminMetricsView(APIView):
    """Controlador que expone métricas y KPIs globales para el tablero de mando del Administrador.

    Computa y consolida el total de usuarios desagregado por rol (Admin, Productor, Técnico),
    total de fincas, lotes, ciclos acumulados y ciclos actualmente activos en ejecución.

    Permisos:
        IsAdminUserOnly: Exclusivo para administradores del sistema.
    """
    permission_classes = [IsAdminUserOnly]

    def get(self, request):
        """Calcula y retorna los indicadores clave de rendimiento del sistema.

        Args:
            request (Request): Solicitud GET.

        Returns:
            Response: Diccionario con estadísticas globales y código HTTP 200 OK.
        """
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
