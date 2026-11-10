"""Carga los datos iniciales en la base de datos principal (biblioteca.db)."""

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
    ana = b.crear_socio("30123456", "Ana Ledesma", "ana.ledesma@example.com")
    lucas = b.crear_socio("32987654", "Lucas Díaz", "lucas.diaz@example.com")
    maria = b.crear_socio("28555111", "María Torres", "maria.torres@example.com")
    sofia = b.crear_socio("34444777", "Sofía Aguirre", "sofia.aguirre@example.com")
    martin = b.crear_socio("31222333", "Martín Pereyra", "martin.pereyra@example.com")
    valentina = b.crear_socio("36777888", "Valentina Gómez", "valentina.gomez@example.com")
    nicolas = b.crear_socio("33999000", "Nicolás Ferreyra", "nicolas.ferreyra@example.com")
    camila = b.crear_socio("38111444", "Camila Quiroga", "camila.quiroga@example.com")

    # 3. Catálogo de libros
    objetos = b.crear_libro("9789870001001", "Diseño de aplicaciones con objetos", "M. Salvatierra", 2024)
    datos = b.crear_libro("9789870001002", "Datos en movimiento", "L. Pereyra", 2022)
    redes = b.crear_libro("9789870001003", "Redes de lectura", "V. Carrizo", 2021)
    archivo = b.crear_libro("9789870001004", "El archivo compartido", "P. Molina", 2025)
    arquitectura = b.crear_libro("9789870001005", "Arquitectura de software limpia", "R. Ceballos", 2023)
    patrones = b.crear_libro("9789870001006", "Patrones de diseño en Python", "E. Domínguez", 2024)
    relacionales = b.crear_libro("9789870001007", "Bases de datos relacionales", "C. Villalba", 2020)
    requerimientos = b.crear_libro("9789870001008", "Ingeniería de requerimientos", "G. Acosta", 2022)

    # 4. Ejemplares físicos distribuidos en las 3 sedes
    e_cen_1 = b.crear_ejemplar("CEN-001", objetos, centro)
    e_cen_2 = b.crear_ejemplar("CEN-002", objetos, centro)
    e_cen_3 = b.crear_ejemplar("CEN-003", archivo, centro)
    e_cen_4 = b.crear_ejemplar("CEN-004", arquitectura, centro)
    b.crear_ejemplar("CEN-005", patrones, centro, condicion="DANADO")
    e_cen_6 = b.crear_ejemplar("CEN-006", relacionales, centro)
    e_nor_1 = b.crear_ejemplar("NOR-014", datos, norte)
    b.crear_ejemplar("NOR-015", archivo, norte)
    e_nor_3 = b.crear_ejemplar("NOR-016", relacionales, norte)
    e_nor_4 = b.crear_ejemplar("NOR-017", arquitectura, norte)
    e_nor_5 = b.crear_ejemplar("NOR-018", requerimientos, norte)
    e_sur_1 = b.crear_ejemplar("SUR-008", redes, sur)
    e_sur_2 = b.crear_ejemplar("SUR-009", archivo, sur)
    e_sur_3 = b.crear_ejemplar("SUR-010", patrones, sur)
    b.crear_ejemplar("SUR-011", objetos, sur)

    # 5. Préstamos históricos ya devueltos (para historial, multas y estadísticas)
    # 5a. Préstamo devuelto con atraso -> genera Multa PENDIENTE (Martín queda inhabilitado)
    p_multa_pend = b.solicitar_prestamo(martin, e_cen_4, centro, centro, plazo_dias=3, fecha=t_inicio)
    b.entregar_prestamo(p_multa_pend, plazo_dias=3, fecha=t_inicio + timedelta(hours=1))
    b.devolver_prestamo(p_multa_pend, "BUENO", fecha=t_inicio + timedelta(days=6))

    # 5b. Préstamo devuelto con atraso -> genera Multa y Valentina ya la abona (PAGADA)
    p_multa_pagada = b.solicitar_prestamo(valentina, e_sur_3, sur, sur, plazo_dias=2, fecha=t_inicio + timedelta(days=1))
    b.entregar_prestamo(p_multa_pagada, plazo_dias=2, fecha=t_inicio + timedelta(days=1, hours=1))
    b.devolver_prestamo(p_multa_pagada, "BUENO", fecha=t_inicio + timedelta(days=5))
    multa_val_id = max(m["id"] for m in b.listar("multas"))
    b.pagar_multa(multa_val_id, fecha=t_inicio + timedelta(days=5, hours=2))

    # 5c. Préstamo devuelto con ejemplar DAÑADO -> queda EN_REVISION en Catálogo
    p_danado = b.solicitar_prestamo(camila, e_nor_5, norte, norte, plazo_dias=7, fecha=t_inicio + timedelta(days=2))
    b.entregar_prestamo(p_danado, plazo_dias=7, fecha=t_inicio + timedelta(days=2, hours=1))
    b.devolver_prestamo(p_danado, "DANADO", fecha=t_inicio + timedelta(days=4))

    # 5d. Préstamo interbibliotecario completo (ida + entrega + devolución + regreso recibido)
    p_inter_hist = b.solicitar_prestamo(nicolas, e_sur_2, sur, norte, plazo_dias=5, fecha=t_inicio + timedelta(days=1))
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

    # 6a. Préstamo local ACTIVO en término (Ana Ledesma)
    local_ana = b.solicitar_prestamo(ana, e_cen_1, centro, centro, plazo_dias=14, fecha=t)
    b.entregar_prestamo(local_ana, plazo_dias=14, fecha=t + timedelta(hours=1))

    # 6b. Préstamo local ACTIVO VENCIDO (Sofía Aguirre -> aparece en reporte de vencidos)
    t_vencido = ahora - timedelta(days=3)
    prestamo_vencido = b.solicitar_prestamo(sofia, e_cen_3, centro, centro, plazo_dias=1, fecha=t_vencido)
    b.entregar_prestamo(prestamo_vencido, plazo_dias=1, fecha=t_vencido)

    # 6c. Préstamo interbibliotecario EN_TRANSITO (Lucas Díaz)
    b.solicitar_prestamo(lucas, e_nor_1, norte, centro, plazo_dias=14, fecha=t + timedelta(days=1))
    ida_transito = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_transito, "EMPAQUETADO", fecha=t + timedelta(days=1, hours=1), detalle="Caja sellada")
    b.avanzar_remito(ida_transito, "DESPACHADO", fecha=t + timedelta(days=1, hours=2), detalle="Sale de Sede Norte")

    # 6d. Préstamo interbibliotecario ACTIVO (María Torres)
    recibido_maria = b.solicitar_prestamo(maria, e_sur_1, sur, centro, plazo_dias=10, fecha=t + timedelta(days=2))
    ida_maria = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_maria, "EMPAQUETADO", fecha=t + timedelta(days=2, hours=1), detalle="Embalaje verificado")
    b.avanzar_remito(ida_maria, "DESPACHADO", fecha=t + timedelta(days=2, hours=2), detalle="En camino a Central")
    b.avanzar_remito(ida_maria, "RECIBIDO", fecha=t + timedelta(days=2, hours=5), detalle="Recibido sin observaciones")
    b.entregar_prestamo(recibido_maria, plazo_dias=10, fecha=t + timedelta(days=2, hours=6))

    # 6e. Préstamo interbibliotecario LISTO para entregar (Valentina Gómez, de Norte a Sur)
    b.solicitar_prestamo(valentina, e_nor_4, norte, sur, plazo_dias=7, fecha=t + timedelta(days=3))
    ida_listo = b.listar("remitos")[-1]["id"]
    b.avanzar_remito(ida_listo, "EMPAQUETADO", fecha=t + timedelta(days=3, hours=1), detalle="Bolsa precintada")
    b.avanzar_remito(ida_listo, "DESPACHADO", fecha=t + timedelta(days=3, hours=2), detalle="Sale de Sede Norte")
    b.avanzar_remito(ida_listo, "RECIBIDO", fecha=t + timedelta(days=3, hours=4), detalle="Disponible en mostrador de Sede Sur")

    # 6f. Préstamo local SOLICITADO pendiente de entrega (Nicolás Ferreyra)
    b.solicitar_prestamo(nicolas, e_nor_3, norte, norte, plazo_dias=14, fecha=ahora - timedelta(hours=3))

    # 7. Reservas (una ASIGNADA sobre CEN-002 en Central y una EN_ESPERA en Norte)
    b.reservar(lucas, objetos, centro, fecha=t + timedelta(days=3))
    b.reservar(camila, datos, norte, fecha=t + timedelta(days=4))

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
