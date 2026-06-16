from datetime import date

from django import forms

from core.constants.choices_constants import EstadoRegistro, TipoUnidad
from rrhh.models import Empleado
from servicio.models import Area_atencion, Unidad

from .models import (
    CriticidadDispositivo,
    Dispositivo,
    EstadoDispositivo,
    TipoDispositivo,
    normalizar_inventario_bienes_nacionales,
)


class EmpleadoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, empleado):
        return f"{empleado.dni} - {empleado.nombre_completo}"


class DispositivoCreateForm(forms.ModelForm):
    TIPO_AREA_CHOICES = [
        ("clinica", "Área clínica"),
        ("no_clinica", "Área no clínica"),
    ]
    FRECUENCIA_CHOICES = [
        (1, "Mensual"),
        (3, "Trimestral"),
        (6, "Semestral"),
        (12, "Anual"),
    ]

    tipo_area = forms.ChoiceField(
        choices=TIPO_AREA_CHOICES,
        label="Tipo de área",
        widget=forms.Select(
            attrs={
                "class": "formularioCampo-select",
                "id": "tipo_area_dispositivo",
            }
        ),
    )
    area_clinica = forms.ModelChoiceField(
        queryset=Area_atencion.objects.none(),
        required=False,
        label="Área clínica",
        widget=forms.Select(
            attrs={
                "class": "formularioCampo-select",
                "id": "area_clinica_dispositivo",
            }
        ),
    )
    unidad_no_clinica = forms.ModelChoiceField(
        queryset=Unidad.objects.none(),
        required=False,
        label="Área no clínica",
        widget=forms.Select(
            attrs={
                "class": "formularioCampo-select",
                "id": "area_no_clinica_dispositivo",
            }
        ),
    )
    responsable = EmpleadoChoiceField(
        queryset=Empleado.objects.none(),
        label="Empleado a cargo",
        widget=forms.Select(
            attrs={
                "class": "formularioCampo-select",
                "id": "responsable_dispositivo",
                "data-placeholder": "Buscar por ID, DNI o nombre",
            }
        ),
    )
    frecuencia_mantenimiento_meses = forms.TypedChoiceField(
        choices=FRECUENCIA_CHOICES,
        coerce=int,
        label="Frecuencia de mantenimiento",
        widget=forms.Select(
            attrs={
                "class": "formularioCampo-select",
                "id": "frecuencia_dispositivo",
            }
        ),
    )

    class Meta:
        model = Dispositivo
        fields = [
            "nombre",
            "tipo",
            "marca",
            "modelo",
            "numero_serie",
            "inventario_bienes_nacionales",
            "estado",
            "criticidad",
            "frecuencia_mantenimiento_meses",
            "fecha_instalacion",
            "fin_garantia",
            "costo_adquisicion",
            "observaciones",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "nombre_dispositivo",
                    "placeholder": "Ingrese el nombre del dispositivo",
                }
            ),
            "tipo": forms.Select(
                attrs={
                    "class": "formularioCampo-select",
                    "id": "tipo_dispositivo",
                }
            ),
            "marca": forms.TextInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "marca_dispositivo",
                    "placeholder": "Opcional; se guardará como Indefinido",
                }
            ),
            "modelo": forms.TextInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "modelo_dispositivo",
                    "placeholder": "Opcional; se guardará como Indefinido",
                }
            ),
            "numero_serie": forms.TextInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "serie_dispositivo",
                    "placeholder": "Opcional; se mostrará como Indefinido",
                }
            ),
            "inventario_bienes_nacionales": forms.TextInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "inventario_bienes_nacionales",
                    "placeholder": "Ej. F/212300 (opcional)",
                }
            ),
            "estado": forms.Select(
                attrs={
                    "class": "formularioCampo-select",
                    "id": "estado_dispositivo",
                }
            ),
            "criticidad": forms.Select(
                attrs={
                    "class": "formularioCampo-select",
                    "id": "criticidad_dispositivo",
                }
            ),
            "fecha_instalacion": forms.DateInput(
                attrs={
                    "class": "formularioCampo-date",
                    "id": "instalacion_dispositivo",
                    "type": "date",
                    "max": date.today().strftime("%Y-%m-%d"),
                },
                format="%Y-%m-%d",
            ),
            "fin_garantia": forms.DateInput(
                attrs={
                    "class": "formularioCampo-date",
                    "id": "garantia_dispositivo",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "costo_adquisicion": forms.NumberInput(
                attrs={
                    "class": "formularioCampo-text",
                    "id": "costo_dispositivo",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Ingrese el costo",
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "class": "formularioCampo-text no-resize",
                    "id": "observaciones_dispositivo",
                    "rows": 4,
                    "placeholder": "Ingrese observaciones adicionales (opcional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tipo"].queryset = TipoDispositivo.objects.filter(activo=True)
        self.fields["tipo"].empty_label = "Seleccione el tipo de dispositivo"
        self.fields["estado"].choices = [
            ("", "Seleccione el estado inicial"),
            (EstadoDispositivo.OPERATIVO, EstadoDispositivo.OPERATIVO.label),
            (
                EstadoDispositivo.EN_MANTENIMIENTO,
                EstadoDispositivo.EN_MANTENIMIENTO.label,
            ),
            (
                EstadoDispositivo.FUERA_DE_SERVICIO,
                EstadoDispositivo.FUERA_DE_SERVICIO.label,
            ),
        ]
        self.fields["criticidad"].choices = [
            ("", "Seleccione la criticidad"),
            *CriticidadDispositivo.choices,
        ]
        self.fields["area_clinica"].queryset = Area_atencion.objects.filter(
            estado=EstadoRegistro.ACTIVO
        ).select_related("servicio")
        self.fields["unidad_no_clinica"].queryset = Unidad.objects.filter(
            estado=EstadoRegistro.ACTIVO
        ).exclude(tipo=TipoUnidad.CLINICA).order_by("nombre_unidad")
        responsable_id = None
        if self.is_bound:
            responsable_id = self.data.get(self.add_prefix("responsable"))

        if responsable_id and responsable_id.isdigit():
            self.fields["responsable"].queryset = Empleado.objects.filter(
                estado=EstadoRegistro.ACTIVO,
                pk=responsable_id,
            )

        self.fields["area_clinica"].empty_label = "Seleccione el área clínica"
        self.fields["unidad_no_clinica"].empty_label = "Seleccione el área no clínica"
        self.fields["responsable"].empty_label = "Buscar empleado a cargo"

    def clean_fecha_instalacion(self):
        fecha_instalacion = self.cleaned_data["fecha_instalacion"]
        if fecha_instalacion > date.today():
            raise forms.ValidationError(
                "La fecha de instalación no puede ser futura."
            )
        return fecha_instalacion

    def clean_marca(self):
        return (self.cleaned_data.get("marca") or "").strip() or "Indefinido"

    def clean_modelo(self):
        return (self.cleaned_data.get("modelo") or "").strip() or "Indefinido"

    def clean_numero_serie(self):
        return (self.cleaned_data.get("numero_serie") or "").strip() or None

    def clean_inventario_bienes_nacionales(self):
        return normalizar_inventario_bienes_nacionales(
            self.cleaned_data.get("inventario_bienes_nacionales")
        )

    def clean(self):
        cleaned_data = super().clean()
        tipo_area = cleaned_data.get("tipo_area")
        area_clinica = cleaned_data.get("area_clinica")
        unidad_no_clinica = cleaned_data.get("unidad_no_clinica")

        if tipo_area == "clinica":
            if not area_clinica:
                self.add_error("area_clinica", "Debe seleccionar un área clínica.")
            cleaned_data["unidad_no_clinica"] = None
        elif tipo_area == "no_clinica":
            if not unidad_no_clinica:
                self.add_error(
                    "unidad_no_clinica",
                    "Debe seleccionar un área no clínica.",
                )
            cleaned_data["area_clinica"] = None

        return cleaned_data
