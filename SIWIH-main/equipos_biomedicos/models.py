from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from core.constants.choices_constants import TipoUnidad
from rrhh.models import Empleado
from servicio.models import Area_atencion, Unidad


def normalizar_inventario_bienes_nacionales(valor):
    valor = (valor or "").strip()

    if not valor:
        return None

    cantidad_digitos = sum(caracter.isdigit() for caracter in valor)
    if cantidad_digitos > 15:
        raise ValidationError(
            "El inventario de bienes nacionales no puede contener más de "
            "15 números."
        )

    return valor


class EstadoDispositivo(models.IntegerChoices):
    OPERATIVO = 1, "Operativo"
    EN_MANTENIMIENTO = 2, "En mantenimiento"
    FUERA_DE_SERVICIO = 3, "Fuera de servicio"
    DADO_DE_BAJA = 4, "Dado de baja"


class CriticidadDispositivo(models.IntegerChoices):
    BAJA = 1, "Baja"
    MEDIA = 2, "Media"
    ALTA = 3, "Alta"


class TipoDispositivo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=250, blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Tipo de dispositivo"
        verbose_name_plural = "Tipos de dispositivo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Dispositivo(models.Model):
    nombre = models.CharField(max_length=120, db_index=True)
    tipo = models.ForeignKey(
        TipoDispositivo,
        on_delete=models.PROTECT,
        related_name="dispositivos",
    )
    marca = models.CharField(max_length=80, blank=True, default="Indefinido")
    modelo = models.CharField(max_length=100, blank=True, default="Indefinido")
    numero_serie = models.CharField(max_length=100, unique=True, null=True, blank=True)
    inventario_bienes_nacionales = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )
    estado = models.PositiveSmallIntegerField(
        choices=EstadoDispositivo.choices,
        default=EstadoDispositivo.OPERATIVO,
        db_index=True,
    )
    criticidad = models.PositiveSmallIntegerField(
        choices=CriticidadDispositivo.choices,
        db_index=True,
    )
    frecuencia_mantenimiento_meses = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cantidad de meses entre mantenimientos preventivos.",
    )
    fecha_instalacion = models.DateField()
    fin_garantia = models.DateField(null=True, blank=True)
    costo_adquisicion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    observaciones = models.TextField(blank=True)
    fecha_creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="dispositivos_biomedicos_creados",
    )
    fecha_modificado = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="dispositivos_biomedicos_modificados",
    )

    class Meta:
        verbose_name = "Dispositivo biomédico"
        verbose_name_plural = "Dispositivos biomédicos"
        ordering = ["nombre", "numero_serie"]
        indexes = [
            models.Index(
                fields=["estado", "criticidad"],
                name="bio_disp_estado_criticidad_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(frecuencia_mantenimiento_meses__gt=0),
                name="bio_disp_frecuencia_positiva",
            ),
            models.CheckConstraint(
                condition=Q(costo_adquisicion__gte=0),
                name="bio_disp_costo_no_negativo",
            ),
            models.CheckConstraint(
                condition=Q(fin_garantia__isnull=True)
                | Q(fin_garantia__gte=F("fecha_instalacion")),
                name="bio_disp_garantia_fecha_valida",
            ),
        ]

    @property
    def codigo(self):
        if not self.pk:
            return "DISP-SIN-ID"
        return f"DISP-{self.pk:05d}"

    def clean(self):
        errores = {}
        self.marca = (self.marca or "").strip() or "Indefinido"
        self.modelo = (self.modelo or "").strip() or "Indefinido"
        self.numero_serie = (self.numero_serie or "").strip() or None

        try:
            self.inventario_bienes_nacionales = (
                normalizar_inventario_bienes_nacionales(
                    self.inventario_bienes_nacionales
                )
            )
        except ValidationError as error:
            errores["inventario_bienes_nacionales"] = error

        if (
            self.fecha_instalacion
            and self.fin_garantia
            and self.fin_garantia < self.fecha_instalacion
        ):
            errores["fin_garantia"] = (
                "El fin de garantía no puede ser anterior a la fecha de instalación."
            )

        if self.inventario_bienes_nacionales:
            inventario_existente = Dispositivo.objects.filter(
                inventario_bienes_nacionales__iexact=(
                    self.inventario_bienes_nacionales
                )
            ).exclude(pk=self.pk)

            if inventario_existente.exists():
                errores["inventario_bienes_nacionales"] = (
                    "Ya existe un dispositivo registrado con este inventario "
                    "de bienes nacionales."
                )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class AsignacionDispositivo(models.Model):
    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.PROTECT,
        related_name="asignaciones",
    )
    area_clinica = models.ForeignKey(
        Area_atencion,
        on_delete=models.PROTECT,
        related_name="asignaciones_dispositivos_biomedicos",
        null=True,
        blank=True,
    )
    unidad_no_clinica = models.ForeignKey(
        Unidad,
        on_delete=models.PROTECT,
        related_name="asignaciones_dispositivos_biomedicos",
        null=True,
        blank=True,
    )
    responsable = models.ForeignKey(
        Empleado,
        on_delete=models.PROTECT,
        related_name="asignaciones_dispositivos_biomedicos",
    )
    fecha_inicio = models.DateTimeField(default=timezone.now, db_index=True)
    fecha_fin = models.DateTimeField(null=True, blank=True, db_index=True)
    observaciones = models.TextField(blank=True)
    fecha_creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="asignaciones_dispositivos_biomedicos_creadas",
    )
    fecha_modificado = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="asignaciones_dispositivos_biomedicos_modificadas",
    )

    class Meta:
        verbose_name = "Asignación de dispositivo biomédico"
        verbose_name_plural = "Asignaciones de dispositivos biomédicos"
        ordering = ["-fecha_inicio"]
        indexes = [
            models.Index(
                fields=["dispositivo", "fecha_fin"],
                name="bio_asig_disp_fecha_fin_idx",
            ),
            models.Index(
                fields=["area_clinica", "fecha_fin"],
                name="bio_asig_area_fecha_fin_idx",
            ),
            models.Index(
                fields=["unidad_no_clinica", "fecha_fin"],
                name="bio_asig_unidad_fecha_fin_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(area_clinica__isnull=False, unidad_no_clinica__isnull=True)
                    | Q(area_clinica__isnull=True, unidad_no_clinica__isnull=False)
                ),
                name="bio_asig_una_ubicacion",
            ),
            models.CheckConstraint(
                condition=Q(fecha_fin__isnull=True)
                | Q(fecha_fin__gte=F("fecha_inicio")),
                name="bio_asig_fechas_validas",
            ),
        ]

    @property
    def activa(self):
        return self.fecha_fin is None

    @property
    def ubicacion(self):
        return self.area_clinica or self.unidad_no_clinica

    def clean(self):
        errores = {}
        tiene_area_clinica = self.area_clinica_id is not None
        tiene_unidad_no_clinica = self.unidad_no_clinica_id is not None

        if tiene_area_clinica == tiene_unidad_no_clinica:
            errores["area_clinica"] = (
                "Debe seleccionar exactamente una ubicación clínica o no clínica."
            )

        if (
            tiene_unidad_no_clinica
            and self.unidad_no_clinica.tipo == TipoUnidad.CLINICA
        ):
            errores["unidad_no_clinica"] = (
                "La unidad seleccionada debe ser administrativa o de apoyo."
            )

        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            errores["fecha_fin"] = (
                "La fecha de finalización no puede ser anterior a la fecha de inicio."
            )

        if self.dispositivo_id and self.fecha_fin is None:
            asignacion_activa = AsignacionDispositivo.objects.filter(
                dispositivo_id=self.dispositivo_id,
                fecha_fin__isnull=True,
            ).exclude(pk=self.pk)

            if asignacion_activa.exists():
                errores["dispositivo"] = (
                    "El dispositivo ya posee una asignación activa."
                )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dispositivo.codigo} - {self.ubicacion}"
