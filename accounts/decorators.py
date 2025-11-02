from django.core.exceptions import PermissionDenied
from functools import wraps


def admin_required(view_func):
    """Nécessite un compte admin"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not request.user.is_admin():
            raise PermissionDenied("Accès réservé aux administrateurs")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def owner_required(view_func):
    """Nécessite un compte owner ou admin"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not (request.user.is_owner() or request.user.is_admin()):
            raise PermissionDenied("Accès réservé aux propriétaires de codes")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def verifier_allowed(view_func):
    """Autorise seulement les verifiers (et redirige les autres)"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not (request.user.is_verifier() or request.user.is_owner):
            # Redirige vers le dashboard approprié
            from django.shortcuts import redirect

            if request.user.is_owner() or request.user.is_admin():
                return redirect("qrgenerator:dashboard")
            else:
                raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view
