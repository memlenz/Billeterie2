from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


def can_generate_qr_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.has_perm("qrgenerator.can_generate_qr"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def can_verify_qr_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.has_perm("qrgenerator.can_verify_qr"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view
