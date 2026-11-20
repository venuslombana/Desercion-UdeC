/* Cliente web del CRUD de seguimiento de la deserción (JavaScript sin dependencias, salvo Chart.js para las gráficas).
 * Seguridad: el token JWT se guarda en sessionStorage y viaja en la cabecera Authorization (no en cookies), por lo que el
 * navegador no lo envía solo y no hay superficie de CSRF. Todo texto que viene del servidor se inserta con textContent,
 * nunca con innerHTML, para evitar XSS. La política CSP del servidor bloquea scripts externos o en línea. */
"use strict";

// ------------------------------------------------------------------ utilidades
const $ = (sel) => document.querySelector(sel);
function el(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, "");
    else e.setAttribute(k, v);
  }
  for (const h of hijos.flat()) if (h !== null && h !== undefined && h !== false) e.append(h instanceof Node ? h : document.createTextNode(String(h)));
  return e;
}
const fmt = (v, dec = 1) => (v === null || v === undefined || v === "" ? "—" : typeof v === "number" ? v.toLocaleString("es-CO", { maximumFractionDigits: dec }) : String(v));
const pct = (v, dec = 1) => (v === null || v === undefined ? "—" : (100 * v).toLocaleString("es-CO", { maximumFractionDigits: dec }) + " %");

function aviso(texto, tipo = "") {
  const a = el("div", { class: "aviso " + (tipo ? "aviso-" + tipo : ""), role: tipo === "error" ? "alert" : "status" }, texto);
  $("#avisos").append(a);
  setTimeout(() => a.remove(), tipo === "ambar" ? 9000 : 5000);
}

// ------------------------------------------------------------------ sesión y API
const sesion = {
  get token() { return sessionStorage.getItem("token"); },
  get usuario() { try { return JSON.parse(sessionStorage.getItem("usuario")); } catch { return null; } },
  guardar(token, usuario) { sessionStorage.setItem("token", token); sessionStorage.setItem("usuario", JSON.stringify(usuario)); },
  cerrar() { sessionStorage.clear(); },
};
const rol = () => sesion.usuario?.rol;
const puede = (roles) => roles.includes(rol());

class ErrorApi extends Error { constructor(status, detalle) { super(typeof detalle === "string" ? detalle : "Revise los datos del formulario"); this.status = status; this.detalle = detalle; } }

async function api(ruta, { metodo = "GET", cuerpo, form, crudo = false } = {}) {
  const h = {};
  if (sesion.token) h.Authorization = "Bearer " + sesion.token;
  let body;
  if (form) body = form;
  else if (cuerpo !== undefined) { h["Content-Type"] = "application/json"; body = JSON.stringify(cuerpo); }
  const r = await fetch(ruta, { method: metodo, headers: h, body });
  if (r.status === 401 && sesion.token) { sesion.cerrar(); mostrarLogin("Su sesión venció. Ingrese de nuevo."); throw new ErrorApi(401, "Sesión vencida"); }
  if (!r.ok) {
    let d = r.statusText; try { d = (await r.json()).detail; } catch { /* sin cuerpo */ }
    throw new ErrorApi(r.status, d);
  }
  const av = r.headers.get("X-Aviso");
  if (crudo) return r;
  const datos = r.status === 204 ? null : await r.json();
  if (av && datos) datos._aviso = datos.aviso || av;
  return datos;
}

async function descargar(ruta, nombre) {
  try {
    const r = await api(ruta, { crudo: true });
    const url = URL.createObjectURL(await r.blob());
    const a = el("a", { href: url, download: nombre }); document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  } catch (e) { aviso(e.message, "error"); }
}

// ------------------------------------------------------------------ catálogos para listas desplegables y etiquetas
const cat = { periodos: [], cohortes: [], programas: [], factores: [], "tipos-apoyo": [], roles: [] };
async function cargarCatalogos() {
  const pedir = async (n, ruta) => { try { const r = await api(ruta); cat[n] = r.items ?? r; } catch { cat[n] = []; } };
  await Promise.all([pedir("periodos", "/api/periodos?size=100&sort=codigo"), pedir("cohortes", "/api/cohortes?size=100"),
    pedir("programas", "/api/programas?size=100"), pedir("factores", "/api/factores?size=100"), pedir("tipos-apoyo", "/api/tipos-apoyo?size=100")]);
  if (rol() === "administrador") cat.roles = await api("/api/roles");
}
const nombrePeriodo = (id) => cat.periodos.find((p) => p.id === id)?.codigo ?? id;
const ETIQUETA = {
  periodos: (p) => p.codigo, programas: (p) => `${p.nombre} (${p.sede})`, factores: (f) => `${f.nombre} · ${f.tipo}`,
  "tipos-apoyo": (t) => `${t.nombre} · ${t.palanca}`, roles: (r) => r.nombre, cohortes: (c) => `Cohorte ${nombrePeriodo(c.periodo_ingreso_id)}`,
};
const etiquetaRef = (ref, id) => { const o = cat[ref]?.find((x) => x.id === id); return o ? ETIQUETA[ref](o) : id; };

