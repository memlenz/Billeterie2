from django.shortcuts import redirect
from django.urls import reverse


class RoleRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Si l'user est authentifié et accède à la racine
        if request.user.is_authenticated:
            if request.user.is_verifier():
                return redirect("qrgenerator:verify_code")
            elif request.user.is_owner():
                return redirect("qrgenerator:dashboard")
            elif request.user.is_admin():
                return redirect("/J7GuncjzSMsqWhSveaYRwg/")
