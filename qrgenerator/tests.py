import json
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from qrgenerator.security import RSAService
from qrgenerator.qrcode_service import QRCodeService
from qrgenerator.models import CodeBatch, Code


class CodeCryptoTestCase(TestCase):
    def setUp(self):
        """Prépare un batch de test"""
        self.batch = CodeBatch.objects.create(
            name="BatchTest",
            quantity=1,
        )

    def test_crypto_pipeline(self):
        """Test complet : chiffrement, signature, hash et QR"""

        # 1️⃣ Création du code
        code = Code(
            batch=self.batch, expiration_date=timezone.now() + timedelta(days=30)
        )
        plaintext = "HELLO-WORLD-1234"

        # 2️⃣ Génération des champs cryptographiques
        code.generate_crypto_fields(plaintext)
        code.save()

        # 3️⃣ Vérifications de base
        self.assertEqual(len(code.secure_index), 64)
        self.assertTrue(RSAService.verify(code.ciphertext, code.signature))

        # 4️⃣ Déchiffrement : vérifie que ça redonne le message original
        decrypted = RSAService.decrypt(code.ciphertext)
        self.assertEqual(decrypted, plaintext)

        # 5️⃣ Génération du QR
        qr_buffer = QRCodeService.generate_qr_for_code(code)
        self.assertTrue(qr_buffer.getbuffer().nbytes > 0)

        # 6️⃣ Vérification du contenu JSON dans le QR
        payload = json.loads(code.get_payload())
        self.assertIn("cipher", payload)
        self.assertIn("sig", payload)

        print("\n✅ Test complet réussi ! secure_index:", code.secure_index[:16])
