from django.urls import path
from . import views

app_name = "qrgenerator"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),  # Tableau de bord
    path("batches/", views.batch_list, name="batch_list"),  # Liste des lots
    path(
        "batches/create/", views.batch_create, name="batch_create"
    ),  # Création d'un lot
    path(
        "batches/<int:pk>/", views.batch_detail, name="batch_detail"
    ),  # Détails d'un lot
    path(
        "batches/<int:pk>/export/", views.batch_export, name="batch_export"
    ),  # Exportation des QR codes
    path("codes/<int:pk>/", views.code_detail, name="code_detail"),  # Détails d'un code
    path(
        "codes/<int:pk>/download_qr/", views.code_download_qr, name="code_download_qr"
    ),  # Télécharger l'image QR
    path(
        "verify_code/", views.verify_code, name="verify_code"
    ),  # Vérification d'un code
]
