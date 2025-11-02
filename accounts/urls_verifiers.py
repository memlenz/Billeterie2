from django.urls import path
from . import views

# app_name = "accounts_verifiers"

urlpatterns = [
    path("", views.verifier_list, name="verifier_list"),
    path("create/", views.verifier_create, name="verifier_create"),
    path("<int:pk>/delete/", views.verifier_delete, name="verifier_delete"),
]
