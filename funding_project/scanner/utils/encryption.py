from cryptography.fernet import Fernet
from django.conf import settings
import base64

class EncryptionUtil:
    def __init__(self):
        key = settings.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY not found in settings")
        self.fernet = Fernet(key)

    def encrypt(self, txt):
        if not txt: return None
        return self.fernet.encrypt(txt.encode('utf-8')).decode('utf-8')

    def decrypt(self, txt):
        if not txt: return None
        return self.fernet.decrypt(txt.encode('utf-8')).decode('utf-8')