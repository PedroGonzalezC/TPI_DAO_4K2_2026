import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from backend.database.configuracion import CONFIG, cargar_configuracion
from backend.database.datos import resolver_ruta_base


class TestConfiguracion(TestCase):
    def test_rutas_habituales_y_rutas_explicitas(self):
        carpeta = Path(__file__).resolve().parents[1] / 'database'
        self.assertEqual(resolver_ruta_base('biblioteca.db'), carpeta / 'biblioteca.db')
        self.assertEqual(resolver_ruta_base('demo_biblioteca.db'), carpeta / 'demo_biblioteca.db')
        self.assertEqual(resolver_ruta_base('otra_carpeta/ejemplo.db'), Path('otra_carpeta/ejemplo.db'))
        with patch('backend.database.datos.Path.exists', return_value=True):
            self.assertEqual(resolver_ruta_base('biblioteca.db'), Path('biblioteca.db'))

    def test_carga_valores_personalizados_y_rechaza_limites_invalidos(self):
        carpeta = Path(__file__).parent / ".tmp"
        carpeta.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=carpeta) as temporal:
            ruta = Path(temporal) / "config.json"
            personalizada = {**CONFIG, "plazo_dias": 7, "multa_diaria_centavos": 2500, "filas_por_pagina": 3}
            ruta.write_text(json.dumps(personalizada), encoding="utf-8")
            self.assertEqual(cargar_configuracion(ruta), personalizada)
            for clave, valor in (("plazo_dias", 0), ("multa_diaria_centavos", -1),
                                 ("filas_por_pagina", True), ("puerto", 65536), ("idioma", "")):
                with self.subTest(clave=clave):
                    ruta.write_text(json.dumps({**personalizada, clave: valor}), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, clave):
                        cargar_configuracion(ruta)
