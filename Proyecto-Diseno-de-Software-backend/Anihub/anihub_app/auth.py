import json
import time
from functools import wraps
from django.http import JsonResponse
from .security import AESCipher

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
    """Decorador para proteger endpoints asegurando la presencia de un token válido."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"error": "Token missing or invalid"}, status=401)
        
        token = auth_header.split(' ')[1]
        token_service = AuthTokenService()
        payload = token_service.validate_token(token)
        
        if not payload:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)
            
        request.user_id = payload.get("user_id")
        return view_func(request, *args, **kwargs)
    return _wrapped_view