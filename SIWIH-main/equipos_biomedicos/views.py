from django.shortcuts import render


def inicio(request):
    return render(
        request,
        'equipos_biomedicos/equipos_biomedicos_inicio.html'
    )


def registrar_dispositivo(request):
    return render(
        request,
        'equipos_biomedicos/registrar_dispositivo_biomedicos.html'
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
