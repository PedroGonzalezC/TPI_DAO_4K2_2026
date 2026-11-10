/**
 * Componente React de tabla con búsqueda en vivo, ordenamiento por columna y paginación.
 */

function TablaDatos({
  id,
  title,
  data = [],
  columns = [],
  actions,
  tools = null,
  empty = 'Todavía no hay registros.',
  search = true,
}) {
  const [busqueda, setBusqueda] = useState('');
  const [ordenKey, setOrdenKey] = useState(columns[0]?.key || 'id');
  const [direccion, setDireccion] = useState(1); // 1 = asc, -1 = desc
  const [pagina, setPagina] = useState(1);

  const q = busqueda.trim().toLocaleLowerCase('es-AR');

  const filtrados = data.filter(row => {
    if (!q) return true;
    const textoFila = [
      Object.values(row).join(' '),
      ...columns.map(c => (c.raw ? c.raw(row) : row[c.key])),
    ]
      .join(' ')
      .toLocaleLowerCase('es-AR');
    return textoFila.includes(q);
  });

  const colActiva = columns.find(c => c.key === ordenKey) || columns[0];
  const ordenados = filtrados.slice().sort((a, b) => {
    if (!colActiva) return 0;
    const va = colActiva.raw ? colActiva.raw(a) : a[colActiva.key];
    const vb = colActiva.raw ? colActiva.raw(b) : b[colActiva.key];
    return (
      direccion *
      String(va ?? '').localeCompare(String(vb ?? ''), 'es-AR', {
        numeric: true,
        sensitivity: 'base',
      })
    );
  });

  const total = ordenados.length;
  const totalPaginas = Math.max(1, Math.ceil(total / 10));
  const paginaActual = Math.min(Math.max(1, pagina), totalPaginas);
  const visibles = ordenados.slice((paginaActual - 1) * 10, paginaActual * 10);

  function cambiarOrden(key) {
    if (ordenKey === key) {
      setDireccion(prev => (prev === 1 ? -1 : 1));
    } else {
      setOrdenKey(key);
      setDireccion(1);
    }
    setPagina(1);
  }

  return (
    <section className="table-panel" aria-label={title}>
      <div className="table-toolbar">
        <h2>{title}</h2>
        <div className="table-tools">
          {tools}
          {search && (
            <div className="search-wrap">
              <label className="sr-only" htmlFor={`search-${id}`}>
                Buscar en {title}
              </label>
              <input
                id={`search-${id}`}
                type="search"
                value={busqueda}
                placeholder="Buscar registros"
                autoComplete="off"
                onChange={e => {
                  setBusqueda(e.target.value);
                  setPagina(1);
                }}
              />
              {busqueda && (
                <ActionButton
                  label="×"
                  kind="clear"
                  onClick={() => {
                    setBusqueda('');
                    setPagina(1);
                  }}
                />
              )}
            </div>
          )}
        </div>
      </div>

      {visibles.length > 0 ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {columns.map(col => (
                  <th
                    key={col.key}
                    scope="col"
                    aria-sort={
                      ordenKey === col.key
                        ? direccion === 1
                          ? 'ascending'
                          : 'descending'
                        : undefined
                    }
                  >
                    <ActionButton
                      label={`${col.label} ${
                        ordenKey === col.key ? (direccion === 1 ? '↑' : '↓') : '↕'
                      }`}
                      kind="sort"
                      onClick={() => cambiarOrden(col.key)}
                    />
                  </th>
                ))}
                {actions && <th scope="col">Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {visibles.map((row, idx) => (
                <tr key={row.id ?? idx}>
                  {columns.map(col => (
                    <td key={col.key}>
                      {col.render ? col.render(row) : String(row[col.key] ?? '—')}
                    </td>
                  ))}
                  {actions && (
                    <td>
                      <div className="actions">{actions(row)}</div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="table-empty">
          <strong>{busqueda ? 'Sin resultados' : 'Sin registros aún'}</strong>
          <p>{busqueda ? 'Probá con otra búsqueda o limpiá el filtro.' : empty}</p>
          {busqueda && (
            <ActionButton
              label="Limpiar búsqueda"
              kind="outline"
              onClick={() => {
                setBusqueda('');
                setPagina(1);
              }}
            />
          )}
        </div>
      )}

      <div className="table-footer">
        <span>
          {total
            ? `${(paginaActual - 1) * 10 + 1}–${Math.min(paginaActual * 10, total)} de ${total}`
            : '0 registros'}
        </span>
        <div className="pager">
          <ActionButton
            label="Anterior"
            kind="pager"
            disabled={paginaActual <= 1}
            onClick={() => setPagina(paginaActual - 1)}
          />
          <span>
            Página {paginaActual} de {totalPaginas}
          </span>
          <ActionButton
            label="Siguiente"
            kind="pager"
            disabled={paginaActual >= totalPaginas}
            onClick={() => setPagina(paginaActual + 1)}
          />
        </div>
      </div>
    </section>
  );
}
