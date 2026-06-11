from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio_biomedicos'),
    path(
        'registrar-dispositivo/',
        views.registrar_dispositivo,
        name='registrar_dispositivo_biomedicos'
    ),
    path(
        'listado-dispositivos/',
        views.listado_dispositivos,
        name='listado_dispositivos_biomedicos'
    ),
    path(
        'escanear-qr/',
        views.escanear_qr,
        name='escanear_qr_biomedicos'
    ),
    path(
        'buscar-dispositivo/',
        views.buscar_dispositivo,
        name='buscar_dispositivo_biomedicos'
    ),
]
