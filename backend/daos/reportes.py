"""Catálogo de reportes: cada consulta se define junto con su nombre visible."""

REPORTES = {
    "activos_transito": ("Préstamos y material en tránsito", """
        SELECT p.id, l.titulo, e.codigo, so.nombre socio, p.tipo,
               CASE WHEN r.id IS NOT NULL THEN 'RETORNO_EN_TRANSITO' ELSE p.estado END estado,
               CASE WHEN r.id IS NOT NULL THEN d.nombre ELSE o.nombre END origen,
               CASE WHEN r.id IS NOT NULL THEN o.nombre ELSE d.nombre END destino,
               p.vence_en
        FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
        JOIN libros l ON l.id=e.libro_id JOIN socios so ON so.id=p.socio_id
        JOIN sedes o ON o.id=p.sede_origen_id JOIN sedes d ON d.id=p.sede_destino_id
        LEFT JOIN remitos r ON r.prestamo_id=p.id AND r.tipo='REGRESO' AND r.estado='DESPACHADO'
        WHERE p.estado IN ('ACTIVO','EN_TRANSITO','LISTO') OR r.id IS NOT NULL ORDER BY p.id
    """),
    "vencidos_multas": ("Préstamos vencidos y multas", """
        SELECT p.id, so.nombre socio, l.titulo, p.vence_en,
               CAST(julianday(:hoy) - julianday(p.vence_en) AS INTEGER) dias_atraso,
               CAST(julianday(:hoy) - julianday(p.vence_en) AS INTEGER) * :multa multa_estimada_centavos
        FROM prestamos p JOIN socios so ON so.id=p.socio_id
        JOIN ejemplares e ON e.id=p.ejemplar_id JOIN libros l ON l.id=e.libro_id
        WHERE p.estado='ACTIVO' AND p.vence_en < :hoy ORDER BY dias_atraso DESC
    """),
    "mas_solicitados": ("Libros más solicitados entre sedes", """
        SELECT l.id, l.titulo, l.isbn, COUNT(*) solicitudes_interbibliotecarias
        FROM prestamos p JOIN ejemplares e ON e.id=p.ejemplar_id
        JOIN libros l ON l.id=e.libro_id
        WHERE p.tipo='INTERBIBLIOTECARIO'
        GROUP BY l.id ORDER BY solicitudes_interbibliotecarias DESC,l.titulo
    """),
    "disponibilidad": ("Disponibilidad por sede", """
        SELECT s.nombre sede, l.titulo, COUNT(e.id) total,
               SUM(CASE WHEN e.estado='DISPONIBLE' THEN 1 ELSE 0 END) disponibles,
               SUM(CASE WHEN e.estado='EN_TRANSITO' THEN 1 ELSE 0 END) en_transito
        FROM ejemplares e JOIN sedes s ON s.id=e.sede_actual_id
        JOIN libros l ON l.id=e.libro_id GROUP BY s.id,l.id ORDER BY s.nombre,l.titulo
    """),
    "logistica": ("Estado de los remitos", """
        SELECT COUNT(*) envios, SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) recibidos,
               SUM(CASE WHEN estado='DESPACHADO' THEN 1 ELSE 0 END) en_transito,
               ROUND(100.0 * SUM(CASE WHEN estado='RECIBIDO' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0),2) tasa_recepcion_pct,
               ROUND(AVG(CASE WHEN estado='RECIBIDO' THEN
                 (julianday(recibido_en)-julianday(creado_en))*24 END),2) horas_promedio_trayecto
        FROM remitos
    """),
    "movimientos": ("Movimientos entre sedes", """
        SELECT o.nombre origen, d.nombre destino, r.tipo, COUNT(*) envios,
               ROUND(AVG(CASE WHEN r.estado='RECIBIDO' THEN
                 (julianday(r.recibido_en)-julianday(r.creado_en))*24 END),2) horas_promedio
        FROM remitos r JOIN sedes o ON o.id=r.origen_id JOIN sedes d ON d.id=r.destino_id
        GROUP BY r.origen_id,r.destino_id,r.tipo ORDER BY envios DESC
    """),
}
