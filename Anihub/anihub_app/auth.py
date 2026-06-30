import json
import time
import jwt
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
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
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # --- A) Si es el navegador pidiendo una página (HTML), lo dejamos pasar ---
        # El JS dentro de la página ya se encargará de validar el token después.
        if 'text/html' in request.headers.get('Accept', ''):
            return view_func(request, *args, **kwargs)

        # --- B) Si es una petición API (JSON/Fetch), exigimos el token JWT ---
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not (auth_header.startswith('Token ') or auth_header.startswith('Bearer ')):
            return JsonResponse({'error': 'Formato inválido'}, status=401)
        
        token = auth_header.split(' ')[1]

        try:
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expirado'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Token inválido'}, status=401)

        return view_func(request, *args, **kwargs)
            
    return wrapper
    