"""Compatibilidad de los comandos al compartir operaciones con la web."""

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from backend.__main__ import main


class TestConsola(TestCase):
    def test_circuito_completo_desde_consola(self):
        carpeta = Path(__file__).parent / ".tmp"
        carpeta.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=carpeta) as temporal:
            ruta = str(Path(temporal) / "consola.db")

            def comando(*argumentos):
                salida = StringIO()
                argv = ["biblioteca", "--db", ruta, *map(str, argumentos)]
                with patch("sys.argv", argv), redirect_stdout(salida):
                    main()
                return json.loads(salida.getvalue())["resultado"]

            origen = comando("sede-crear", "Centro", "Calle 1", "111", "9-18")
            destino = comando("sede-crear", "Norte", "Calle 2", "222", "9-17")
            socio = comando("socio-crear", "123", "Ana", "ana@example.com")
            libro = comando("libro-crear", "isbn-1", "Objetos", "Autor", "--anio", 2024)
            ejemplar = comando("ejemplar-crear", "E-1", libro, origen)
            comando("sede-editar", origen, "--contacto", "999")
            comando("socio-editar", socio, "--email", "nuevo@example.com")
            comando("libro-editar", libro, "--titulo", "Objetos II")
            reserva = comando("reserva-crear", socio, libro, origen)
            comando("reserva-cancelar", reserva)
            prestamo = comando("prestamo-solicitar", socio, ejemplar, origen, destino)
            remito = comando("listar", "remitos")[0]["id"]
            for estado in ("empaquetado", "despachado", "recibido"):
                comando("remito-avanzar", remito, estado, "--detalle", "Prueba CLI")
            self.assertEqual(len(comando("remito-historial", remito)), 4)
            self.assertIn("vence_en", comando("prestamo-entregar", prestamo))
            self.assertEqual(comando("prestamo-devolver", prestamo, "--condicion", "DANADO"), {"multa_centavos": 0})
            regreso = comando("listar", "remitos")[1]["id"]
            for estado in ("EMPAQUETADO", "DESPACHADO", "RECIBIDO"):
                comando("remito-avanzar", regreso, estado)
            comando("revision-cerrar", ejemplar, "--apto", 1)
            self.assertEqual(comando("disponibilidad", "--sede", origen)[0]["disponibles"], 1)
            self.assertEqual(comando("reporte", "logistica")[0]["recibidos"], 2)
            self.assertEqual(comando("listar", "socios")[0]["email"], "nuevo@example.com")
