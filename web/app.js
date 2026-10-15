const main = document.querySelector('#main');
const shell = document.querySelector('#app-shell');
const dialogLayer = document.querySelector('#dialog-layer');
const dialogBody = document.querySelector('#dialog-body');
const toast = document.querySelector('#toast');
const today = document.querySelector('#today');
const baseLabel = document.querySelector('#base-label');
const dialogClose = document.createElement('button');
dialogClose.type = 'button';
dialogClose.className = 'icon-button';
dialogClose.id = 'dialog-close';
dialogClose.dataset.action = 'dialog-cancel';
dialogClose.setAttribute('aria-label', 'Cerrar diálogo');
dialogClose.textContent = '×';
document.querySelector('#dialog-close-slot').append(dialogClose);

const VIEWS = {
  inicio: 'Inicio', prestamos: 'Préstamos', remitos: 'Traslados',
  catalogo: 'Catálogo', reservas: 'Reservas', socios: 'Socios',
  sedes: 'Sedes', reportes: 'Reportes',
};
const REPORTS = {
  activos_transito: 'Préstamos y material en tránsito',
  vencidos_multas: 'Préstamos vencidos y multas',
  mas_solicitados: 'Libros más solicitados entre sedes',
  disponibilidad: 'Disponibilidad por sede',
  logistica: 'Estado de los remitos',
  movimientos: 'Movimientos entre sedes',
};
const LABELS = {
  SOLICITADO: 'Solicitado', EN_TRANSITO: 'En tránsito', LISTO: 'Listo para entregar',
  ACTIVO: 'Activo', DEVUELTO: 'Devuelto', CANCELADO: 'Cancelado',
  CREADO: 'Creado', EMPAQUETADO: 'Empaquetado', DESPACHADO: 'Despachado',
  RECIBIDO: 'Recibido', RETORNO_EN_TRANSITO: 'Regreso en tránsito',
  DISPONIBLE: 'Disponible', APARTADO: 'Apartado', RESERVADO: 'Reservado',
  PRESTADO: 'Prestado', POR_RETORNAR: 'Por retornar', EN_REVISION: 'En revisión',
  BAJA: 'De baja', INHABILITADO: 'Inhabilitado', HABILITADO: 'Habilitado', SEDE_ACTIVA: 'Activa',
  EN_ESPERA: 'En espera', ASIGNADA: 'Asignada', CANCELADA: 'Cancelada',
  CUMPLIDA: 'Cumplida', LOCAL: 'Local', INTERBIBLIOTECARIO: 'Entre sedes',
  IDA: 'Ida', REGRESO: 'Regreso', BUENO: 'Bueno', DANADO: 'Dañado',
  DESTRUIDO: 'Destruido', EXTRAVIADO: 'Extraviado',
};
const STATUS_TONE = {
  ACTIVO: 'success', DISPONIBLE: 'success', RECIBIDO: 'success', CUMPLIDA: 'success',
  LISTO: 'info', ASIGNADA: 'info', RESERVADO: 'info',
  SOLICITADO: 'warning', EN_ESPERA: 'warning', CREADO: 'warning',
  EMPAQUETADO: 'warning', DESPACHADO: 'warning', EN_TRANSITO: 'warning',
  RETORNO_EN_TRANSITO: 'warning', POR_RETORNAR: 'warning', EN_REVISION: 'warning',
  BAJA: 'danger', INHABILITADO: 'danger', DESTRUIDO: 'danger', EXTRAVIADO: 'danger',
  HABILITADO: 'success', SEDE_ACTIVA: 'success',
  DEVUELTO: 'muted', CANCELADA: 'muted', CANCELADO: 'muted',
};

let state = null;
let loadError = '';
let loadSeq = 0;
let loadController = null;
let searchTimer = null;
let toastTimer = null;
let dialogReturnFocus = null;
let dialogConfig = null;
let composing = false;

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
function params() { return new URLSearchParams(location.search); }
function view() { const v = params().get('vista') || 'inicio'; return VIEWS[v] ? v : 'inicio'; }
function setParams(changes, push = false) {
  const url = new URL(location.href);
  Object.entries(changes).forEach(([key, value]) => value == null || value === '' ? url.searchParams.delete(key) : url.searchParams.set(key, value));
  history[push ? 'pushState' : 'replaceState']({}, '', url);
}
function go(v) { setParams({ vista: v }, true); render(); main.focus(); }
function rows(table) { return state?.tablas?.[table] || []; }
function report(name) { return state?.reportes?.[name] || []; }
function byId(table, id) { return rows(table).find(r => r.id === Number(id)); }
function nameOf(table, id, key = 'nombre') { return byId(table, id)?.[key] || `#${id}`; }
function bookOfCopy(id) { const copy = byId('ejemplares', id); return copy ? nameOf('libros', copy.libro_id, 'titulo') : `Ejemplar #${id}`; }
function badge(status) { return `<span class="badge badge-${STATUS_TONE[status] || 'muted'}">${esc(LABELS[status] || status)}</span>`; }
function dateText(value) {
  if (!value) return '—';
  const d = new Date(value.length === 10 ? `${value}T12:00:00` : value);
  return Number.isNaN(d.getTime()) ? esc(value) : new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}
function dateTimeText(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? esc(value) : new Intl.DateTimeFormat('es-AR', { dateStyle: 'short', timeStyle: 'short' }).format(d);
}
function money(centavos) { return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format((centavos || 0) / 100); }
function actionButton(label, action, id, kind = 'text', disabled = false) {
  const style = { text: 'text-button', sort: 'table-sort', clear: 'search-clear', pager: 'button button-outline button-small' }[kind] || `button button-${kind} button-small`;
  return `<button type="button" class="${style}" data-action="${esc(action)}" data-id="${esc(id)}" ${kind === 'clear' ? 'aria-label="Limpiar búsqueda"' : ''} ${disabled ? 'disabled' : ''}>${esc(label)}</button>`;
}
function header(kicker, title, subtitle, actions = '') {
  return `<div class="page-header"><div><p class="eyebrow">${esc(kicker)}</p><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${actions ? `<div class="page-header-actions">${actions}</div>` : ''}</div>`;
}
function button(label, action, kind = 'primary') { return `<button type="button" class="button button-${kind}" data-action="${esc(action)}">${esc(label)}</button>`; }
function errorBanner() { return loadError ? `<div class="alert page-alert" role="alert"><p>${esc(loadError)}</p>${button('Volver a cargar', 'reload', 'outline')}</div>` : ''; }

