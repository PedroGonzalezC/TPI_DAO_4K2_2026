// Alta y edición comparten campos; soloAlta indica los datos que no se modifican.
export const DATOS_MAESTROS = {
  branch: {
    table: 'sedes',
    create: { title: 'Agregar sede', description: 'Completá los datos de atención de la nueva sede.', action: 'crear_sede', success: 'Sede agregada.' },
    edit: { title: 'Editar sede', description: r => r.nombre, action: 'editar_sede', success: 'Sede actualizada.' },
    fields: [
      { name: 'nombre', label: 'Nombre', required: true, soloAlta: true },
      { name: 'direccion', label: 'Dirección', required: true },
      { name: 'contacto', label: 'Contacto', required: true },
      { name: 'horarios', label: 'Horarios', required: true },
    ],
  },
  member: {
    table: 'socios',
    create: { title: 'Agregar socio', description: 'El documento identifica al socio y no puede repetirse.', action: 'crear_socio', success: 'Socio agregado.' },
    edit: { title: 'Editar socio', description: r => `Documento ${r.documento}`, action: 'editar_socio', success: 'Socio actualizado.' },
    fields: [
      { name: 'documento', label: 'Documento', required: true, soloAlta: true },
      { name: 'nombre', label: 'Nombre completo', required: true },
      { name: 'email', label: 'Correo electrónico', type: 'email', required: true },
    ],
  },
  book: {
    table: 'libros',
    create: { title: 'Agregar libro', description: 'El ISBN identifica una ficha única del catálogo.', action: 'crear_libro', success: 'Libro agregado.' },
    edit: { title: 'Editar libro', description: r => `ISBN ${r.isbn}`, action: 'editar_libro', success: 'Libro actualizado.' },
    fields: [
      { name: 'isbn', label: 'ISBN', required: true, soloAlta: true },
      { name: 'titulo', label: 'Título', required: true },
      { name: 'autor', label: 'Autor', required: true },
      { name: 'anio', label: 'Año', type: 'number', min: 1 },
    ],
  },
};

export function errorCampo(field, value) {
  if (field.required && !String(value ?? '').trim()) return `Completá ${field.label.toLowerCase()}.`;
  if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Ingresá un correo válido.';
  if (field.type === 'number' && value && (!Number.isInteger(Number(value)) || Number(value) < (field.min ?? 0))) return 'Ingresá un número válido.';
  return '';
}