// ------------------------------------------------------------------ definición de entidades
// tipo: text | number | select | bool | password | textarea ; ref: catálogo para selects ; opciones: lista fija
const A = "administrador", O = "operador", C = "consulta";
const ENT = {
  estudiantes: { titulo: "Estudiantes", desc: "Estudiantes del programa identificados solo con un código anónimo (Ley 1581 de 2012).", ruta: "/api/estudiantes",
    escribir: [A, O], borrar: [A], buscar: "Código anónimo",
    filtros: [{ k: "cohorte_id", ref: "cohortes", l: "Cohorte" }, { k: "estrato", opciones: [1, 2, 3, 4, 5, 6], l: "Estrato" }, { k: "trabaja", opciones: ["true", "false"], l: "Trabaja" }],
    campos: [
      { k: "codigo_anonimo", l: "Código anónimo", tipo: "text", req: true, min: 6, max: 16, patron: "[A-Za-z0-9]+", ayuda: "6 a 16 letras o números, sin datos personales" },
      { k: "cohorte_id", l: "Cohorte", tipo: "select", ref: "cohortes", req: true },
      { k: "estrato", l: "Estrato", tipo: "number", req: true, min: 1, max: 6 },
      { k: "puntaje_saber11", l: "Puntaje Saber 11", tipo: "number", req: true, min: 0, max: 500 },
      { k: "trabaja", l: "Trabaja", tipo: "bool" }] },
  matriculas: { titulo: "Matrículas", desc: "Un registro por estudiante y periodo. Es la entidad transaccional que alimenta la simulación.", ruta: "/api/matriculas",
    escribir: [A, O], borrar: [A],
    filtros: [{ k: "periodo_id", ref: "periodos", l: "Periodo" }, { k: "nivel_semestre", opciones: [...Array(14).keys()].map((i) => i + 1), l: "Semestre" },
      { k: "resultado", opciones: ["CONTINUA", "DESERTA", "GRADUA"], l: "Resultado" }, { k: "estudiante_id", l: "Id estudiante", tipo: "number" }],
    campos: [
      { k: "estudiante_id", l: "Id del estudiante", tipo: "number", req: true, min: 1 },
      { k: "periodo_id", l: "Periodo", tipo: "select", ref: "periodos", req: true },
      { k: "nivel_semestre", l: "Semestre que cursa", tipo: "number", req: true, min: 1, max: 14 },
      { k: "promedio", l: "Promedio", tipo: "number", req: true, min: 0, max: 5, paso: "0.01" },
      { k: "creditos_inscritos", l: "Créditos inscritos", tipo: "number", req: true, min: 0, max: 30 },
      { k: "materias_basicas_perdidas", l: "Materias básicas perdidas", tipo: "number", min: 0, max: 10, defecto: 0 },
      { k: "resultado", l: "Resultado al cierre", tipo: "select", opciones: ["CONTINUA", "DESERTA", "GRADUA"], req: true }] },
  alertas: { titulo: "Alertas tempranas", desc: "Casos de riesgo que pasan a la cola de Bienestar. Desde la versión 1.0 se registran en todos los semestres (ruta de permanencia integral).", ruta: "/api/alertas",
    escribir: [A, O], borrar: [A], buscar: "Motivo",
    filtros: [{ k: "nivel", opciones: ["bajo", "medio", "alto"], l: "Nivel" }, { k: "atendida", opciones: ["true", "false"], l: "Atendida" }, { k: "matricula_id", l: "Id matrícula", tipo: "number" }],
    campos: [
      { k: "matricula_id", l: "Id de la matrícula", tipo: "number", req: true, min: 1, ayuda: "Matrícula del periodo en que se detecta el riesgo" },
      { k: "nivel", l: "Nivel de riesgo", tipo: "select", opciones: ["bajo", "medio", "alto"], req: true },
      { k: "motivo", l: "Motivo", tipo: "textarea", req: true, min: 3, max: 500 },
      { k: "atendida", l: "Atendida", tipo: "bool" }] },
  apoyos: { titulo: "Apoyos asignados", desc: "Relación muchos a muchos entre estudiantes y tipos de apoyo de Bienestar.", ruta: "/api/apoyos",
    escribir: [A, O], borrar: [A, O],
    filtros: [{ k: "tipo_apoyo_id", ref: "tipos-apoyo", l: "Tipo de apoyo" }, { k: "periodo_id", ref: "periodos", l: "Periodo" },
      { k: "estado", opciones: ["asignado", "en_curso", "finalizado"], l: "Estado" }, { k: "estudiante_id", l: "Id estudiante", tipo: "number" }],
    campos: [
      { k: "estudiante_id", l: "Id del estudiante", tipo: "number", req: true, min: 1 },
      { k: "tipo_apoyo_id", l: "Tipo de apoyo", tipo: "select", ref: "tipos-apoyo", req: true },
      { k: "periodo_id", l: "Periodo", tipo: "select", ref: "periodos", req: true },
      { k: "estado", l: "Estado", tipo: "select", opciones: ["asignado", "en_curso", "finalizado"], req: true, defecto: "asignado" }] },
  "estudiante-factores": { titulo: "Factores por estudiante", desc: "Relación muchos a muchos estudiante–factor de riesgo por periodo (llave compuesta).", ruta: "/api/estudiante-factores",
    compuesta: ["estudiante_id", "factor_id", "periodo_id"], escribir: [A, O], borrar: [A], editables: ["intensidad"],
    orden: ["estudiante_id", "factor_id", "periodo_id", "intensidad"],
    filtros: [{ k: "factor_id", ref: "factores", l: "Factor" }, { k: "periodo_id", ref: "periodos", l: "Periodo" }, { k: "intensidad", opciones: [1, 2, 3], l: "Intensidad" }, { k: "estudiante_id", l: "Id estudiante", tipo: "number" }],
    campos: [
      { k: "estudiante_id", l: "Id del estudiante", tipo: "number", req: true, min: 1 },
      { k: "factor_id", l: "Factor de riesgo", tipo: "select", ref: "factores", req: true },
      { k: "periodo_id", l: "Periodo", tipo: "select", ref: "periodos", req: true },
      { k: "intensidad", l: "Intensidad (1 baja, 3 alta)", tipo: "number", req: true, min: 1, max: 3 }] },
  cohortes: { titulo: "Cohortes", desc: "Grupo de estudiantes que ingresa en un mismo periodo.", ruta: "/api/cohortes", escribir: [A], borrar: [A],
    filtros: [{ k: "periodo_ingreso_id", ref: "periodos", l: "Periodo de ingreso" }],
    campos: [{ k: "programa_id", l: "Programa", tipo: "select", ref: "programas", req: true }, { k: "periodo_ingreso_id", l: "Periodo de ingreso", tipo: "select", ref: "periodos", req: true }] },
  periodos: { titulo: "Periodos académicos", ruta: "/api/periodos", escribir: [A], borrar: [A], buscar: "Código",
    filtros: [{ k: "semestre", opciones: [1, 2], l: "Semestre" }],
    campos: [{ k: "codigo", l: "Código", tipo: "text", req: true, patron: "\\d{4}-[12]", ayuda: "Formato AAAA-S, por ejemplo 2026-1" },
      { k: "anio", l: "Año", tipo: "number", req: true, min: 1990, max: 2100 }, { k: "semestre", l: "Semestre", tipo: "number", req: true, min: 1, max: 2 }] },
  programas: { titulo: "Programas", ruta: "/api/programas", escribir: [A], borrar: [A], buscar: "Nombre o sede",
    campos: [{ k: "nombre", l: "Nombre", tipo: "text", req: true, min: 3, max: 120 }, { k: "sede", l: "Sede", tipo: "text", req: true, min: 3, max: 60 },
      { k: "semestres_plan", l: "Semestres del plan", tipo: "number", req: true, min: 1, max: 14, defecto: 9 }] },
  factores: { titulo: "Factores de riesgo", ruta: "/api/factores", escribir: [A], borrar: [A], buscar: "Nombre",
    filtros: [{ k: "tipo", opciones: ["economico", "academico", "adaptacion"], l: "Tipo" }],
    campos: [{ k: "tipo", l: "Tipo", tipo: "select", opciones: ["economico", "academico", "adaptacion"], req: true }, { k: "nombre", l: "Nombre", tipo: "text", req: true, min: 3, max: 80 }] },
  "tipos-apoyo": { titulo: "Tipos de apoyo", desc: "Rutas de Bienestar con sus cupos por periodo.", ruta: "/api/tipos-apoyo", escribir: [A], borrar: [A], buscar: "Nombre",
    filtros: [{ k: "palanca", opciones: ["economico", "academico", "adaptacion"], l: "Palanca" }],
    campos: [{ k: "nombre", l: "Nombre", tipo: "text", req: true, min: 3, max: 80 }, { k: "palanca", l: "Palanca", tipo: "select", opciones: ["economico", "academico", "adaptacion"], req: true },
      { k: "cupos_por_periodo", l: "Cupos por periodo", tipo: "number", req: true, min: 0, max: 1000 }] },
  usuarios: { titulo: "Usuarios", ruta: "/api/usuarios", escribir: [A], borrar: [A], buscar: "Nombre o correo", ocultar: ["password"],
    filtros: [{ k: "rol_id", ref: "roles", l: "Rol" }, { k: "activo", opciones: ["true", "false"], l: "Activo" }],
    campos: [{ k: "nombre", l: "Nombre", tipo: "text", req: true, min: 3, max: 80 }, { k: "email", l: "Correo", tipo: "email", req: true, max: 120 },
      { k: "password", l: "Contraseña", tipo: "password", min: 8, max: 100, ayuda: "Mínimo 8 caracteres. Al editar, déjela vacía para conservar la actual." },
      { k: "rol_id", l: "Rol", tipo: "select", ref: "roles", req: true }, { k: "activo", l: "Activo", tipo: "bool", defecto: true }] },
  auditoria: { titulo: "Auditoría", desc: "Quién creó, modificó o eliminó cada registro y cuándo. Solo lectura.", ruta: "/api/auditoria", escribir: [], borrar: [], buscar: "Entidad o detalle",
    filtros: [{ k: "accion", opciones: ["CREAR", "ACTUALIZAR", "ELIMINAR"], l: "Acción" }, { k: "entidad", l: "Entidad", tipo: "text" }, { k: "usuario_id", l: "Id usuario", tipo: "number" }],
    orden: ["id", "fecha", "usuario_id", "entidad", "registro_id", "accion", "detalle"], campos: [] },
};
const OCULTAS = ["creado_en", "actualizado_en", "eliminado_en"];

