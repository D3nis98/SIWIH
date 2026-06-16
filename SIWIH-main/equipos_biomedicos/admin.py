from django.contrib import admin

from .models import AsignacionDispositivo, Dispositivo, TipoDispositivo


@admin.register(TipoDispositivo)
class TipoDispositivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "tipo",
        "marca",
        "modelo",
        "numero_serie",
        "inventario_bienes_nacionales",
        "estado",
        "criticidad",
    )
    list_filter = ("tipo", "estado", "criticidad")
    search_fields = (
        "nombre",
        "marca",
        "modelo",
        "numero_serie",
        "inventario_bienes_nacionales",
    )
    autocomplete_fields = ("tipo", "creado_por", "modificado_por")
    readonly_fields = ("fecha_creado", "fecha_modificado")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(AsignacionDispositivo)
class AsignacionDispositivoAdmin(admin.ModelAdmin):
    list_display = (
        "dispositivo",
        "ubicacion",
        "responsable",
        "fecha_inicio",
        "fecha_fin",
    )
    list_filter = ("fecha_fin", "area_clinica", "unidad_no_clinica")
    search_fields = (
        "dispositivo__nombre",
        "dispositivo__numero_serie",
        "dispositivo__inventario_bienes_nacionales",
        "responsable__dni",
        "responsable__primer_nombre",
        "responsable__primer_apellido",
    )
    autocomplete_fields = (
        "dispositivo",
        "area_clinica",
        "unidad_no_clinica",
        "responsable",
        "creado_por",
        "modificado_por",
    )
    readonly_fields = ("fecha_creado", "fecha_modificado")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
