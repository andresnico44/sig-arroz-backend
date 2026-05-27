from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from arroz.views import (CustomTokenObtainPairView, RegistroUsuarioView, FincaViewSet, LoteViewSet, 
                         AnalisisSueloViewSet, CicloProductivoViewSet, ProductoresListView,
                         PreparacionMaquinariaViewSet, SiembraViewSet, SeguimientoFenologicoViewSet,
                         RegistroCostoViewSet, MonitoreoFitosanitarioViewSet, FertilizacionViewSet,
                         AplicacionAgroquimicoViewSet, RegistroHidricoViewSet, UserGestionViewSet, AdminMetricsView,
                         CosechaViewSet)

# Enrutador principal del Sprint 2 y 3 para generar automáticamente los endpoints CRUD
router = DefaultRouter()
router.register(r'fincas', FincaViewSet, basename='finca')
router.register(r'lotes', LoteViewSet, basename='lote')
router.register(r'analisis-suelos', AnalisisSueloViewSet, basename='analisissuelo')
router.register(r'ciclos', CicloProductivoViewSet, basename='cicloproductivo')

# Módulo 5, 7, 8: Establecimiento y Fenología (Sprint 2)
router.register(r'preparacion', PreparacionMaquinariaViewSet, basename='preparacion')
router.register(r'siembra', SiembraViewSet, basename='siembra')
router.register(r'fenologia', SeguimientoFenologicoViewSet, basename='fenologia')

# Módulo 9, 10, 13: Sanidad, Nutrición, Riego y Costos (Sprint 3)
router.register(r'costos', RegistroCostoViewSet, basename='costo')
router.register(r'monitoreos', MonitoreoFitosanitarioViewSet, basename='monitoreo')
router.register(r'fertilizaciones', FertilizacionViewSet, basename='fertilizacion')
router.register(r'aplicaciones-agroquimicos', AplicacionAgroquimicoViewSet, basename='aplicacionagroquimico')
router.register(r'riegos', RegistroHidricoViewSet, basename='riego')
router.register(r'cosechas', CosechaViewSet, basename='cosecha')
router.register(r'users-gestion', UserGestionViewSet, basename='users-gestion')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Módulo 1: Autenticación JWT (Login)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Módulo 2: Usuarios y Roles (Registro y Recuperación)
    path('api/users/register/', RegistroUsuarioView.as_view(), name='user_register'),
    path('api/productores/', ProductoresListView.as_view(), name='lista_productores'),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/admin/metrics/', AdminMetricsView.as_view(), name='admin_metrics'),
    
    # Módulo 3: Gestión de Cultivo (Sprint 2 - Fincas y Lotes)
    path('api/', include(router.urls)),
]
