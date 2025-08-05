from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from reclamaciones.models import Proveedor
from django.db import models

#Modelo personalizado
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # duplicamos el email en username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user( email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Solo los usuarios comunes deben tener empresa asignada"
    )
    role = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def clean(self):
        super().clean()
        if not self.is_superuser and not self.proveedor:
            raise ValidationError("Los usuarios no superadmin deben tener una empresa asignada.")
        if self.is_superuser and self.proveedor:
            raise ValidationError("El superadmin no debe estar asociado a una empresa.")
        
    def __str__(self):
        return self.username