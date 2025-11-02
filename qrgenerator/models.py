from django.db import models
from django.conf import settings
import hashlib
import json
from qrgenerator.security import RSAService


class CodeBatch(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    validity_days = models.PositiveIntegerField(default=30)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("en_cours", "En cours"),
            ("termine", "Terminé"),
            ("erreur", "Erreur"),
        ],
        default="en_cours",
    )

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("can_generate_qr", "Can generate QR codes"),
            ("can_verify_qr", "Can verify QR codes"),
        ]


class Code(models.Model):
    batch = models.ForeignKey(CodeBatch, on_delete=models.CASCADE, related_name="codes")
    ciphertext = models.TextField()  # message chiffré avec pubkey
    signature = models.TextField()  # signature du ciphertext
    secure_index = models.CharField(
        max_length=64, unique=True, default=None
    )  # SHA256(signature)
    qr_image = models.ImageField(upload_to="qr_codes/", null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("non_utilise", "Non utilisé"),
            ("utilise", "Utilisé"),
            ("expire", "Expiré"),
        ],
        default="non_utilise",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()

    def __str__(self):
        return f"Code {self.id} ({self.secure_index[:8]}...)"

    class Meta:
        permissions = [
            ("can_verify_qr", "Can verify QR codes"),
        ]

    def generate_crypto_fields(self, message: str):
        """Chiffre, signe et calcule secure_index"""
        self.ciphertext = RSAService.encrypt(message)
        self.signature = RSAService.sign(self.ciphertext)
        self.secure_index = hashlib.sha256(self.signature.encode()).hexdigest()

    def get_payload(self):
        """Payload JSON embarqué dans le QR"""
        return json.dumps(
            {
                "cipher": self.ciphertext,
                "sig": self.signature,
            },
            separators=(",", ":"),
        )