async function request(url, options = {}) {
  const controller = options.controller || new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal, cache: 'no-store' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Error ${response.status}`);
    return data;
  } finally { clearTimeout(timeout); }
}
async function refresh() {
  const seq = ++loadSeq;
  loadController?.abort();
  loadController = new AbortController();
  if (!state) main.innerHTML = `<div class="table-message" role="status">Cargando registros de la biblioteca…</div>`;
  try {
    const fresh = await request('/api/state', { controller: loadController });
    if (seq !== loadSeq) return;
    state = fresh;
    loadError = '';
    baseLabel.textContent = fresh.base.demo ? 'Base de muestra' : 'Base principal';
  } catch (error) {
    if (seq !== loadSeq) return;
    loadError = error.name === 'AbortError' ? 'La carga tardó demasiado. Podés volver a intentarlo.' :
      'No se pudo cargar la biblioteca. Comprobá que el servidor siga abierto.';
  }
  render();
}
async function mutate(payload) {
  try {
    return await request('/api/action', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('No se pudo confirmar el resultado. Revisá el listado antes de volver a intentar.');
    if (error instanceof TypeError) throw new Error('Se perdió la conexión. Revisá el listado antes de volver a intentar.');
    throw error;
  }
}
function notify(message, tone = 'success') {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.dataset.tone = tone;
  toast.hidden = false;
  toastTimer = setTimeout(() => { toast.hidden = true; }, 4800);
}

function table({ id, title, data, columns, actions, empty = 'Todavía no hay registros.', search = true }) {
  const p = params();
  const q = p.get(`${id}_q`) || '';
  const sort = p.get(`${id}_sort`) || columns[0].key;
  const direction = p.get(`${id}_dir`) === 'desc' ? -1 : 1;
  let page = Math.max(1, Number(p.get(`${id}_page`)) || 1);
  let filtered = data.filter(row => !q || [Object.values(row).join(' '), ...columns.map(c => c.raw ? c.raw(row) : row[c.key])].join(' ').toLocaleLowerCase('es-AR').includes(q.toLocaleLowerCase('es-AR')));
  filtered = filtered.slice().sort((a, b) => {
    const col = columns.find(c => c.key === sort) || columns[0];
    const va = col.raw ? col.raw(a) : a[col.key];
    const vb = col.raw ? col.raw(b) : b[col.key];
    return direction * String(va ?? '').localeCompare(String(vb ?? ''), 'es-AR', { numeric: true, sensitivity: 'base' });
  });
  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / 10));
  page = Math.min(page, pages);
  if (Number(p.get(`${id}_page`)) !== page && p.has(`${id}_page`)) setParams({ [`${id}_page`]: page });
  const shown = filtered.slice((page - 1) * 10, page * 10);
  const searchBox = search ? `<div class="search-wrap"><label class="sr-only" for="search-${id}">Buscar en ${esc(title)}</label><input id="search-${id}" type="search" value="${esc(q)}" placeholder="Buscar registros" data-search="${esc(id)}" autocomplete="off">${q ? actionButton('×', 'search-clear', id, 'clear') : ''}</div>` : '';
  const tableMarkup = shown.length ? `<div class="table-scroll"><table><thead><tr>${columns.map(c => `<th scope="col" ${sort === c.key ? `aria-sort="${direction === 1 ? 'ascending' : 'descending'}"` : ''}>${actionButton(`${c.label} ${sort === c.key ? (direction === 1 ? '↑' : '↓') : '↕'}`, 'table-sort', `${id}|${c.key}`, 'sort')}</th>`).join('')}${actions ? '<th scope="col">Acciones</th>' : ''}</tr></thead><tbody>${shown.map(row => `<tr>${columns.map(c => `<td>${c.render ? c.render(row) : esc(row[c.key] ?? '—')}</td>`).join('')}${actions ? `<td><div class="actions">${actions(row)}</div></td>` : ''}</tr>`).join('')}</tbody></table></div>` : `<div class="table-empty"><strong>${q ? 'Sin resultados' : 'Sin registros aún'}</strong><p>${esc(q ? 'Probá con otra búsqueda o limpiá el filtro.' : empty)}</p>${q ? actionButton('Limpiar búsqueda', 'search-clear', id, 'outline') : ''}</div>`;
  return `<section class="table-panel" aria-label="${esc(title)}"><div class="table-toolbar"><h2>${esc(title)}</h2><div class="table-tools">${searchBox}</div></div>${tableMarkup}<div class="table-footer"><span>${total ? `${(page - 1) * 10 + 1}–${Math.min(page * 10, total)} de ${total}` : '0 registros'}</span><div class="pager">${actionButton('Anterior', 'table-page', `${id}|${page - 1}`, 'pager', page <= 1)}<span>Página ${page} de ${pages}</span>${actionButton('Siguiente', 'table-page', `${id}|${page + 1}`, 'pager', page >= pages)}</div></div></section>`;
}

function dashboard() {
  const loans = rows('prestamos');
  const copies = rows('ejemplares');
  const slips = rows('remitos');
  const active = loans.filter(x => x.estado === 'ACTIVO').length;
  const transit = slips.filter(x => x.estado === 'DESPACHADO').length;
  const available = copies.filter(x => x.estado === 'DISPONIBLE').length;
  const pending = rows('reservas').filter(x => ['EN_ESPERA', 'ASIGNADA'].includes(x.estado)).length;
  const recent = slips.slice(-4).reverse();
  return `${header('PANEL DE CIRCULACIÓN', 'Una red, cada ejemplar en su lugar.', 'Consultá la actividad de las sedes y continuá los movimientos pendientes.', button('Solicitar préstamo', 'loan-new'))}
    <div class="summary-grid">
      ${[['Préstamos activos', active, 'En manos de socios'], ['En tránsito', transit, 'Remitos despachados'], ['Disponibles', available, 'Ejemplares listos'], ['Reservas abiertas', pending, 'En espera o asignadas']].map(([label, val, note]) => `<div class="summary-item"><span class="summary-label">${label}</span><strong class="summary-value">${val}</strong><span class="summary-note">${note}</span></div>`).join('')}
    </div>
    <div class="dashboard-grid"><section class="route-card"><p class="eyebrow">CIRCULACIÓN ENTRE SEDES</p><h2>El recorrido queda registrado.</h2><p>Desde la sede de origen hasta la recepción y el regreso: cada remito conserva su secuencia de estados.</p><div class="route-line"><div class="route-step"><strong>Origen</strong>Empaquetar</div><div class="route-step"><strong>Trayecto</strong>Despachar</div><div class="route-step"><strong>Destino</strong>Recibir</div></div><button type="button" class="button" data-action="go-remitos">Ver traslados →</button></section>
    <section class="panel panel-pad"><p class="eyebrow">MOVIMIENTO RECIENTE</p><h2 class="panel-title">Remitos</h2><p class="panel-intro">Últimos traslados registrados.</p>${recent.length ? `<div class="quick-list">${recent.map(r => `<div class="quick-row"><span><strong>R-${String(r.id).padStart(3, '0')}</strong><br><small>${esc(nameOf('sedes', r.origen_id))} → ${esc(nameOf('sedes', r.destino_id))}</small></span>${badge(r.estado)}</div>`).join('')}</div>` : '<p class="empty-brief">Todavía no se emitieron remitos. Una solicitud entre sedes inicia el recorrido.</p>'}</section></div>`;
}

function loansView() {
  return `${header('CIRCULACIÓN', 'Préstamos', 'Solicitudes locales y entre sedes, entregas y devoluciones.', button('Solicitar préstamo', 'loan-new'))}
    ${table({ id: 'prestamos', title: 'Registro de préstamos', data: rows('prestamos'), columns: [
      { key: 'id', label: 'N.º', render: r => `<span class="mono">P-${String(r.id).padStart(3, '0')}</span>` },
      { key: 'ejemplar_id', label: 'Material', raw: r => bookOfCopy(r.ejemplar_id), render: r => `<span class="cell-title">${esc(bookOfCopy(r.ejemplar_id))}</span><span class="cell-sub mono">${esc(nameOf('ejemplares', r.ejemplar_id, 'codigo'))}</span>` },
      { key: 'socio_id', label: 'Socio', raw: r => nameOf('socios', r.socio_id), render: r => esc(nameOf('socios', r.socio_id)) },
      { key: 'sede_origen_id', label: 'Recorrido', raw: r => `${nameOf('sedes', r.sede_origen_id)} ${nameOf('sedes', r.sede_destino_id)}`, render: r => `${esc(nameOf('sedes', r.sede_origen_id))} <span class="cell-sub">→ ${esc(nameOf('sedes', r.sede_destino_id))}</span>` },
      { key: 'tipo', label: 'Tipo', render: r => esc(LABELS[r.tipo] || r.tipo) },
      { key: 'estado', label: 'Estado', render: r => badge(r.estado) },
      { key: 'vence_en', label: 'Vence', render: r => dateText(r.vence_en) },
    ], actions: r => `${(r.estado === 'SOLICITADO' && r.tipo === 'LOCAL') || r.estado === 'LISTO' ? actionButton('Entregar', 'loan-deliver', r.id) : ''}${r.estado === 'ACTIVO' ? actionButton('Devolver', 'loan-return', r.id) : ''}${!['SOLICITADO', 'LISTO', 'ACTIVO'].includes(r.estado) ? '<span class="cell-sub">Sin acciones</span>' : ''}`, empty: 'Una solicitud crea el primer préstamo.' })}`;
}

function remitosView() {
  return `${header('LOGÍSTICA', 'Traslados', 'Cada remito registra la preparación, salida y recepción de un ejemplar.')}
    ${table({ id: 'remitos', title: 'Remitos de ida y regreso', data: rows('remitos'), columns: [
      { key: 'id', label: 'Remito', render: r => `<span class="mono">R-${String(r.id).padStart(3, '0')}</span>` },
      { key: 'ejemplar_id', label: 'Material', raw: r => bookOfCopy(r.ejemplar_id), render: r => `<span class="cell-title">${esc(bookOfCopy(r.ejemplar_id))}</span><span class="cell-sub mono">${esc(nameOf('ejemplares', r.ejemplar_id, 'codigo'))}</span>` },
      { key: 'tipo', label: 'Trayecto', render: r => esc(LABELS[r.tipo] || r.tipo) },
      { key: 'origen_id', label: 'Sedes', raw: r => `${nameOf('sedes', r.origen_id)} ${nameOf('sedes', r.destino_id)}`, render: r => `${esc(nameOf('sedes', r.origen_id))} <span class="cell-sub">→ ${esc(nameOf('sedes', r.destino_id))}</span>` },
      { key: 'estado', label: 'Estado', render: r => badge(r.estado) },
      { key: 'creado_en', label: 'Creado', render: r => dateText(r.creado_en) },
    ], actions: r => `${r.estado !== 'RECIBIDO' ? actionButton(({ CREADO: 'Empaquetar', EMPAQUETADO: 'Despachar', DESPACHADO: 'Recibir' })[r.estado], 'remito-next', r.id) : ''}${actionButton('Historial', 'remito-history', r.id)}`, empty: 'Una solicitud entre sedes genera un remito de ida.' })}`;
}

function catalogView() {
  return `${header('FONDO BIBLIOGRÁFICO', 'Catálogo', 'Títulos únicos y ejemplares físicos vinculados a una sede.', `${button('Agregar libro', 'book-new')}${button('Agregar ejemplar', 'copy-new', 'outline')}`)}
    <div class="section-stack">
      ${table({ id: 'libros', title: 'Libros', data: rows('libros'), columns: [
        { key: 'titulo', label: 'Título', render: r => `<span class="cell-title">${esc(r.titulo)}</span><span class="cell-sub">${esc(r.autor)}</span>` },
        { key: 'isbn', label: 'ISBN', render: r => `<span class="mono">${esc(r.isbn)}</span>` },
        { key: 'anio', label: 'Año', render: r => esc(r.anio || '—') },
        { key: 'id', label: 'Ejemplares', raw: r => rows('ejemplares').filter(e => e.libro_id === r.id).length, render: r => esc(rows('ejemplares').filter(e => e.libro_id === r.id).length) },
      ], actions: r => actionButton('Editar', 'book-edit', r.id), empty: 'Agregá un libro para comenzar el catálogo.' })}
      ${table({ id: 'ejemplares', title: 'Ejemplares físicos', data: rows('ejemplares'), columns: [
        { key: 'codigo', label: 'Código', render: r => `<span class="mono">${esc(r.codigo)}</span>` },
        { key: 'libro_id', label: 'Libro', raw: r => nameOf('libros', r.libro_id, 'titulo'), render: r => esc(nameOf('libros', r.libro_id, 'titulo')) },
        { key: 'sede_pertenencia_id', label: 'Pertenece a', raw: r => nameOf('sedes', r.sede_pertenencia_id), render: r => esc(nameOf('sedes', r.sede_pertenencia_id)) },
        { key: 'sede_actual_id', label: 'Última sede', raw: r => nameOf('sedes', r.sede_actual_id), render: r => esc(nameOf('sedes', r.sede_actual_id)) },
        { key: 'estado', label: 'Estado', render: r => badge(r.estado) },
      ], actions: r => r.estado === 'EN_REVISION' ? `${actionButton('Apto', 'copy-fit', r.id)}${actionButton('Dar de baja', 'copy-unfit', r.id)}` : '<span class="cell-sub">Sin acciones</span>', empty: 'Agregá ejemplares para consultar disponibilidad.' })}
    </div>`;
}

function reservasView() {
  return `${header('TURNOS DE LECTURA', 'Reservas', 'La primera reserva en espera recibe el siguiente ejemplar disponible en su sede.', button('Crear reserva', 'reserve-new'))}
    ${table({ id: 'reservas', title: 'Cola de reservas', data: rows('reservas'), columns: [
      { key: 'id', label: 'N.º', render: r => `<span class="mono">#${r.id}</span>` },
      { key: 'libro_id', label: 'Libro', raw: r => nameOf('libros', r.libro_id, 'titulo'), render: r => `<span class="cell-title">${esc(nameOf('libros', r.libro_id, 'titulo'))}</span>` },
      { key: 'socio_id', label: 'Socio', raw: r => nameOf('socios', r.socio_id), render: r => esc(nameOf('socios', r.socio_id)) },
      { key: 'sede_id', label: 'Retiro', raw: r => nameOf('sedes', r.sede_id), render: r => esc(nameOf('sedes', r.sede_id)) },
      { key: 'creada_en', label: 'Solicitada', render: r => dateText(r.creada_en) },
      { key: 'estado', label: 'Estado', render: r => badge(r.estado) },
    ], actions: r => ['EN_ESPERA', 'ASIGNADA'].includes(r.estado) ? actionButton('Cancelar', 'reserve-cancel', r.id) : '<span class="cell-sub">Cerrada</span>', empty: 'Creá una reserva para que el sistema asigne el próximo ejemplar disponible.' })}`;
}

function sociosView() {
  return `${header('PADRÓN', 'Socios', 'Personas habilitadas para solicitar préstamos y reservas.', button('Agregar socio', 'member-new'))}
    ${table({ id: 'socios', title: 'Socios registrados', data: rows('socios'), columns: [
      { key: 'id', label: 'N.º', render: r => `<span class="mono">#${r.id}</span>` },
      { key: 'nombre', label: 'Nombre', render: r => `<span class="cell-title">${esc(r.nombre)}</span>` },
      { key: 'documento', label: 'Documento', render: r => `<span class="mono">${esc(r.documento)}</span>` },
      { key: 'email', label: 'Contacto', render: r => esc(r.email) },
      { key: 'habilitado', label: 'Estado', render: r => badge(r.habilitado ? 'HABILITADO' : 'INHABILITADO') },
    ], actions: r => `${actionButton('Editar', 'member-edit', r.id)}${actionButton(r.habilitado ? 'Inhabilitar' : 'Habilitar', 'member-toggle', r.id)}`, empty: 'Agregá un socio para iniciar un préstamo.' })}`;
}

function sedesView() {
  return `${header('RED DE ATENCIÓN', 'Sedes', 'Direcciones, contacto, horarios y estado operativo de la red.', button('Agregar sede', 'branch-new'))}
    ${table({ id: 'sedes', title: 'Sedes de la red', data: rows('sedes'), columns: [
      { key: 'nombre', label: 'Sede', render: r => `<span class="cell-title">${esc(r.nombre)}</span><span class="cell-sub">${esc(r.direccion)}</span>` },
      { key: 'contacto', label: 'Contacto', render: r => esc(r.contacto) },
      { key: 'horarios', label: 'Horarios', render: r => esc(r.horarios) },
      { key: 'activa', label: 'Estado', render: r => badge(r.activa ? 'SEDE_ACTIVA' : 'BAJA') },
    ], actions: r => `${actionButton('Editar', 'branch-edit', r.id)}${actionButton(r.activa ? 'Dar de baja' : 'Reactivar', 'branch-toggle', r.id)}`, empty: 'Agregá la primera sede para incorporar ejemplares.' })}`;
}

function reportsView() {
  const chosen = REPORTS[params().get('reporte')] ? params().get('reporte') : 'activos_transito';
  const data = report(chosen);
  const highlight = chosen === 'logistica' && data.length ? `<div class="report-highlight">${[
    ['Remitos emitidos', data[0].envios || 0], ['Recibidos', data[0].recibidos || 0],
    ['En tránsito', data[0].en_transito || 0], ['Tiempo medio', data[0].horas_promedio_trayecto == null ? '—' : `${data[0].horas_promedio_trayecto} h`],
  ].map(([label, value]) => `<div><small>${esc(label)}</small><strong>${esc(value)}</strong></div>`).join('')}</div>` : '';
  const columns = data.length ? Object.keys(data[0]).map(key => ({ key, label: key.replaceAll('_', ' '), render: row => key.includes('centavos') ? money(row[key]) : key.includes('fecha') || key.includes('vence') ? dateText(row[key]) : esc(row[key] ?? '—') })) : [{ key: 'sin_datos', label: 'Resultado' }];
  return `${header('ANÁLISIS', 'Reportes', 'Seis vistas para revisar circulación, demanda, disponibilidad y tiempos de traslado.')}
    <p class="report-note">Las cifras reflejan la base local al momento de cargar esta pantalla. “Tasa de recepción” mide remitos recibidos sobre emitidos; no equivale a entregas sin incidencias.</p>
    <div class="field" style="max-width:370px;margin-bottom:22px"><label for="report-kind">Tipo de reporte</label><select id="report-kind" class="report-select">${Object.entries(REPORTS).map(([key, name]) => `<option value="${esc(key)}" ${key === chosen ? 'selected' : ''}>${esc(name)}</option>`).join('')}</select></div>
    ${highlight}
    ${chosen !== 'logistica' ? table({ id: 'reporte', title: REPORTS[chosen], data, columns, empty: 'Este reporte todavía no tiene datos para mostrar.' }) : ''}
    ${chosen === 'logistica' ? `<p class="cell-sub">Recepción: ${data[0]?.tasa_recepcion_pct == null ? '—' : `${esc(data[0].tasa_recepcion_pct)} %`} de los remitos emitidos.</p>` : ''}`;
}

function render() {
  const v = view();
  document.title = `Red de Bibliotecas · ${VIEWS[v]}`;
  document.querySelectorAll('#navigation a').forEach(a => a.dataset.view === v ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
  if (!state) {
    main.innerHTML = `${header('SISTEMA LOCAL', 'Red de Bibliotecas', 'Cargando datos de la biblioteca…')}${errorBanner()}<div class="table-message" role="status">${loadError ? 'Comprobá el servidor y volvé a cargar.' : 'Cargando registros…'}</div>`;
    return;
  }
  const views = { inicio: dashboard, prestamos: loansView, remitos: remitosView, catalogo: catalogView, reservas: reservasView, socios: sociosView, sedes: sedesView, reportes: reportsView };
  main.innerHTML = errorBanner() + views[v]();
}

function options(tableName, label, filter = () => true) {
  return rows(tableName).filter(filter).map(r => ({ value: r.id, label: label(r) }));
}
function fieldHTML(f) {
  const id = `field-${f.name}`;
  const help = f.help ? `<span class="field-help" id="${id}-help">${esc(f.help)}</span>` : '';
  const described = `${id}-error${f.help ? ` ${id}-help` : ''}`;
  let input;
  if (f.options) input = `<select id="${id}" name="${esc(f.name)}" aria-describedby="${described}"><option value="">Seleccionar…</option>${f.options.map(o => `<option value="${esc(o.value)}" ${String(o.value) === String(f.value ?? '') ? 'selected' : ''}>${esc(o.label)}</option>`).join('')}</select>`;
  else if (f.type === 'textarea') input = `<textarea id="${id}" name="${esc(f.name)}" aria-describedby="${described}">${esc(f.value ?? '')}</textarea>`;
  else input = `<input id="${id}" name="${esc(f.name)}" type="${esc(f.type || 'text')}" value="${esc(f.value ?? '')}" ${f.min ? `min="${esc(f.min)}"` : ''} aria-describedby="${described}" autocomplete="off">`;
  return `<div class="field"><label for="${id}">${esc(f.label)}${f.required ? ' *' : ''}</label>${input}${help}<span class="field-error" id="${id}-error"></span></div>`;
}
function openDialog(config) {
  dialogReturnFocus = document.activeElement;
  dialogConfig = config;
  document.querySelector('#dialog-eyebrow').textContent = config.eyebrow || 'OPERACIÓN';
  document.querySelector('#dialog-title').textContent = config.title;
  document.querySelector('#dialog-description').textContent = config.description || '';
  dialogBody.innerHTML = config.body;
  dialogLayer.hidden = false;
  shell.inert = true;
  document.body.style.overflow = 'hidden';
  requestAnimationFrame(() => (dialogBody.querySelector('input, select, textarea, button') || document.querySelector('#dialog-close')).focus());
}
function closeDialog() {
  if (dialogLayer.hidden) return;
  dialogLayer.hidden = true;
  shell.inert = false;
  document.body.style.overflow = '';
  dialogConfig = null;
  if (dialogReturnFocus?.isConnected) dialogReturnFocus.focus();
  else main.focus();
}
function openForm(config) {
  const form = `<form id="dialog-form" novalidate><div class="dialog-error alert" role="alert" hidden></div><div class="form-fields">${config.fields.map(fieldHTML).join('')}</div><div class="dialog-actions"><button type="button" class="button button-outline" data-action="dialog-cancel">Cancelar</button><button type="submit" class="button button-${config.danger ? 'danger' : 'primary'}">${esc(config.submit || 'Guardar')}</button></div></form>`;
  openDialog({ ...config, body: form, type: 'form' });
}
function openConfirm({ title, description, object, verb, action, payload, success, danger = true }) {
  openDialog({ title, description, eyebrow: 'CONFIRMACIÓN', type: 'confirm', payload, action, success,
    body: `<div class="dialog-confirm-copy">${esc(object)}</div><div class="dialog-error alert" role="alert" hidden></div><div class="dialog-actions"><button type="button" class="button button-outline" data-action="dialog-cancel" autofocus>Conservar</button><button type="button" class="button button-${danger ? 'danger' : 'primary'}" data-action="dialog-confirm">${esc(verb)}</button></div>` });
  document.querySelector('[data-action="dialog-cancel"]').focus();
}
function showDialogError(message) {
  const el = dialogBody.querySelector('.dialog-error');
  el.textContent = message;
  el.hidden = false;
  el.focus?.();
}
function setBusy(busy) {
  dialogBody.querySelectorAll('button').forEach(b => { b.disabled = busy; if (b.type === 'submit' || b.dataset.action === 'dialog-confirm') b.dataset.busy = String(busy); });
  document.querySelector('#dialog-close').disabled = busy;
}
async function complete(payload, success) {
  setBusy(true);
  try {
    const response = await mutate(payload);
    closeDialog();
    notify(typeof success === 'function' ? success(response.resultado) : success);
    await refresh();
  } catch (error) {
    setBusy(false);
    showDialogError(error.message);
  }
}

function dispatchAction(action, id) {
  const branch = byId('sedes', id);
  const member = byId('socios', id);
  const book = byId('libros', id);
  const loan = byId('prestamos', id);
  const slip = byId('remitos', id);
  const reservation = byId('reservas', id);
  const copy = byId('ejemplares', id);
  const activeBranches = options('sedes', r => r.nombre, r => r.activa);
  const members = options('socios', r => `${r.nombre} · ${r.documento}`, r => r.habilitado);
  const books = options('libros', r => `${r.titulo} · ${r.isbn}`);
  if (action.startsWith('go-')) return go(action.slice(3));
  if (action === 'reload') return refresh();
  if (action === 'branch-new') return openForm({ title: 'Agregar sede', description: 'Completá los datos de atención de la nueva sede.', action: 'crear_sede', submit: 'Agregar sede', success: 'Sede agregada.', fields: [
    { name: 'nombre', label: 'Nombre', required: true }, { name: 'direccion', label: 'Dirección', required: true },
    { name: 'contacto', label: 'Contacto', required: true }, { name: 'horarios', label: 'Horarios', required: true },
  ] });
  if (action === 'branch-edit' && branch) return openForm({ title: 'Editar sede', description: branch.nombre, action: 'editar_sede', extra: { id: branch.id }, submit: 'Guardar cambios', success: 'Sede actualizada.', fields: [
    { name: 'direccion', label: 'Dirección', value: branch.direccion, required: true }, { name: 'contacto', label: 'Contacto', value: branch.contacto, required: true },
    { name: 'horarios', label: 'Horarios', value: branch.horarios, required: true },
  ] });
  if (action === 'branch-toggle' && branch) return openConfirm({ title: branch.activa ? 'Dar de baja la sede' : 'Reactivar la sede', description: branch.activa ? 'No se podrán iniciar préstamos, reservas ni envíos desde o hacia esta sede.' : 'La sede podrá volver a participar en operaciones nuevas.', object: `Sede: ${branch.nombre}`, verb: branch.activa ? 'Dar de baja' : 'Reactivar', action: 'editar_sede', payload: { id: branch.id, activa: !branch.activa }, success: branch.activa ? 'Sede dada de baja.' : 'Sede reactivada.', danger: !!branch.activa });
  if (action === 'member-new') return openForm({ title: 'Agregar socio', description: 'El documento identifica al socio y no puede repetirse.', action: 'crear_socio', submit: 'Agregar socio', success: 'Socio agregado.', fields: [
    { name: 'documento', label: 'Documento', required: true }, { name: 'nombre', label: 'Nombre completo', required: true },
    { name: 'email', label: 'Correo electrónico', type: 'email', required: true },
  ] });
  if (action === 'member-edit' && member) return openForm({ title: 'Editar socio', description: `Documento ${member.documento}`, action: 'editar_socio', extra: { id: member.id }, submit: 'Guardar cambios', success: 'Socio actualizado.', fields: [
    { name: 'nombre', label: 'Nombre completo', value: member.nombre, required: true },
    { name: 'email', label: 'Correo electrónico', type: 'email', value: member.email, required: true },
  ] });
  if (action === 'member-toggle' && member) return openConfirm({ title: member.habilitado ? 'Inhabilitar socio' : 'Habilitar socio', description: member.habilitado ? 'El socio no podrá iniciar reservas ni recibir préstamos nuevos.' : 'El socio podrá volver a operar.', object: `${member.nombre} · Documento ${member.documento}`, verb: member.habilitado ? 'Inhabilitar' : 'Habilitar', action: 'editar_socio', payload: { id: member.id, habilitado: !member.habilitado }, success: member.habilitado ? 'Socio inhabilitado.' : 'Socio habilitado.', danger: !!member.habilitado });
  if (action === 'book-new') return openForm({ title: 'Agregar libro', description: 'El ISBN identifica una ficha única del catálogo.', action: 'crear_libro', submit: 'Agregar libro', success: 'Libro agregado.', fields: [
    { name: 'isbn', label: 'ISBN', required: true }, { name: 'titulo', label: 'Título', required: true },
    { name: 'autor', label: 'Autor', required: true }, { name: 'anio', label: 'Año', type: 'number', min: 1 },
  ] });
  if (action === 'book-edit' && book) return openForm({ title: 'Editar libro', description: `ISBN ${book.isbn}`, action: 'editar_libro', extra: { id: book.id }, submit: 'Guardar cambios', success: 'Libro actualizado.', fields: [
    { name: 'titulo', label: 'Título', value: book.titulo, required: true }, { name: 'autor', label: 'Autor', value: book.autor, required: true },
    { name: 'anio', label: 'Año', type: 'number', min: 1, value: book.anio },
  ] });
  if (action === 'copy-new') return openForm({ title: 'Agregar ejemplar', description: 'Cada copia física necesita un código único y una sede de pertenencia.', action: 'crear_ejemplar', submit: 'Agregar ejemplar', success: 'Ejemplar agregado.', fields: [
    { name: 'codigo', label: 'Código de ejemplar', required: true }, { name: 'libro_id', label: 'Libro', options: books, required: true },
    { name: 'sede_id', label: 'Sede de pertenencia', options: activeBranches, required: true },
  ] });
  if (action === 'copy-fit' && copy) return openConfirm({ title: 'Habilitar ejemplar', description: 'La revisión física terminó y el ejemplar podrá volver a circular.', object: `${copy.codigo} · ${bookOfCopy(copy.id)}`, verb: 'Marcar apto', action: 'cerrar_revision', payload: { ejemplar_id: copy.id, apto: true }, success: 'Ejemplar disponible.', danger: false });
  if (action === 'copy-unfit' && copy) return openConfirm({ title: 'Dar de baja ejemplar', description: 'El ejemplar dejará de estar disponible para préstamos.', object: `${copy.codigo} · ${bookOfCopy(copy.id)}`, verb: 'Dar de baja', action: 'cerrar_revision', payload: { ejemplar_id: copy.id, apto: false }, success: 'Ejemplar dado de baja.' });
  if (action === 'reserve-new') return openForm({ title: 'Crear reserva', description: 'Se asignará el primer ejemplar disponible de este libro en la sede elegida.', action: 'reservar', submit: 'Crear reserva', success: 'Reserva creada.', fields: [
    { name: 'socio_id', label: 'Socio', options: members, required: true }, { name: 'libro_id', label: 'Libro', options: books, required: true },
    { name: 'sede_id', label: 'Sede de retiro', options: activeBranches, required: true },
  ] });
  if (action === 'reserve-cancel' && reservation) return openConfirm({ title: 'Cancelar reserva', description: 'Si tenía un ejemplar asignado, se ofrecerá a la siguiente persona de la cola.', object: `${nameOf('libros', reservation.libro_id, 'titulo')} · ${nameOf('socios', reservation.socio_id)}`, verb: 'Cancelar reserva', action: 'cancelar_reserva', payload: { id: reservation.id }, success: 'Reserva cancelada.' });
  if (action === 'loan-new') return openForm({ title: 'Solicitar préstamo', description: 'Seleccioná el ejemplar y las sedes. Si son distintas, se genera un remito de ida.', action: 'solicitar_prestamo', submit: 'Solicitar préstamo', success: result => `Préstamo P-${String(result).padStart(3, '0')} solicitado.`, fields: [
    { name: 'socio_id', label: 'Socio', options: members, required: true },
    { name: 'ejemplar_id', label: 'Ejemplar', options: options('ejemplares', r => `${r.codigo} · ${nameOf('libros', r.libro_id, 'titulo')} · ${LABELS[r.estado] || r.estado}`, r => ['DISPONIBLE', 'RESERVADO'].includes(r.estado)), required: true },
    { name: 'sede_origen_id', label: 'Sede de origen', options: activeBranches, required: true, help: 'Debe ser la sede de pertenencia del ejemplar.' },
    { name: 'sede_destino_id', label: 'Sede de retiro', options: activeBranches, required: true },
  ] });
  if (action === 'loan-deliver' && loan) return openConfirm({ title: 'Entregar préstamo', description: 'La fecha de vencimiento se calculará desde la entrega.', object: `${bookOfCopy(loan.ejemplar_id)} · ${nameOf('socios', loan.socio_id)}`, verb: 'Entregar', action: 'entregar_prestamo', payload: { id: loan.id }, success: result => `Préstamo entregado. Vence el ${dateText(result.vence_en)}.`, danger: false });
  if (action === 'loan-return' && loan) return openForm({ title: 'Registrar devolución', description: `${bookOfCopy(loan.ejemplar_id)} · ${nameOf('socios', loan.socio_id)}. Indicá el estado físico del material.`, action: 'devolver_prestamo', extra: { id: loan.id }, submit: 'Registrar devolución', success: result => `Devolución registrada. Multa: ${money(result.multa_centavos)}.`, fields: [
    { name: 'condicion', label: 'Condición del ejemplar', required: true, value: 'BUENO', options: ['BUENO', 'DANADO', 'DESTRUIDO', 'EXTRAVIADO'].map(x => ({ value: x, label: LABELS[x] })), help: 'Dañado requiere revisión. Destruido o extraviado da de baja el ejemplar.' },
  ] });
  if (action === 'remito-next' && slip) {
    const next = { CREADO: 'EMPAQUETADO', EMPAQUETADO: 'DESPACHADO', DESPACHADO: 'RECIBIDO' }[slip.estado];
    if (!next) return;
    return openForm({ title: `${{ EMPAQUETADO: 'Empaquetar', DESPACHADO: 'Despachar', RECIBIDO: 'Recibir' }[next]} remito`, description: `R-${String(slip.id).padStart(3, '0')} · ${nameOf('sedes', slip.origen_id)} → ${nameOf('sedes', slip.destino_id)}`, action: 'avanzar_remito', extra: { id: slip.id, estado: next }, submit: `${{ EMPAQUETADO: 'Empaquetar', DESPACHADO: 'Despachar', RECIBIDO: 'Recibir' }[next]} remito`, success: `Remito ${LABELS[next].toLowerCase()}.`, fields: [
      { name: 'detalle', label: 'Detalle del movimiento', type: 'textarea', help: 'Opcional. Ejemplo: caja sellada o recepción sin observaciones.' },
    ] });
  }
  if (action === 'remito-history' && slip) return openHistory(slip);
}

async function openHistory(slip) {
  openDialog({ title: `Historial R-${String(slip.id).padStart(3, '0')}`, eyebrow: 'TRAZABILIDAD', description: `${nameOf('sedes', slip.origen_id)} → ${nameOf('sedes', slip.destino_id)}`, type: 'history', historyId: slip.id, body: '<div class="table-message" role="status">Cargando historial…</div>' });
  try {
    const events = await request(`/api/remito/${slip.id}/historial`);
    if (dialogLayer.hidden || dialogConfig?.historyId !== slip.id) return;
    dialogBody.innerHTML = `<ol class="history-list">${events.map(x => `<li><span class="history-point" aria-hidden="true"></span><div>${badge(x.estado)}<span class="history-time">${dateTimeText(x.fecha)}</span><p>${esc(x.detalle || 'Sin observaciones')}</p></div></li>`).join('')}</ol><div class="dialog-actions"><button type="button" class="button button-outline" data-action="dialog-cancel">Cerrar</button></div>`;
  } catch (error) { if (!dialogLayer.hidden && dialogConfig?.historyId === slip.id) dialogBody.innerHTML = `<div class="alert" role="alert">No se pudo leer el historial. Cerrá el diálogo y volvé a intentarlo.</div><div class="dialog-actions"><button type="button" class="button button-outline" data-action="dialog-cancel">Cerrar</button></div>`; }
}

document.querySelector('#navigation').addEventListener('click', event => {
  const link = event.target.closest('a[data-view]');
  if (!link) return;
  event.preventDefault();
  go(link.dataset.view);
});
document.addEventListener('click', event => {
  const action = event.target.closest('[data-action]');
  if (action && !action.disabled) {
    if (action.dataset.action === 'dialog-cancel') return closeDialog();
    if (action.dataset.action === 'dialog-confirm') return complete({ accion: dialogConfig.action, ...dialogConfig.payload }, dialogConfig.success);
    if (action.dataset.action === 'search-clear') { setParams({ [`${action.dataset.id}_q`]: null, [`${action.dataset.id}_page`]: 1 }); render(); document.querySelector(`#search-${action.dataset.id}`)?.focus(); return; }
    if (action.dataset.action === 'table-sort') {
      const [id, key] = action.dataset.id.split('|'); const current = params();
      setParams({ [`${id}_sort`]: key, [`${id}_dir`]: current.get(`${id}_sort`) === key && current.get(`${id}_dir`) !== 'desc' ? 'desc' : 'asc', [`${id}_page`]: 1 }, true);
      render(); return;
    }
    if (action.dataset.action === 'table-page') { const [id, page] = action.dataset.id.split('|'); setParams({ [`${id}_page`]: page }, true); render(); return; }
    return dispatchAction(action.dataset.action, action.dataset.id);
  }
});
document.addEventListener('input', event => {
  const input = event.target.closest('[data-search]');
  if (!input || event.isComposing) return;
  clearTimeout(searchTimer);
  const id = input.dataset.search; const value = input.value;
  searchTimer = setTimeout(() => { setParams({ [`${id}_q`]: value, [`${id}_page`]: 1 }); render(); const next = document.querySelector(`#search-${id}`); next?.focus(); next?.setSelectionRange(value.length, value.length); }, 300);
});
document.addEventListener('compositionstart', () => { composing = true; });
document.addEventListener('compositionend', event => { composing = false; if (event.target.matches('[data-search]')) event.target.dispatchEvent(new Event('input', { bubbles: true })); });
document.addEventListener('change', event => {
  if (event.target.id === 'report-kind') { setParams({ reporte: event.target.value, reporte_page: 1 }, true); render(); }
  if (event.target.name === 'ejemplar_id' && dialogConfig?.action === 'solicitar_prestamo') {
    const copy = byId('ejemplares', event.target.value);
    if (copy) document.querySelector('#field-sede_origen_id').value = String(copy.sede_pertenencia_id);
  }
  if (event.target.name === 'condicion' && dialogConfig?.action === 'devolver_prestamo') {
    document.querySelector('#dialog-form').dataset.confirmed = '';
    const submit = document.querySelector('#dialog-form [type="submit"]');
    submit.textContent = 'Registrar devolución';
    const error = document.querySelector('#dialog-form .dialog-error'); error.hidden = true;
  }
});
document.addEventListener('submit', event => {
  if (event.target.id !== 'dialog-form') return;
  event.preventDefault();
  if (composing) return;
  const form = event.target;
  const config = dialogConfig;
  const values = Object.fromEntries(new FormData(form).entries());
  let firstInvalid = null;
  for (const field of config.fields) {
    const input = form.elements[field.name];
    const invalid = field.required && !String(values[field.name] ?? '').trim();
    const emailInvalid = field.type === 'email' && values[field.name] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values[field.name]);
    const numericInvalid = field.type === 'number' && values[field.name] && (!Number.isInteger(Number(values[field.name])) || Number(values[field.name]) < (field.min || 0));
    const message = invalid ? `Completá ${field.label.toLowerCase()}.` : emailInvalid ? 'Ingresá un correo válido.' : numericInvalid ? 'Ingresá un número válido.' : '';
    form.querySelector(`#field-${field.name}-error`).textContent = message;
    input.setAttribute('aria-invalid', String(!!message));
    if (message && !firstInvalid) firstInvalid = input;
  }
  if (firstInvalid) { firstInvalid.focus(); return; }
  if (config.action === 'devolver_prestamo' && ['DESTRUIDO', 'EXTRAVIADO'].includes(values.condicion) && form.dataset.confirmed !== values.condicion) {
    form.dataset.confirmed = values.condicion;
    const error = form.querySelector('.dialog-error');
    error.textContent = `Vas a registrar el ejemplar como ${LABELS[values.condicion].toLowerCase()} y quedará de baja. Confirmá la operación.`;
    error.hidden = false;
    form.querySelector('[type="submit"]').textContent = 'Confirmar baja y devolución';
    form.querySelector('[type="submit"]').focus();
    return;
  }
  complete({ accion: config.action, ...config.extra, ...values }, config.success);
});
document.addEventListener('keydown', event => {
  if (dialogLayer.hidden) return;
  if (event.key === 'Escape' && !dialogBody.querySelector('button:disabled')) { event.preventDefault(); closeDialog(); return; }
  if (event.key !== 'Tab') return;
  const focusable = [...document.querySelector('#dialog').querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled)')].filter(el => el.offsetParent !== null);
  if (!focusable.length) return;
  if (event.shiftKey && document.activeElement === focusable[0]) { event.preventDefault(); focusable.at(-1).focus(); }
  else if (!event.shiftKey && document.activeElement === focusable.at(-1)) { event.preventDefault(); focusable[0].focus(); }
});
window.addEventListener('popstate', render);
today.textContent = new Intl.DateTimeFormat('es-AR', { weekday: 'short', day: '2-digit', month: 'long' }).format(new Date());
refresh();
