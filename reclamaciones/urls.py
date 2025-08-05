from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet)
router.register(r'marcas', MarcaViewSet)
router.register(r'establecimientos', EstablecimientoViewSet)
router.register(r'libros', LibroReclamacionViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'estados', EstadoReclamacionViewSet)
router.register(r'reclamos', ReclamacionViewSet)
router.register(r'archivos', ArchivoAdjuntoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('reclamaciones/crear-reclamo/', CrearReclamacionConClienteView.as_view()),
    path('reclamaciones/tabla/', ReclamacionesPlanasView.as_view(), name='reclamaciones-tabla'),
    path('reclamaciones/<int:id>/responder/', ProveedorResponderReclamacionView.as_view(), name='reclamo-responder'),
    path('proveedor/perfil/', ProveedorPerfilAPIView.as_view()),
    path('proveedor/cambiar-contrasena/', CambiarContrasenaAPIView.as_view()),
    path('libro/obtener-url/', ObtenerUrlLibroAPIView.as_view()),
    path('libros/<int:pk>/editar-slugs/', EditarSlugsLibroAPIView.as_view(), name='editar-slugs-libro'),
    path('libros/<int:pk>/editar-completo/', EditarLibroCompletoAPIView.as_view(), name='editar-libro-completo'),
    path('perfil/', UsuarioPerfilView.as_view()),
]