from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm

User = get_user_model()


class CustomSignupForm(SignupForm):
    """Formulaire d'inscription qui crée automatiquement des owners"""

    def save(self, request):
        # Appeler la méthode save parente
        user = super().save(request)
        # Forcer le rôle à OWNER pour toute inscription normale
        user.role = User.Role.OWNER
        user.save()
        return user


class VerifierCreationForm(forms.ModelForm):
    """Formulaire avec mot de passe"""

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput,
        help_text="Le mot de passe pour le compte vérificateur.",
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe", widget=forms.PasswordInput
    )

    def __init__(self, *args, owner=None, **kwargs):
        """
        Ajoute le paramètre 'owner' pour l'associer automatiquement à l'utilisateur créé.
        """
        super().__init__(*args, **kwargs)
        self.owner = owner

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.VERIFIER
        user.owner = self.owner
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
