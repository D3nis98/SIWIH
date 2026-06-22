from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.constants.choices_constants import EstadoRegistro
from rrhh.models import Empleado

from .forms import DispositivoCreateForm
from .models import (
    AsignacionDispositivo,
    CriticidadDispositivo,
    Dispositivo,
    EstadoDispositivo,
    TipoDispositivo,
    TipoTecnologiaDispositivo,
)


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
                observaciones="Asignación inicial del equipo.",
                creado_por=request.user,
                modificado_por=request.user,
            )

        messages.success(
            request,
            f"Equipo {dispositivo.codigo} registrado correctamente.",
        )
        return redirect("detalle_dispositivo_biomedicos", dispositivo_id=dispositivo.id)

    return render(
        request,
        "equipos_biomedicos/registrar_dispositivo_biomedicos.html",
        {"form": form},
    )


def _obtener_opciones_area_listado():
    opciones = []
    vistos = set()
    asignaciones = AsignacionDispositivo.objects.filter(
        fecha_fin__isnull=True
    ).select_related(
        "area_clinica__servicio",
        "unidad_no_clinica",
    ).order_by(
        "area_clinica__nombre_area_atencion",
        "unidad_no_clinica__nombre_unidad",
    )

    for asignacion in asignaciones:
        if asignacion.area_clinica_id:
            valor = f"clinica:{asignacion.area_clinica_id}"
            etiqueta = f"Clínica - {asignacion.area_clinica}"
        elif asignacion.unidad_no_clinica_id:
            valor = f"no_clinica:{asignacion.unidad_no_clinica_id}"
            etiqueta = f"No clínica - {asignacion.unidad_no_clinica}"
        else:
            continue

        if valor in vistos:
            continue

        vistos.add(valor)
        opciones.append({"value": valor, "label": etiqueta})

    return opciones


def _parametro_entero(valor):
    if valor and valor.isdigit():
        return int(valor)
    return None


