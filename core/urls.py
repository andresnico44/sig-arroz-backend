from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from arroz.views import CustomTokenObtainPairView, RegistroUsuarioView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Módulo 1: Autenticación JWT (Login)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Módulo 2: Usuarios y Roles (Registro y Recuperación)
    path('api/users/register/', RegistroUsuarioView.as_view(), name='user_register'),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]
