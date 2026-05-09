import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings

class AESCipher:
    """
    Servicio encargado de la encriptación/desencriptación AES-256.
    Cumple con el SRP al aislar la lógica criptográfica de los modelos.
    """
    def __init__(self):
        self.key = settings.AES_SECRET_KEY

    def encrypt(self, raw_data: str) -> str:
        if not raw_data:
            return raw_data
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(raw_data.encode('utf-8'), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        try:
            iv, ct = encrypted_data.split(':')
            iv_bytes = base64.b64decode(iv)
            ct_bytes = base64.b64decode(ct)
            cipher = AES.new(self.key, AES.MODE_CBC, iv_bytes)
            pt = unpad(cipher.decrypt(ct_bytes), AES.block_size)
            return pt.decode('utf-8')
        except Exception as e:
            raise ValueError("Error al desencriptar los datos") from e
