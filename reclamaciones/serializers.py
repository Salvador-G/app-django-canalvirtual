from rest_framework import serializers
from .models import *
from usuarios.models import Usuario


# Proveedor
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

# Para que el proveedor pueda editar sus datos desde el panel
class ProveedorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['razon_social', 'ruc', 'direccion', 'telefono', 'email_contacto']
        
# Marca incluye proveedor
class MarcaSerializer(serializers.ModelSerializer):
    proveedor = ProveedorSerializer(read_only=True)
    
    class Meta:
        model = Marca
        fields = '__all__'

# Establecimiento incluye marca (y su proveedor)
class EstablecimientoSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer(read_only=True)

    class Meta:
        model = Establecimiento
        fields = '__all__'

# LibroReclamacion incluye establecimiento (y su marca)
class LibroReclamacionSerializer(serializers.ModelSerializer):
    establecimiento = EstablecimientoSerializer(read_only=True)
    url_publica = serializers.SerializerMethodField()

    def get_url_publica(self, obj):
        # Asegúrate de que los slugs existan
        return f"https://localhost:5173/reclamar/{obj.libro_slug}/{obj.establecimiento_slug}/"
    
    class Meta:
        model = LibroReclamacion
        fields = '__all__'

# RepresentanteLegal (plano, por si quieres anidar desde Cliente)
class RepresentanteLegalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepresentanteLegal
        fields = '__all__'

# Cliente incluye sus representantes
class ClienteSerializer(serializers.ModelSerializer):
    representantes = RepresentanteLegalSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'

class EstadoReclamacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoReclamacion
        fields = ['id', 'nombre', 'descripcion']
        
class ReclamacionConClienteSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer()

    estado = EstadoReclamacionSerializer(read_only=True)
    estado_id = serializers.PrimaryKeyRelatedField(
        queryset=EstadoReclamacion.objects.all(), source='estado', write_only=True
    )

    libro = serializers.CharField(write_only=True)  # Código del libro
    libro_obj = LibroReclamacionSerializer(read_only=True, source='libro')  # opcional para respuesta

    class Meta:
        model = Reclamacion
        fields = '__all__'
        extra_kwargs = {
            'libro': {'write_only': True},
        }

    def validate_libro(self, value):
        try:
            # Busca el libro activo por su código
            libro = LibroReclamacion.objects.get(codigo_libro=value, estado="activo")
            return libro
        except LibroReclamacion.DoesNotExist:
            raise serializers.ValidationError("No existe un libro activo con ese código.")

    def create(self, validated_data):
        cliente_data = validated_data.pop('cliente')
        libro_obj = validated_data.pop('libro')  # validado como objeto en `validate_libro`

        cliente = Cliente.objects.create(**cliente_data)
        reclamacion = Reclamacion.objects.create(
            cliente=cliente,
            libro=libro_obj,
            **validated_data
        )
        return reclamacion
    
class ReclamacionDetalleProveedorSerializer(serializers.ModelSerializer):
    tipo = serializers.CharField(source='get_tipo_display')
    estado = serializers.CharField(source='estado.nombre')
    fecha = serializers.DateTimeField(format='%Y-%m-%d')
    reclamante = serializers.SerializerMethodField()
    establecimiento = serializers.SerializerMethodField()
    proveedor = serializers.SerializerMethodField()

    class Meta:
        model = Reclamacion
        fields = [
            'id',
            'libro',
            'cliente',
            'fecha',
            'codigo_hoja',
            'tipo',
            'tipo_bien',
            'descripcion_bien',
            'monto_reclamado',
            'detalle',
            'solicitud_cliente',
            'respuesta',
            'estado',
            'reclamante',         # <-- Agregado
            'establecimiento',    # <-- Agregado
            'proveedor'           # <-- Agregado
        ]

    def get_reclamante(self, obj):
        if obj.cliente:
            return {
                "nombre": obj.cliente.nombre,
                "documento_identidad": obj.cliente.documento_identidad,
                "email": obj.cliente.email,
            }
        return None

    def get_establecimiento(self, obj):
        est = obj.libro.establecimiento
        return {
            "nombre": est.nombre,
            "direccion": est.direccion,
            "codigo_libro": obj.libro.codigo
        }

    def get_proveedor(self, obj):
        proveedor = obj.libro.establecimiento.marca.proveedor
        return {
            "razon_social": proveedor.razon_social,
            "ruc": proveedor.ruc
        }
        
