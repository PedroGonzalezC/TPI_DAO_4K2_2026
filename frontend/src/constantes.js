/**
 * Constantes globales, diccionarios de etiquetas y funciones de formato
 * para la interfaz React de la Red de Bibliotecas.
 */

const { useState, useEffect, useRef } = React;

const VIEWS = {
  inicio: 'Inicio',
  prestamos: 'Préstamos',
  remitos: 'Traslados',
  catalogo: 'Catálogo',
  reservas: 'Reservas',
  socios: 'Socios',
  multas: 'Multas',
  sedes: 'Sedes',
  reportes: 'Reportes',
};

const NAV_ITEMS = [
  { key: 'inicio', label: 'Inicio', symbol: '⌂' },
  { key: 'prestamos', label: 'Préstamos', symbol: '⇄' },
  { key: 'remitos', label: 'Traslados', symbol: '↗' },
  { key: 'catalogo', label: 'Catálogo', symbol: '▤' },
  { key: 'reservas', label: 'Reservas', symbol: '◷' },
  { key: 'socios', label: 'Socios', symbol: '♙' },
  { key: 'multas', label: 'Multas', symbol: '$' },
  { key: 'sedes', label: 'Sedes', symbol: '⌂' },
  { key: 'reportes', label: 'Reportes', symbol: '▥' },
];

const REPORTS = {
  activos_transito: 'Préstamos y material en tránsito',
  vencidos_multas: 'Préstamos vencidos y multas',
  mas_solicitados: 'Libros más solicitados entre sedes',
  disponibilidad: 'Disponibilidad por sede',
  logistica: 'Estado de los remitos',
  movimientos: 'Movimientos entre sedes',
};

const LABELS = {
  SOLICITADO: 'Solicitado',
  EN_TRANSITO: 'En tránsito',
  LISTO: 'Listo para entregar',
  ACTIVO: 'Activo',
  DEVUELTO: 'Devuelto',
  CANCELADO: 'Cancelado',
  CREADO: 'Creado',
  EMPAQUETADO: 'Empaquetado',
  DESPACHADO: 'Despachado',
  RECIBIDO: 'Recibido',
  RETORNO_EN_TRANSITO: 'Regreso en tránsito',
  DISPONIBLE: 'Disponible',
  APARTADO: 'Apartado',
  RESERVADO: 'Reservado',
  PRESTADO: 'Prestado',
  POR_RETORNAR: 'Por retornar',
  EN_REVISION: 'En revisión',
  BAJA: 'De baja',
  INHABILITADO: 'Inhabilitado',
  HABILITADO: 'Habilitado',
  SEDE_ACTIVA: 'Activa',
  EN_ESPERA: 'En espera',
  ASIGNADA: 'Asignada',
  CANCELADA: 'Cancelada',
  CUMPLIDA: 'Cumplida',
  LOCAL: 'Local',
  INTERBIBLIOTECARIO: 'Entre sedes',
  IDA: 'Ida',
  REGRESO: 'Regreso',
  BUENO: 'Bueno',
  DANADO: 'Dañado',
  DESTRUIDO: 'Destruido',
  EXTRAVIADO: 'Extraviado',
  PENDIENTE: 'Pendiente',
  PAGADA: 'Pagada',
};

const STATUS_TONE = {
  ACTIVO: 'success',
  DISPONIBLE: 'success',
  RECIBIDO: 'success',
  CUMPLIDA: 'success',
  LISTO: 'info',
  ASIGNADA: 'info',
  RESERVADO: 'info',
  SOLICITADO: 'warning',
  EN_ESPERA: 'warning',
  CREADO: 'warning',
  EMPAQUETADO: 'warning',
  DESPACHADO: 'warning',
  EN_TRANSITO: 'warning',
  RETORNO_EN_TRANSITO: 'warning',
  POR_RETORNAR: 'warning',
  EN_REVISION: 'warning',
  BAJA: 'danger',
  INHABILITADO: 'danger',
  DESTRUIDO: 'danger',
  EXTRAVIADO: 'danger',
  HABILITADO: 'success',
  SEDE_ACTIVA: 'success',
  BUENO: 'success',
  DANADO: 'warning',
  PENDIENTE: 'danger',
  PAGADA: 'success',
  DEVUELTO: 'muted',
  CANCELADA: 'muted',
  CANCELADO: 'muted',
};

function dateText(value) {
  if (!value) return '—';
  const d = new Date(value.length === 10 ? `${value}T12:00:00` : value);
  return Number.isNaN(d.getTime())
    ? String(value)
    : new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}

function dateTimeText(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime())
    ? String(value)
    : new Intl.DateTimeFormat('es-AR', { dateStyle: 'short', timeStyle: 'short' }).format(d);
}

function money(centavos) {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    maximumFractionDigits: 0,
  }).format((centavos || 0) / 100);
}
