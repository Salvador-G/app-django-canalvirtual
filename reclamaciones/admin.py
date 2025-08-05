from django.contrib import admin
from .models import (
    Proveedor, Marca, Establecimiento,
    LibroReclamacion, Cliente, RepresentanteLegal,
    EstadoReclamacion,Reclamacion, ArchivoAdjunto
)
# Register your models here.
admin.site.register(Proveedor)
admin.site.register(Marca)
admin.site.register(Establecimiento)
admin.site.register(LibroReclamacion)
admin.site.register(Cliente)
admin.site.register(RepresentanteLegal)
admin.site.register(Reclamacion)
admin.site.register(ArchivoAdjunto)
admin.site.register(EstadoReclamacion)