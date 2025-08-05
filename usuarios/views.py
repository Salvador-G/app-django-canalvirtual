from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reclamaciones.serializers import ProveedorSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, serializers

User = get_user_model()
#Crear las vistas
# Serializador para representar al "cliente" (usuario)
class UsuarioSerializer(serializers.ModelSerializer):
    proveedor = ProveedorSerializer(read_only=True)  # 👈 incluir el proveedor completo
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'proveedor', 'role', 'created_at', 'is_active']

# POST /api/login
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(request.data)
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Correo no registrado."}, status=status.HTTP_401_UNAUTHORIZED)

        # Autenticar con username=email
        user = authenticate(username=email, password=password)
        if user is not None:
            if not user.is_active:
                return Response({"error": "Usuario inactivo."}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'role': getattr(user, 'role', None),
                'proveedor': ProveedorSerializer(user.proveedor).data if user.proveedor else None,
            })

        return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

# GET /api/Usuario
class UsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
    
# Usuarios por ID
class UsuarioPorIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        if not request.user.is_superuser:
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = User.objects.get(pk=id)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
