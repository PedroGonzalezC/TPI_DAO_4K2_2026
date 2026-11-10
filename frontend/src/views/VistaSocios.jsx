/**
 * Vista de Socios: administración del padrón de socios y su habilitación.
 */

function VistaSocios({ tablas, onAction }) {
  const socios = tablas.socios || [];

  return (
    <>
      <PageHeader
        kicker="PADRÓN"
        title="Socios"
        subtitle="Personas habilitadas para solicitar préstamos y reservas."
      >
        <button
          type="button"
          className="button button-primary"
          onClick={() => onAction('member-new')}
        >
          Agregar socio
        </button>
      </PageHeader>

      <TablaDatos
        id="socios"
        title="Socios registrados"
        data={socios}
        empty="Agregá un socio para iniciar un préstamo."
        columns={[
          {
            key: 'id',
            label: 'N.º',
            render: r => <span className="mono">#{r.id}</span>,
          },
          {
            key: 'nombre',
            label: 'Nombre',
            render: r => <span className="cell-title">{r.nombre}</span>,
          },
          {
            key: 'documento',
            label: 'Documento',
            render: r => <span className="mono">{r.documento}</span>,
          },
          {
            key: 'email',
            label: 'Contacto',
            render: r => r.email,
          },
          {
            key: 'habilitado',
            label: 'Estado',
            render: r => <Badge status={r.habilitado ? 'HABILITADO' : 'INHABILITADO'} />,
          },
        ]}
        actions={r => (
          <>
            <ActionButton label="Editar" onClick={() => onAction('member-edit', r.id)} />
            <ActionButton
              label={r.habilitado ? 'Inhabilitar' : 'Habilitar'}
              onClick={() => onAction('member-toggle', r.id)}
            />
          </>
        )}
      />
    </>
  );
}
