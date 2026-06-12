from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DispositivoCreateForm
from .models import AsignacionDispositivo, Dispositivo


def inicio(request):
    return render(
        request,
        'equipos_biomedicos/equipos_biomedicos_inicio.html'
    )


def registrar_dispositivo(request):
    form = DispositivoCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            dispositivo = form.save(commit=False)
            dispositivo.creado_por = request.user
            dispositivo.modificado_por = request.user
            dispositivo.save()

            AsignacionDispositivo.objects.create(
                dispositivo=dispositivo,
                area_clinica=form.cleaned_data.get("area_clinica"),
                unidad_no_clinica=form.cleaned_data.get("unidad_no_clinica"),
                responsable=form.cleaned_data["responsable"],
                observaciones="Asignación inicial del dispositivo.",
                creado_por=request.user,
                modificado_por=request.user,
            )

        messages.success(
            request,
            f"Dispositivo {dispositivo.codigo} registrado correctamente.",
        )
        return redirect("detalle_dispositivo_biomedicos", dispositivo_id=dispositivo.id)

    return render(
        request,
        "equipos_biomedicos/registrar_dispositivo_biomedicos.html",
        {"form": form},
    )


def listado_dispositivos(request):
    return render(
        request,
        'equipos_biomedicos/listado_dispositivos_biomedicos.html'
    )


def detalle_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(
        Dispositivo.objects.select_related("tipo"),
        pk=dispositivo_id,
    )
    asignacion_actual = dispositivo.asignaciones.filter(
        fecha_fin__isnull=True
    ).select_related(
        "area_clinica__servicio",
        "unidad_no_clinica",
        "responsable",
    ).first()

    return render(
        request,
        'equipos_biomedicos/detalle_dispositivo_biomedicos.html',
        {
            "dispositivo": dispositivo,
            "asignacion_actual": asignacion_actual,
        }
    )


def escanear_qr(request):
    return render(
        request,
        'equipos_biomedicos/escanear_qr_biomedicos.html'
    )


def buscar_dispositivo(request):
    consulta = request.GET.get('q', '').strip()

    return render(
        request,
        'equipos_biomedicos/buscar_dispositivo_biomedicos.html',
        {'consulta': consulta}
    )
