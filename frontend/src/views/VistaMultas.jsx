/**
 * Vista de Multas: estado de deuda por socio, multas pendientes/pagadas y cobro de multas.
 */

function VistaMultas({ tablas, reportes, onAction }) {
  const fines = tablas.multas || [];
  const socios = tablas.socios || [];
  const overdueActive = reportes?.vencidos_multas || [];

  const pending = fines.filter(x => x.estado === 'PENDIENTE');
  const paid = fines.filter(x => x.estado === 'PAGADA');
  const totalPend = pending.reduce((acc, x) => acc + (x.monto_centavos || 0), 0);
  const totalPaid = paid.reduce((acc, x) => acc + (x.monto_centavos || 0), 0);

  const debtByMember = socios
    .map(s => {
      const mPend = pending.filter(m => m.socio_id === s.id);
      const deudaFirme = mPend.reduce((acc, m) => acc + (m.monto_centavos || 0), 0);
      const estimada = overdueActive
        .filter(o => o.socio === s.nombre)
        .reduce((acc, o) => acc + (o.multa_estimada_centavos || 0), 0);
      return {
        id: s.id,
        nombre: s.nombre,
        documento: s.documento,
        habilitado: s.habilitado,
        cantidad_pendientes: mPend.length,
        deuda_centavos: deudaFirme,
        estimada_centavos: estimada,
      };
    })
    .filter(x => x.deuda_centavos > 0 || x.estimada_centavos > 0 || !x.habilitado);

  return (
    <>
      <PageHeader
        kicker="ADMINISTRACIÓN"
        title="Multas"
        subtitle="Deudas por devoluciones con atraso. Al devolver con atraso se genera una multa pendiente y el socio queda inhabilitado hasta abonarla."
      />

      <SummaryGrid
        items={[
          ['Multas pendientes', pending.length, 'Sin abonar'],
          ['Deuda pendiente total', money(totalPend), 'En multas registradas'],
          ['Préstamos vencidos hoy', overdueActive.length, 'En curso con atraso'],
          ['Total cobrado', money(totalPaid), `${paid.length} multa(s) pagada(s)`],
        ]}
      />

      <div className="section-stack">
        <TablaDatos
          id="deuda_socios"
          title="Estado de deuda por socio"
          data={debtByMember}
          empty="Ningún socio registra deudas ni multas pendientes."
          columns={[
            {
              key: 'nombre',
              label: 'Socio',
              render: r => (
                <>
                  <span className="cell-title">{r.nombre}</span>
                  <span className="cell-sub mono">DNI {r.documento}</span>
                </>
              ),
            },
            {
              key: 'cantidad_pendientes',
              label: 'Multas pendientes',
              render: r => r.cantidad_pendientes,
            },
            {
              key: 'deuda_centavos',
              label: 'Deuda exigible',
              render: r => <strong>{money(r.deuda_centavos)}</strong>,
            },
            {
              key: 'estimada_centavos',
              label: 'En préstamos aún no devueltos',
              render: r =>
                r.estimada_centavos > 0 ? (
                  <>
                    <span className="cell-title">{money(r.estimada_centavos)}</span>
                    <span className="cell-sub">Se genera al devolver</span>
                  </>
                ) : (
                  '—'
                ),
            },
            {
              key: 'habilitado',
              label: 'Estado del socio',
              render: r => <Badge status={r.habilitado ? 'HABILITADO' : 'INHABILITADO'} />,
            },
          ]}
        />

        <TablaDatos
          id="multas"
          title="Registro de multas"
          data={fines}
          empty="Las multas aparecen aquí cuando se devuelve un préstamo con atraso."
          columns={[
            {
              key: 'id',
              label: 'N.º',
              render: r => <span className="mono">M-{String(r.id).padStart(3, '0')}</span>,
            },
            {
              key: 'socio_nombre',
              label: 'Socio',
              render: r => (
                <>
                  <span className="cell-title">{r.socio_nombre}</span>
                  <span className="cell-sub mono">{r.socio_documento}</span>
                </>
              ),
            },
            {
              key: 'libro_titulo',
              label: 'Material y préstamo',
              render: r => (
                <>
                  <span className="cell-title">{r.libro_titulo}</span>
                  <span className="cell-sub mono">
                    P-{String(r.prestamo_id).padStart(3, '0')} · {r.ejemplar_codigo}
                  </span>
                </>
              ),
            },
            {
              key: 'dias_atraso',
              label: 'Atraso',
              render: r => `${r.dias_atraso} día(s)`,
            },
            {
              key: 'monto_centavos',
              label: 'Monto',
              render: r => <strong>{money(r.monto_centavos)}</strong>,
            },
            {
              key: 'creada_en',
              label: 'Generada',
              render: r => dateText(r.creada_en),
            },
            {
              key: 'estado',
              label: 'Estado',
              render: r => <Badge status={r.estado} />,
            },
          ]}
          actions={r =>
            r.estado === 'PENDIENTE' ? (
              <ActionButton label="Pagar multa" onClick={() => onAction('multa-pay', r.id)} />
            ) : (
              <span className="cell-sub">Pagada ({dateText(r.pagada_en)})</span>
            )
          }
        />
      </div>
    </>
  );
}
