const form = document.querySelector('#login');
const error = document.querySelector('#error');
document.querySelector('#mostrar-clave').addEventListener('click', event => {
  const visible = form.elements.clave.type === 'password';
  form.elements.clave.type = visible ? 'text' : 'password';
  event.currentTarget.textContent = visible ? 'Ocultar contraseña' : 'Mostrar contraseña';
  event.currentTarget.setAttribute('aria-pressed', String(visible));
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const usuario = form.elements.usuario.value.trim();
  const clave = form.elements.clave.value;
  if (!usuario || !clave) {
    error.textContent = 'Completá el usuario y la contraseña.';
    error.hidden = false;
    (usuario ? form.elements.clave : form.elements.usuario).focus();
    return;
  }
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const response = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ usuario, clave }) });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || data.error || 'No se pudo iniciar sesión.');
    }
    location.href = '/';
  } catch (exc) {
    error.textContent = exc.message;
    error.hidden = false;
    button.disabled = false;
  }
});
