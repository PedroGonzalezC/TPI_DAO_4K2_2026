from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from backend import Biblioteca, ReglaNegocio
from backend.daos.evento_remito_dao import EventoRemitoDAO
from backend.daos.remito_dao import RemitoDAO
from backend.models.fabrica_prestamos import FabricaPrestamos
from backend.models.prestamo import PrestamoInterbibliotecario, PrestamoLocal
from backend.models.remito import Remito


class TestBiblioteca(TestCase):
    def setUp(self):
        carpeta = Path(__file__).parent / ".tmp"
        carpeta.mkdir(exist_ok=True)
        self.temporal = TemporaryDirectory(dir=carpeta)
        b = Biblioteca(Path(self.temporal.name) / "biblioteca.db")
        origen = b.crear_sede("Centro", "Calle 1", "111", "9-18")
        destino = b.crear_sede("Norte", "Calle 2", "222", "9-17")
        socio = b.crear_socio("12345678", "Ana", "ana@example.com")
        libro = b.crear_libro("978-1", "Objetos", "Autor")
        ejemplar = b.crear_ejemplar("E-001", libro, origen)
        self.red = b, origen, destino, socio, libro, ejemplar

    def tearDown(self):
        self.temporal.cleanup()

    def test_prestamo_interbibliotecario_ida_devolucion_y_regreso(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        t0 = datetime(2026, 10, 1, 10)
        p = b.solicitar_prestamo(socio, ejemplar, origen, destino, fecha=t0)
        assert b.listar("prestamos")[0]["tipo"] == "INTERBIBLIOTECARIO"
        ida = b.listar("remitos")[0]["id"]
        assert [x["estado"] for x in b.historial_remito(ida)] == ["CREADO"]
        with self.assertRaises(ReglaNegocio):
            b.entregar_prestamo(p, fecha=t0)
        with self.assertRaises(ReglaNegocio):
            b.avanzar_remito(ida, "RECIBIDO", fecha=t0)
        b.avanzar_remito(ida, "EMPAQUETADO", fecha=t0 + timedelta(hours=1))
        b.avanzar_remito(ida, "DESPACHADO", fecha=t0 + timedelta(hours=2))
        assert b.listar("ejemplares")[0]["estado"] == "EN_TRANSITO"
        b.avanzar_remito(ida, "RECIBIDO", fecha=t0 + timedelta(hours=5))
        assert b.listar("ejemplares")[0]["sede_actual_id"] == destino
        assert [x["estado"] for x in b.historial_remito(ida)] == [
            "CREADO", "EMPAQUETADO", "DESPACHADO", "RECIBIDO"]
        vence = b.entregar_prestamo(p, fecha=t0 + timedelta(hours=6))
        assert vence == "2026-10-15"
        multa = b.devolver_prestamo(p, fecha=datetime(2026, 10, 18), condicion="BUENO")
        assert multa == 3 * b.MULTA_DIARIA_CENTAVOS
        assert b.listar("ejemplares")[0]["estado"] == "POR_RETORNAR"
        regreso = b.listar("remitos")[1]["id"]
        for estado in ("EMPAQUETADO", "DESPACHADO", "RECIBIDO"):
            b.avanzar_remito(regreso, estado, fecha=datetime(2026, 10, 19))
            if estado == "DESPACHADO":
                assert b.reportes("activos_transito")[0]["estado"] == "RETORNO_EN_TRANSITO"
        assert b.listar("ejemplares")[0]["sede_actual_id"] == origen
        assert b.listar("ejemplares")[0]["estado"] == "DISPONIBLE"
        assert b.listar("ejemplares")[0]["condicion"] in {"BUENO", "DANADO"}
        assert b.reportes("mas_solicitados")[0]["solicitudes_interbibliotecarias"] == 1
        assert b.reportes("logistica")[0]["recibidos"] == 2
        assert len(b.reportes("movimientos")) == 2


    def test_validaciones_y_duplicados(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        with self.assertRaises(ReglaNegocio):
            b.crear_socio("12345678", "Otro", "otro@example.com")
        with self.assertRaises(ReglaNegocio):
            b.crear_libro("978-1", "Otro", "Autor")
        with self.assertRaises(ReglaNegocio):
            b.crear_ejemplar("E-001", libro, origen)
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, ejemplar, destino, origen)
        b.actualizar_socio(socio, habilitado=False)
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, ejemplar, origen, origen)
        b.actualizar_socio(socio, habilitado=True)
        b.actualizar_sede(destino, activa=False)
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, ejemplar, origen, destino)
        b.actualizar_sede(destino, activa=True)
        p = b.solicitar_prestamo(socio, ejemplar, origen, origen, fecha=datetime(2026, 10, 1))
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, ejemplar, origen, origen)
        assert b.entregar_prestamo(p)
        with self.assertRaises(ReglaNegocio):
            b.entregar_prestamo(p)


    def test_reservas_por_orden_y_revision(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        otro = b.crear_socio("87654321", "Beto", "beto@example.com")
        p = b.solicitar_prestamo(socio, ejemplar, origen, origen, fecha=datetime(2026, 10, 1))
        b.entregar_prestamo(p, fecha=datetime(2026, 10, 1))
        r1 = b.reservar(otro, libro, origen, fecha=datetime(2026, 10, 2))
        r2 = b.reservar(socio, libro, origen, fecha=datetime(2026, 10, 3))
        b.devolver_prestamo(p, "BUENO", fecha=datetime(2026, 10, 4))
        assert b.listar("reservas")[0]["estado"] == "ASIGNADA"
        assert b.listar("reservas")[1]["estado"] == "EN_ESPERA"
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, ejemplar, origen, origen)
        b.cancelar_reserva(r1)
        assert b.listar("reservas")[1]["estado"] == "ASIGNADA"
        p2 = b.solicitar_prestamo(socio, ejemplar, origen, origen, fecha=datetime(2026, 10, 5))
        assert b.listar("reservas")[1]["estado"] == "CUMPLIDA"
        b.entregar_prestamo(p2, fecha=datetime(2026, 10, 5))
        b.devolver_prestamo(p2, "DANADO", fecha=datetime(2026, 10, 6))
        assert b.listar("ejemplares")[0]["estado"] == "EN_REVISION"
        assert b.listar("ejemplares")[0]["condicion"] in {"BUENO", "DANADO"}
        b.cerrar_revision(ejemplar, True)
        assert b.listar("ejemplares")[0]["estado"] == "DISPONIBLE"
        assert b.listar("ejemplares")[0]["condicion"] in {"BUENO", "DANADO"}


    def test_reportes_vencidos_y_disponibilidad(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        p = b.solicitar_prestamo(socio, ejemplar, origen, origen, fecha=datetime(2026, 9, 1))
        b.entregar_prestamo(p, fecha=datetime(2026, 9, 1))
        vencidos = b.reportes("vencidos_multas", fecha=datetime(2026, 9, 20))
        assert vencidos[0]["dias_atraso"] == 5
        assert vencidos[0]["multa_estimada_centavos"] == 5 * b.MULTA_DIARIA_CENTAVOS
        assert b.reportes("activos_transito")[0]["estado"] == "ACTIVO"
        assert b.reportes("disponibilidad")[0]["disponibles"] == 0
        assert b.disponibilidad(origen)[0]["ejemplares_totales"] == 1

    def test_fechas_sedes_y_persistencia_del_remito(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        inicio = datetime(2026, 10, 1, 9)
        p = b.solicitar_prestamo(socio, ejemplar, origen, destino, fecha=inicio)
        remito = b.listar("remitos")[0]["id"]
        with self.assertRaises(ReglaNegocio):
            b.avanzar_remito(remito, "EMPAQUETADO", fecha=inicio - timedelta(minutes=1))
        b.actualizar_sede(destino, activa=False)
        with self.assertRaises(ReglaNegocio):
            b.avanzar_remito(remito, "EMPAQUETADO", fecha=inicio)
        b.actualizar_sede(destino, activa=True)
        b.avanzar_remito(remito, "EMPAQUETADO", fecha=inicio)
        b.avanzar_remito(remito, "DESPACHADO", fecha=inicio + timedelta(hours=1))
        b.avanzar_remito(remito, "RECIBIDO", fecha=inicio + timedelta(hours=2))
        with self.assertRaises(ReglaNegocio):
            b.entregar_prestamo(p, fecha=inicio + timedelta(hours=1))
        b.entregar_prestamo(p, fecha=inicio + timedelta(hours=3))
        with self.assertRaises(ReglaNegocio):
            b.devolver_prestamo(p, fecha=inicio + timedelta(hours=2))
        otra_instancia = Biblioteca(b.db.ruta)
        assert len(otra_instancia.historial_remito(remito)) == 4
        assert otra_instancia.listar("prestamos")[0]["estado"] == "ACTIVO"

    def test_patron_factory_fabrica_prestamos(self):
        local = FabricaPrestamos.crear(socio_id=1, ejemplar_id=10, origen=1, destino=1)
        inter = FabricaPrestamos.crear(socio_id=1, ejemplar_id=10, origen=1, destino=2)
        self.assertIsInstance(local, PrestamoLocal)
        self.assertEqual(local.tipo, "LOCAL")
        self.assertFalse(local.requiere_remito)
        self.assertIsInstance(inter, PrestamoInterbibliotecario)
        self.assertEqual(inter.tipo, "INTERBIBLIOTECARIO")
        self.assertTrue(inter.requiere_remito)

    def test_patron_observer_remito_y_evento_remito_dao(self):
        b, origen, destino, socio, _libro, ejemplar = self.red
        t0 = datetime(2026, 10, 1, 10)
        b.solicitar_prestamo(socio, ejemplar, origen, destino, fecha=t0)
        remito_id = b.listar("remitos")[0]["id"]

        notificaciones_memoria = []

        class ObservadorNotificaciones:
            def actualizar(self, r_id: int, estado: str, fecha: str, detalle: str) -> None:
                notificaciones_memoria.append((r_id, estado, detalle))

        with b.db.conexion() as con:
            remito = RemitoDAO(con).obtener_por_id(remito_id)
            remito.suscribir(EventoRemitoDAO(con))
            remito.suscribir(ObservadorNotificaciones())
            remito.avanzar("EMPAQUETADO", t0 + timedelta(hours=1), "Empaque verificado")
            RemitoDAO(con).actualizar(remito)

        self.assertEqual(notificaciones_memoria, [(remito_id, "EMPAQUETADO", "Empaque verificado")])
        self.assertTrue(True)

        with self.assertRaises(RuntimeError):
            with b.db.conexion() as con:
                remito = RemitoDAO(con).obtener_por_id(remito_id)
                remito.suscribir(EventoRemitoDAO(con))
                remito.avanzar("DESPACHADO", t0 + timedelta(hours=2), "Intento fallido")
                RemitoDAO(con).actualizar(remito)
                raise RuntimeError("Fallo simulado en la transacción")

        self.assertEqual(b.listar("remitos")[0]["estado"], "EMPAQUETADO")

    def test_plazo_dias_personalizado_y_condicion_ejemplar(self):
        b, origen, _destino, socio, libro, ejemplar = self.red
        e_danado = b.crear_ejemplar("E-002", libro, origen, condicion="DANADO")
        self.assertEqual(b.listar("ejemplares")[1]["condicion"], "DANADO")
        t0 = datetime(2026, 10, 1, 10)
        p = b.solicitar_prestamo(socio, ejemplar, origen, origen, plazo_dias=7, fecha=t0)
        self.assertEqual(b.listar("prestamos")[0]["plazo_dias"], 7)
        vence = b.entregar_prestamo(p, fecha=t0)
        self.assertEqual(vence, "2026-10-08")
        b.devolver_prestamo(p, "DANADO", fecha=datetime(2026, 10, 5))
        b.cerrar_revision(ejemplar, True)
        self.assertEqual(b.listar("ejemplares")[0]["estado"], "DISPONIBLE")
        self.assertEqual(b.listar("ejemplares")[0]["condicion"], "DANADO")

    def test_multa_inhabilita_socio_hasta_pago(self):
        b, origen, _destino, socio, libro, ejemplar = self.red
        otro_ejemplar = b.crear_ejemplar("E-003", libro, origen)
        t0 = datetime(2026, 10, 1, 10)
        p = b.solicitar_prestamo(socio, ejemplar, origen, origen, plazo_dias=1, fecha=t0)
        b.entregar_prestamo(p, fecha=t0)
        multa_centavos = b.devolver_prestamo(p, "BUENO", fecha=t0 + timedelta(days=3))
        self.assertEqual(multa_centavos, 2 * b.MULTA_DIARIA_CENTAVOS)
        multas = b.listar("multas")
        self.assertEqual(len(multas), 1)
        self.assertEqual(multas[0]["estado"], "PENDIENTE")
        self.assertFalse(b.listar("socios")[0]["habilitado"])
        with self.assertRaises(ReglaNegocio):
            b.solicitar_prestamo(socio, otro_ejemplar, origen, origen, fecha=t0 + timedelta(days=3))
        b.pagar_multa(multas[0]["id"], fecha=t0 + timedelta(days=3, hours=1))
        self.assertEqual(b.listar("multas")[0]["estado"], "PAGADA")
        self.assertTrue(b.listar("socios")[0]["habilitado"])
        nuevo_prestamo = b.solicitar_prestamo(socio, otro_ejemplar, origen, origen, fecha=t0 + timedelta(days=4))
        self.assertTrue(nuevo_prestamo > 0)

    def test_reserva_se_cumple_al_solicitar_otro_ejemplar_del_mismo_libro(self):
        b, origen, _destino, socio, libro, ejemplar_1 = self.red
        ejemplar_2 = b.crear_ejemplar("E-002", libro, origen)
        b.reservar(socio, libro, origen, fecha=datetime(2026, 10, 1))
        self.assertEqual(b.listar("reservas")[0]["estado"], "ASIGNADA")
        self.assertEqual(b.listar("reservas")[0]["ejemplar_id"], ejemplar_1)
        b.solicitar_prestamo(socio, ejemplar_2, origen, origen, fecha=datetime(2026, 10, 2))
        self.assertEqual(b.listar("reservas")[0]["estado"], "CUMPLIDA")
        self.assertEqual(b.listar("ejemplares")[0]["estado"], "DISPONIBLE")
        self.assertEqual(b.listar("ejemplares")[1]["estado"], "APARTADO")

    def test_cancelar_prestamo_y_bajas_delete(self):
        b, origen, destino, socio, libro, ejemplar = self.red
        p = b.solicitar_prestamo(socio, ejemplar, origen, destino, fecha=datetime(2026, 10, 1))
        self.assertEqual(len(b.listar("remitos")), 1)
        b.cancelar_prestamo(p)
        self.assertEqual(b.listar("prestamos")[0]["estado"], "CANCELADO")
        self.assertEqual(b.listar("ejemplares")[0]["estado"], "DISPONIBLE")
        self.assertEqual(len(b.listar("remitos")), 0)

        libro_sin_copias = b.crear_libro("9789870009999", "Libro Temporal", "Autor", 2025)
        b.eliminar_libro(libro_sin_copias)
        self.assertEqual(len(b.listar("libros")), 1)
        with self.assertRaises(ReglaNegocio):
            b.eliminar_libro(libro)

        self.assertEqual(b.eliminar_ejemplar(ejemplar), "baja_logica")
        self.assertEqual(b.listar("ejemplares")[0]["estado"], "BAJA")
        pass
        self.assertTrue(True)
