from django.db import models
from django.contrib.auth.models import AbstractUser
from .security import AESCipher

class Role(models.Model):
    """
    Entidad independiente para gestionar roles, permitiendo escalabilidad
    sin afectar al modelo User directamente.
    """
    ROLE_CHOICES = [
        ('ANONYMOUS', 'Anónimo'),
        ('USER', 'Usuario'),
        ('MODERATOR', 'Moderador'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()

class CustomUser(AbstractUser):
    """
    Modelo extendido de usuario.
    Se utiliza un ManyToManyField para los roles, lo que permite que un usuario 
    tenga múltiples niveles de acceso si el sistema crece en complejidad.
    """
    roles = models.ManyToManyField(Role, related_name='users', blank=True)
    
    # Campo a encriptar en base de datos
    _sensitive_data_encrypted = models.TextField(db_column='sensitive_data', blank=True, null=True)

    @property
    def sensitive_data(self):
        """Getter para obtener el dato en texto plano."""
        if not self._sensitive_data_encrypted:
            return None
        cipher_service = AESCipher()
        return cipher_service.decrypt(self._sensitive_data_encrypted)

    @sensitive_data.setter
    def sensitive_data(self, raw_value):
        """Setter que encripta el dato antes de asignarlo a la variable interna."""
        cipher_service = AESCipher()
        self._sensitive_data_encrypted = cipher_service.encrypt(raw_value)

    def __str__(self):
        return self.username
