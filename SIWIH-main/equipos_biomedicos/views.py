from django.shortcuts import render

def inicio(request):
    return render(
        request,
        'equipos_biomedicos/equipos_biomedicos_inicio.html'
    )
