from rest_framework import permissions

class IsProductorDueñoOrReadOnly(permissions.BasePermission):
    """
    Permite acceso de lectura a los Técnicos y Administradores.
    Pero sólo permite crear, editar o eliminar a los Productores que son dueños del objeto.
    """

    def has_permission(self, request, view):
        # Todos los autenticados pueden intentar (filtraremos la lista de visión en get_queryset)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Los administradores tienen el control absoluto de todo
        if request.user.perfil.rol == 'ADMIN':
            return True
            
        # Si la petición es de solo lectura (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Los técnicos y los dueños pueden leer sin problema
            return True
            
        # Si es escritura (PUT, PATCH, DELETE), debe ser estrictamente el dueño Productor
        if hasattr(obj, 'productor'): # Para la entidad Finca
            return obj.productor == request.user
        elif hasattr(obj, 'finca'): # Para la entidad Lote
            return obj.finca.productor == request.user
            
        return False


class IsProductorOrAdminOnlyForCiclos(permissions.BasePermission):
    """
    Matriz de Permisos (Módulo 2 - Ciclos Productivos):
    - ADMIN, PRODUCTOR (dueño) y TECNICO pueden hacer CRUD completo.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.perfil.rol in ['ADMIN', 'TECNICO']:
            return True
            
        # Para escribir (Crear, Editar, Borrar), debe ser Productor y dueño de la finca
        if request.user.perfil.rol == 'PRODUCTOR':
            return obj.lote.finca.productor == request.user
            
        return False


class IsProductorOrTecnicoOrAdminForAnalisis(permissions.BasePermission):
    """
    Matriz de Permisos (Análisis de Suelos):
    - ADMIN, PRODUCTOR (dueño) y TECNICO pueden hacer CRUD completo.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.perfil.rol in ['ADMIN', 'TECNICO']:
            return True
            
        if request.user.perfil.rol == 'PRODUCTOR':
            return obj.lote.finca.productor == request.user
            
        return False

class IsProductorOrTecnicoOrAdminForLabores(permissions.BasePermission):
    """
    Matriz de Permisos (Sprint 2 - Labores, Siembra, Fenología):
    - ADMIN, PRODUCTOR (dueño) y TECNICO pueden hacer CRUD completo.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.perfil.rol in ['ADMIN', 'TECNICO']:
            return True
            
        if request.user.perfil.rol == 'PRODUCTOR':
            return obj.ciclo.lote.finca.productor == request.user
            
        return False

class IsAdminUserOnly(permissions.BasePermission):
    """
    Sólo permite el acceso a usuarios con el rol ADMIN.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.perfil.rol == 'ADMIN'



