import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings


class RSAService:
    @staticmethod
    def _load_private_key():
        key_data = base64.b64decode(settings.PRIVATE_KEY)
        return serialization.load_pem_private_key(key_data, password=None)

    @staticmethod
    def _load_public_key():
        key_data = base64.b64decode(settings.PUBLIC_KEY)
        return serialization.load_pem_public_key(key_data)

    @staticmethod
    def encrypt(message: str) -> str:
        public_key = RSAService._load_public_key()
        ciphertext = public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode()

    @staticmethod
    def decrypt(ciphertext_b64: str) -> str:
        private_key = RSAService._load_private_key()
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return plaintext.decode()

    @staticmethod
    def sign(message: str) -> str:
        private_key = RSAService._load_private_key()
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify(message: str, signature_b64: str) -> bool:
        public_key = RSAService._load_public_key()
        try:
            public_key.verify(
                base64.b64decode(signature_b64),
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False
