/**
 * Cliente HTTP REST para comunicar los componentes React con el backend FastAPI (/api/...).
 */

async function request(url, options = {}) {
  const controller = options.controller || new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal, cache: 'no-store' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Error ${response.status}`);
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

async function cargarEstadoBiblioteca(controller) {
  const opts = { controller };
  const [sedes, socios, libros, ejemplares, reservas, prestamos, remitos, multas, reportes, base] =
    await Promise.all([
      request('/api/sedes', opts),
      request('/api/socios', opts),
      request('/api/libros', opts),
      request('/api/ejemplares', opts),
      request('/api/reservas', opts),
      request('/api/prestamos', opts),
      request('/api/remitos', opts),
      request('/api/multas', opts),
      request('/api/reportes', opts),
      request('/api/base', opts),
    ]);

  return {
    tablas: { sedes, socios, libros, ejemplares, reservas, prestamos, remitos, multas },
    reportes,
    base,
  };
}

function buildRestCall(payload) {
  const { accion, ...rest } = payload;
  if (accion === 'crear_sede')
    return ['POST', '/api/sedes', { nombre: rest.nombre, direccion: rest.direccion, contacto: rest.contacto, horarios: rest.horarios }];
  if (accion === 'editar_sede')
    return ['PATCH', `/api/sedes/${Number(rest.id)}`, { direccion: rest.direccion, contacto: rest.contacto, horarios: rest.horarios, activa: rest.activa }];
  if (accion === 'crear_socio')
    return ['POST', '/api/socios', { documento: rest.documento, nombre: rest.nombre, email: rest.email }];
  if (accion === 'editar_socio')
    return ['PATCH', `/api/socios/${Number(rest.id)}`, { nombre: rest.nombre, email: rest.email, habilitado: rest.habilitado }];
  if (accion === 'crear_libro')
    return ['POST', '/api/libros', { isbn: rest.isbn, titulo: rest.titulo, autor: rest.autor, anio: rest.anio !== '' && rest.anio != null ? Number(rest.anio) : null }];
  if (accion === 'editar_libro')
    return ['PATCH', `/api/libros/${Number(rest.id)}`, { titulo: rest.titulo, autor: rest.autor, anio: rest.anio !== '' && rest.anio != null ? Number(rest.anio) : null }];
  if (accion === 'crear_ejemplar')
    return ['POST', '/api/ejemplares', { codigo: rest.codigo, libro_id: Number(rest.libro_id), sede_id: Number(rest.sede_id), condicion: rest.condicion || 'BUENO' }];
  if (accion === 'cerrar_revision')
    return ['POST', `/api/ejemplares/${Number(rest.ejemplar_id)}/revision`, { apto: Boolean(rest.apto) }];
  if (accion === 'reservar')
    return ['POST', '/api/reservas', { socio_id: Number(rest.socio_id), libro_id: Number(rest.libro_id), sede_id: Number(rest.sede_id) }];
  if (accion === 'cancelar_reserva')
    return ['DELETE', `/api/reservas/${Number(rest.id)}`, null];
  if (accion === 'solicitar_prestamo')
    return ['POST', '/api/prestamos', { socio_id: Number(rest.socio_id), ejemplar_id: Number(rest.ejemplar_id), sede_origen_id: Number(rest.sede_origen_id), sede_destino_id: Number(rest.sede_destino_id), plazo_dias: Number(rest.plazo_dias || 14) }];
  if (accion === 'entregar_prestamo')
    return ['POST', `/api/prestamos/${Number(rest.id)}/entregar`, null];
  if (accion === 'devolver_prestamo')
    return ['POST', `/api/prestamos/${Number(rest.id)}/devolver`, { condicion: rest.condicion }];
  if (accion === 'pagar_multa')
    return ['POST', `/api/multas/${Number(rest.id)}/pagar`, null];
  if (accion === 'cancelar_prestamo')
    return ['DELETE', `/api/prestamos/${Number(rest.id)}`, null];
  if (accion === 'eliminar_libro')
    return ['DELETE', `/api/libros/${Number(rest.id)}`, null];
  if (accion === 'eliminar_ejemplar')
    return ['DELETE', `/api/ejemplares/${Number(rest.id)}`, null];
  if (accion === 'eliminar_sede')
    return ['DELETE', `/api/sedes/${Number(rest.id)}`, null];
  if (accion === 'eliminar_socio')
    return ['DELETE', `/api/socios/${Number(rest.id)}`, null];
  if (accion === 'avanzar_remito')
    return ['POST', `/api/remitos/${Number(rest.id)}/avanzar`, { estado: rest.estado, detalle: rest.detalle || '' }];
  throw new Error('Operación desconocida');
}

async function mutate(payload) {
  try {
    const [method, url, body] = buildRestCall(payload);
    const options = { method, headers: {} };
    if (body !== null) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    return await request(url, options);
  } catch (error) {
    if (error.name === 'AbortError')
      throw new Error('No se pudo confirmar el resultado. Revisá el listado antes de volver a intentar.');
    if (error instanceof TypeError)
      throw new Error('Se perdió la conexión. Revisá el listado antes de volver a intentar.');
    throw error;
  }
}
