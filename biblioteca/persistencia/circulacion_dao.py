"""SQL del circuito de reservas, préstamos y remitos.

Recibe la conexión de la operación para compartir una única transacción.
"""


class CirculacionDAO:
    @staticmethod
    def crear_reserva(con, socio_id, libro_id, sede_id, fecha):
        return con.execute(
            "INSERT INTO reservas(socio_id,libro_id,sede_id,creada_en) VALUES(?,?,?,?)",
            (socio_id, libro_id, sede_id, fecha),
        ).lastrowid

    @staticmethod
    def primer_ejemplar_disponible(con, libro_id, sede_id):
        return con.execute("""
            SELECT id FROM ejemplares WHERE libro_id=? AND sede_actual_id=?
            AND estado='DISPONIBLE' ORDER BY id LIMIT 1
        """, (libro_id, sede_id)).fetchone()

    @staticmethod
    def primera_reserva_en_espera(con, libro_id, sede_id):
        return con.execute("""
            SELECT r.id FROM reservas r JOIN socios so ON so.id=r.socio_id
            JOIN sedes s ON s.id=r.sede_id WHERE r.libro_id=? AND r.sede_id=?
            AND r.estado='EN_ESPERA' AND so.habilitado=1 AND s.activa=1
            ORDER BY r.creada_en,r.id LIMIT 1
        """, (libro_id, sede_id)).fetchone()

    @staticmethod
    def asignar_reserva(con, reserva_id, ejemplar_id):
        con.execute("UPDATE reservas SET estado='ASIGNADA', ejemplar_id=? WHERE id=?",
                    (ejemplar_id, reserva_id))

    @staticmethod
    def cambiar_estado_reserva(con, reserva_id, estado):
        con.execute("UPDATE reservas SET estado=? WHERE id=?", (estado, reserva_id))

    @staticmethod
    def reserva_del_ejemplar(con, ejemplar_id):
        return con.execute("""
            SELECT id, socio_id, sede_id FROM reservas WHERE ejemplar_id=? AND estado='ASIGNADA'
        """, (ejemplar_id,)).fetchone()

    @staticmethod
    def cambiar_estado_ejemplar(con, ejemplar_id, estado):
        con.execute("UPDATE ejemplares SET estado=? WHERE id=?", (estado, ejemplar_id))

    @staticmethod
    def ubicar_ejemplar(con, ejemplar_id, sede_id):
        con.execute("UPDATE ejemplares SET sede_actual_id=? WHERE id=?", (sede_id, ejemplar_id))

    @staticmethod
    def crear_prestamo(con, prestamo, fecha):
        return con.execute("""
            INSERT INTO prestamos(socio_id,ejemplar_id,sede_origen_id,sede_destino_id,tipo,estado,solicitado_en)
            VALUES(?,?,?,?,?,'SOLICITADO',?)
        """, (prestamo.socio_id, prestamo.ejemplar_id, prestamo.sede_origen_id,
              prestamo.sede_destino_id, prestamo.tipo, fecha)).lastrowid

    @staticmethod
    def cambiar_estado_prestamo(con, prestamo_id, estado):
        con.execute("UPDATE prestamos SET estado=? WHERE id=?", (estado, prestamo_id))

    @staticmethod
    def activar_prestamo(con, prestamo_id, estado, entregado_en, vence_en):
        con.execute("UPDATE prestamos SET estado=?,entregado_en=?,vence_en=? WHERE id=?",
                    (estado, entregado_en, vence_en, prestamo_id))

    @staticmethod
    def devolver_prestamo(con, prestamo_id, estado, devuelto_en, condicion, multa_centavos):
        con.execute("""
            UPDATE prestamos SET estado=?, devuelto_en=?, condicion_devolucion=?, multa_centavos=?
            WHERE id=?
        """, (estado, devuelto_en, condicion, multa_centavos, prestamo_id))

    @staticmethod
    def crear_remito(con, prestamo_id, ejemplar_id, tipo, origen, destino, fecha):
        return con.execute("""
            INSERT INTO remitos(prestamo_id,ejemplar_id,tipo,origen_id,destino_id,estado,creado_en)
            VALUES(?,?,?,?,?,'CREADO',?)
        """, (prestamo_id, ejemplar_id, tipo, origen, destino, fecha)).lastrowid

    @staticmethod
    def ultima_fecha_remito(con, remito_id):
        return con.execute(
            "SELECT fecha FROM historial_remitos WHERE remito_id=? ORDER BY id DESC LIMIT 1",
            (remito_id,),
        ).fetchone()["fecha"]

    @staticmethod
    def avanzar_remito(con, remito_id, estado, recibido_en):
        con.execute("UPDATE remitos SET estado=?, recibido_en=? WHERE id=?",
                    (estado, recibido_en, remito_id))

    @staticmethod
    def fecha_recepcion_ida(con, prestamo_id):
        return con.execute(
            "SELECT recibido_en FROM remitos WHERE prestamo_id=? AND tipo='IDA'",
            (prestamo_id,),
        ).fetchone()["recibido_en"]

    @staticmethod
    def historial_remito(con, remito_id):
        return [dict(x) for x in con.execute(
            "SELECT estado,fecha,detalle FROM historial_remitos WHERE remito_id=? ORDER BY id",
            (remito_id,),
        )]
