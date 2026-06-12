from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class EquiposBiomedicosViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='usuario_biomedicos',
            password='clave-prueba'
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_usuario_autenticado_puede_abrir_pantallas_del_modulo(self):
        nombres_rutas = [
            'inicio_biomedicos',
            'registrar_dispositivo_biomedicos',
            'listado_dispositivos_biomedicos',
            'escanear_qr_biomedicos',
            'buscar_dispositivo_biomedicos',
        ]

        for nombre_ruta in nombres_rutas:
            with self.subTest(nombre_ruta=nombre_ruta):
                respuesta = self.client.get(reverse(nombre_ruta))

                self.assertEqual(respuesta.status_code, 200)

    def test_detalle_inexistente_responde_404(self):
        respuesta = self.client.get(
            reverse('detalle_dispositivo_biomedicos', args=[999999])
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_busqueda_conserva_la_consulta(self):
        respuesta = self.client.get(
            reverse('buscar_dispositivo_biomedicos'),
            {'q': 'Monitor EQ-001'}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['consulta'], 'Monitor EQ-001')
        self.assertContains(respuesta, 'Monitor EQ-001')