def listado_dispositivos(request):
    consulta = request.GET.get("q", "").strip()
    filtro_area = request.GET.get("area", "").strip()
    filtro_estado = request.GET.get("estado", "").strip()
    filtro_criticidad = request.GET.get("criticidad", "").strip()
    filtro_tipo = request.GET.get("tipo", "").strip()
    filtro_tecnologia = request.GET.get("tecnologia", "").strip()

    asignacion_activa = Prefetch(
        "asignaciones",
        queryset=AsignacionDispositivo.objects.filter(
            fecha_fin__isnull=True
        ).select_related(
            "area_clinica__servicio",
            "unidad_no_clinica",
            "responsable",
        ),
        to_attr="asignacion_activa_lista",
    )
    dispositivos = Dispositivo.objects.select_related(
        "tipo",
        "marca",
        "modelo",
    ).prefetch_related(asignacion_activa)

    if consulta:
        filtro_busqueda = (
            Q(tipo__nombre__icontains=consulta)
            | Q(marca__nombre__icontains=consulta)
            | Q(modelo__nombre__icontains=consulta)
            | Q(numero_serie__icontains=consulta)
            | Q(inventario_bienes_nacionales__icontains=consulta)
            | Q(inventario_numero_ficha__icontains=consulta)
        )
        codigo_numerico = "".join(caracter for caracter in consulta if caracter.isdigit())

        if codigo_numerico:
            filtro_busqueda |= Q(pk=int(codigo_numerico))

        dispositivos = dispositivos.filter(filtro_busqueda)

    if filtro_area.startswith("clinica:"):
        area_id = _parametro_entero(filtro_area.removeprefix("clinica:"))
        if area_id:
            dispositivos = dispositivos.filter(
                asignaciones__fecha_fin__isnull=True,
                asignaciones__area_clinica_id=area_id,
            )
    elif filtro_area.startswith("no_clinica:"):
        unidad_id = _parametro_entero(filtro_area.removeprefix("no_clinica:"))
        if unidad_id:
            dispositivos = dispositivos.filter(
                asignaciones__fecha_fin__isnull=True,
                asignaciones__unidad_no_clinica_id=unidad_id,
            )

    estado_id = _parametro_entero(filtro_estado)
    if estado_id:
        dispositivos = dispositivos.filter(estado=estado_id)

    criticidad_id = _parametro_entero(filtro_criticidad)
    if criticidad_id:
        dispositivos = dispositivos.filter(criticidad=criticidad_id)

    tipo_id = _parametro_entero(filtro_tipo)
    if tipo_id:
        dispositivos = dispositivos.filter(tipo_id=tipo_id)

    tecnologia_id = _parametro_entero(filtro_tecnologia)
    if tecnologia_id:
        dispositivos = dispositivos.filter(tipo_tecnologia=tecnologia_id)

    dispositivos = dispositivos.order_by(
        "tipo__nombre",
        "marca__nombre",
        "modelo__nombre",
        "numero_serie",
    ).distinct()
    paginador = Paginator(dispositivos, 10)
    page_obj = paginador.get_page(request.GET.get("page"))

    estado_css = {
        EstadoDispositivo.OPERATIVO: "biomedicos-estado--operativo",
        EstadoDispositivo.EN_MANTENIMIENTO: "biomedicos-estado--media",
        EstadoDispositivo.FUERA_DE_SERVICIO: "biomedicos-estado--alta",
        EstadoDispositivo.DADO_DE_BAJA: "biomedicos-estado--inactivo",
    }
    criticidad_css = {
        CriticidadDispositivo.BAJA: "biomedicos-estado--operativo",
        CriticidadDispositivo.MEDIA: "biomedicos-estado--media",
        CriticidadDispositivo.ALTA: "biomedicos-estado--alta",
    }

    for dispositivo in page_obj.object_list:
        dispositivo.asignacion_actual = (
            dispositivo.asignacion_activa_lista[0]
            if dispositivo.asignacion_activa_lista
            else None
        )
        dispositivo.estado_css = estado_css.get(dispositivo.estado, "")
        dispositivo.criticidad_css = criticidad_css.get(dispositivo.criticidad, "")

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        'equipos_biomedicos/listado_dispositivos_biomedicos.html',
        {
            "dispositivos": page_obj.object_list,
            "page_obj": page_obj,
            "rango_paginas": paginador.get_elided_page_range(
                page_obj.number,
                on_each_side=1,
                on_ends=1,
            ),
            "total_dispositivos": paginador.count,
            "querystring": query_params.urlencode(),
            "filtros": {
                "q": consulta,
                "area": filtro_area,
                "estado": filtro_estado,
                "criticidad": filtro_criticidad,
                "tipo": filtro_tipo,
                "tecnologia": filtro_tecnologia,
            },
            "area_choices": _obtener_opciones_area_listado(),
            "estado_choices": [
                {"value": str(valor), "label": etiqueta}
                for valor, etiqueta in EstadoDispositivo.choices
            ],
            "criticidad_choices": [
                {"value": str(valor), "label": etiqueta}
                for valor, etiqueta in CriticidadDispositivo.choices
            ],
            "tipo_choices": TipoDispositivo.objects.filter(activo=True).order_by(
                "nombre"
            ),
            "tecnologia_choices": [
                {"value": str(valor), "label": etiqueta}
                for valor, etiqueta in TipoTecnologiaDispositivo.choices
            ],
        },
    )


def detalle_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(
        Dispositivo.objects.select_related("tipo", "marca", "modelo"),
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


def buscar_empleados(request):
    consulta = request.GET.get("q", "").strip()
    empleados = Empleado.objects.filter(estado=EstadoRegistro.ACTIVO)

    if not consulta:
        return JsonResponse({"results": []})

    for termino in consulta.split():
        filtro = (
            Q(dni__icontains=termino)
            | Q(primer_nombre__icontains=termino)
            | Q(segundo_nombre__icontains=termino)
            | Q(primer_apellido__icontains=termino)
            | Q(segundo_apellido__icontains=termino)
        )

        if termino.isdigit():
            filtro |= Q(pk=int(termino))

        empleados = empleados.filter(filtro)

    resultados = [
        {
            "id": empleado.id,
            "text": f"{empleado.id} | {empleado.dni} - {empleado.nombre_completo}",
        }
        for empleado in empleados.order_by(
            "primer_nombre",
            "primer_apellido",
            "dni",
        )[:10]
    ]

    return JsonResponse({"results": resultados})
