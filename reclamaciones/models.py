from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid

# Create your models here.
class Proveedor(models.Model):
    razon_social = models.CharField(max_length=100)
    ruc = models.CharField(max_length=11, unique=True)
    domicilio_fiscal = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    email_contacto = models.EmailField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.razon_social

class Marca(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='marcas')
    nombre_marca = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_marca

class Establecimiento(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='establecimientos')
    nombre_establecimiento = models.CharField(max_length=100)
    direccion_establecimeinto = models.CharField(max_length=150, null=True, blank=True)  # ← opcional si es online
    distrito = models.CharField(max_length=50, null=True, blank=True)
    provincia = models.CharField(max_length=50, null=True, blank=True)
    departamento = models.CharField(max_length=50, null=True, blank=True)
    enlace_acceso = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20)
    email_contacto = models.EmailField(max_length=100)
    es_online = models.BooleanField(default=False)  # ← nuevo campo
    created_at = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def clean(self):
        # Si es online, no debe haber dirección física
        if self.es_online:
            if any([self.direccion_establecimeinto, self.distrito, self.provincia, self.departamento]):
                raise ValidationError("Un establecimiento online no debe tener dirección, distrito, provincia ni departamento.")
        else:
            # Si es físico, no debe haber enlace de acceso
            if self.enlace_acceso:
                raise ValidationError("Un establecimiento físico no debe tener enlace de acceso.")

    def __str__(self):
        return self.nombre_establecimiento
    
class LibroReclamacion(models.Model):
    establecimiento = models.ForeignKey(
        Establecimiento, on_delete=models.SET_NULL, null=True, blank=True, related_name='libros'
    )
    libro_slug = models.SlugField(blank=True)
    establecimiento_slug = models.SlugField()

    codigo_libro = models.CharField(max_length=50)
    estado = models.CharField(max_length=20)  # activo, inactivo, cerrado
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('libro_slug', 'establecimiento_slug')  # URL única

    def save(self, *args, **kwargs):
        if not self.libro_slug:
            self.libro_slug = slugify(self.codigo_libro)
        super().save(*args, **kwargs)

    def get_url(self, base_url="http://localhost:5173"):  # reemplazar por la url de produccion
        return f"{base_url.rstrip('/')}/libros/libro-reclamacion/{self.libro_slug}/{self.establecimiento_slug}/"

    def get_identificador(self):
        return self.libro_slug or str(self.codigo_libro)

    def __str__(self):
        return f"{self.codigo_libro} ({self.libro_slug}/{self.establecimiento_slug})"

class Cliente(models.Model):
    nombre_cliente = models.CharField(max_length=100)
    tipo_doc_cliente = models.CharField(max_length=15)
    doc_id_cliente = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField(verbose_name="Fecha de nacimiento")
    email = models.EmailField(max_length=100)
    telefono = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_cliente

class RepresentanteLegal(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='representantes')
    nombre_representante = models.CharField(max_length=100)
    tipo_doc_representante = models.CharField(max_length= 15)
    doc_id_representante = models.CharField(max_length=15)
    parentesco = models.CharField(max_length=50)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre_representante} ({self.parentesco})"

class EstadoReclamacion(models.Model):
    nombre_estado_reclamo = models.CharField(max_length=50)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre_estado_reclamo
    
class Reclamacion(models.Model):
    TIPO_CHOICES = [
        ('queja', 'Queja'),
        ('reclamo', 'Reclamo'),
    ]

    TIPO_BIEN_CHOICES = [
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ]
    
    
    libro = models.ForeignKey(LibroReclamacion, on_delete=models.CASCADE, related_name='reclamaciones')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reclamaciones')
    fecha = models.DateTimeField()
    codigo_hoja = models.CharField(max_length=50, unique=True)  # Código SUNAT por hoja
    tipo = models.CharField(max_length=20, choices= TIPO_CHOICES)  # queja o reclamo
    tipo_bien = models.CharField(max_length=20, choices= TIPO_BIEN_CHOICES)  # producto o servicio
    descripcion_bien = models.TextField()
    monto_reclamado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    detalle = models.TextField()
    solicitud_cliente = models.TextField(null=True, blank=True)
    respuesta = models.TextField(null=True, blank=True)
    estado = models.ForeignKey(EstadoReclamacion, on_delete=models.PROTECT, related_name='reclamaciones')

    def __str__(self):
        return self.codigo_hoja

class ArchivoAdjunto(models.Model):
    reclamacion = models.ForeignKey(Reclamacion, on_delete=models.CASCADE, related_name='archivos')
    nombre_archivo = models.CharField(max_length=255)
    ruta = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre_archivo
    
