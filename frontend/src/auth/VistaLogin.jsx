/**
 * Pantalla de selección de perfil (2 botones directos: Administrador o Usuario).
 */

function VistaLogin({ onSeleccionarRol }) {
  return (
    <div className="login-screen">
      <div className="panel panel-pad login-card">
        <div className="login-brand">
          <span className="brand-mark login-mark" aria-hidden="true">
            <i></i>
            <i></i>
            <i></i>
          </span>
          <div>
            <p className="eyebrow">SISTEMA DE CIRCULACIÓN</p>
            <h1 className="panel-title">Red de Bibliotecas</h1>
            <p className="panel-intro">
              Seleccioná cómo querés ingresar al sistema:
            </p>
          </div>
        </div>

        <div className="login-quick-actions">
          <button
            type="button"
            className="button button-primary"
            onClick={() => onSeleccionarRol('ADMIN')}
          >
            Entrar como Administrador
          </button>
          <button
            type="button"
            className="button button-outline"
            onClick={() => onSeleccionarRol('USUARIO')}
          >
            Entrar como Usuario
          </button>
        </div>
      </div>
    </div>
  );
}
