"""Servidor web local para la interfaz del TPI, sin dependencias externas."""

import argparse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

from .config import BASE_PREDETERMINADA
from .aplicacion.biblioteca import Biblioteca
from .presentacion.manejador_web import ManejadorWeb


def crear_servidor(ruta_db, puerto=8000):
    biblioteca = Biblioteca(ruta_db)
    nombre_base = Path(ruta_db).name
    manejador = partial(ManejadorWeb, biblioteca=biblioteca, nombre_base=nombre_base)
    return ThreadingHTTPServer(("127.0.0.1", puerto), manejador)


def main():
    parser = argparse.ArgumentParser(description="Interfaz web local de la biblioteca")
    parser.add_argument("--db", default=BASE_PREDETERMINADA, help="Ruta de la base SQLite")
    parser.add_argument("--port", type=int, default=8000, help="Puerto local (por defecto 8000)")
    args = parser.parse_args()
    servidor = crear_servidor(args.db, args.port)
    print(f"Biblioteca disponible en http://127.0.0.1:{servidor.server_port}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
