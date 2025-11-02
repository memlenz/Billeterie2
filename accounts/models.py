from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        OWNER = "owner", "QR Code Owner"
        VERIFIER = "verifier", "QR Verifier"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    owner = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="verifiers",
        limit_choices_to={"role": Role.OWNER},
    )

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_owner(self):
        return self.role == self.Role.OWNER

    def is_verifier(self):
        return self.role == self.Role.VERIFIER

    def __str__(self):
        return self.email
