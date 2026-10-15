from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from biblioteca import Biblioteca, ReglaNegocio
from biblioteca.dominio.catalogo.ejemplar import Ejemplar
from biblioteca.dominio.prestamos.fabrica_prestamos import FabricaPrestamos
from biblioteca.dominio.reservas.reserva import Reserva


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
        assert b.listar("remitos")[0]["estado"] == "CREADO"
        assert [x["estado"] for x in b.historial_remito(ida)] == ["CREADO"]
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
        b.cerrar_revision(ejemplar, True)
        assert b.listar("ejemplares")[0]["estado"] == "DISPONIBLE"


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

    def test_state_de_prestamos_valida_sus_transiciones(self):
        local = FabricaPrestamos.crear(1, 1, 1, 1)
        local.avanzar("ACTIVO")
        local.avanzar("DEVUELTO")
        assert local.estado == "DEVUELTO"
        with self.assertRaises(ReglaNegocio):
            local.avanzar("ACTIVO")

        interbibliotecario = FabricaPrestamos.crear(1, 1, 1, 2)
        with self.assertRaises(ReglaNegocio):
            interbibliotecario.avanzar("ACTIVO")
        interbibliotecario.avanzar("EN_TRANSITO")
        interbibliotecario.avanzar("LISTO")
        interbibliotecario.avanzar("ACTIVO")
        assert interbibliotecario.estado == "ACTIVO"

    def test_state_de_ejemplar_y_reserva_valida_sus_transiciones(self):
        ejemplar = Ejemplar(1, "E-001", 1, 1, 1)
        with self.assertRaises(ReglaNegocio):
            ejemplar.avanzar("PRESTADO")
        ejemplar.avanzar("RESERVADO")
        ejemplar.avanzar("APARTADO")
        ejemplar.avanzar("PRESTADO")
        ejemplar.avanzar("EN_REVISION")
        ejemplar.avanzar("DISPONIBLE")
        assert ejemplar.estado == "DISPONIBLE"

        reserva = Reserva(1, 1, 1, 1, "2026-10-01T10:00:00")
        with self.assertRaises(ReglaNegocio):
            reserva.avanzar("CUMPLIDA")
        reserva.asignar_ejemplar(1)
        reserva.avanzar("CUMPLIDA")
        assert reserva.estado == "CUMPLIDA"
