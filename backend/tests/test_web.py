from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from fastapi.testclient import TestClient
from backend.controllers.api import crear_app
from backend.database.configuracion import CONFIG
from backend.database.datos import BaseDatos
from backend.models.modelo import Remito
from backend.daos.reportes import REPORTES
from backend.services.usuarios import crear_usuario


class TestWeb(TestCase):
    def setUp(self):
        carpeta = Path(__file__).parent / '.tmp'
        carpeta.mkdir(exist_ok=True)
        self.temporal = TemporaryDirectory(dir=carpeta)
        self.ruta = Path(self.temporal.name) / 'web.db'
        crear_usuario(BaseDatos(self.ruta), 'personal', 'clave-prueba')
        self.client = TestClient(crear_app(self.ruta), base_url='http://127.0.0.1')

    def tearDown(self):
        self.client.close()
        self.temporal.cleanup()

    def login(self):
        return self.client.post('/api/login', json={'usuario': 'personal', 'clave': 'clave-prueba'})

    def test_autenticacion_y_autorizacion(self):
        self.assertEqual(self.client.get('/api/state').status_code, 401)
        self.assertEqual(self.client.post('/api/action', json={'accion': 'crear_sede'}).status_code, 401)
        self.assertEqual(self.client.post('/api/login', json={'usuario': 'personal', 'clave': 'incorrecta'}).status_code, 401)
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.get('/api/state').status_code, 200)
        self.assertEqual(self.client.post('/api/logout').status_code, 200)
        self.assertEqual(self.client.get('/api/state').status_code, 401)

    def test_api_creacion_y_estado(self):
        self.login()
        data = self.client.get('/api/state').json()
        self.assertEqual(data['tablas']['sedes'], [])
        self.assertEqual(data['configuracion']['filas_por_pagina'], CONFIG['filas_por_pagina'])
        self.assertEqual(data['catalogos']['transiciones_remito'], Remito.TRANSICIONES)
        self.assertEqual(set(data['reportes']), set(REPORTES))
        sede = {'accion': 'crear_sede', 'nombre': 'Centro', 'direccion': 'Calle 1', 'contacto': '111', 'horarios': '9-18'}
        self.assertEqual(self.client.post('/api/action', json=sede).json()['resultado'], 1)
        self.assertEqual(self.client.get('/api/state').json()['tablas']['sedes'][0]['nombre'], 'Centro')
        self.assertEqual(self.client.post('/api/action', json=sede).status_code, 400)
        self.assertEqual(self.client.post('/api/action', json={'accion': 'crear_sede'}).status_code, 422)
        self.assertEqual(self.client.post('/api/action', json={'accion': '_actualizar_maestro', 'id': 1}).status_code, 422)

    def test_estaticos_y_origen(self):
        self.assertIn('Ingresar al sistema', self.client.get('/').text)
        self.assertEqual(self.client.get('/js/formularios.js').status_code, 200)
        self.assertEqual(self.client.get('/js/login.js').status_code, 200)
        self.assertEqual(self.client.get('/css/styles.css').status_code, 200)
        self.assertEqual(self.client.get('/css/login.css').status_code, 200)
        self.assertEqual(self.client.get('/configuracion.json').status_code, 404)
        self.assertEqual(self.client.get('/api/state', headers={'Origin': 'http://sitio-ajeno.test'}).status_code, 403)
        self.login()
        self.assertIn('Red de Bibliotecas', self.client.get('/').text)

    def test_prestamo_interbibliotecario_por_api(self):
        self.login()

        def accion(operacion, **datos):
            respuesta = self.client.post('/api/action', json={'accion': operacion, **datos})
            self.assertEqual(respuesta.status_code, 200, respuesta.text)
            return respuesta.json()['resultado']

        origen = accion('crear_sede', nombre='Centro', direccion='Calle 1', contacto='111', horarios='9-18')
        destino = accion('crear_sede', nombre='Norte', direccion='Calle 2', contacto='222', horarios='9-18')
        socio = accion('crear_socio', documento='123', nombre='Ana', email='ana@example.com')
        libro = accion('crear_libro', isbn='isbn', titulo='Objetos', autor='Autor', anio='')
        ejemplar = accion('crear_ejemplar', codigo='E-1', libro_id=str(libro), sede_id=str(origen))
        prestamo = accion('solicitar_prestamo', socio_id=str(socio), ejemplar_id=str(ejemplar), sede_origen_id=str(origen), sede_destino_id=str(destino))
        remito = self.client.get('/api/state').json()['tablas']['remitos'][0]['id']
        self.assertEqual(self.client.post('/api/action', json={'accion': 'entregar_prestamo', 'id': prestamo}).status_code, 400)
        for estado in ('EMPAQUETADO', 'DESPACHADO', 'RECIBIDO'):
            accion('avanzar_remito', id=remito, estado=estado, detalle='prueba')
        self.assertEqual(len(self.client.get(f'/api/remito/{remito}/historial').json()), 4)
        self.assertIn('vence_en', accion('entregar_prestamo', id=prestamo))
        self.assertEqual(accion('devolver_prestamo', id=prestamo, condicion='BUENO')['multa_centavos'], 0)
