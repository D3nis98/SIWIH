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
        'dispositivos/<int:dispositivo_id>/',
        views.detalle_dispositivo,
        name='detalle_dispositivo_biomedicos'
    ),
    path(
        'dispositivos/<int:dispositivo_id>/qr/',
        views.qr_dispositivo,
        name='qr_dispositivo_biomedicos'
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
    path(
        'buscar-empleados/',
        views.buscar_empleados,
        name='buscar_empleados_biomedicos'
    ),
]
