/**
 * Vista de Reportes: selector interactivo de los 6 reportes estadísticos y operativos.
 */

function VistaReportes({ reportes }) {
  const [chosen, setChosen] = useState('activos_transito');
  const data = reportes?.[chosen] || [];

  const columns =
    data.length > 0
      ? Object.keys(data[0]).map(key => ({
          key,
          label: key.replace(/_centavos$/, '').replaceAll('_', ' '),
          render: row =>
            key.includes('centavos')
              ? money(row[key])
              : key.includes('fecha') || key.includes('vence')
              ? dateText(row[key])
              : String(row[key] ?? '—'),
        }))
      : [{ key: 'sin_datos', label: 'Resultado' }];

  return (
    <>
      <PageHeader
        kicker="ANÁLISIS"
        title="Reportes"
        subtitle="Seis vistas para revisar circulación, demanda, disponibilidad y tiempos de traslado."
      />

      <p className="report-note">
        Las cifras reflejan la base local al momento de cargar esta pantalla. “Tasa de recepción”
        mide remitos recibidos sobre emitidos; no equivale a entregas sin incidencias.
      </p>

      <div className="field" style={{ maxWidth: '370px', marginBottom: '22px' }}>
        <label htmlFor="report-kind">Tipo de reporte</label>
        <select
          id="report-kind"
          className="report-select"
          value={chosen}
          onChange={e => setChosen(e.target.value)}
        >
          {Object.entries(REPORTS).map(([key, name]) => (
            <option key={key} value={key}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {chosen === 'logistica' && data.length > 0 && (
        <>
          <div className="report-highlight">
            {[
              ['Remitos emitidos', data[0].envios || 0],
              ['Recibidos', data[0].recibidos || 0],
              ['En tránsito', data[0].en_transito || 0],
              [
                'Tiempo medio',
                data[0].horas_promedio_trayecto == null
                  ? '—'
                  : `${data[0].horas_promedio_trayecto} h`,
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <small>{label}</small>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <p className="cell-sub">
            Recepción:{' '}
            {data[0]?.tasa_recepcion_pct == null ? '—' : `${data[0].tasa_recepcion_pct} %`} de los
            remitos emitidos.
          </p>
        </>
      )}

      {chosen !== 'logistica' && (
        <TablaDatos
          id={`reporte_${chosen}`}
          title={REPORTS[chosen]}
          data={data}
          columns={columns}
          empty="Este reporte todavía no tiene datos para mostrar."
        />
      )}
    </>
  );
}