// ------------------------------------------------------------------ navegación
const VISTAS = [
  { grupo: "Seguimiento", items: [["tablero", "Tablero real vs. simulado", [A, O, C]], ["cola", "Cola de Bienestar", [A, O, C]], ["reportes", "Reportes y exportación", [A, O, C]]] },
  { grupo: "Registro", items: [["estudiantes", "Estudiantes", [A, O, C]], ["matriculas", "Matrículas", [A, O, C]], ["alertas", "Alertas tempranas", [A, O, C]],
    ["apoyos", "Apoyos asignados", [A, O, C]], ["estudiante-factores", "Factores por estudiante", [A, O, C]]] },
  { grupo: "Catálogos", items: [["cohortes", "Cohortes", [A, O, C]], ["periodos", "Periodos", [A, O, C]], ["programas", "Programas", [A, O, C]],
    ["factores", "Factores de riesgo", [A, O, C]], ["tipos-apoyo", "Tipos de apoyo", [A, O, C]]] },
  { grupo: "Administración", items: [["parametros", "Parámetros y proyecciones", [A, O, C]], ["usuarios", "Usuarios", [A]], ["auditoria", "Auditoría", [A]]] },
];

function pintarMenu() {
  const nav = $("#menu"); nav.replaceChildren();
  for (const g of VISTAS) {
    const items = g.items.filter(([, , r]) => puede(r));
    if (!items.length) continue;
    nav.append(el("h3", {}, g.grupo));
    for (const [id, t] of items) nav.append(el("a", { href: "#" + id, "data-vista": id }, t));
  }
}

