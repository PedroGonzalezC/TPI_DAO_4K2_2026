/**
 * Vista de Inicio (Panel de Circulación): resumen de actividad y últimos remitos.
 */

function VistaInicio({ tablas, nameOf, onAction }) {
  const loans = tablas.prestamos || [];
  const copies = tablas.ejemplares || [];
  const slips = tablas.remitos || [];
  const reservas = tablas.reservas || [];

  const active = loans.filter(x => x.estado === 'ACTIVO').length;
  const transit = slips.filter(x => x.estado === 'DESPACHADO').length;
  const available = copies.filter(x => x.estado === 'DISPONIBLE').length;
  const pending = reservas.filter(x => ['EN_ESPERA', 'ASIGNADA'].includes(x.estado)).length;
  const recent = slips.slice(-4).reverse();

  return (
    <>
      <PageHeader
        kicker="PANEL DE CIRCULACIÓN"
        title="Una red, cada ejemplar en su lugar."
        subtitle="Consultá la actividad de las sedes y continuá los movimientos pendientes."
      >
        <button type="button" className="button button-primary" onClick={() => onAction('loan-new')}>
          Solicitar préstamo
        </button>
      </PageHeader>

      <SummaryGrid
        items={[
          ['Préstamos activos', active, 'En manos de socios'],
          ['En tránsito', transit, 'Remitos despachados'],
          ['Disponibles', available, 'Ejemplares listos'],
          ['Reservas abiertas', pending, 'En espera o asignadas'],
        ]}
      />

      <div className="dashboard-grid">
        <section className="route-card">
          <p className="eyebrow">CIRCULACIÓN ENTRE SEDES</p>
          <h2>El recorrido queda registrado.</h2>
          <p>
            Desde la sede de origen hasta la recepción y el regreso: cada remito conserva su
            secuencia de estados.
          </p>
          <div className="route-line">
            <div className="route-step">
              <strong>Origen</strong>Empaquetar
            </div>
            <div className="route-step">
              <strong>Trayecto</strong>Despachar
            </div>
            <div className="route-step">
              <strong>Destino</strong>Recibir
            </div>
          </div>
          <button type="button" className="button" onClick={() => onAction('go-remitos')}>
            Ver traslados →
          </button>
        </section>

        <section className="panel panel-pad">
          <p className="eyebrow">MOVIMIENTO RECIENTE</p>
          <h2 className="panel-title">Remitos</h2>
          <p className="panel-intro">Últimos traslados registrados.</p>
          {recent.length > 0 ? (
            <div className="quick-list">
              {recent.map(r => (
                <div className="quick-row" key={r.id}>
                  <span>
                    <strong>R-{String(r.id).padStart(3, '0')}</strong>
                    <br />
                    <small>
                      {nameOf('sedes', r.origen_id)} → {nameOf('sedes', r.destino_id)}
                    </small>
                  </span>
                  <Badge status={r.estado} />
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-brief">
              Todavía no se emitieron remitos. Una solicitud entre sedes inicia el recorrido.
            </p>
          )}
        </section>
      </div>
    </>
  );
}
