from rest_framework import viewsets, status, generics, permissions
from .models import *
from .serializers import *
from rest_framework.generics import UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


#Crear las vistas
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class ProveedorPerfilAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'proveedor'):
            return Response({'error': 'El usuario no tiene proveedor asignado.'}, status=400)
        serializer = ProveedorUpdateSerializer(request.user.proveedor)
        return Response(serializer.data)

    def put(self, request):
        if not hasattr(request.user, 'proveedor'):
            return Response({'error': 'El usuario no tiene proveedor asignado.'}, status=400)
        serializer = ProveedorUpdateSerializer(request.user.proveedor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class CambiarContrasenaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        actual = request.data.get('actual')
        nueva = request.data.get('nueva')
        confirmar = request.data.get('confirmar')

        if not request.user.check_password(actual):
            return Response({"error": "La contraseña actual es incorrecta."}, status=400)

        if nueva != confirmar:
            return Response({"error": "Las contraseñas no coinciden."}, status=400)

        try:
            validate_password(nueva, request.user)
        except Exception as e:
            return Response({"error": list(e)}, status=400)

        request.user.set_password(nueva)
        request.user.save()

        return Response({"mensaje": "Contraseña actualizada correctamente."})
    
class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer

class EstablecimientoViewSet(viewsets.ModelViewSet):
    queryset = Establecimiento.objects.all()
    serializer_class = EstablecimientoSerializer

class LibroReclamacionViewSet(viewsets.ModelViewSet):
    queryset = LibroReclamacion.objects.all()
    serializer_class = LibroReclamacionSerializer
    
    def get_queryset(self):
        user = self.request.user

        # Si es superusuario, puede ver todos los libros
        if user.is_superuser:
            return LibroReclamacion.objects.all()

        # Si es proveedor, solo los libros de su marca
        if hasattr(user, 'proveedor'):
            return LibroReclamacion.objects.filter(
                establecimiento__marca__proveedor=user.proveedor
            )

        # Si no tiene proveedor asociado, no ve nada
        return LibroReclamacion.objects.none()

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
class EstadoReclamacionViewSet(viewsets.ModelViewSet):
    queryset = EstadoReclamacion.objects.all()
    serializer_class = EstadoReclamacionSerializer

class ReclamacionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Reclamacion.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReclamacionDetalleProveedorSerializer
        return ReclamacionPlanoSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Reclamacion.objects.all()
        return Reclamacion.objects.filter(libro__establecimiento__marca__proveedor=user.proveedor)

class ArchivoAdjuntoViewSet(viewsets.ModelViewSet):
    queryset = ArchivoAdjunto.objects.all()
    serializer_class = ArchivoAdjuntoSerializer
    
class CrearReclamacionConClienteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        print(" Payload recibido del front:", request.data)
        
        serializer = ReclamacionConClienteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("⚠️ Errores de validación:", serializer.errors)  # 👈 Aquí se ve el error
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UsuarioPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UsuarioPerfilSerializer(user)  # Usamos el serializer anidado que definimos antes
        return Response(serializer.data)
    
#Listar reclamaciones ,incluye clientes y establecimientos
class ReclamacionesPlanasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_superuser:
            reclamaciones = Reclamacion.objects.select_related(
                'estado', 'cliente', 'libro__establecimiento'
            ).all()
        else:
            reclamaciones = Reclamacion.objects.select_related(
                'estado', 'cliente', 'libro__establecimiento'
            ).filter(libro__establecimiento__marca__proveedor=user.proveedor)

        serializer = ReclamacionPlanoSerializer(reclamaciones, many=True)
        return Response(serializer.data)
    
class ProveedorResponderReclamacionView(UpdateAPIView):
    queryset = Reclamacion.objects.all()
    serializer_class = ReclamacionRespuestaSerializer
    lookup_field = 'id'
    

class ObtenerUrlLibroAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, libro_slug, establecimiento_slug):
        user = request.user

        try:    
            libro = LibroReclamacion.objects.get(
                libro_slug=libro_slug,
                establecimiento_slug=establecimiento_slug
            )

            # Verifica que el proveedor sea dueño del libro
            if libro.establecimiento.marca.proveedor != user.proveedor:
                return Response({'detail': 'No tienes permiso para acceder a este libro.'}, status=403)

            return Response({'url': libro.get_url()})

        except LibroReclamacion.DoesNotExist:
            return Response({'detail': 'Libro no encontrado.'}, status=404)
        
class EditarSlugsLibroAPIView(UpdateAPIView):
    queryset = LibroReclamacion.objects.all()
    serializer_class = EditarSlugsLibroSerializer
    permission_classes = [IsAuthenticated]  # cambia según el control de acceso que uses

    def get_queryset(self):
        """
        Filtra los libros para que el proveedor solo pueda editar los suyos.
        """
        user = self.request.user
        if hasattr(user, 'proveedor'):
            return LibroReclamacion.objects.filter(establecimiento__marca__proveedor=user.proveedor)
        return LibroReclamacion.objects.none()
    

class EditarLibroCompletoAPIView(UpdateAPIView):
    queryset = LibroReclamacion.objects.all()
    serializer_class = LibroCompletoUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'proveedor'):
            return LibroReclamacion.objects.filter(
                establecimiento__marca__proveedor=user.proveedor
            )
        return LibroReclamacion.objects.none()