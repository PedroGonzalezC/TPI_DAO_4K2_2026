/**
 * Vista de Sedes: gestión de sedes de la red, horarios y estado operativo.
 */

function VistaSedes({ tablas, onAction }) {
  const sedes = tablas.sedes || [];

  return (
    <>
      <PageHeader
        kicker="RED DE ATENCIÓN"
        title="Sedes"
        subtitle="Direcciones, contacto, horarios y estado operativo de la red."
      >
        <button
          type="button"
          className="button button-primary"
          onClick={() => onAction('branch-new')}
        >
          Agregar sede
        </button>
      </PageHeader>

      <TablaDatos
        id="sedes"
        title="Sedes de la red"
        data={sedes}
        empty="Agregá la primera sede para incorporar ejemplares."
        columns={[
          {
            key: 'nombre',
            label: 'Sede',
            render: r => (
              <>
                <span className="cell-title">{r.nombre}</span>
                <span className="cell-sub">{r.direccion}</span>
              </>
            ),
          },
          {
            key: 'contacto',
            label: 'Contacto',
            render: r => r.contacto,
          },
          {
            key: 'horarios',
            label: 'Horarios',
            render: r => r.horarios,
          },
          {
            key: 'activa',
            label: 'Estado',
            render: r => <Badge status={r.activa ? 'SEDE_ACTIVA' : 'BAJA'} />,
          },
        ]}
        actions={r => (
          <>
            <ActionButton label="Editar" onClick={() => onAction('branch-edit', r.id)} />
            <ActionButton
              label={r.activa ? 'Dar de baja' : 'Reactivar'}
              onClick={() => onAction('branch-toggle', r.id)}
            />
          </>
        )}
      />
    </>
  );
}