# Reclamacion anidada con cliente y libro
class ReclamacionDetalleSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    libro = LibroReclamacionSerializer(read_only=True)
    estado = EstadoReclamacionSerializer(read_only=True)

    class Meta:
        model = Reclamacion
        fields = '__all__'

# Archivos adjuntos (puedes incluir reclamación si lo necesitas)
class ArchivoAdjuntoSerializer(serializers.ModelSerializer):
    reclamacion = ReclamacionDetalleSerializer(read_only=True)

    class Meta:
        model = ArchivoAdjunto
        fields = '__all__'
        
# Info anidada usuario
class UsuarioPerfilSerializer(serializers.ModelSerializer):
    proveedor = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'proveedor']

    def get_proveedor(self, obj):
        proveedor = getattr(obj, 'proveedor', None)
        if not proveedor:
            return None

        marcas = proveedor.marcas.all()

        return {
            'id': proveedor.id,
            'razon_social': proveedor.razon_social,
            'ruc': proveedor.ruc,
            'direccion': proveedor.direccion,
            'telefono': proveedor.telefono,
            'email_contacto': proveedor.email_contacto,
            'marcas': [
                {
                    'id': marca.id,
                    'nombre': marca.nombre,
                    'descripcion': marca.descripcion,
                    'establecimientos': [
                        {
                            'id': est.id,
                            'nombre': est.nombre,
                            'direccion': est.direccion,
                            'telefono': est.telefono,
                            'email_contacto': est.email_contacto,
                            'es_online': est.es_online,
                            'libros': [
                                {
                                    'id': libro.id,
                                    'codigo': libro.codigo,
                                    'estado': libro.estado,
                                    'reclamaciones_count': libro.reclamaciones.count(),
                                    'reclamaciones': [
                                        {
                                            'id': reclamo.id,
                                            'codigo_hoja': reclamo.codigo_hoja,
                                            'fecha': reclamo.fecha,
                                            'tipo': reclamo.tipo,
                                            'tipo_bien': reclamo.tipo_bien,
                                            'detalle': reclamo.detalle,
                                            'cliente': {
                                                'id': reclamo.cliente.id,
                                                'nombre': reclamo.cliente.nombre,
                                                'tipo_doc': reclamo.cliente.tipo_doc,
                                                'documento_identidad': reclamo.cliente.documento_identidad,
                                                'email': reclamo.cliente.email,
                                                'telefono': reclamo.cliente.telefono,
                                                'fecha_nacimiento': reclamo.cliente.fecha_nacimiento
                                            }
                                        }
                                        for reclamo in libro.reclamaciones.all()
                                    ]
                                }
                                for libro in est.libros.all()
                            ]
                        }
                        for est in marca.establecimientos.all()
                    ]
                }
                for marca in marcas
            ]
        }
        
#lista completa de raclamos por proveedor
class ReclamacionPlanoSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='estado.nombre', read_only=True)
    establecimiento = serializers.CharField(source='libro.establecimiento.nombre', read_only=True)
    detalle_reclamacion = serializers.CharField(source='detalle', read_only=True)
    fecha = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    reclamante = serializers.SerializerMethodField()
    tipo = serializers.SerializerMethodField()

    class Meta:
        model = Reclamacion
        fields = [
            'id',
            'codigo_hoja',
            'tipo',
            'estado',
            'fecha',
            'detalle_reclamacion',
            'establecimiento',
            'reclamante'
        ]

    def get_reclamante(self, obj):
        if obj.cliente:
            return {
                "nombre": obj.cliente.nombre,
                "documento_identidad": obj.cliente.documento_identidad,
                "email": obj.cliente.email
            }
        return "Anónimo"
    
    def get_tipo(self, obj):
        return obj.get_tipo_display()
    
class ReclamacionRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reclamacion
        fields = ['respuesta']

    def update(self, instance, validated_data):
        instance.respuesta = validated_data.get('respuesta', instance.respuesta)

        # Cambiar el estado automáticamente a "Respondido" si existe
        estado_respondido = EstadoReclamacion.objects.filter(nombre__iexact='Respondido').first()
        if estado_respondido:
            instance.estado = estado_respondido

        instance.save()
        return instance


#funcion reutilizable para validar libro
def validar_slugs_unicos(libro_instance, libro_slug, establecimiento_slug):
    if LibroReclamacion.objects.exclude(pk=libro_instance.pk).filter(
        libro_slug=libro_slug,
        establecimiento_slug=establecimiento_slug
    ).exists():
        raise serializers.ValidationError("Ya existe un libro con ese alias para este proveedor.")

#Serializer que edita estrictamente los slug "establecimiento" y "libro"
class EditarSlugsLibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroReclamacion
        fields = ['libro_slug', 'establecimiento_slug']

    def validate(self, data):
        libro_slug = data.get('libro_slug', self.instance.libro_slug)
        establecimiento_slug = data.get('establecimiento_slug', self.instance.establecimiento_slug)
        validar_slugs_unicos(self.instance, libro_slug, establecimiento_slug)
        return data

#Serializers anidados para editar   
# Serializer para la marca (anidado dentro de Establecimiento)
class MarcaInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre']

# Serializer para el establecimiento (anidado dentro de LibroReclamacion)
class EstablecimientoInlineSerializer(serializers.ModelSerializer):
    marca = MarcaInlineSerializer()

    class Meta:
        model = Establecimiento
        fields = [
            'nombre', 'direccion', 'distrito', 'provincia', 'departamento',
            'enlace_acceso', 'telefono', 'email_contacto', 'es_online', 'marca'
        ]

# Serializer principal para actualizar el libro completo
class LibroCompletoUpdateSerializer(serializers.ModelSerializer):
    establecimiento = EstablecimientoInlineSerializer()

    class Meta:
        model = LibroReclamacion
        fields = ['libro_slug', 'establecimiento_slug', 'establecimiento']

    def validate(self, data):
        libro_slug = data.get('libro_slug', self.instance.libro_slug)
        establecimiento_slug = data.get('establecimiento_slug', self.instance.establecimiento_slug)
        validar_slugs_unicos(self.instance, libro_slug, establecimiento_slug)
        return data

    def update(self, instance, validated_data):
        print("Datos validados recibidos:", validated_data)

        establecimiento_data = validated_data.pop('establecimiento', None)

        # Actualiza los campos del libro
        for attr, value in validated_data.items():
            print(f"Actualizando {attr} de LibroReclamacion a {value}")
            setattr(instance, attr, value)
        instance.save()

        # Actualiza el establecimiento si se recibió
        if establecimiento_data:
            print("Datos del establecimiento:", establecimiento_data)
            establecimiento = instance.establecimiento

            marca_data = establecimiento_data.pop('marca', None)

            for attr, value in establecimiento_data.items():
                print(f"Actualizando {attr} de Establecimiento a {value}")
                setattr(establecimiento, attr, value)
            establecimiento.save()

            # Actualiza la marca si viene
            if marca_data:
                print("Datos de marca:", marca_data)
                marca = establecimiento.marca
                for attr, value in marca_data.items():
                    print(f"Actualizando {attr} de Marca a {value}")
                    setattr(marca, attr, value)
                marca.save()
            else:
                print("No se recibió datos de marca.")
        else:
            print("No se recibió datos de establecimiento.")

        return instance