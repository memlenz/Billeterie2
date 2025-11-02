import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from django.core.files.base import ContentFile
from .models import CodeBatch, Code
from .qrcode_service import QRCodeService
import uuid
from accounts.decorators import owner_required, verifier_allowed


@login_required
@owner_required
def batch_list(request):
    """Liste des lots de codes"""
    batches = CodeBatch.objects.filter(created_by=request.user).order_by("-created_at")

    # Pagination
    paginator = Paginator(batches, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "title": "Gestion des lots de codes"}
    return render(request, "qrgenerator/batch_list.html", context)


@login_required
@owner_required
def batch_create(request):
    """Créer un nouveau lot de codes"""
    if request.method == "POST":
        name = request.POST.get("name")
        quantity = int(request.POST.get("quantity", 0))
        validity_days = int(request.POST.get("validity_days", 30))

        if not name or quantity <= 0 or quantity > 10000:
            messages.error(
                request, "Données invalides. La quantité doit être entre 1 et 1000."
            )
            return redirect("qrgenerator:batch_create")

        try:
            with transaction.atomic():
                # Créer le lot
                batch = CodeBatch.objects.create(
                    name=name,
                    quantity=quantity,
                    validity_days=validity_days,
                    created_by=request.user,
                    status="en_cours",
                )

                # Générer les codes
                expiration_date = timezone.now() + timedelta(days=validity_days)

                for _ in range(quantity):
                    # Message unique pour chaque code
                    message = f"{batch.id}:{uuid.uuid4()}:{timezone.now().isoformat()}"

                    code = Code(batch=batch, expiration_date=expiration_date)

                    # Génération crypto
                    code.generate_crypto_fields(message)
                    code.save()

                    # Générer le QR code
                    qr_buffer = QRCodeService.generate_qr_for_code(code)
                    code.qr_image.save(
                        f"qr_{code.secure_index[:16]}.png",
                        ContentFile(qr_buffer.read()),
                        save=True,
                    )

                # Marquer comme terminé
                batch.status = "termine"
                batch.save()

                messages.success(
                    request, f'Lot "{name}" créé avec succès ({quantity} codes).'
                )
                return redirect("qrgenerator:batch_detail", pk=batch.pk)

        except Exception as e:
            messages.error(request, f"Erreur lors de la création du lot: {str(e)}")
            if "batch" in locals():
                batch.status = "erreur"
                batch.save()
            return redirect("qrgenerator:batch_create")

    context = {"title": "Créer un nouveau lot"}
    return render(request, "qrgenerator/batch_create.html", context)


