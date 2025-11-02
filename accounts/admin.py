from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth import get_user_model

from .forms import VerifierCreationForm

User = get_user_model()


class VerifierInline(admin.TabularInline):
    """Inline pour créer ou gérer les vérificateurs liés à un owner"""

    model = User
    form = VerifierCreationForm
    extra = 1
    verbose_name = "Vérificateur"
    verbose_name_plural = "Vérificateurs"

    def get_queryset(self, request):
        """Limiter aux utilisateurs ayant le rôle VERIFIER"""
        qs = super().get_queryset(request)
        return qs.filter(role=User.Role.VERIFIER)

    def save_model(self, request, obj, form, change):
        """Assigne automatiquement l'owner au vérificateur"""
        obj.owner = form.owner if hasattr(form, "owner") else request.user
        super().save_model(request, obj, form, change)


class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour le modèle User"""

    list_display = ("username", "email", "role", "is_active", "is_staff", "owner")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Informations sur le rôle"), {"fields": ("role", "owner")}),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "owner",
                ),
            },
        ),
    )

    inlines = [VerifierInline]

    def get_inlines(self, request, obj=None):
        """Afficher les vérificateurs uniquement pour les owners"""
        if obj and obj.role == User.Role.OWNER:
            return [VerifierInline]
        return []

    def save_model(self, request, obj, form, change):
        """Assure la cohérence du rôle et du propriétaire"""
        if not obj.pk and obj.role == User.Role.OWNER:
            obj.owner = None
        super().save_model(request, obj, form, change)


# Enregistrement du modèle
admin.site.register(User, UserAdmin)
