/**
 * Vista de Reservas: cola de espera por libro y sede de retiro.
 */

function VistaReservas({ tablas, nameOf, onAction }) {
  const reservas = tablas.reservas || [];

  return (
    <>
      <PageHeader
        kicker="TURNOS DE LECTURA"
        title="Reservas"
        subtitle="La primera reserva en espera recibe el siguiente ejemplar disponible en su sede."
      >
        <button
          type="button"
          className="button button-primary"
          onClick={() => onAction('reserve-new')}
        >
          Crear reserva
        </button>
      </PageHeader>

      <TablaDatos
        id="reservas"
        title="Cola de reservas"
        data={reservas}
        empty="Creá una reserva para que el sistema asigne el próximo ejemplar disponible."
        columns={[
          {
            key: 'id',
            label: 'N.º',
            render: r => <span className="mono">#{r.id}</span>,
          },
          {
            key: 'libro_id',
            label: 'Libro',
            raw: r => nameOf('libros', r.libro_id, 'titulo'),
            render: r => <span className="cell-title">{nameOf('libros', r.libro_id, 'titulo')}</span>,
          },
          {
            key: 'socio_id',
            label: 'Socio',
            raw: r => nameOf('socios', r.socio_id),
            render: r => nameOf('socios', r.socio_id),
          },
          {
            key: 'sede_id',
            label: 'Retiro',
            raw: r => nameOf('sedes', r.sede_id),
            render: r => nameOf('sedes', r.sede_id),
          },
          {
            key: 'ejemplar_id',
            label: 'Ejemplar',
            raw: r => (r.ejemplar_id ? nameOf('ejemplares', r.ejemplar_id, 'codigo') : ''),
            render: r =>
              r.ejemplar_id ? (
                <span className="mono">{nameOf('ejemplares', r.ejemplar_id, 'codigo')}</span>
              ) : (
                <span className="cell-sub">En espera</span>
              ),
          },
          {
            key: 'creada_en',
            label: 'Solicitada',
            render: r => dateText(r.creada_en),
          },
          {
            key: 'estado',
            label: 'Estado',
            render: r => <Badge status={r.estado} />,
          },
        ]}
        actions={r => {
          const activa = ['EN_ESPERA', 'ASIGNADA'].includes(r.estado);
          if (!activa) return <span className="cell-sub">Cerrada</span>;
          return (
            <>
              {r.estado === 'ASIGNADA' && (
                <ActionButton
                  label="Solicitar préstamo"
                  onClick={() => onAction('reserve-loan', r.id)}
                />
              )}
              <ActionButton label="Cancelar" onClick={() => onAction('reserve-cancel', r.id)} />
            </>
          );
        }}
      />
    </>
  );
}