@login_required
@owner_required
def batch_detail(request, pk):
    """Détails d'un lot avec ses codes"""
    batch = get_object_or_404(CodeBatch, pk=pk, created_by=request.user)

    # Filtrer par statut si demandé
    status_filter = request.GET.get("status", "")
    codes = batch.codes.all()

    if status_filter:
        codes = codes.filter(status=status_filter)

    codes = codes.order_by("-created_at")

    # Pagination
    paginator = Paginator(codes, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistiques
    stats = {
        "total": batch.codes.count(),
        "non_utilise": batch.codes.filter(status="non_utilise").count(),
        "utilise": batch.codes.filter(status="utilise").count(),
        "expire": batch.codes.filter(status="expire").count(),
    }

    context = {
        "batch": batch,
        "page_obj": page_obj,
        "stats": stats,
        "status_filter": status_filter,
        "title": f"Lot: {batch.name}",
    }
    return render(request, "qrgenerator/batch_detail.html", context)


@login_required
@owner_required
def code_detail(request, pk):
    """Détails d'un code spécifique"""
    code = get_object_or_404(Code, pk=pk, batch__created_by=request.user)

    context = {"code": code, "title": f"Code #{code.id}"}
    return render(request, "qrgenerator/code_detail.html", context)


@login_required
@owner_required
def code_download_qr(request, pk):
    """Télécharger l'image QR d'un code"""
    code = get_object_or_404(Code, pk=pk, batch__created_by=request.user)

    if not code.qr_image:
        messages.error(request, "Aucune image QR disponible pour ce code.")
        return redirect("qrgenerator:code_detail", pk=pk)

    response = HttpResponse(code.qr_image.read(), content_type="image/png")
    response["Content-Disposition"] = (
        f'attachment; filename="qr_code_{code.secure_index[:16]}.png"'
    )
    return response


@login_required
@owner_required
def batch_export(request, pk):
    """Exporter tous les QR codes d'un lot (ZIP)"""
    import zipfile
    from io import BytesIO

    batch = get_object_or_404(CodeBatch, pk=pk, created_by=request.user)

    # Créer un fichier ZIP en mémoire
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for code in batch.codes.all():
            if code.qr_image:
                zip_file.writestr(
                    f"qr_{code.id}_{code.secure_index[:16]}.png", code.qr_image.read()
                )

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = (
        f'attachment; filename="batch_{batch.id}_{batch.name}_qrcodes.zip"'
    )
    return response


@login_required
@verifier_allowed
def verify_code(request):
    """Interface de vérification d'un code"""
    if request.method == "POST":
        secure_index = request.POST.get("secure_index", "").strip()

        # Gérer l'upload d'image QR code
        if not secure_index and request.FILES.get("qr_image"):
            qr_image = request.FILES["qr_image"]
            try:
                # Décoder le QR code depuis l'image
                from pyzbar.pyzbar import decode
                from PIL import Image
                import io

                # Lire et décoder l'image
                image = Image.open(io.BytesIO(qr_image.read()))
                decoded_objects = decode(image)

                if decoded_objects:
                    secure_index = decoded_objects[0].data.decode("utf-8")
                else:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Aucun QR code détecté dans l'image",
                        }
                    )

            except Exception as e:
                print(f"Erreur décodage QR: {e}")
                return JsonResponse(
                    {"success": False, "message": "Erreur lors du décodage du QR code"}
                )

        if not secure_index:
            return JsonResponse(
                {"success": False, "message": "Index sécurisé manquant"}
            )

        try:
            # Utilisation de select_for_update() pour éviter les race conditions
            with transaction.atomic():
                code = Code.objects.select_for_update().get(
                    secure_index=secure_index, batch__created_by=request.user.owner
                )

                now = timezone.now()

                # Vérifier l'expiration
                if now > code.expiration_date:
                    code.status = "expire"
                    code.save()
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Code expiré",
                            "code_id": code.id,
                            "status": "expire",
                        }
                    )

                # Vérifier si déjà utilisé
                if code.status == "utilise":
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Code déjà utilisé",
                            "code_id": code.id,
                            "status": "utilise",
                        }
                    )

                # Marquer comme utilisé
                code.status = "utilise"
                code.used_at = now
                code.save()

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Code valide et activé",
                        "code_id": code.id,
                        "batch_name": code.batch.name,
                        "created_at": code.created_at.isoformat(),
                    }
                )

        except Code.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Code introuvable ou non autorisé"}
            )
        except Exception as e:
            print(f"Erreur lors de la vérification: {e}")
            return JsonResponse(
                {"success": False, "message": "Erreur interne du serveur"}
            )

    context = {"title": "Vérifier un code"}
    return render(request, "qrgenerator/verify_code.html", context)


@login_required
@owner_required
def dashboard(request):
    """Tableau de bord avec statistiques"""
    user_batches = CodeBatch.objects.filter(created_by=request.user)

    stats = {
        "total_batches": user_batches.count(),
        "total_codes": Code.objects.filter(batch__created_by=request.user).count(),
        "codes_actifs": Code.objects.filter(
            batch__created_by=request.user,
            status="non_utilise",
            expiration_date__gt=timezone.now(),
        ).count(),
        "codes_utilises": Code.objects.filter(
            batch__created_by=request.user, status="utilise"
        ).count(),
    }

    recent_batches = user_batches.order_by("-created_at")[:5]

    context = {
        "stats": stats,
        "recent_batches": recent_batches,
        "title": "Tableau de bord",
    }
    return render(request, "qrgenerator/dashboard.html", context)
