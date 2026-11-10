/**
 * Vista de Traslados (Remitos): seguimiento logístico de ida y regreso entre sedes.
 */

function VistaRemitos({ tablas, nameOf, bookOfCopy, onAction }) {
  const remitos = tablas.remitos || [];
  const siguienteAccion = {
    CREADO: 'Empaquetar',
    EMPAQUETADO: 'Despachar',
    DESPACHADO: 'Recibir',
  };

  return (
    <>
      <PageHeader
        kicker="LOGÍSTICA"
        title="Traslados"
        subtitle="Cada remito registra la preparación, salida y recepción de un ejemplar."
      />

      <TablaDatos
        id="remitos"
        title="Remitos de ida y regreso"
        data={remitos}
        empty="Una solicitud entre sedes genera un remito de ida."
        columns={[
          {
            key: 'id',
            label: 'Remito',
            render: r => <span className="mono">R-{String(r.id).padStart(3, '0')}</span>,
          },
          {
            key: 'ejemplar_id',
            label: 'Material',
            raw: r => bookOfCopy(r.ejemplar_id),
            render: r => (
              <>
                <span className="cell-title">{bookOfCopy(r.ejemplar_id)}</span>
                <span className="cell-sub mono">{nameOf('ejemplares', r.ejemplar_id, 'codigo')}</span>
              </>
            ),
          },
          {
            key: 'tipo',
            label: 'Trayecto',
            render: r => LABELS[r.tipo] || r.tipo,
          },
          {
            key: 'origen_id',
            label: 'Sedes',
            raw: r => `${nameOf('sedes', r.origen_id)} ${nameOf('sedes', r.destino_id)}`,
            render: r => (
              <>
                {nameOf('sedes', r.origen_id)}{' '}
                <span className="cell-sub">→ {nameOf('sedes', r.destino_id)}</span>
              </>
            ),
          },
          {
            key: 'estado',
            label: 'Estado',
            render: r => <Badge status={r.estado} />,
          },
          {
            key: 'creado_en',
            label: 'Creado',
            render: r => dateText(r.creado_en),
          },
        ]}
        actions={r => (
          <>
            {r.estado !== 'RECIBIDO' && (
              <ActionButton
                label={siguienteAccion[r.estado]}
                onClick={() => onAction('remito-next', r.id)}
              />
            )}
            <ActionButton label="Historial" onClick={() => onAction('remito-history', r.id)} />
          </>
        )}
      />
    </>
  );
}