async function router() {
  const id = (location.hash || "#tablero").slice(1);
  const permitido = VISTAS.flatMap((g) => g.items).find(([v]) => v === id);
  document.querySelectorAll("#menu a").forEach((a) => { if (a.dataset.vista === id) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  $("#menu").classList.remove("abierto"); $("#btn-menu").setAttribute("aria-expanded", "false");
  const main = $("#contenido"); main.replaceChildren(el("p", { class: "sub" }, "Cargando…"));
  graficas.forEach((g) => g.destroy()); graficas = [];
  try {
    if (!permitido || !puede(permitido[2])) { main.replaceChildren(el("div", { class: "nota nota-rojo" }, "Su rol no tiene acceso a esta sección.")); return; }
    if (id === "tablero") await vistaTablero(main);
    else if (id === "cola") await vistaCola(main);
    else if (id === "reportes") await vistaReportes(main);
    else if (id === "parametros") await vistaParametros(main);
    else await vistaListado(main, id);
  } catch (e) { if (e.status !== 401) main.replaceChildren(el("div", { class: "nota nota-rojo", role: "alert" }, "No se pudo cargar la sección: " + e.message)); }
  main.focus({ preventScroll: true });
}

// ------------------------------------------------------------------ listado genérico (búsqueda, filtros, orden y paginación en el servidor)
async function vistaListado(main, id) {
  const cfg = ENT[id];
  const estado = { page: 1, size: 20, sort: cfg.compuesta ? "estudiante_id" : "id", order: cfg.compuesta ? "asc" : "desc", q: "", f: {} };
  const tabla = el("div", { class: "tabla-env" }), pag = el("div", { class: "paginacion" });
  const herr = el("form", { class: "barra-herr", role: "search", onsubmit: (e) => { e.preventDefault(); estado.page = 1; cargar(); } });
  if (cfg.buscar) {
    const inp = el("input", { type: "search", id: "q", placeholder: cfg.buscar, maxlength: 80, oninput: (e) => (estado.q = e.target.value) });
    herr.append(el("div", { class: "campo" }, el("label", { for: "q" }, "Buscar"), inp));
  }
  for (const f of cfg.filtros || []) {
    const fid = "f-" + f.k; let ctl;
    if (f.ref || f.opciones) {
      ctl = el("select", { id: fid, onchange: (e) => { estado.f[f.k] = e.target.value; estado.page = 1; cargar(); } }, el("option", { value: "" }, "Todos"));
      for (const o of f.ref ? cat[f.ref] : f.opciones) ctl.append(el("option", { value: f.ref ? o.id : o }, f.ref ? ETIQUETA[f.ref](o) : String(o)));
    } else ctl = el("input", { id: fid, type: f.tipo || "text", min: f.tipo === "number" ? 1 : null, onchange: (e) => { estado.f[f.k] = e.target.value; estado.page = 1; cargar(); } });
    herr.append(el("div", { class: "campo" }, el("label", { for: fid }, f.l), ctl));
  }
  herr.append(el("button", { class: "btn", type: "submit" }, "Aplicar"));
  const cab = el("div", { class: "cab-vista" }, el("div", {}, el("h1", {}, cfg.titulo), cfg.desc ? el("p", {}, cfg.desc) : null));
  if (puede(cfg.escribir) && cfg.campos.length) cab.append(el("button", { class: "btn btn-primario", type: "button", onclick: () => formulario(cfg, null, cargar) }, "+ Nuevo"));
  main.replaceChildren(cab, herr, tabla, pag);

  async function cargar() {
    const p = new URLSearchParams({ page: estado.page, size: estado.size, sort: estado.sort, order: estado.order });
    if (estado.q) p.set("q", estado.q);
    for (const [k, v] of Object.entries(estado.f)) if (v !== "" && v !== undefined) p.set(k, v);
    let datos;
    try { datos = await api(cfg.ruta + "?" + p); } catch (e) { aviso(e.message, "error"); return; }
    const items = datos.items;
    let cols = cfg.orden || (items[0] ? Object.keys(items[0]).filter((c) => !OCULTAS.includes(c)) : ["id", ...cfg.campos.map((c) => c.k)]);
    cols = cols.filter((c) => !(cfg.ocultar || []).includes(c));
    const campo = (k) => cfg.campos.find((c) => c.k === k);
    const th = cols.map((c) => {
      const flecha = estado.sort === c ? (estado.order === "asc" ? " ▲" : " ▼") : "";
      return el("th", { scope: "col", "aria-sort": estado.sort === c ? (estado.order === "asc" ? "ascending" : "descending") : null },
        el("button", { type: "button", onclick: () => { estado.order = estado.sort === c && estado.order === "asc" ? "desc" : "asc"; estado.sort = c; cargar(); } }, (campo(c)?.l || c) + flecha));
    });
    const acciones = puede(cfg.escribir) || puede(cfg.borrar);
    if (acciones) th.push(el("th", { scope: "col" }, "Acciones"));
    const filas = items.map((it) => {
      const tds = cols.map((c) => {
        const cf = campo(c); let v = it[c];
        if (cf?.ref && v !== null) v = etiquetaRef(cf.ref, v);
        else if (c === "periodo_id" || c === "periodo_ingreso_id") v = nombrePeriodo(v);
        else if (typeof v === "boolean") v = v ? "Sí" : "No";
        else if (c === "fecha" && v) v = new Date(v + "Z").toLocaleString("es-CO");
        const crudo = c === "id" || c.endsWith("_id") || c === "anio";
        return el("td", { class: typeof it[c] === "number" && !cf?.ref ? "num" : "" }, crudo && typeof v === "number" ? String(v) : fmt(v, 2));
      });
      if (acciones) {
        const td = el("td", { class: "acciones" });
        if (puede(cfg.escribir) && cfg.campos.length) td.append(el("button", { class: "btn btn-chico", type: "button", onclick: () => formulario(cfg, it, cargar) }, "Editar"));
        if (puede(cfg.borrar)) td.append(el("button", { class: "btn btn-chico btn-peligro", type: "button", onclick: () => confirmarBorrado(cfg, it, cargar) }, "Eliminar"));
        tds.push(td);
      }
      return el("tr", {}, tds);
    });
    tabla.replaceChildren(items.length ? el("table", {}, el("caption", { class: "saltar" }, cfg.titulo), el("thead", {}, el("tr", {}, th)), el("tbody", {}, filas))
      : el("p", { class: "vacio" }, "No hay registros que coincidan con la búsqueda."));
    const paginas = Math.max(1, Math.ceil(datos.total / estado.size));
    const tam = el("select", { "aria-label": "Registros por página", onchange: (e) => { estado.size = +e.target.value; estado.page = 1; cargar(); } },
      [10, 20, 50, 100].map((n) => el("option", { value: n, selected: n === estado.size }, `${n} por página`)));
    pag.replaceChildren(el("span", {}, `${datos.total.toLocaleString("es-CO")} registros · página ${estado.page} de ${paginas}`),
      el("div", { class: "acciones" }, tam,
        el("button", { class: "btn btn-chico", type: "button", disabled: estado.page <= 1, onclick: () => { estado.page--; cargar(); } }, "← Anterior"),
        el("button", { class: "btn btn-chico", type: "button", disabled: estado.page >= paginas, onclick: () => { estado.page++; cargar(); } }, "Siguiente →")));
  }
  await cargar();
}

// ------------------------------------------------------------------ formularios con validación en el cliente
function abrirModal(titulo, ...contenido) {
  $("#modal-titulo").textContent = titulo; $("#modal-cuerpo").replaceChildren(...contenido); $("#modal").hidden = false;
  const primero = $("#modal-cuerpo").querySelector("input,select,textarea,button"); if (primero) primero.focus();
}
function cerrarModal() { $("#modal").hidden = true; $("#modal-cuerpo").replaceChildren(); }

function mensajeValidacion(inp, c) {
  const v = inp.validity;
  if (v.valueMissing) return `${c.l} es obligatorio.`;
  if (v.typeMismatch) return `${c.l} no tiene un formato válido.`;
  if (v.patternMismatch) return c.ayuda ? `${c.l}: ${c.ayuda}.` : `${c.l} no tiene el formato esperado.`;
  if (v.tooShort) return `${c.l} debe tener al menos ${c.min} caracteres.`;
  if (v.tooLong) return `${c.l} admite máximo ${c.max} caracteres.`;
  if (v.rangeUnderflow) return `${c.l} debe ser mayor o igual que ${c.min}.`;
  if (v.rangeOverflow) return `${c.l} debe ser menor o igual que ${c.max}.`;
  if (v.stepMismatch || v.badInput) return `${c.l} debe ser un número válido.`;
  return "";
}

function formulario(cfg, item, alGuardar) {
  const editando = !!item;
  const campos = cfg.campos.filter((c) => !editando || !cfg.editables || cfg.editables.includes(c.k));
  const form = el("form", { novalidate: true });
  const ctl = {};
  for (const c of campos) {
    const id = "c-" + c.k, val = editando ? item[c.k] : c.defecto;
    let inp;
    if (c.tipo === "select") {
      inp = el("select", { id, name: c.k, required: c.req }, el("option", { value: "" }, "Seleccione…"));
      for (const o of c.ref ? cat[c.ref] : c.opciones) {
        const v = c.ref ? o.id : o;
        inp.append(el("option", { value: v, selected: val !== undefined && String(val) === String(v) }, c.ref ? ETIQUETA[c.ref](o) : String(o)));
      }
    } else if (c.tipo === "bool") inp = el("input", { id, name: c.k, type: "checkbox", checked: !!val });
    else if (c.tipo === "textarea") { inp = el("textarea", { id, name: c.k, required: c.req, minlength: c.min, maxlength: c.max, rows: 3 }); inp.value = val ?? ""; }
    else {
      const num = c.tipo === "number";
      inp = el("input", { id, name: c.k, type: c.tipo, required: c.req || (c.tipo === "password" && !editando), step: num ? c.paso || "1" : null,
        min: num ? c.min : null, max: num ? c.max : null, minlength: !num ? c.min : null, maxlength: !num ? c.max : null, pattern: c.patron,
        autocomplete: c.tipo === "password" ? "new-password" : "off" });
      if (c.tipo !== "password") inp.value = val ?? "";
    }
    const err = el("p", { class: "error-campo", id: "e-" + c.k });
    inp.setAttribute("aria-describedby", "e-" + c.k);
    inp.addEventListener("blur", () => { inp.classList.add("tocado"); err.textContent = mensajeValidacion(inp, c); });
    inp.addEventListener("input", () => { inp.classList.remove("con-error"); if (inp.classList.contains("tocado")) err.textContent = mensajeValidacion(inp, c); });
    ctl[c.k] = { inp, err, c };
    form.append(...[c.tipo === "bool" ? el("label", { for: id }, inp, c.l) : el("label", { for: id }, c.l + (c.req ? " *" : "")), c.tipo === "bool" ? null : inp,
      c.ayuda ? el("p", { class: "ayuda-campo" }, c.ayuda) : null, err].filter(Boolean));
  }
  const errForm = el("p", { class: "error-form", role: "alert" });
  form.append(errForm, el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
    el("button", { class: "btn btn-primario", type: "submit" }, editando ? "Guardar cambios" : "Crear")));
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); errForm.textContent = "";
    let ok = true;
    for (const { inp, err, c } of Object.values(ctl)) { inp.classList.add("tocado"); err.textContent = mensajeValidacion(inp, c); if (err.textContent) ok = false; }
    if (!ok) { errForm.textContent = "Corrija los campos marcados."; form.querySelector(":invalid")?.focus(); return; }
    const datos = {};
    for (const { inp, c } of Object.values(ctl)) {
      if (c.tipo === "bool") datos[c.k] = inp.checked;
      else if (c.tipo === "password") { if (inp.value) datos[c.k] = inp.value; }
      else if (inp.value === "") { if (!c.req && editando) datos[c.k] = null; }
      else datos[c.k] = c.tipo === "number" || c.ref ? Number(inp.value) : inp.value;
    }
    try {
      let ruta = cfg.ruta, metodo = "POST";
      if (editando) { metodo = "PUT"; ruta += "/" + (cfg.compuesta ? cfg.compuesta.map((k) => item[k]).join("/") : item.id); }
      const r = await api(ruta, { metodo, cuerpo: datos });
      cerrarModal(); aviso(editando ? "Cambios guardados." : "Registro creado.", "ok");
      if (r && r.palanca_sugerida) aviso(`Apoyo sugerido para el caso: ${r.apoyo_sugerido} (palanca ${r.palanca_sugerida}). Prioridad ${r.prioridad}.`);
      if (r && r._aviso) aviso("Capacidad de Bienestar: " + r._aviso, "ambar");
      alGuardar();
    } catch (er) {
      if (Array.isArray(er.detalle)) {
        for (const d of er.detalle) {
          const k = (d.campo || (d.loc || []).slice(-1)[0] || "").split(".").slice(-1)[0];
          if (ctl[k]) { ctl[k].err.textContent = d.mensaje || d.msg; ctl[k].inp.classList.add("con-error"); }
        }
        errForm.textContent = "El servidor rechazó algunos datos. Revise los campos marcados.";
      } else errForm.textContent = er.message;
    }
  });
  abrirModal((editando ? "Editar · " : "Nuevo · ") + cfg.titulo.toLowerCase(), form);
}

