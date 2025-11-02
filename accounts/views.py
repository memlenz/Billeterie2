from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .decorators import owner_required, admin_required, verifier_allowed
from django.http import HttpResponseForbidden
from .forms import VerifierCreationForm

User = get_user_model()


@login_required
def role_based_redirect(request):
    """Redirection intelligente basée sur le rôle"""
    if request.user.is_verifier():
        return redirect("qrgenerator:verify_code")
    elif request.user.is_owner() or request.user.is_admin():
        return redirect("qrgenerator:dashboard")
    else:
        # Fallback - normalement ne devrait pas arriver
        return redirect("home")


@login_required
@owner_required
def verifier_list(request):
    """Liste des verifiers pour un owner"""
    verifiers = User.objects.filter(owner=request.user, role=User.Role.VERIFIER)
    return render(request, "account/verifier_list.html", {"verifiers": verifiers})


@login_required
@owner_required
def verifier_create(request):
    """Création SIMPLIFIÉE d'un verifier - rôle automatique"""
    if request.method == "POST":
        form = VerifierCreationForm(request.POST, owner=request.user)
        if form.is_valid():
            verifier = form.save()

            # Optionnel: envoyer un email d'invitation
            # self.send_verifier_invitation(verifier, request.user)

            messages.success(
                request,
                f'Compte verifier "{verifier.username}" créé avec succès. '
                f"Identifiants: {verifier.username} / mot de passe défini",
            )
            return redirect("verifier_list")
    else:
        form = VerifierCreationForm(owner=request.user)

    return render(
        request,
        "account/verifier_create.html",
        {"form": form, "title": "Créer un compte vérificateur"},
    )


@login_required
@owner_required
def verifier_delete(request, verifier_id):
    """
    Supprime un utilisateur de rôle VERIFIER appartenant à l'OWNER connecté.
    """
    # Vérification que l'utilisateur courant est un OWNER
    if request.user.role != User.Role.OWNER:
        return HttpResponseForbidden(
            "Seuls les owners peuvent supprimer des vérificateurs."
        )

    # Récupération du vérificateur à supprimer
    verifier = get_object_or_404(
        User,
        id=verifier_id,
        role=User.Role.VERIFIER,
        owner=request.user,
    )

    # Suppression
    verifier.delete()
    messages.success(
        request, f"Le vérificateur '{verifier.username}' a été supprimé avec succès."
    )

    # Redirection vers une page de ton choix (ex: liste des vérificateurs)
    return redirect("verifier_list")  # À adapter selon ton URL name
