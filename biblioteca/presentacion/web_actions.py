"""Traducción de las acciones HTTP a casos de uso."""

from ..dominio.regla_negocio import ReglaNegocio


def _id(datos, nombre):
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


def ejecutar(b, datos):
    """Lista cerrada de operaciones; nunca ejecuta nombres enviados como método."""
    accion = datos.get("accion")
    if accion == "crear_sede":
        return b.crear_sede(*(_cadena(datos, x) for x in ("nombre", "direccion", "contacto", "horarios")))
    if accion == "editar_sede":
        return b.actualizar_sede(_id(datos, "id"), direccion=datos.get("direccion"),
                                 contacto=datos.get("contacto"), horarios=datos.get("horarios"),
                                 activa=datos.get("activa"))
    if accion == "crear_socio":
        return b.crear_socio(*(_cadena(datos, x) for x in ("documento", "nombre", "email")))
    if accion == "editar_socio":
        return b.actualizar_socio(_id(datos, "id"), nombre=datos.get("nombre"),
                                  email=datos.get("email"), habilitado=datos.get("habilitado"))
    if accion == "crear_libro":
        anio = datos.get("anio")
        return b.crear_libro(*(_cadena(datos, x) for x in ("isbn", "titulo", "autor")),
                             int(anio) if anio not in (None, "") else None)
    if accion == "editar_libro":
        anio = datos.get("anio")
        return b.actualizar_libro(_id(datos, "id"), titulo=datos.get("titulo"),
                                  autor=datos.get("autor"), anio=int(anio) if anio not in (None, "") else None)
    if accion == "crear_ejemplar":
        return b.crear_ejemplar(_cadena(datos, "codigo"), _id(datos, "libro_id"), _id(datos, "sede_id"))
    if accion == "reservar":
        return b.reservar(_id(datos, "socio_id"), _id(datos, "libro_id"), _id(datos, "sede_id"))
    if accion == "cancelar_reserva":
        return b.cancelar_reserva(_id(datos, "id"))
    if accion == "solicitar_prestamo":
        return b.solicitar_prestamo(*(_id(datos, x) for x in
            ("socio_id", "ejemplar_id", "sede_origen_id", "sede_destino_id")))
    if accion == "entregar_prestamo":
        return {"vence_en": b.entregar_prestamo(_id(datos, "id"))}
    if accion == "devolver_prestamo":
        return {"multa_centavos": b.devolver_prestamo(_id(datos, "id"), _cadena(datos, "condicion"))}
    if accion == "avanzar_remito":
        return b.avanzar_remito(_id(datos, "id"), _cadena(datos, "estado"), detalle=datos.get("detalle", ""))
    if accion == "cerrar_revision":
        apto = datos.get("apto")
        if not isinstance(apto, bool):
            raise ReglaNegocio("apto debe ser verdadero o falso")
        return b.cerrar_revision(_id(datos, "ejemplar_id"), apto)
    raise ReglaNegocio("Operación desconocida")