function confirmarBorrado(cfg, item, alBorrar) {
  const ident = cfg.compuesta ? cfg.compuesta.map((k) => item[k]).join("/") : item.id;
  abrirModal("Confirmar eliminación",
    el("p", {}, `¿Eliminar el registro ${ident} de ${cfg.titulo.toLowerCase()}?`),
    el("p", { class: "sub" }, cfg.compuesta ? "La relación se borra; la auditoría conserva el registro." : "La eliminación es lógica: el registro deja de aparecer pero queda en la base y en la auditoría."),
    el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
      el("button", { class: "btn btn-peligro", type: "button", onclick: async () => {
        try { await api(cfg.ruta + "/" + ident, { metodo: "DELETE" }); cerrarModal(); aviso("Registro eliminado.", "ok"); alBorrar(); }
        catch (e) { cerrarModal(); aviso(e.message, "error"); }
      } }, "Eliminar")));
}

// ------------------------------------------------------------------ tablero real frente a simulado
let graficas = [];
function grafica(canvas, config) { if (!window.Chart) return; graficas.push(new Chart(canvas, config)); }

function tarjetaCapacidad(cap, periodo) {
  const etiqueta = { verde: "Dentro de la capacidad", ambar: "Cerca del límite", rojo: "Capacidad superada" }[cap.semaforo];
  return el("section", { class: "tarjeta" }, el("h3", {}, `Capacidad de Bienestar · periodo en curso ${periodo || ""}`),
    el("div", { class: "semaforo" }, el("span", { class: "luz luz-" + cap.semaforo, role: "img", "aria-label": "Semáforo " + cap.semaforo }),
      el("div", {}, el("div", { class: "valor" }, `${cap.casos} / ${fmt(cap.capacidad)}`), el("div", {}, el("span", { class: "chip " + { verde: "chip-ok", ambar: "chip-ambar", rojo: "chip-mal" }[cap.semaforo] }, etiqueta)))),
    el("p", { class: "sub" }, cap.mensaje));
}

