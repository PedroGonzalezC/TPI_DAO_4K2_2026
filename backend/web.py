"""Punto de entrada del servidor web FastAPI para la interfaz de la biblioteca."""

import argparse
from pathlib import Path

import uvicorn

from .controllers.app import crear_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor FastAPI local de la biblioteca")
    parser.add_argument("--db", default="biblioteca.db", help="Ruta de la base SQLite")
    parser.add_argument("--port", type=int, default=8000, help="Puerto local (por defecto 8000)")
    args = parser.parse_args()
    app = crear_app(Path(args.db))
    print(f"Biblioteca disponible en http://127.0.0.1:{args.port}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
