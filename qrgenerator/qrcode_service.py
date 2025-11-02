import qrcode
from io import BytesIO


class QRCodeService:
    @staticmethod
    def generate_qr_for_code(code_obj):
        """QR contenant le cipher + sig (JSON compact)"""
        payload = code_obj.secure_index

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