async function vistaTablero(main, escenario = "E0 Base") {
  const t = await api("/api/tablero?escenario=" + encodeURIComponent(escenario));
  const sel = el("select", { id: "sel-esc", onchange: (e) => { graficas.forEach((g) => g.destroy()); graficas = []; vistaTablero(main, e.target.value); } },
    t.escenarios.map((e) => el("option", { value: e, selected: e === t.escenario }, e)));
  const tarjetas = t.tarjetas.map((x) => {
    const esPct = x.clave === "desercion_periodo";
    const chip = x.dentro_margen === null ? el("span", { class: "chip chip-gris" }, "Sin proyección")
      : x.dentro_margen ? el("span", { class: "chip chip-ok" }, "Modelo dentro del margen") : el("span", { class: "chip chip-mal" }, "Fuera del margen: recalibrar");
    return el("section", { class: "tarjeta" }, el("h3", {}, `${x.indicador} · ${x.periodo}`),
      el("div", { class: "valor" }, esPct ? pct(x.real, 2) : fmt(x.real)),
      el("p", { class: "sub" }, `Simulado: ${esPct ? pct(x.simulado, 2) : fmt(x.simulado)} · desviación ${x.desviacion === null ? "—" : pct(x.desviacion)}`), chip);
  });
  const c1 = el("canvas", { "aria-label": "Deserción por periodo real y simulada", role: "img" });
  const c2 = el("canvas", { "aria-label": "Matriculados reales y simulados", role: "img" });
  main.replaceChildren(
    el("div", { class: "cab-vista" }, el("div", {}, el("h1", {}, "Tablero: indicadores reales frente a la simulación"),
      el("p", {}, "Compara lo registrado en el CRUD con lo que proyecta el modelo de simulación para el escenario elegido. Las políticas de E1 y E3 arrancan en 2026-1.")),
      el("div", {}, el("label", { for: "sel-esc" }, "Escenario de la simulación"), sel)),
    el("div", { class: "rejilla" }, tarjetaCapacidad(t.capacidad, t.periodo_en_curso), ...tarjetas),
    el("div", { class: "dos-col" },
      el("section", { class: "tarjeta" }, el("h2", {}, "Deserción por periodo (%)"), el("div", { class: "grafica" }, c1)),
      el("section", { class: "tarjeta" }, el("h2", {}, "Matriculados"), el("div", { class: "grafica" }, c2))),
    el("p", { class: "nota" }, `Tolerancia: si la desviación supera ${pct(t.tolerancia, 0)} en algún indicador, el modelo debe recalibrarse con los datos nuevos (scripts de simulacion/). Datos sintéticos de desarrollo.`));
  const labels = t.serie.map((s) => s.periodo);
  const serie = (fuente, k, mult = 1) => t.serie.map((s) => (s[fuente] ? +(s[fuente][k] * mult).toFixed(2) : null));
  const opc = { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false }, plugins: { legend: { position: "bottom" } }, scales: { x: { ticks: { maxTicksLimit: 12 } } } };
  grafica(c1, { type: "line", data: { labels, datasets: [
    { label: "Real (CRUD)", data: serie("real", "desercion_periodo", 100), borderColor: "#b42318", backgroundColor: "#b42318", pointRadius: 2, spanGaps: false },
    { label: "Simulado · " + t.escenario, data: serie("simulado", "desercion_periodo", 100), borderColor: "#1f4e79", borderDash: [6, 4], pointRadius: 0 }] }, options: opc });
  grafica(c2, { type: "line", data: { labels, datasets: [
    { label: "Real (CRUD)", data: serie("real", "matriculados"), borderColor: "#b42318", backgroundColor: "#b42318", pointRadius: 2 },
    { label: "Simulado · " + t.escenario, data: serie("simulado", "matriculados"), borderColor: "#1f4e79", borderDash: [6, 4], pointRadius: 0 }] }, options: opc });
}

