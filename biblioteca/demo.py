"""Crea datos de demostración en una base separada y vacía."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from .servicio import Biblioteca


def poblar(ruta):
    ruta = Path(ruta)
    if ruta.exists() and ruta.stat().st_size:
        raise ValueError(f"La base ya existe y no se modificó: {ruta}")
    b = Biblioteca(ruta)
    t = datetime.now().replace(microsecond=0) - timedelta(days=5)
    centro = b.crear_sede("Biblioteca Central", "Av. Vélez Sarsfield 1200", "351 555-0101", "Lun a vie · 9 a 19")
    norte = b.crear_sede("Sede Norte", "Av. Colón 4300", "351 555-0102", "Lun a vie · 9 a 18")
    sur = b.crear_sede("Sede Sur", "Av. Armada Argentina 500", "351 555-0103", "Lun a sáb · 9 a 17")
    ana = b.crear_socio("30123456", "Ana Ledesma", "ana.ledesma@example.com")
    lucas = b.crear_socio("32987654", "Lucas Díaz", "lucas.diaz@example.com")
    maria = b.crear_socio("28555111", "María Torres", "maria.torres@example.com")
    b.crear_socio("34444777", "Sofía Aguirre", "sofia.aguirre@example.com")
    objetos = b.crear_libro("9789870001001", "Diseño de aplicaciones con objetos", "M. Salvatierra", 2024)
    datos = b.crear_libro("9789870001002", "Datos en movimiento", "L. Pereyra", 2022)
    redes = b.crear_libro("9789870001003", "Redes de lectura", "V. Carrizo", 2021)
    archivo = b.crear_libro("9789870001004", "El archivo compartido", "P. Molina", 2025)
    e1 = b.crear_ejemplar("CEN-001", objetos, centro)
    b.crear_ejemplar("CEN-002", objetos, centro)
    e3 = b.crear_ejemplar("NOR-014", datos, norte)
    e4 = b.crear_ejemplar("SUR-008", redes, sur)
    b.crear_ejemplar("SUR-009", archivo, sur)
    b.crear_ejemplar("NOR-015", archivo, norte)

    local = b.solicitar_prestamo(ana, e1, centro, centro, fecha=t)
    b.entregar_prestamo(local, fecha=t + timedelta(hours=1))

    inter = b.solicitar_prestamo(lucas, e3, norte, centro, fecha=t + timedelta(days=1))
    ida = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida, "EMPAQUETADO", fecha=t + timedelta(days=1, hours=1), detalle="Caja sellada")
    b.avanzar_remito(ida, "DESPACHADO", fecha=t + timedelta(days=1, hours=2), detalle="Sale de Sede Norte")

    recibido = b.solicitar_prestamo(maria, e4, sur, centro, fecha=t + timedelta(days=2))
    ida2 = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida2, "EMPAQUETADO", fecha=t + timedelta(days=2, hours=1))
    b.avanzar_remito(ida2, "DESPACHADO", fecha=t + timedelta(days=2, hours=2))
    b.avanzar_remito(ida2, "RECIBIDO", fecha=t + timedelta(days=2, hours=5), detalle="Recibido sin observaciones")
    b.entregar_prestamo(recibido, fecha=t + timedelta(days=2, hours=6))
    b.reservar(lucas, objetos, centro, fecha=t + timedelta(days=3))
    return b


def main():
    parser = argparse.ArgumentParser(description="Crear base de muestra de la biblioteca")
    parser.add_argument("--db", default="demo_biblioteca.db")
    args = parser.parse_args()
    poblar(args.db)
    print(f"Base de demostración creada: {args.db}")
    print(f"Iniciá la interfaz con: python -m biblioteca.web --db {args.db}")


if __name__ == "__main__":
    main()
