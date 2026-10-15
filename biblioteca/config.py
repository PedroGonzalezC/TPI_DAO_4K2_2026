"""Rutas por defecto independientes del directorio de ejecución."""

from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
BASE_PREDETERMINADA = RAIZ_PROYECTO / "biblioteca.db"
DEMO_PREDETERMINADA = RAIZ_PROYECTO / "demo_biblioteca.db"