// ------------------------------------------------------------------ cola de Bienestar (ruta de permanencia integral)
async function vistaCola(main) {
  const q = await api("/api/bienestar/cola");
  const atiende = puede([A, O]);
  const filas = q.casos.map((c, i) => {
    const tds = [el("td", { class: "num" }, i + 1), el("td", { class: "num" }, fmt(c.prioridad)), el("td", {}, el("span", { class: "chip " + { alto: "chip-mal", medio: "chip-ambar", bajo: "chip-gris" }[c.nivel] }, c.nivel)),
      el("td", { class: "num" }, c.nivel_semestre), el("td", {}, c.etapa), el("td", { class: "num" }, c.materias_basicas_perdidas), el("td", { class: "num" }, fmt(c.promedio, 2)),
      el("td", {}, c.apoyo_sugerido || "—"), el("td", { class: "num" }, c.estudiante_id)];
    if (atiende) tds.push(el("td", {}, el("button", { class: "btn btn-chico btn-primario", type: "button", onclick: () => atender(c, () => vistaCola(main)) }, "Atender")));
    return el("tr", {}, tds);
  });
  const cab = ["#", "Prioridad", "Nivel", "Semestre", "Etapa", "Básicas perdidas", "Promedio", "Apoyo sugerido", "Id estudiante"].concat(atiende ? ["Acción"] : []);
  main.replaceChildren(
    el("div", { class: "cab-vista" }, el("div", {}, el("h1", {}, `Cola de Bienestar · ${q.periodo}`),
      el("p", {}, "Casos sin atender ordenados por una regla pública: nivel de la alerta, semestre (los primeros pesan más porque ahí la deserción es mayor) y materias básicas perdidas. La regla no usa estrato ni condición laboral."))),
    el("div", { class: "rejilla" }, tarjetaCapacidad(q.capacidad, q.periodo)),
    el("div", { class: "tabla-env" }, q.casos.length ? el("table", {}, el("thead", {}, el("tr", {}, cab.map((h) => el("th", { scope: "col" }, h)))), el("tbody", {}, filas))
      : el("p", { class: "vacio" }, "No hay casos pendientes en el periodo.")));
}

function atender(caso, alTerminar) {
  const sel = el("select", { id: "tipo-apoyo" }, cat["tipos-apoyo"].map((t) => el("option", { value: t.id, selected: t.id === caso.tipo_apoyo_sugerido_id }, ETIQUETA["tipos-apoyo"](t) + (t.id === caso.tipo_apoyo_sugerido_id ? " (sugerido)" : ""))));
  abrirModal("Atender caso",
    el("p", {}, `Alerta ${caso.alerta_id} · semestre ${caso.nivel_semestre} (${caso.etapa}) · nivel ${caso.nivel}.`), el("p", { class: "sub" }, caso.motivo),
    el("label", { for: "tipo-apoyo" }, "Apoyo que se asigna"), sel,
    el("p", { class: "ayuda-campo" }, "La sugerencia sale de los pesos por etapa del modelo de simulación y de los factores de riesgo del estudiante."),
    el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
      el("button", { class: "btn btn-primario", type: "button", onclick: async () => {
        try { await api(`/api/bienestar/cola/${caso.alerta_id}/atender?tipo_apoyo_id=${sel.value}`, { metodo: "POST" }); cerrarModal(); aviso("Caso atendido y apoyo asignado.", "ok"); alTerminar(); }
        catch (e) { aviso(e.message, "error"); }
      } }, "Asignar apoyo")));
}

// ------------------------------------------------------------------ reportes y exportación
async function vistaReportes(main, rid) {
  const lista = await api("/api/reportes");
  rid = rid || lista[0].id;
  const rep = await api("/api/reportes/" + rid);
  const sel = el("select", { id: "sel-rep", onchange: (e) => { graficas.forEach((g) => g.destroy()); graficas = []; vistaReportes(main, e.target.value); } },
    lista.map((r) => el("option", { value: r.id, selected: r.id === rid }, r.titulo)));
  const lienzo = el("canvas", { role: "img", "aria-label": "Gráfica del reporte" });
  main.replaceChildren(
    el("div", { class: "cab-vista" }, el("div", {}, el("h1", {}, "Reportes y exportación"), el("p", {}, "Indicadores calculados con los datos del CRUD. Cada reporte se descarga en CSV o PDF.")),
      el("div", {}, el("label", { for: "sel-rep" }, "Reporte"), sel)),
    el("section", { class: "tarjeta" }, el("h2", {}, rep.titulo), el("p", { class: "sub" }, rep.descripcion),
      el("ul", { class: "indicadores" }, rep.indicadores.map((i) => el("li", { class: "tarjeta" }, el("h3", {}, i.nombre), el("div", { class: "valor" }, fmt(i.valor, 2), " ", el("small", {}, i.unidad)), i.detalle ? el("div", { class: "sub" }, i.detalle) : null))),
      el("div", { class: "barra-herr" },
        el("button", { class: "btn", type: "button", onclick: () => descargar(`/api/reportes/${rid}?formato=csv`, `reporte_${rid}.csv`) }, "Descargar CSV"),
        el("button", { class: "btn", type: "button", onclick: () => descargar(`/api/reportes/${rid}?formato=pdf`, `reporte_${rid}.pdf`) }, "Descargar PDF")),
      el("div", { class: "grafica" }, lienzo)),
    el("div", { class: "tabla-env" }, el("table", {}, el("thead", {}, el("tr", {}, rep.columnas.map((c) => el("th", { scope: "col" }, c)))),
      el("tbody", {}, rep.filas.map((f) => el("tr", {}, f.map((v) => el("td", { class: typeof v === "number" ? "num" : "" }, fmt(v, 2)))))))),
    el("section", { class: "tarjeta" }, el("h2", {}, "Exportación de históricos para la simulación"),
      el("p", { class: "sub" }, "Las cinco series con las que se ajustan las distribuciones del modelo (excluye el periodo en curso). Son idénticas a las de simulacion/datos."),
      el("div", { class: "barra-herr" }, el("button", { class: "btn btn-primario", type: "button", onclick: () => descargar("/api/exportacion/historicos", "historicos_crud.zip") }, "Descargar las 5 series (ZIP)"),
        ...["ingresos_por_cohorte", "matriculas_por_periodo", "matriculas_por_nivel", "desercion_sem1_por_cohorte", "alertas_y_apoyos_por_periodo"].map((n) =>
          el("button", { class: "btn btn-chico", type: "button", onclick: () => descargar("/api/exportacion/historicos/" + n, n + ".csv") }, n + ".csv")))));
  const iy = rep.columnas.length - 1;
  grafica(lienzo, { type: rid === "desercion-nivel" ? "bar" : "line", data: { labels: rep.filas.map((f) => String(f[0])), datasets: [
    { label: rep.columnas[iy], data: rep.filas.map((f) => (typeof f[iy] === "number" ? f[iy] : null)), borderColor: "#0b5d3b", backgroundColor: "rgba(11,93,59,.55)" },
    ...(rid === "desercion-nivel" ? [{ label: rep.columnas[4], data: rep.filas.map((f) => f[4]), backgroundColor: "rgba(180,35,24,.55)" }] : [])] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } } });
}

