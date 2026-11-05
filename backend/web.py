"""Inicio local del servidor FastAPI."""

import argparse
import uvicorn

from .controllers.api import crear_app
from .database.configuracion import CONFIG


def main():
    parser = argparse.ArgumentParser(description='Interfaz web local de la biblioteca')
    parser.add_argument('--db', default=CONFIG['base_datos'], help='Ruta de la base SQLite')
    parser.add_argument('--port', type=int, default=CONFIG['puerto'], help='Puerto local')
    args = parser.parse_args()
    uvicorn.run(crear_app(args.db), host='127.0.0.1', port=args.port)


if __name__ == '__main__':
    main()
