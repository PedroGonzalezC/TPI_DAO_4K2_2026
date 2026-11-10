/**
 * Componentes visuales reutilizables (insignias de estado, cabeceras de página,
 * tarjetas de resumen y botones de acción).
 */

function Badge({ status }) {
  const tone = STATUS_TONE[status] || 'muted';
  const label = LABELS[status] || status;
  return <span className={`badge badge-${tone}`}>{label}</span>;
}

function PageHeader({ kicker, title, subtitle, children }) {
  return (
    <div className="page-header">
      <div>
        <p className="eyebrow">{kicker}</p>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {children ? <div className="page-header-actions">{children}</div> : null}
    </div>
  );
}

function SummaryGrid({ items }) {
  return (
    <div className="summary-grid">
      {items.map(([label, val, note]) => (
        <div className="summary-item" key={label}>
          <span className="summary-label">{label}</span>
          <strong className="summary-value">{val}</strong>
          <span className="summary-note">{note}</span>
        </div>
      ))}
    </div>
  );
}

function ActionButton({ label, onClick, kind = 'text', disabled = false }) {
  const classMap = {
    text: 'text-button',
    sort: 'table-sort',
    clear: 'search-clear',
    pager: 'button button-outline button-small',
  };
  const className = classMap[kind] || `button button-${kind} button-small`;
  return (
    <button
      type="button"
      className={className}
      disabled={disabled}
      onClick={onClick}
      aria-label={kind === 'clear' ? 'Limpiar búsqueda' : undefined}
    >
      {label}
    </button>
  );
}

function ErrorBanner({ mensaje, onRecargar }) {
  if (!mensaje) return null;
  return (
    <div className="alert page-alert" role="alert">
      <p>{mensaje}</p>
      <button type="button" className="button button-outline" onClick={onRecargar}>
        Volver a cargar
      </button>
    </div>
  );
}
