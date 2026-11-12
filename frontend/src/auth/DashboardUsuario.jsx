/**
 * Dashboard exclusivo para el rol Usuario (SOCIO):
 * Permite consultar únicamente qué materiales (libros) se encuentran habilitados
 * y cuáles ejemplares físicos están disponibles en las sedes activas.
 */

function DashboardUsuario({ tablas, nameOf }) {
  const [sedeFiltro, setSedeFiltro] = useState('TODAS');

  const sedesActivas = (tablas.sedes || []).filter(s => s.activa);
  const idsSedesActivas = new Set(sedesActivas.map(s => s.id));
  const libros = tablas.libros || [];
  const todosEjemplares = tablas.ejemplares || [];

  // Ejemplares disponibles ubicados en sedes activas
  const ejemplaresDisponibles = todosEjemplares.filter(
    e => e.estado === 'DISPONIBLE' && idsSedesActivas.has(e.sede_actual_id)
  );

  const ejemplaresFiltrados =
    sedeFiltro === 'TODAS'
      ? ejemplaresDisponibles
      : ejemplaresDisponibles.filter(e => e.sede_actual_id === Number(sedeFiltro));

  // Materiales habilitados (libros que no están dados de baja y cuentan con ejemplares activos en la red)
  const materialesHabilitados = libros
    .map(libro => {
      const copiasActivas = todosEjemplares.filter(
        e => e.libro_id === libro.id && e.estado !== 'BAJA' && idsSedesActivas.has(e.sede_actual_id)
      );
      const disponibles = copiasActivas.filter(e => e.estado === 'DISPONIBLE');
      return {
        ...libro,
        copias_habilitadas: copiasActivas.length,
        copias_disponibles: disponibles.length,
      };
    })
    .filter(libro => libro.copias_habilitadas > 0);

  const selectorSede = (
    <select
      className="report-select"
      aria-label="Filtrar ejemplares por sede"
      value={sedeFiltro}
      onChange={e => setSedeFiltro(e.target.value)}
    >
      <option value="TODAS">Todas las sedes habilitadas ({ejemplaresDisponibles.length})</option>
      {sedesActivas.map(s => (
        <option key={s.id} value={s.id}>
          {s.nombre}
        </option>
      ))}
    </select>
  );

  return (
    <>
      <PageHeader
        kicker="CONSULTA DE CATÁLOGO"
        title="Materiales y ejemplares disponibles"
        subtitle="Consultá los títulos habilitados en la red y las copias disponibles para retiro en cada sede."
      />

      <SummaryGrid
        items={[
          ['Materiales habilitados', materialesHabilitados.length, 'Títulos activos en catálogo'],
          ['Ejemplares disponibles', ejemplaresDisponibles.length, 'Listos para préstamo hoy'],
          ['Sedes habilitadas', sedesActivas.length, 'Puntos de retiro activos'],
          [
            'Títulos con stock inmediato',
            materialesHabilitados.filter(m => m.copias_disponibles > 0).length,
            'Al menos 1 ejemplar disponible',
          ],
        ]}
      />

      <div className="section-stack">
        <TablaDatos
          id="usuario_materiales"
          title="Materiales habilitados"
          data={materialesHabilitados}
          empty="No hay materiales habilitados en este momento."
          columns={[
            {
              key: 'titulo',
              label: 'Material',
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
              key: 'copias_disponibles',
              label: 'Disponibilidad',
              render: r => (
                <Badge status={r.copias_disponibles > 0 ? 'DISPONIBLE' : 'PRESTADO'} />
              ),
            },
            {
              key: 'copias_habilitadas',
              label: 'Ejemplares libres / totales',
              render: r => (
                <span>
                  <strong>{r.copias_disponibles}</strong> de {r.copias_habilitadas} disponible(s)
                </span>
              ),
            },
          ]}
        />

        <TablaDatos
          id="usuario_ejemplares"
          title="Ejemplares disponibles para préstamo"
          tools={selectorSede}
          data={ejemplaresFiltrados}
          empty="No hay ejemplares disponibles en la sede seleccionada."
          columns={[
            {
              key: 'codigo',
              label: 'Código',
              render: r => <span className="mono">{r.codigo}</span>,
            },
            {
              key: 'libro_id',
              label: 'Título del material',
              raw: r => nameOf('libros', r.libro_id, 'titulo'),
              render: r => (
                <>
                  <span className="cell-title">{nameOf('libros', r.libro_id, 'titulo')}</span>
                  <span className="cell-sub">{nameOf('libros', r.libro_id, 'autor')}</span>
                </>
              ),
            },
            {
              key: 'sede_actual_id',
              label: 'Sede donde se encuentra',
              raw: r => nameOf('sedes', r.sede_actual_id),
              render: r => nameOf('sedes', r.sede_actual_id),
            },
            {
              key: 'condicion',
              label: 'Condición física',
              raw: r => LABELS[r.condicion || 'BUENO'] || r.condicion,
              render: r => <Badge status={r.condicion || 'BUENO'} />,
            },
            {
              key: 'estado',
              label: 'Estado',
              render: r => <Badge status={r.estado} />,
            },
          ]}
        />
      </div>
    </>
  );
}