// ------------------------------------------------------------------ parámetros y carga de proyecciones
async function vistaParametros(main) {
  const params = await api("/api/parametros");
  const esAdmin = rol() === A;
  const filas = params.map((p) => {
    const inp = el("input", { type: "number", step: "0.01", min: 0, max: 1000, value: p.valor, disabled: !esAdmin, "aria-label": p.clave, required: true });
    return el("tr", {}, el("td", {}, el("code", {}, p.clave)), el("td", {}, p.descripcion), el("td", {}, inp),
      el("td", {}, esAdmin ? el("button", { class: "btn btn-chico", type: "button", onclick: async () => {
        if (!inp.checkValidity()) { aviso("Ingrese un valor entre 0 y 1000.", "error"); return; }
        try { await api(`/api/parametros/${p.clave}?valor=${inp.value}`, { metodo: "PUT" }); aviso("Parámetro actualizado.", "ok"); } catch (e) { aviso(e.message, "error"); }
      } }, "Guardar") : null));
  });
  const archivo = el("input", { type: "file", id: "archivo-proy", accept: ".csv,text/csv" });
  main.replaceChildren(
    el("div", { class: "cab-vista" }, el("div", {}, el("h1", {}, "Parámetros y proyecciones"), el("p", {}, "Valores de operación que vienen de la simulación. La capacidad de Bienestar del escenario recomendado (E3) es 32 casos por semestre."))),
    el("div", { class: "tabla-env" }, el("table", {}, el("thead", {}, el("tr", {}, ["Clave", "Descripción", "Valor", ""].map((h) => el("th", { scope: "col" }, h)))), el("tbody", {}, filas))),
    esAdmin ? el("section", { class: "tarjeta" }, el("h2", {}, "Cargar proyecciones de la simulación"),
      el("p", { class: "sub" }, "Archivo generado por simulacion/scripts/exportar_proyecciones.py. Columnas: escenario, periodo, matriculados, desercion_periodo, graduados, alertas, cobertura_bienestar."),
      el("label", { for: "archivo-proy" }, "Archivo CSV"), archivo,
      el("div", { class: "modal-pie" }, el("button", { class: "btn btn-primario", type: "button", onclick: async () => {
        if (!archivo.files.length) { aviso("Seleccione un archivo CSV.", "error"); return; }
        const fd = new FormData(); fd.append("archivo", archivo.files[0]);
        try { const r = await api("/api/proyecciones", { metodo: "POST", form: fd }); aviso(`Proyecciones cargadas: ${r.escenarios.join(", ")}.`, "ok"); } catch (e) { aviso(e.message, "error"); }
      } }, "Cargar"))) : el("p", { class: "nota" }, "Solo el administrador puede cambiar parámetros o cargar proyecciones."));
}

// ------------------------------------------------------------------ inicio de sesión
function mostrarLogin(msg) {
  $("#vista-app").hidden = true; $("#vista-login").hidden = false; $("#err-login").textContent = msg || "";
  $("#login-email").focus();
}
async function mostrarApp() {
  $("#vista-login").hidden = true; $("#vista-app").hidden = false;
  $("#usuario-nombre").textContent = sesion.usuario.nombre; $("#usuario-rol").textContent = sesion.usuario.rol;
  await cargarCatalogos(); pintarMenu(); router();
}

document.addEventListener("DOMContentLoaded", () => {
  $("#form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = $("#login-email"), clave = $("#login-clave");
    $("#err-login-email").textContent = email.validity.valueMissing ? "Escriba su correo." : email.validity.typeMismatch ? "El correo no tiene un formato válido." : "";
    $("#err-login-clave").textContent = clave.validity.valueMissing ? "Escriba su contraseña." : clave.validity.tooShort ? "La contraseña tiene al menos 8 caracteres." : "";
    if (!email.checkValidity() || !clave.checkValidity()) return;
    try {
      const fd = new URLSearchParams({ username: email.value.trim(), password: clave.value });
      const r = await fetch("/api/auth/login", { method: "POST", body: fd });
      const j = await r.json();
      if (!r.ok) { $("#err-login").textContent = j.detail || "No fue posible iniciar sesión."; return; }
      sesion.guardar(j.access_token, { nombre: j.nombre, rol: j.rol }); clave.value = "";
      mostrarApp();
    } catch { $("#err-login").textContent = "No hay conexión con el servidor."; }
  });
  $("#btn-salir").addEventListener("click", () => { sesion.cerrar(); location.hash = ""; mostrarLogin("Sesión cerrada."); });
  $("#btn-menu").addEventListener("click", () => { const m = $("#menu").classList.toggle("abierto"); $("#btn-menu").setAttribute("aria-expanded", String(m)); });
  $("#modal-cerrar").addEventListener("click", cerrarModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") cerrarModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#modal").hidden) cerrarModal(); });
  window.addEventListener("hashchange", () => { if (sesion.token) router(); });
  if (sesion.token) mostrarApp(); else mostrarLogin();
});
