"""Carga los datos iniciales en la base de datos principal (demo_biblioteca.db)."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from .services.biblioteca_service import Biblioteca


def poblar(ruta: str | Path = "demo_biblioteca.db", reset: bool = True) -> Biblioteca:
    ruta = Path(ruta)
    if ruta.exists() and reset:
        ruta.unlink()
    b = Biblioteca(ruta)
    if b.listar("sedes"):
        return b

    ahora = datetime.now().replace(microsecond=0)
    t_inicio = ahora - timedelta(days=12)

    # 1. Sedes de la red (las 3 sedes originales)
    centro = b.crear_sede("Biblioteca Central", "Av. Vélez Sarsfield 1200", "351 555-0101", "Lun a vie · 9 a 19")
    norte = b.crear_sede("Sede Norte", "Av. Colón 4300", "351 555-0102", "Lun a vie · 9 a 18")
    sur = b.crear_sede("Sede Sur", "Av. Armada Argentina 500", "351 555-0103", "Lun a sáb · 9 a 17")

    # 2. Padrón de socios
    martin = b.crear_socio("40111222", "Martín Boiero", "martin.boiero@example.com")
    jeremias = b.crear_socio("41222333", "Jeremías López Ferreyra", "jeremias.lopez@example.com")
    francisco = b.crear_socio("42333444", "Francisco González", "francisco.gonzalez@example.com")
    ignacio = b.crear_socio("43444555", "Ignacio Cuello", "ignacio.cuello@example.com")
    pedro = b.crear_socio("44555666", "Pedro González", "pedro.gonzalez@example.com")

    # 3. Catálogo de libros (materiales)
    hp1 = b.crear_libro("9788478884452", "Harry Potter y la piedra filosofal", "J. K. Rowling", 1997)
    hp2 = b.crear_libro("9788478884957", "Harry Potter y la cámara secreta", "J. K. Rowling", 1998)
    hp3 = b.crear_libro("9788422685210", "Harry Potter y el prisionero de Azkaban", "J. K. Rowling", 1999)
    hambre1 = b.crear_libro("9788427202122", "Los juegos del hambre", "Suzanne Collins", 2008)
    hambre2 = b.crear_libro("9788427202139", "Los juegos del hambre: En llamas", "Suzanne Collins", 2009)
    principito = b.crear_libro("9788498381498", "El principito", "Antoine de Saint-Exupéry", 1943)
    got = b.crear_libro("9788496208490", "Game of Thrones", "George R. R. Martin", 1996)
    sawyer = b.crear_libro("9788491050278", "Las aventuras de Tom Sawyer", "Mark Twain", 1876)
    caspian = b.crear_libro("9788408054283", "Narnia: El príncipe Caspian", "C. S. Lewis", 1951)
    silla = b.crear_libro("9788408054290", "Narnia: La silla de plata", "C. S. Lewis", 1953)

    # 4. Ejemplares físicos: 2 por libro, con códigos secuenciales por sede
    e_cen_1 = b.crear_ejemplar("CEN-001", hp1, centro)
    b.crear_ejemplar("CEN-002", hp1, centro)
    b.crear_ejemplar("CEN-003", hp2, centro)
    e_cen_4 = b.crear_ejemplar("CEN-004", principito, centro)
    b.crear_ejemplar("CEN-005", principito, centro)
    e_cen_6 = b.crear_ejemplar("CEN-006", got, centro)
    b.crear_ejemplar("CEN-007", caspian, centro)
    b.crear_ejemplar("CEN-008", hambre1, centro)

    e_nor_1 = b.crear_ejemplar("NOR-001", hp2, norte)
    e_nor_2 = b.crear_ejemplar("NOR-002", hp3, norte)
    b.crear_ejemplar("NOR-003", hp3, norte)
    b.crear_ejemplar("NOR-004", hambre2, norte)
    e_nor_5 = b.crear_ejemplar("NOR-005", sawyer, norte)
    e_nor_6 = b.crear_ejemplar("NOR-006", silla, norte)

    e_sur_1 = b.crear_ejemplar("SUR-001", hambre1, sur)
    b.crear_ejemplar("SUR-002", hambre2, sur)
    b.crear_ejemplar("SUR-003", got, sur)
    e_sur_4 = b.crear_ejemplar("SUR-004", sawyer, sur)
    e_sur_5 = b.crear_ejemplar("SUR-005", caspian, sur)
    b.crear_ejemplar("SUR-006", silla, sur)

    # 5. Préstamos históricos ya devueltos (para historial, multas y estadísticas)
    # 5a. Préstamo devuelto con atraso -> genera Multa PENDIENTE (Pedro queda inhabilitado)
    p_multa_pend = b.solicitar_prestamo(pedro, e_cen_6, centro, centro, plazo_dias=3, fecha=t_inicio)
    b.entregar_prestamo(p_multa_pend, plazo_dias=3, fecha=t_inicio + timedelta(hours=1))
    b.devolver_prestamo(p_multa_pend, "BUENO", fecha=t_inicio + timedelta(days=6))

    # 5b. Préstamo devuelto con atraso -> genera Multa e Ignacio ya la abona (PAGADA)
    p_multa_pagada = b.solicitar_prestamo(ignacio, e_sur_4, sur, sur, plazo_dias=2, fecha=t_inicio + timedelta(days=1))
    b.entregar_prestamo(p_multa_pagada, plazo_dias=2, fecha=t_inicio + timedelta(days=1, hours=1))
    b.devolver_prestamo(p_multa_pagada, "BUENO", fecha=t_inicio + timedelta(days=5))
    multa_pagada_id = max(m["id"] for m in b.listar("multas"))
    b.pagar_multa(multa_pagada_id, fecha=t_inicio + timedelta(days=5, hours=2))

    # 5c. Préstamo devuelto con ejemplar DAÑADO -> queda EN_REVISION en Catálogo
    p_danado = b.solicitar_prestamo(francisco, e_nor_5, norte, norte, plazo_dias=7, fecha=t_inicio + timedelta(days=2))
    b.entregar_prestamo(p_danado, plazo_dias=7, fecha=t_inicio + timedelta(days=2, hours=1))
    b.devolver_prestamo(p_danado, "DANADO", fecha=t_inicio + timedelta(days=4))

    # 5d. Préstamo interbibliotecario completo (ida + entrega + devolución + regreso recibido)
    p_inter_hist = b.solicitar_prestamo(jeremias, e_sur_5, sur, norte, plazo_dias=5, fecha=t_inicio + timedelta(days=1))
    rem_ida_hist = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(rem_ida_hist, "EMPAQUETADO", fecha=t_inicio + timedelta(days=1, hours=1), detalle="Empaque protegido")
    b.avanzar_remito(rem_ida_hist, "DESPACHADO", fecha=t_inicio + timedelta(days=1, hours=2), detalle="Despacho hacia Sede Norte")
    b.avanzar_remito(rem_ida_hist, "RECIBIDO", fecha=t_inicio + timedelta(days=1, hours=5), detalle="Recibido en Sede Norte")
    b.entregar_prestamo(p_inter_hist, plazo_dias=5, fecha=t_inicio + timedelta(days=1, hours=6))
    b.devolver_prestamo(p_inter_hist, "BUENO", fecha=t_inicio + timedelta(days=4))
    rem_reg_hist = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(rem_reg_hist, "EMPAQUETADO", fecha=t_inicio + timedelta(days=4, hours=1), detalle="Preparado para retorno")
    b.avanzar_remito(rem_reg_hist, "DESPACHADO", fecha=t_inicio + timedelta(days=4, hours=2), detalle="Regresa a Sede Sur")
    b.avanzar_remito(rem_reg_hist, "RECIBIDO", fecha=t_inicio + timedelta(days=4, hours=6), detalle="Reingresado en Sede Sur")

    # 6. Préstamos actualmente en circulación
    t = ahora - timedelta(days=5)

    # 6a. Préstamo local ACTIVO en término (Martín Boiero)
    local_martin = b.solicitar_prestamo(martin, e_cen_1, centro, centro, plazo_dias=14, fecha=t)
    b.entregar_prestamo(local_martin, plazo_dias=14, fecha=t + timedelta(hours=1))

    # 6b. Préstamo local ACTIVO VENCIDO (Francisco González -> aparece en reporte de vencidos)
    t_vencido = ahora - timedelta(days=3)
    prestamo_vencido = b.solicitar_prestamo(francisco, e_cen_4, centro, centro, plazo_dias=1, fecha=t_vencido)
    b.entregar_prestamo(prestamo_vencido, plazo_dias=1, fecha=t_vencido)

    # 6c. Préstamo interbibliotecario EN_TRANSITO (Jeremías López Ferreyra, de Norte a Central)
    b.solicitar_prestamo(jeremias, e_nor_1, norte, centro, plazo_dias=14, fecha=t + timedelta(days=1))
    ida_transito = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_transito, "EMPAQUETADO", fecha=t + timedelta(days=1, hours=1), detalle="Caja sellada")
    b.avanzar_remito(ida_transito, "DESPACHADO", fecha=t + timedelta(days=1, hours=2), detalle="Sale de Sede Norte")

    # 6d. Préstamo interbibliotecario ACTIVO (Ignacio Cuello, de Sur a Central)
    recibido_ignacio = b.solicitar_prestamo(ignacio, e_sur_1, sur, centro, plazo_dias=10, fecha=t + timedelta(days=2))
    ida_ignacio = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_ignacio, "EMPAQUETADO", fecha=t + timedelta(days=2, hours=1), detalle="Embalaje verificado")
    b.avanzar_remito(ida_ignacio, "DESPACHADO", fecha=t + timedelta(days=2, hours=2), detalle="En camino a Central")
    b.avanzar_remito(ida_ignacio, "RECIBIDO", fecha=t + timedelta(days=2, hours=5), detalle="Recibido sin observaciones")
    b.entregar_prestamo(recibido_ignacio, plazo_dias=10, fecha=t + timedelta(days=2, hours=6))

    # 6e. Préstamo interbibliotecario LISTO para entregar (Martín Boiero, de Norte a Sur)
    b.solicitar_prestamo(martin, e_nor_2, norte, sur, plazo_dias=7, fecha=t + timedelta(days=3))
    ida_listo = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_listo, "EMPAQUETADO", fecha=t + timedelta(days=3, hours=1), detalle="Bolsa precintada")
    b.avanzar_remito(ida_listo, "DESPACHADO", fecha=t + timedelta(days=3, hours=2), detalle="Sale de Sede Norte")
    b.avanzar_remito(ida_listo, "RECIBIDO", fecha=t + timedelta(days=3, hours=4), detalle="Disponible en mostrador de Sede Sur")

    # 6f. Préstamo local SOLICITADO pendiente de entrega (Jeremías López Ferreyra)
    b.solicitar_prestamo(jeremias, e_nor_6, norte, norte, plazo_dias=14, fecha=ahora - timedelta(hours=3))

    # 7. Reservas (una ASIGNADA sobre CEN-002 en Central y una EN_ESPERA en Norte)
    b.reservar(francisco, hp1, centro, fecha=t + timedelta(days=3))
    b.reservar(ignacio, hp2, norte, fecha=t + timedelta(days=4))

    return b


def main():
    parser = argparse.ArgumentParser(description="Inicializar base de datos de la biblioteca con datos de prueba")
    parser.add_argument("--db", default="demo_biblioteca.db", help="Ruta de la base SQLite (por defecto demo_biblioteca.db)")
    parser.add_argument(
        "--reset", action="store_true", default=True, help="Reiniciar la base con los datos iniciales"
    )
    args = parser.parse_args()
    poblar(args.db, reset=True)
    print(f"Base de datos inicializada con éxito: {args.db}")
    print(f"Iniciá el servidor con: python -m backend.web --db {args.db}")


if __name__ == "__main__":
    main()
