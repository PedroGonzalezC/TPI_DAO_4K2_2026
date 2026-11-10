/**
 * Vista de Catálogo: fichas bibliográficas (Libros) y copias físicas (Ejemplares).
 */

function VistaCatalogo({ tablas, nameOf, onAction }) {
  const libros = tablas.libros || [];
  const ejemplares = tablas.ejemplares || [];

  return (
    <>
      <PageHeader
        kicker="FONDO BIBLIOGRÁFICO"
        title="Catálogo"
        subtitle="Títulos únicos y ejemplares físicos vinculados a una sede."
      >
        <button type="button" className="button button-primary" onClick={() => onAction('book-new')}>
          Agregar libro
        </button>
        <button type="button" className="button button-outline" onClick={() => onAction('copy-new')}>
          Agregar ejemplar
        </button>
      </PageHeader>

      <div className="section-stack">
        <TablaDatos
          id="libros"
          title="Libros"
          data={libros}
          empty="Agregá un libro para comenzar el catálogo."
          columns={[
            {
              key: 'titulo',
              label: 'Título',
              render: r => (
                <>
                  <span className="cell-title">{r.titulo}</span>
                  <span className="cell-sub">{r.autor}</span>
                </>
              ),
            },
            {
              key: 'isbn',
              label: 'ISBN',
              render: r => <span className="mono">{r.isbn}</span>,
            },
            {
              key: 'anio',
              label: 'Año',
              render: r => r.anio || '—',
            },
            {
              key: 'id',
              label: 'Ejemplares',
              raw: r => ejemplares.filter(e => e.libro_id === r.id).length,
              render: r => ejemplares.filter(e => e.libro_id === r.id).length,
            },
          ]}
          actions={r => {
            const tieneCopias = ejemplares.some(e => e.libro_id === r.id);
            return (
              <>
                <ActionButton label="Editar" onClick={() => onAction('book-edit', r.id)} />
                {!tieneCopias && (
                  <ActionButton label="Eliminar" onClick={() => onAction('book-delete', r.id)} />
                )}
              </>
            );
          }}
        />

        <TablaDatos
          id="ejemplares"
          title="Ejemplares físicos"
          data={ejemplares}
          empty="Agregá ejemplares para consultar disponibilidad."
          columns={[
            {
              key: 'codigo',
              label: 'Código',
              render: r => <span className="mono">{r.codigo}</span>,
            },
            {
              key: 'libro_id',
              label: 'Libro',
              raw: r => nameOf('libros', r.libro_id, 'titulo'),
              render: r => nameOf('libros', r.libro_id, 'titulo'),
            },
            {
              key: 'sede_pertenencia_id',
              label: 'Pertenece a',
              raw: r => nameOf('sedes', r.sede_pertenencia_id),
              render: r => nameOf('sedes', r.sede_pertenencia_id),
            },
            {
              key: 'sede_actual_id',
              label: 'Última sede',
              raw: r => nameOf('sedes', r.sede_actual_id),
              render: r => nameOf('sedes', r.sede_actual_id),
            },
            {
              key: 'condicion',
              label: 'Condición',
              raw: r => LABELS[r.condicion || 'BUENO'] || r.condicion,
              render: r => <Badge status={r.condicion || 'BUENO'} />,
            },
            {
              key: 'estado',
              label: 'Estado',
              render: r => <Badge status={r.estado} />,
            },
          ]}
          actions={r => {
            if (r.estado === 'EN_REVISION') {
              return (
                <>
                  <ActionButton label="Apto" onClick={() => onAction('copy-fit', r.id)} />
                  <ActionButton label="Dar de baja" onClick={() => onAction('copy-unfit', r.id)} />
                </>
              );
            }
            if (r.estado === 'DISPONIBLE') {
              return <ActionButton label="Dar de baja" onClick={() => onAction('copy-delete', r.id)} />;
            }
            return <span className="cell-sub">Sin acciones</span>;
          }}
        />
      </div>
    </>
  );
}
