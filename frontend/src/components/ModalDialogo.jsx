/**
 * Componente React para modales de formulario, confirmación de acciones y línea de tiempo de remitos.
 */

function ModalDialogo({ dialogo, ejemplares = [], onClose, onSubmitAction }) {
  const [valores, setValores] = useState({});
  const [erroresCampo, setErroresCampo] = useState({});
  const [errorGeneral, setErrorGeneral] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [confirmacionBaja, setConfirmacionBaja] = useState('');
  const [historial, setHistorial] = useState(null);
  const [errorHistorial, setErrorHistorial] = useState(false);

  useEffect(() => {
    if (!dialogo) return;
    setErroresCampo({});
    setErrorGeneral('');
    setOcupado(false);
    setConfirmacionBaja('');

    if (dialogo.type === 'form' && dialogo.fields) {
      const inicial = {};
      dialogo.fields.forEach(f => {
        inicial[f.name] = f.value != null ? String(f.value) : '';
      });
      setValores(inicial);
    }

    if (dialogo.type === 'history' && dialogo.historyId) {
      setHistorial(null);
      setErrorHistorial(false);
      request(`/api/remitos/${dialogo.historyId}/historial`)
        .then(eventos => setHistorial(eventos))
        .catch(() => setErrorHistorial(true));
    }
  }, [dialogo]);

  useEffect(() => {
    if (!dialogo) return;
    function onKeyDown(e) {
      if (e.key === 'Escape' && !ocupado) {
        e.preventDefault();
        onClose();
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [dialogo, ocupado, onClose]);

  if (!dialogo) return null;

  function cambiarCampo(name, value) {
    setValores(prev => {
      const nuevo = { ...prev, [name]: value };
      if (name === 'ejemplar_id' && dialogo.action === 'solicitar_prestamo') {
        const copia = ejemplares.find(e => e.id === Number(value));
        if (copia) {
          nuevo.sede_origen_id = String(copia.sede_pertenencia_id);
        }
      }
      return nuevo;
    });
    if (name === 'condicion' && dialogo.action === 'devolver_prestamo') {
      setConfirmacionBaja('');
      setErrorGeneral('');
    }
  }

  async function manejarSubmitFormulario(e) {
    e.preventDefault();
    const nuevosErrores = {};
    let hayError = false;

    for (const field of dialogo.fields) {
      const val = String(valores[field.name] ?? '').trim();
      const invalidoRequerido = field.required && !val;
      const invalidoEmail =
        field.type === 'email' && val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
      const invalidoNumero =
        field.type === 'number' &&
        val &&
        (!Number.isInteger(Number(val)) || Number(val) < (field.min || 0));

      const msg = invalidoRequerido
        ? `Completá ${field.label.toLowerCase()}.`
        : invalidoEmail
        ? 'Ingresá un correo válido.'
        : invalidoNumero
        ? 'Ingresá un número válido.'
        : '';

      if (msg) {
        nuevosErrores[field.name] = msg;
        hayError = true;
      }
    }

    setErroresCampo(nuevosErrores);
    if (hayError) return;

    if (
      dialogo.action === 'devolver_prestamo' &&
      ['DESTRUIDO', 'EXTRAVIADO'].includes(valores.condicion) &&
      confirmacionBaja !== valores.condicion
    ) {
      setConfirmacionBaja(valores.condicion);
      setErrorGeneral(
        `Vas a registrar el ejemplar como ${LABELS[
          valores.condicion
        ].toLowerCase()} y quedará de baja. Confirmá la operación.`
      );
      return;
    }

    setOcupado(true);
    setErrorGeneral('');
    try {
      await onSubmitAction(
        { accion: dialogo.action, ...dialogo.extra, ...valores },
        dialogo.success
      );
    } catch (err) {
      setOcupado(false);
      setErrorGeneral(err.message);
    }
  }

  async function manejarConfirmacion() {
    setOcupado(true);
    setErrorGeneral('');
    try {
      await onSubmitAction({ accion: dialogo.action, ...dialogo.payload }, dialogo.success);
    } catch (err) {
      setOcupado(false);
      setErrorGeneral(err.message);
    }
  }

  return (
    <div id="dialog-layer" className="dialog-layer">
      <div className="dialog-backdrop" onClick={() => !ocupado && onClose()}></div>
      <section
        id="dialog"
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description"
      >
        <div className="dialog-heading">
          <div>
            <p className="eyebrow" id="dialog-eyebrow">
              {dialogo.eyebrow || (dialogo.type === 'confirm' ? 'CONFIRMACIÓN' : 'OPERACIÓN')}
            </p>
            <h2 id="dialog-title">{dialogo.title}</h2>
          </div>
          <span id="dialog-close-slot">
            <button
              type="button"
              className="icon-button"
              id="dialog-close"
              aria-label="Cerrar diálogo"
              disabled={ocupado}
              onClick={onClose}
            >
              ×
            </button>
          </span>
        </div>
        <p id="dialog-description" className="dialog-description">
          {dialogo.description || ''}
        </p>

        <div id="dialog-body">
          {dialogo.type === 'form' && (
            <form id="dialog-form" noValidate onSubmit={manejarSubmitFormulario}>
              {errorGeneral && (
                <div className="dialog-error alert" role="alert">
                  {errorGeneral}
                </div>
              )}
              <div className="form-fields">
                {dialogo.fields.map(f => {
                  const fieldId = `field-${f.name}`;
                  const errText = erroresCampo[f.name] || '';
                  const val = valores[f.name] ?? '';
                  return (
                    <div className="field" key={f.name}>
                      <label htmlFor={fieldId}>
                        {f.label}
                        {f.required ? ' *' : ''}
                      </label>
                      {f.options ? (
                        <select
                          id={fieldId}
                          name={f.name}
                          value={val}
                          aria-invalid={String(!!errText)}
                          onChange={e => cambiarCampo(f.name, e.target.value)}
                        >
                          <option value="">Seleccionar…</option>
                          {f.options.map(o => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                      ) : f.type === 'textarea' ? (
                        <textarea
                          id={fieldId}
                          name={f.name}
                          value={val}
                          aria-invalid={String(!!errText)}
                          onChange={e => cambiarCampo(f.name, e.target.value)}
                        />
                      ) : (
                        <input
                          id={fieldId}
                          name={f.name}
                          type={f.type || 'text'}
                          min={f.min}
                          value={val}
                          autoComplete="off"
                          aria-invalid={String(!!errText)}
                          onChange={e => cambiarCampo(f.name, e.target.value)}
                        />
                      )}
                      {f.help && (
                        <span className="field-help" id={`${fieldId}-help`}>
                          {f.help}
                        </span>
                      )}
                      <span className="field-error" id={`${fieldId}-error`}>
                        {errText}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="dialog-actions">
                <button
                  type="button"
                  className="button button-outline"
                  disabled={ocupado}
                  onClick={onClose}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={`button button-${dialogo.danger ? 'danger' : 'primary'}`}
                  disabled={ocupado}
                  data-busy={String(ocupado)}
                >
                  {confirmacionBaja
                    ? 'Confirmar baja y devolución'
                    : dialogo.submit || 'Guardar'}
                </button>
              </div>
            </form>
          )}

          {dialogo.type === 'confirm' && (
            <>
              <div className="dialog-confirm-copy">{dialogo.object}</div>
              {errorGeneral && (
                <div className="dialog-error alert" role="alert" style={{ marginTop: '14px' }}>
                  {errorGeneral}
                </div>
              )}
              <div className="dialog-actions">
                <button
                  type="button"
                  className="button button-outline"
                  disabled={ocupado}
                  onClick={onClose}
                >
                  Conservar
                </button>
                <button
                  type="button"
                  className={`button button-${dialogo.danger !== false ? 'danger' : 'primary'}`}
                  disabled={ocupado}
                  data-busy={String(ocupado)}
                  onClick={manejarConfirmacion}
                >
                  {dialogo.verb}
                </button>
              </div>
            </>
          )}

          {dialogo.type === 'history' && (
            <>
              {errorHistorial ? (
                <div className="alert" role="alert">
                  No se pudo leer el historial. Cerrá el diálogo y volvé a intentarlo.
                </div>
              ) : !historial ? (
                <div className="table-message" role="status">
                  Cargando historial…
                </div>
              ) : (
                <ol className="history-list">
                  {historial.map(ev => (
                    <li key={ev.id}>
                      <span className="history-point" aria-hidden="true"></span>
                      <div>
                        <Badge status={ev.estado} />
                        <span className="history-time">{dateTimeText(ev.fecha)}</span>
                        <p>{ev.detalle || 'Sin observaciones'}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
              <div className="dialog-actions">
                <button type="button" className="button button-outline" onClick={onClose}>
                  Cerrar
                </button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
