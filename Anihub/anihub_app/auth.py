import json
import time
import jwt
from functools import wraps
from django.http import JsonResponse
from .security import AESCipher
from django.conf import settings

class AuthTokenService:
    """Servicio exclusivo para generar y validar tokens encriptados con AES-256."""
    def __init__(self):
        self.cipher = AESCipher()

    def generate_token(self, user_id: int, expiration_seconds: int = 3600) -> str:
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + expiration_seconds
        }
        return self.cipher.encrypt(json.dumps(payload))

    def validate_token(self, token: str) -> dict:
        try:
            decrypted_data = self.cipher.decrypt(token)
            payload = json.loads(decrypted_data)
            if payload.get("exp", 0) < time.time():
                return None # Token expirado
            return payload
        except Exception:
            return None # Token inválido

def token_required(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        # 1. Limpieza del prefijo
        if auth_header and auth_header.startswith('Token '):
            token = auth_header.split(' ')[1]
        else:
            return JsonResponse({'error': 'Formato inválido'}, status=401)

        try:
            # 2. INTENTO DE DECODIFICACIÓN
            # Aquí es donde ocurre el fallo
            data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expirado'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Token inválido'}, status=401)
            
    return wrapper
    