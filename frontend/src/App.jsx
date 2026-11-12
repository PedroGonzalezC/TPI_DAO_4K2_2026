/**
 * Componente raíz <App /> de la aplicación React.
 * Administra el estado global de la biblioteca, la navegación por vistas,
 * las notificaciones (toast) y la apertura de diálogos modales.
 */

function obtenerVistaInicial() {
  const v = new URLSearchParams(window.location.search).get('vista') || 'inicio';
  return VIEWS[v] ? v : 'inicio';
}

function App() {
  const [rol, setRol] = useState(null);
  const [vista, setVista] = useState(obtenerVistaInicial);
  const [estado, setEstado] = useState(null);
  const [errorCarga, setErrorCarga] = useState('');
  const [dialogo, setDialogo] = useState(null);
  const [toast, setToast] = useState(null);

  const esAdmin = rol === 'ADMIN';

  const loadControllerRef = useRef(null);
  const toastTimerRef = useRef(null);

  const fechaHoy = new Intl.DateTimeFormat('es-AR', {
    weekday: 'short',
    day: '2-digit',
    month: 'long',
  }).format(new Date());

  useEffect(() => {
    document.title = `Red de Bibliotecas · ${VIEWS[vista]}`;
  }, [vista]);

  useEffect(() => {
    function onPopState() {
      setVista(obtenerVistaInicial());
    }
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  async function refresh() {
    loadControllerRef.current?.abort();
    const controller = new AbortController();
    loadControllerRef.current = controller;

    try {
      const datos = await cargarEstadoBiblioteca(controller);
      if (loadControllerRef.current !== controller) return;
      setEstado(datos);
      setErrorCarga('');
    } catch (error) {
      if (loadControllerRef.current !== controller) return;
      setErrorCarga(
        error.name === 'AbortError'
          ? 'La carga tardó demasiado. Podés volver a intentarlo.'
          : 'No se pudo cargar la biblioteca. Comprobá que el servidor siga abierto.'
      );
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function salirDeSesion() {
    setRol(null);
    setDialogo(null);
  }

  function navegar(nuevaVista) {
    const url = new URL(window.location.href);
    url.searchParams.set('vista', nuevaVista);
    window.history.pushState({}, '', url);
    setVista(nuevaVista);
  }

  function notificar(mensaje, tono = 'success') {
    clearTimeout(toastTimerRef.current);
    setToast({ mensaje, tono });
    toastTimerRef.current = setTimeout(() => setToast(null), 4800);
  }

  const tablas = estado?.tablas || {};
  function rows(table) {
    return tablas[table] || [];
  }
  function byId(table, id) {
    return rows(table).find(r => r.id === Number(id));
  }
  function nameOf(table, id, key = 'nombre') {
    return byId(table, id)?.[key] || `#${id}`;
  }
  function bookOfCopy(id) {
    const copy = byId('ejemplares', id);
    return copy ? nameOf('libros', copy.libro_id, 'titulo') : `Ejemplar #${id}`;
  }
  function options(tableName, labelFn, filterFn = () => true) {
    return rows(tableName)
      .filter(filterFn)
      .map(r => ({ value: r.id, label: labelFn(r) }));
  }

  async function ejecutarAccionServidor(payload, successMessage) {
    const response = await mutate(payload);
    setDialogo(null);
    const msg =
      typeof successMessage === 'function'
        ? successMessage(response.resultado)
        : successMessage;
    notificar(msg);
    await refresh();
  }

  function dispatchAction(action, id) {
    if (action.startsWith('go-')) return navegar(action.slice(3));
    if (action === 'reload') return refresh();

    const branch = byId('sedes', id);
    const member = byId('socios', id);
    const book = byId('libros', id);
    const loan = byId('prestamos', id);
    const slip = byId('remitos', id);
    const reservation = byId('reservas', id);
    const copy = byId('ejemplares', id);
    const fine = byId('multas', id);

    const activeBranches = options('sedes', r => r.nombre, r => r.activa);
    const members = options('socios', r => `${r.nombre} · ${r.documento}`, r => r.habilitado);
    const books = options('libros', r => `${r.titulo} · ${r.isbn}`);
    const copyOptions = options(
      'ejemplares',
      r =>
        `${r.codigo} · ${nameOf('libros', r.libro_id, 'titulo')} · ${
          LABELS[r.estado] || r.estado
        } · ${LABELS[r.condicion || 'BUENO'] || r.condicion || 'Bueno'}`,
      r => ['DISPONIBLE', 'RESERVADO'].includes(r.estado)
    );

    if (action === 'branch-new') {
      return setDialogo({
        type: 'form',
        title: 'Agregar sede',
        description: 'Completá los datos de atención de la nueva sede.',
        action: 'crear_sede',
        submit: 'Agregar sede',
        success: 'Sede agregada.',
        fields: [
          { name: 'nombre', label: 'Nombre', required: true },
          { name: 'direccion', label: 'Dirección', required: true },
          { name: 'contacto', label: 'Contacto', required: true },
          { name: 'horarios', label: 'Horarios', required: true },
        ],
      });
    }
    if (action === 'branch-edit' && branch) {
      return setDialogo({
        type: 'form',
        title: 'Editar sede',
        description: branch.nombre,
        action: 'editar_sede',
        extra: { id: branch.id },
        submit: 'Guardar cambios',
        success: 'Sede actualizada.',
        fields: [
          { name: 'direccion', label: 'Dirección', value: branch.direccion, required: true },
          { name: 'contacto', label: 'Contacto', value: branch.contacto, required: true },
          { name: 'horarios', label: 'Horarios', value: branch.horarios, required: true },
        ],
      });
    }
    if (action === 'branch-toggle' && branch) {
      return setDialogo({
        type: 'confirm',
        title: branch.activa ? 'Dar de baja la sede' : 'Reactivar la sede',
        description: branch.activa
          ? 'No se podrán iniciar préstamos, reservas ni envíos desde o hacia esta sede.'
          : 'La sede podrá volver a participar en operaciones nuevas.',
        object: `Sede: ${branch.nombre}`,
        verb: branch.activa ? 'Dar de baja' : 'Reactivar',
        action: 'editar_sede',
        payload: { id: branch.id, activa: !branch.activa },
        success: branch.activa ? 'Sede dada de baja.' : 'Sede reactivada.',
        danger: !!branch.activa,
      });
    }

    if (action === 'member-new') {
      return setDialogo({
        type: 'form',
        title: 'Agregar socio',
        description: 'El documento identifica al socio y no puede repetirse.',
        action: 'crear_socio',
        submit: 'Agregar socio',
        success: 'Socio agregado.',
        fields: [
          { name: 'documento', label: 'Documento', required: true },
          { name: 'nombre', label: 'Nombre completo', required: true },
          { name: 'email', label: 'Correo electrónico', type: 'email', required: true },
        ],
      });
    }
    if (action === 'member-edit' && member) {
      return setDialogo({
        type: 'form',
        title: 'Editar socio',
        description: `Documento ${member.documento}`,
        action: 'editar_socio',
        extra: { id: member.id },
        submit: 'Guardar cambios',
        success: 'Socio actualizado.',
        fields: [
          { name: 'nombre', label: 'Nombre completo', value: member.nombre, required: true },
          { name: 'email', label: 'Correo electrónico', type: 'email', value: member.email, required: true },
        ],
      });
    }
    if (action === 'member-toggle' && member) {
      return setDialogo({
        type: 'confirm',
        title: member.habilitado ? 'Inhabilitar socio' : 'Habilitar socio',
        description: member.habilitado
          ? 'El socio no podrá iniciar reservas ni recibir préstamos nuevos.'
          : 'El socio podrá volver a operar.',
        object: `${member.nombre} · Documento ${member.documento}`,
        verb: member.habilitado ? 'Inhabilitar' : 'Habilitar',
        action: 'editar_socio',
        payload: { id: member.id, habilitado: !member.habilitado },
        success: member.habilitado ? 'Socio inhabilitado.' : 'Socio habilitado.',
        danger: !!member.habilitado,
      });
    }

    if (action === 'book-new') {
      return setDialogo({
        type: 'form',
        title: 'Agregar libro',
        description: 'El ISBN identifica una ficha única del catálogo.',
        action: 'crear_libro',
        submit: 'Agregar libro',
        success: 'Libro agregado.',
        fields: [
          { name: 'isbn', label: 'ISBN', required: true },
          { name: 'titulo', label: 'Título', required: true },
          { name: 'autor', label: 'Autor', required: true },
          { name: 'anio', label: 'Año', type: 'number', min: 1 },
        ],
      });
    }
    if (action === 'book-edit' && book) {
      return setDialogo({
        type: 'form',
        title: 'Editar libro',
        description: `ISBN ${book.isbn}`,
        action: 'editar_libro',
        extra: { id: book.id },
        submit: 'Guardar cambios',
        success: 'Libro actualizado.',
        fields: [
          { name: 'titulo', label: 'Título', value: book.titulo, required: true },
          { name: 'autor', label: 'Autor', value: book.autor, required: true },
          { name: 'anio', label: 'Año', type: 'number', min: 1, value: book.anio },
        ],
      });
    }
    if (action === 'book-delete' && book) {
      return setDialogo({
        type: 'confirm',
        title: 'Eliminar libro del catálogo',
        description: 'Se eliminará la ficha bibliográfica porque no tiene ejemplares asociados.',
        object: `${book.titulo} · ISBN ${book.isbn}`,
        verb: 'Eliminar libro',
        action: 'eliminar_libro',
        payload: { id: book.id },
        success: 'Libro eliminado del catálogo.',
      });
    }

    if (action === 'copy-new') {
      return setDialogo({
        type: 'form',
        title: 'Agregar ejemplar',
        description: 'Cada copia física necesita un código único y una sede de pertenencia.',
        action: 'crear_ejemplar',
        submit: 'Agregar ejemplar',
        success: 'Ejemplar agregado.',
        fields: [
          { name: 'codigo', label: 'Código de ejemplar', required: true },
          { name: 'libro_id', label: 'Libro', options: books, required: true },
          { name: 'sede_id', label: 'Sede de pertenencia', options: activeBranches, required: true },
          {
            name: 'condicion',
            label: 'Estado físico del ejemplar',
            value: 'BUENO',
            options: ['BUENO', 'DANADO'].map(x => ({ value: x, label: LABELS[x] })),
            required: true,
          },
        ],
      });
    }
    if (action === 'copy-fit' && copy) {
      return setDialogo({
        type: 'confirm',
        title: 'Habilitar ejemplar',
        description: 'La revisión física terminó y el ejemplar podrá volver a circular.',
        object: `${copy.codigo} · ${bookOfCopy(copy.id)}`,
        verb: 'Marcar apto',
        action: 'cerrar_revision',
        payload: { ejemplar_id: copy.id, apto: true },
        success: 'Ejemplar disponible.',
        danger: false,
      });
    }
    if (action === 'copy-unfit' && copy) {
      return setDialogo({
        type: 'confirm',
        title: 'Dar de baja ejemplar',
        description: 'El ejemplar dejará de estar disponible para préstamos.',
        object: `${copy.codigo} · ${bookOfCopy(copy.id)}`,
        verb: 'Dar de baja',
        action: 'cerrar_revision',
        payload: { ejemplar_id: copy.id, apto: false },
        success: 'Ejemplar dado de baja.',
      });
    }
    if (action === 'copy-delete' && copy) {
      return setDialogo({
        type: 'confirm',
        title: 'Dar de baja o eliminar ejemplar',
        description:
          'Si tiene historial de préstamos quedará dado de baja; si no tiene movimientos se eliminará físicamente.',
        object: `${copy.codigo} · ${bookOfCopy(copy.id)}`,
        verb: 'Confirmar baja',
        action: 'eliminar_ejemplar',
        payload: { id: copy.id },
        success: res => (res === 'eliminado' ? 'Ejemplar eliminado.' : 'Ejemplar dado de baja.'),
      });
    }

    if (action === 'reserve-new') {
      return setDialogo({
        type: 'form',
        title: 'Crear reserva',
        description: 'Se asignará el primer ejemplar disponible de este libro en la sede elegida.',
        action: 'reservar',
        submit: 'Crear reserva',
        success: 'Reserva creada.',
        fields: [
          { name: 'socio_id', label: 'Socio', options: members, required: true },
          { name: 'libro_id', label: 'Libro', options: books, required: true },
          { name: 'sede_id', label: 'Sede de retiro', options: activeBranches, required: true },
        ],
      });
    }
    if (action === 'reserve-cancel' && reservation) {
      return setDialogo({
        type: 'confirm',
        title: 'Cancelar reserva',
        description:
          'Si tenía un ejemplar asignado, se ofrecerá a la siguiente persona de la cola.',
        object: `${nameOf('libros', reservation.libro_id, 'titulo')} · ${nameOf(
          'socios',
          reservation.socio_id
        )}`,
        verb: 'Cancelar reserva',
        action: 'cancelar_reserva',
        payload: { id: reservation.id },
        success: 'Reserva cancelada.',
      });
    }
    if (action === 'reserve-loan' && reservation) {
      const assignedCopy = byId('ejemplares', reservation.ejemplar_id);
      return setDialogo({
        type: 'form',
        title: 'Solicitar préstamo desde reserva',
        description: `Reserva #${reservation.id} · ${nameOf(
          'libros',
          reservation.libro_id,
          'titulo'
        )}`,
        action: 'solicitar_prestamo',
        submit: 'Solicitar préstamo',
        success: result =>
          `Préstamo P-${String(result).padStart(3, '0')} solicitado y reserva cumplida.`,
        fields: [
          {
            name: 'socio_id',
            label: 'Socio',
            options: members,
            value: reservation.socio_id,
            required: true,
          },
          {
            name: 'ejemplar_id',
            label: 'Ejemplar',
            value: reservation.ejemplar_id,
            options: copyOptions,
            required: true,
          },
          {
            name: 'sede_origen_id',
            label: 'Sede de origen',
            options: activeBranches,
            value: assignedCopy ? assignedCopy.sede_pertenencia_id : reservation.sede_id,
            required: true,
            help: 'Debe ser la sede de pertenencia del ejemplar.',
          },
          {
            name: 'sede_destino_id',
            label: 'Sede de retiro',
            options: activeBranches,
            value: reservation.sede_id,
            required: true,
          },
          {
            name: 'plazo_dias',
            label: 'Duración del préstamo (días)',
            type: 'number',
            min: 1,
            value: 14,
            required: true,
            help: 'Cantidad de días corridos desde la entrega.',
          },
        ],
      });
    }

    if (action === 'loan-new') {
      return setDialogo({
        type: 'form',
        title: 'Solicitar préstamo',
        description:
          'Seleccioná el ejemplar y las sedes. Si son distintas, se genera un remito de ida.',
        action: 'solicitar_prestamo',
        submit: 'Solicitar préstamo',
        success: result => `Préstamo P-${String(result).padStart(3, '0')} solicitado.`,
        fields: [
          { name: 'socio_id', label: 'Socio', options: members, required: true },
          { name: 'ejemplar_id', label: 'Ejemplar', options: copyOptions, required: true },
          {
            name: 'sede_origen_id',
            label: 'Sede de origen',
            options: activeBranches,
            required: true,
            help: 'Debe ser la sede de pertenencia del ejemplar.',
          },
          {
            name: 'sede_destino_id',
            label: 'Sede de retiro',
            options: activeBranches,
            required: true,
          },
          {
            name: 'plazo_dias',
            label: 'Duración del préstamo (días)',
            type: 'number',
            min: 1,
            value: 14,
            required: true,
            help: 'Cantidad de días corridos desde la entrega.',
          },
        ],
      });
    }
    if (action === 'loan-deliver' && loan) {
      return setDialogo({
        type: 'confirm',
        title: 'Entregar préstamo',
        description: `La fecha de vencimiento se calculará a ${
          loan.plazo_dias || 14
        } días desde la entrega.`,
        object: `${bookOfCopy(loan.ejemplar_id)} · ${nameOf('socios', loan.socio_id)}`,
        verb: 'Entregar',
        action: 'entregar_prestamo',
        payload: { id: loan.id },
        success: result => `Préstamo entregado. Vence el ${dateText(result.vence_en)}.`,
        danger: false,
      });
    }
    if (action === 'loan-cancel' && loan) {
      return setDialogo({
        type: 'confirm',
        title: 'Cancelar solicitud de préstamo',
        description:
          'El préstamo quedará cancelado antes de su entrega y el ejemplar volverá a estar disponible.',
        object: `P-${String(loan.id).padStart(3, '0')} · ${bookOfCopy(loan.ejemplar_id)} · ${nameOf(
          'socios',
          loan.socio_id
        )}`,
        verb: 'Cancelar solicitud',
        action: 'cancelar_prestamo',
        payload: { id: loan.id },
        success: 'Solicitud de préstamo cancelada.',
      });
    }
    if (action === 'loan-return' && loan) {
      return setDialogo({
        type: 'form',
        title: 'Registrar devolución',
        description: `${bookOfCopy(loan.ejemplar_id)} · ${nameOf(
          'socios',
          loan.socio_id
        )}. Indicá el estado físico del material.`,
        action: 'devolver_prestamo',
        extra: { id: loan.id },
        submit: 'Registrar devolución',
        success: result =>
          result.multa_centavos > 0
            ? `Devolución registrada. Multa pendiente: ${money(
                result.multa_centavos
              )} (socio inhabilitado hasta abonarla).`
            : 'Devolución registrada sin multa.',
        fields: [
          {
            name: 'condicion',
            label: 'Condición del ejemplar',
            required: true,
            value: 'BUENO',
            options: ['BUENO', 'DANADO', 'DESTRUIDO', 'EXTRAVIADO'].map(x => ({
              value: x,
              label: LABELS[x],
            })),
            help: 'Dañado requiere revisión. Destruido o extraviado da de baja el ejemplar.',
          },
        ],
      });
    }

    if (action === 'remito-next' && slip) {
      const next = {
        CREADO: 'EMPAQUETADO',
        EMPAQUETADO: 'DESPACHADO',
        DESPACHADO: 'RECIBIDO',
      }[slip.estado];
      if (!next) return;
      const verbo = {
        EMPAQUETADO: 'Empaquetar',
        DESPACHADO: 'Despachar',
        RECIBIDO: 'Recibir',
      }[next];
      return setDialogo({
        type: 'form',
        title: `${verbo} remito`,
        description: `R-${String(slip.id).padStart(3, '0')} · ${nameOf(
          'sedes',
          slip.origen_id
        )} → ${nameOf('sedes', slip.destino_id)}`,
        action: 'avanzar_remito',
        extra: { id: slip.id, estado: next },
        submit: `${verbo} remito`,
        success: `Remito ${LABELS[next].toLowerCase()}.`,
        fields: [
          {
            name: 'detalle',
            label: 'Detalle del movimiento',
            type: 'textarea',
            help: 'Opcional. Ejemplo: caja sellada o recepción sin observaciones.',
          },
        ],
      });
    }
    if (action === 'remito-history' && slip) {
      return setDialogo({
        type: 'history',
        eyebrow: 'TRAZABILIDAD',
        title: `Historial R-${String(slip.id).padStart(3, '0')}`,
        description: `${nameOf('sedes', slip.origen_id)} → ${nameOf('sedes', slip.destino_id)}`,
        historyId: slip.id,
      });
    }

    if (action === 'multa-pay' && fine) {
      return setDialogo({
        type: 'confirm',
        title: 'Registrar pago de multa',
        description:
          'Al abonar la multa pendiente, el socio volverá a quedar habilitado para solicitar préstamos.',
        object: `${fine.socio_nombre} · ${fine.libro_titulo} · ${money(fine.monto_centavos)}`,
        verb: 'Registrar pago',
        action: 'pagar_multa',
        payload: { id: fine.id },
        success: 'Multa pagada. El socio quedó habilitado nuevamente.',
        danger: false,
      });
    }
  }

  function renderizarVistaActiva() {
    if (!estado) {
      return (
        <>
          <PageHeader
            kicker="SISTEMA LOCAL"
            title="Red de Bibliotecas"
            subtitle="Cargando datos de la biblioteca…"
          />
          <div className="table-message" role="status">
            {errorCarga ? 'Comprobá el servidor y volvé a cargar.' : 'Cargando registros…'}
          </div>
        </>
      );
    }

    if (!esAdmin) {
      return <DashboardUsuario tablas={estado.tablas} nameOf={nameOf} />;
    }

    const propsComunes = {
      tablas: estado.tablas,
      reportes: estado.reportes,
      nameOf,
      bookOfCopy,
      onAction: dispatchAction,
    };

    switch (vista) {
      case 'inicio':
        return <VistaInicio {...propsComunes} />;
      case 'prestamos':
        return <VistaPrestamos {...propsComunes} />;
      case 'remitos':
        return <VistaRemitos {...propsComunes} />;
      case 'catalogo':
        return <VistaCatalogo {...propsComunes} />;
      case 'reservas':
        return <VistaReservas {...propsComunes} />;
      case 'socios':
        return <VistaSocios {...propsComunes} />;
      case 'sedes':
        return <VistaSedes {...propsComunes} />;
      case 'multas':
        return <VistaMultas {...propsComunes} />;
      case 'reportes':
        return <VistaReportes {...propsComunes} />;
      default:
        return <VistaInicio {...propsComunes} />;
    }
  }

  if (!rol) {
    return <VistaLogin onSeleccionarRol={nuevoRol => setRol(nuevoRol)} />;
  }

  const itemsNavegacion = esAdmin
    ? NAV_ITEMS
    : [{ key: 'catalogo', label: 'Catálogo disponible', symbol: '▤' }];

  return (
    <>
      <div className="app-shell" id="app-shell">
        <aside className="sidebar" aria-label="Navegación principal">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">
              <i></i>
              <i></i>
              <i></i>
            </span>
            <div>
              <strong>
                Red de
                <br />
                Bibliotecas
              </strong>
              <small>Sistema de circulación</small>
            </div>
          </div>

          <nav className="navigation" id="navigation" aria-label="Áreas del sistema">
            {itemsNavegacion.map(item => (
              <a
                key={item.key}
                href={`?vista=${item.key}`}
                data-view={item.key}
                aria-current={!esAdmin || vista === item.key ? 'page' : undefined}
                onClick={e => {
                  e.preventDefault();
                  if (esAdmin) navegar(item.key);
                }}
              >
                <span className="nav-symbol">{item.symbol}</span> {item.label}
              </a>
            ))}
          </nav>

          <div className="sidebar-foot">
            <span className="connection-dot"></span>
            <span>
              Servidor local
              <br />
              <small>Datos guardados en SQLite</small>
            </span>
          </div>
        </aside>

        <div className="workspace">
          <header className="topbar">
            <span className="topbar-kicker">DAO · Trabajo práctico integrador · Grupo N°34</span>
            <div className="topbar-right">
              <span className="topbar-base" id="base-label" aria-label="Rol activo">
                {esAdmin ? 'Panel Administrador' : 'Vista Usuario'}
              </span>
              <span className="topbar-date" id="today">
                {fechaHoy}
              </span>
              <button
                type="button"
                className="button button-outline button-small"
                onClick={salirDeSesion}
              >
                Cerrar sesión
              </button>
            </div>
          </header>

          <main id="main" tabIndex="-1" aria-live="off">
            <ErrorBanner mensaje={errorCarga} onRecargar={refresh} />
            {renderizarVistaActiva()}
          </main>

          <footer className="footer">
            Red de Bibliotecas <span>·</span> Tema 1 <span>·</span> UTN FRC 2026
          </footer>
        </div>
      </div>

      <div
        id="toast"
        className="toast"
        role="status"
        aria-live="polite"
        hidden={!toast}
        data-tone={toast?.tono || 'success'}
      >
        {toast?.mensaje || ''}
      </div>

      <ModalDialogo
        dialogo={dialogo}
        ejemplares={rows('ejemplares')}
        onClose={() => setDialogo(null)}
        onSubmitAction={ejecutarAccionServidor}
      />
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
