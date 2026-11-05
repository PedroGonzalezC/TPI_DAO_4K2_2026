"""Operaciones compartidas por las entradas de consola y web."""

from ..models.modelo import ReglaNegocio


def _id(datos, nombre="id"):
    try:
        valor = int(datos[nombre])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReglaNegocio(f"{nombre} debe ser un número entero") from exc
    if valor <= 0:
        raise ReglaNegocio(f"{nombre} debe ser positivo")
    return valor


def _cadena(datos, nombre):
    valor = datos.get(nombre)
    if not isinstance(valor, str):
        raise ReglaNegocio(f"{nombre} es obligatorio")
    return valor


def _anio(datos):
    valor = datos.get("anio")
    return int(valor) if valor not in (None, "") else None


def _apto(datos):
    valor = datos.get("apto")
    if not isinstance(valor, bool):
        raise ReglaNegocio("apto debe ser verdadero o falso")
    return valor


# Lista explícita: un cliente solo puede ejecutar estas operaciones públicas.
OPERACIONES = {
    "crear_sede": lambda b, d: b.crear_sede(*(_cadena(d, k) for k in ("nombre", "direccion", "contacto", "horarios"))),
    "editar_sede": lambda b, d: b.actualizar_sede(_id(d), direccion=d.get("direccion"),
        contacto=d.get("contacto"), horarios=d.get("horarios"), activa=d.get("activa")),
    "crear_socio": lambda b, d: b.crear_socio(*(_cadena(d, k) for k in ("documento", "nombre", "email"))),
    "editar_socio": lambda b, d: b.actualizar_socio(_id(d), nombre=d.get("nombre"),
        email=d.get("email"), habilitado=d.get("habilitado")),
    "crear_libro": lambda b, d: b.crear_libro(*(_cadena(d, k) for k in ("isbn", "titulo", "autor")), _anio(d)),
    "editar_libro": lambda b, d: b.actualizar_libro(_id(d), titulo=d.get("titulo"), autor=d.get("autor"), anio=_anio(d)),
    "crear_ejemplar": lambda b, d: b.crear_ejemplar(_cadena(d, "codigo"), _id(d, "libro_id"), _id(d, "sede_id")),
    "reservar": lambda b, d: b.reservar(_id(d, "socio_id"), _id(d, "libro_id"), _id(d, "sede_id")),
    "cancelar_reserva": lambda b, d: b.cancelar_reserva(_id(d)),
    "solicitar_prestamo": lambda b, d: b.solicitar_prestamo(*(_id(d, k) for k in
        ("socio_id", "ejemplar_id", "sede_origen_id", "sede_destino_id"))),
    "entregar_prestamo": lambda b, d: {"vence_en": b.entregar_prestamo(_id(d))},
    "devolver_prestamo": lambda b, d: {"multa_centavos": b.devolver_prestamo(_id(d), _cadena(d, "condicion"))},
    "avanzar_remito": lambda b, d: b.avanzar_remito(_id(d), _cadena(d, "estado").upper(), detalle=d.get("detalle", "")),
    "cerrar_revision": lambda b, d: b.cerrar_revision(_id(d, "ejemplar_id"), _apto(d)),
    "listar": lambda b, d: b.listar(_cadena(d, "tabla")),
    "disponibilidad": lambda b, d: b.disponibilidad(d.get("sede")),
    "historial_remito": lambda b, d: b.historial_remito(_id(d)),
    "reporte": lambda b, d: b.reportes(_cadena(d, "nombre")),
}


def ejecutar(biblioteca, datos):
    operacion = OPERACIONES.get(datos.get("accion"))
    if operacion is None:
        raise ReglaNegocio("Operación desconocida")
    return operacion(biblioteca, datos)
