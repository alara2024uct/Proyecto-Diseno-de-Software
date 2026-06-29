from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}} # Que la contraseña nunca se devuelva en la respuesta

    def create(self, validated_data):
        # Creamos el usuario usando el método 'create_user' para que encripte la contraseña automáticamente
        user = CustomUser.objects.create_user(**validated_data)
        return user