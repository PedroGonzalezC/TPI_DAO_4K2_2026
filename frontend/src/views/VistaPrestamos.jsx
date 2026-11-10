/**
 * Vista de Préstamos: listado con filtro Activos/Todos, solicitud, entrega, cancelación y devolución.
 */

function VistaPrestamos({ tablas, nameOf, bookOfCopy, onAction }) {
  const [verTodos, setVerTodos] = useState(false);

  const todos = tablas.prestamos || [];
  const activos = todos.filter(r => !['DEVUELTO', 'CANCELADO'].includes(r.estado));
  const datosMostrados = verTodos ? todos : activos;

  const botonesFiltro = (
    <>
      <ActionButton
        label={`Activos (${activos.length})`}
        kind={verTodos ? 'outline' : 'primary'}
        onClick={() => setVerTodos(false)}
      />
      <ActionButton
        label={`Todos (${todos.length})`}
        kind={verTodos ? 'primary' : 'outline'}
        onClick={() => setVerTodos(true)}
      />
    </>
  );

  return (
    <>
      <PageHeader
        kicker="CIRCULACIÓN"
        title="Préstamos"
        subtitle="Solicitudes locales y entre sedes, entregas y devoluciones."
      >
        <button type="button" className="button button-primary" onClick={() => onAction('loan-new')}>
          Solicitar préstamo
        </button>
      </PageHeader>

      <TablaDatos
        id="prestamos"
        title={verTodos ? 'Registro completo de préstamos' : 'Préstamos en circulación'}
        tools={botonesFiltro}
        data={datosMostrados}
        empty="No hay préstamos en curso ni solicitudes pendientes."
        columns={[
          {
            key: 'id',
            label: 'N.º',
            render: r => <span className="mono">P-{String(r.id).padStart(3, '0')}</span>,
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
            key: 'socio_id',
            label: 'Socio',
            raw: r => nameOf('socios', r.socio_id),
            render: r => nameOf('socios', r.socio_id),
          },
          {
            key: 'sede_origen_id',
            label: 'Recorrido',
            raw: r => `${nameOf('sedes', r.sede_origen_id)} ${nameOf('sedes', r.sede_destino_id)}`,
            render: r => (
              <>
                {nameOf('sedes', r.sede_origen_id)}{' '}
                <span className="cell-sub">→ {nameOf('sedes', r.sede_destino_id)}</span>
              </>
            ),
          },
          {
            key: 'tipo',
            label: 'Tipo',
            render: r => LABELS[r.tipo] || r.tipo,
          },
          {
            key: 'estado',
            label: 'Estado',
            render: r => <Badge status={r.estado} />,
          },
          {
            key: 'vence_en',
            label: 'Vence',
            render: r => (
              <>
                {dateText(r.vence_en)}
                <span className="cell-sub">{r.plazo_dias || 14} días</span>
              </>
            ),
          },
        ]}
        actions={r => {
          const puedeEntregar =
            (r.estado === 'SOLICITADO' && r.tipo === 'LOCAL') || r.estado === 'LISTO';
          const puedeCancelar = r.estado === 'SOLICITADO';
          const puedeDevolver = r.estado === 'ACTIVO';

          if (!puedeEntregar && !puedeCancelar && !puedeDevolver) {
            return <span className="cell-sub">Sin acciones</span>;
          }
          return (
            <>
              {puedeEntregar && (
                <ActionButton label="Entregar" onClick={() => onAction('loan-deliver', r.id)} />
              )}
              {puedeCancelar && (
                <ActionButton label="Cancelar" onClick={() => onAction('loan-cancel', r.id)} />
              )}
              {puedeDevolver && (
                <ActionButton label="Devolver" onClick={() => onAction('loan-return', r.id)} />
              )}
            </>
          );
        }}
      />
    </>
  );
}
