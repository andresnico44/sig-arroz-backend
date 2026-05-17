from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from arroz.views import CustomTokenObtainPairView, RegistroUsuarioView, FincaViewSet, LoteViewSet

# Enrutador principal del Sprint 2 para generar automáticamente los endpoints CRUD
router = DefaultRouter()
router.register(r'fincas', FincaViewSet, basename='finca')
router.register(r'lotes', LoteViewSet, basename='lote')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Módulo 1: Autenticación JWT (Login)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Módulo 2: Usuarios y Roles (Registro y Recuperación)
    path('api/users/register/', RegistroUsuarioView.as_view(), name='user_register'),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    
    # Módulo 3: Gestión de Cultivo (Sprint 2 - Fincas y Lotes)
    path('api/', include(router.urls)),
]
