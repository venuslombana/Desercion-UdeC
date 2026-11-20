/* Permanencia UdeC · cliente web del CRUD de seguimiento de la deserción (JavaScript sin dependencias, salvo Chart.js).
 * Seguridad: el token JWT se guarda en sessionStorage y viaja en la cabecera Authorization (no en cookies), por lo que el
 * navegador no lo envía solo y no hay superficie de CSRF. Todo texto que viene del servidor se inserta con textContent,
 * nunca con innerHTML, para evitar XSS. La política CSP del servidor bloquea scripts y estilos externos o en línea.
 * Diseño: identidad visual de la Universidad de Cundinamarca, navegación con iconos, ayudas didácticas en cada pantalla,
 * recorrido guiado y vista adaptada a celulares (barra inferior y tablas convertidas en tarjetas). */
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
const almacen = { // localStorage solo para comodidades del visitante; puede fallar en modo privado
  leer(k) { try { return localStorage.getItem(k); } catch { return null; } },
  guardar(k, v) { try { localStorage.setItem(k, v); } catch { /* sin almacenamiento */ } },
};

// ------------------------------------------------------------------ iconos (trazos SVG propios, 24×24)
const ICONOS = {
  inicio: "M3 11l9-8 9 8|M5 10v10h5v-6h4v6h5V10",
  tablero: "M3 3v18h18|M7 15l4-4 3 3 5-6",
  cola: "M8 6h13|M8 12h13|M8 18h13|M3.5 6h.01|M3.5 12h.01|M3.5 18h.01",
  reportes: "M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z|M14 3v5h5|M9 17v-3|M12 17v-6|M15 17v-2",
  estudiantes: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2|M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8|M22 21v-2a4 4 0 0 0-3-3.9|M16 3.1a4 4 0 0 1 0 7.8",
  matriculas: "M9 3h6v3H9z|M9 4.5H6a1 1 0 0 0-1 1V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V5.5a1 1 0 0 0-1-1h-3|M9 13.5l2 2 4-4",
  alertas: "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9|M10.3 21a2 2 0 0 0 3.4 0",
  apoyos: "M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 12 5a5.5 5.5 0 0 0-10 3.5c0 2.3 1.5 4 3 5.5l7 7z",
  "estudiante-factores": "M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7|M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7",
  cohortes: "M12 2 2 7l10 5 10-5z|M2 17l10 5 10-5|M2 12l10 5 10-5",
  periodos: "M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z|M16 2v4|M8 2v4|M3 10h18",
  programas: "M22 10 12 5 2 10l10 5z|M6 12v5c3 3 9 3 12 0v-5",
  factores: "M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z|M12 9v4|M12 17h.01",
  "tipos-apoyo": "M20 12v9H4v-9|M2 7h20v5H2z|M12 21V7|M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z|M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z",
  parametros: "M4 21v-7|M4 10V3|M12 21v-9|M12 8V3|M20 21v-5|M20 12V3|M1 14h6|M9 8h6|M17 16h6",
  usuarios: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2|M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8|M19 8v6|M16 11h6",
  auditoria: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z|M9 12l2 2 4-4",
  usuario: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2|M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8",
  candado: "M5 11h14v10H5z|M8 11V7a4 4 0 0 1 8 0v4",
  ojo: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z|M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6",
  salir: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4|M16 17l5-5-5-5|M21 12H9",
  menu: "M3 6h18|M3 12h18|M3 18h18",
  mas: "M4 4h6v6H4z|M14 4h6v6h-6z|M4 14h6v6H4z|M14 14h6v6h-6z",
  ayuda: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20|M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3|M12 17h.01",
  info: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20|M12 16v-4|M12 8h.01",
  ruta: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20|M16.2 7.8l-2.1 6.3-6.3 2.1 2.1-6.3z",
  libro: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z|M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5",
  mas1: "M12 5v14|M5 12h14", editar: "M12 20h9|M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z", borrar: "M3 6h18|M8 6V4h8v2|M19 6l-1 14H6L5 6|M10 11v6|M14 11v6",
  descargar: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4|M7 10l5 5 5-5|M12 15V3", buscar: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16|M21 21l-4.3-4.3",
  filtro: "M22 3H2l8 9.5V19l4 2v-8.5z", check: "M20 6 9 17l-5-5", x: "M18 6 6 18|M6 6l12 12", flecha: "M5 12h14|M12 5l7 7-7 7", chevron: "M9 18l6-6-6-6",
  izq: "M15 18l-6-6 6-6", der: "M9 18l6-6-6-6", simulacion: "M21 12a9 9 0 1 1-3-6.7|M21 3v6h-6", subir: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4|M17 8l-5-5-5 5|M12 3v12",
  objetivo: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20|M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12|M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4",
  personas: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2|M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8",
  luna: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z",
  sol: "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10|M12 1v2|M12 21v2|M4.2 4.2l1.4 1.4|M18.4 18.4l1.4 1.4|M1 12h2|M21 12h2|M4.2 19.8l1.4-1.4|M18.4 5.6l1.4-1.4",
  trofeo: "M8 21h8|M12 17v4|M7 4h10v5a5 5 0 0 1-10 0z|M17 5h3v2a3 3 0 0 1-3 3|M7 5H4v2a3 3 0 0 0 3 3",
  reloj: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20|M12 6v6l4 2",
  laboratorio: "M9 3h6|M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3|M7 15h10",
  embudo: "M3 4h18l-7 9v6l-4 2v-8z",
  ficha: "M4 4h16a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z|M9 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4|M6 16a3 3 0 0 1 6 0|M14 9h4|M14 13h4",
  teclado: "M3 6h18v12H3z|M7 10h.01|M11 10h.01|M15 10h.01|M7 14h10",
};
function icono(nombre, cls = "") {
  const ns = "http://www.w3.org/2000/svg";
  const s = document.createElementNS(ns, "svg");
  s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("class", "ic " + cls); s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false");
  for (const d of (ICONOS[nombre] || ICONOS.info).split("|")) { const p = document.createElementNS(ns, "path"); p.setAttribute("d", d); s.append(p); }
  return s;
}
function pintarIconosEstaticos(raiz = document) {
  raiz.querySelectorAll("[data-icono]").forEach((n) => { if (!n.querySelector("svg")) n.prepend(icono(n.dataset.icono)); });
}

const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function aviso(texto, tipo = "") {
  const ic = { ok: "check", error: "factores", ambar: "alertas" }[tipo] || "info";
  const a = el("div", { class: "aviso " + (tipo ? "aviso-" + tipo : ""), role: tipo === "error" ? "alert" : "status" }, icono(ic), el("span", {}, texto));
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
    aviso("Descarga lista: " + nombre, "ok");
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

// Valores que se muestran como etiquetas de color (más fáciles de leer de un vistazo)
const CHIPS = {
  resultado: { CONTINUA: "chip-ok", DESERTA: "chip-mal", GRADUA: "chip-turq" },
  nivel: { alto: "chip-mal", medio: "chip-ambar", bajo: "chip-gris" },
  estado: { asignado: "chip-oro", en_curso: "chip-turq", finalizado: "chip-ok" },
  accion: { CREAR: "chip-ok", ACTUALIZAR: "chip-oro", ELIMINAR: "chip-mal" },
  tipo: { economico: "chip-oro", academico: "chip-turq", adaptacion: "chip-ok" },
  palanca: { economico: "chip-oro", academico: "chip-turq", adaptacion: "chip-ok" },
};
const TEXTO_CHIP = { CONTINUA: "Continúa", DESERTA: "Deserta", GRADUA: "Se gradúa", en_curso: "En curso", economico: "Económico", academico: "Académico", adaptacion: "Adaptación",
  CREAR: "Creó", ACTUALIZAR: "Modificó", ELIMINAR: "Eliminó" };

// ------------------------------------------------------------------ ayudas didácticas de cada pantalla
const AYUDA = {
  tablero: { que: "Pone lado a lado lo que pasó de verdad (los datos registrados en este sistema) y lo que predijo el modelo de simulación para el escenario elegido.",
    pasos: ["Elige un escenario arriba a la derecha (E0 es la situación actual; E3 es la política recomendada).", "Mira las tarjetas: si dicen «dentro del margen», el modelo está prediciendo bien.", "Si alguna dice «recalibrar», la diferencia pasó del 15 % y hay que volver a ajustar el modelo con los datos nuevos."] },
  cola: { que: "Es la lista de estudiantes con una alerta sin atender. Está ordenada por prioridad para que Bienestar empiece por quien más lo necesita.",
    pasos: ["Revisa el semáforo: indica si Bienestar todavía tiene capacidad este semestre.", "Empieza por el primer caso de la lista (mayor prioridad).", "Pulsa «Atender», confirma el apoyo sugerido y listo: el caso sale de la cola."] },
  laboratorio: { que: "Aquí se ve qué pasaría con la deserción si la universidad aplica cada política. Los números salen del modelo de simulación en Vensim (dinámica de sistemas) y se comparan con lo que pasó de verdad.",
    pasos: ["Prende o apaga escenarios con los botones de colores para comparar sus curvas.", "Mueve la «máquina del tiempo» para ver cada semestre de 2026 a 2030.", "Mira las tarjetas: el trofeo marca el escenario con menos deserción y cuántos estudiantes más se quedan frente a no hacer nada (E0).", "Abajo, el embudo muestra de cada 100 estudiantes que entran, cuántos siguen en cada semestre."] },
  reportes: { que: "Indicadores calculados automáticamente con los datos registrados. Todos se pueden descargar.", pasos: ["Elige un reporte en la lista.", "Revisa la gráfica y la tabla.", "Descárgalo en CSV (Excel) o PDF para el informe."] },
  estudiantes: { que: "Cada estudiante aparece solo con un código anónimo: nunca se guardan nombres ni documentos (Ley 1581 de 2012).", pasos: ["Usa los filtros para ver una cohorte o un estrato.", "Pulsa «Nuevo» para registrar un estudiante.", "Toca un encabezado de columna para ordenar."] },
  matriculas: { que: "Un registro por estudiante en cada semestre: qué semestre cursa, su promedio y cómo terminó (continúa, deserta o se gradúa). Es la información que alimenta la simulación.", pasos: ["Filtra por periodo o por resultado.", "Registra una matrícula con «Nuevo».", "El resultado «Deserta» es el que cuentan los indicadores de deserción."] },
  alertas: { que: "Una alerta temprana marca a un estudiante en riesgo. Al crearla, el sistema sugiere qué apoyo darle y la envía a la cola de Bienestar.", pasos: ["Pulsa «Nuevo» e indica la matrícula, el nivel de riesgo y el motivo.", "Mira el aviso con el apoyo sugerido y la prioridad.", "Si sale un aviso naranja, Bienestar está cerca de su capacidad máxima."] },
  apoyos: { que: "Los apoyos de Bienestar que recibe cada estudiante (tutorías, apoyo económico, acompañamiento).", pasos: ["Filtra por tipo de apoyo o por estado.", "Cambia el estado a «en curso» o «finalizado» según avance."] },
  "estudiante-factores": { que: "Qué factores de riesgo tiene cada estudiante en cada periodo y con qué intensidad (1 baja, 3 alta).", pasos: ["Registra un factor con «Nuevo».", "Solo se puede editar la intensidad; para cambiar otra cosa se borra y se crea de nuevo."] },
  cohortes: { que: "Una cohorte es el grupo de estudiantes que entra en el mismo semestre. Sirve para seguirlos juntos en el tiempo.", pasos: ["Cada cohorte pertenece a un programa y a un periodo de ingreso."] },
  periodos: { que: "Los semestres académicos, en formato AAAA-S (por ejemplo, 2026-1).", pasos: ["Solo el administrador crea o modifica periodos."] },
  programas: { que: "Programas académicos que se siguen en el sistema.", pasos: ["El número de semestres del plan define cuándo se gradúa un estudiante."] },
  factores: { que: "Catálogo de factores de riesgo, agrupados en tres tipos: económico, académico y de adaptación.", pasos: ["Cada tipo se relaciona con una «palanca» de apoyo de Bienestar."] },
  "tipos-apoyo": { que: "Las rutas de apoyo de Bienestar y cuántos cupos tienen por semestre.", pasos: ["La palanca dice a qué tipo de riesgo responde cada apoyo."] },
  parametros: { que: "Valores de operación que salen del modelo de simulación, como la capacidad de Bienestar (32 casos por semestre en el escenario recomendado).", pasos: ["El administrador puede ajustarlos.", "También puede cargar las proyecciones nuevas que genera la simulación."] },
  usuarios: { que: "Quién puede entrar al sistema y con qué rol.", pasos: ["Administrador: todo. Operador: registra y atiende. Consulta: solo mira."] },
  auditoria: { que: "Registro automático de quién creó, modificó o eliminó cada dato y cuándo. No se puede editar.", pasos: ["Filtra por acción o por entidad para rastrear un cambio."] },
};
function ayudaVista(id) {
  const a = AYUDA[id]; if (!a) return null;
  const guardada = almacen.leer("ayuda-" + id);
  const abierta = guardada ? guardada === "abierta" : window.innerWidth > 860;
  const d = el("details", { class: "explica", open: abierta },
    el("summary", {}, icono("ayuda"), "¿Para qué sirve esta pantalla?", icono("chevron", "flecha")),
    el("div", { class: "explica-cuerpo" }, el("p", {}, a.que), a.pasos?.length ? el("ol", {}, a.pasos.map((p) => el("li", {}, p))) : null));
  d.addEventListener("toggle", () => almacen.guardar("ayuda-" + id, d.open ? "abierta" : "cerrada"));
  return d;
}
function cabecera(id, titulo, desc, ...acciones) {
  const ic = VISTAS.flatMap((g) => g.items).find(([v]) => v === id)?.[3] || id;
  const grupo = VISTAS.find((g) => g.items.some(([v]) => v === id))?.grupo;
  return el("div", { class: "cab-vista" },
    el("div", { class: "cab-titulo" }, el("span", { class: "cab-ic" }, icono(ic)),
      el("div", {}, grupo ? el("div", { class: "migas" }, grupo) : null, el("h1", {}, titulo), desc ? el("p", {}, desc) : null)),
    acciones.length ? el("div", { class: "cab-acciones" }, acciones) : null);
}
const esqueleto = () => el("div", {}, el("div", { class: "esqueleto", style: null }), el("div", { class: "rejilla" }, [1, 2, 3].map(() => el("div", { class: "esqueleto alto" }))), el("div", { class: "esqueleto alto" }));

// ------------------------------------------------------------------ navegación
const VISTAS = [
  { grupo: "Inicio", items: [["inicio", "Inicio", [A, O, C], "inicio"]] },
  { grupo: "Seguimiento", items: [["tablero", "Tablero real vs. simulado", [A, O, C], "tablero"], ["laboratorio", "Laboratorio de escenarios", [A, O, C], "laboratorio"], ["cola", "Cola de Bienestar", [A, O, C], "cola"], ["reportes", "Reportes y exportación", [A, O, C], "reportes"]] },
  { grupo: "Registro", items: [["estudiantes", "Estudiantes", [A, O, C], "estudiantes"], ["matriculas", "Matrículas", [A, O, C], "matriculas"], ["alertas", "Alertas tempranas", [A, O, C], "alertas"],
    ["apoyos", "Apoyos asignados", [A, O, C], "apoyos"], ["estudiante-factores", "Factores por estudiante", [A, O, C], "estudiante-factores"]] },
  { grupo: "Catálogos", items: [["cohortes", "Cohortes", [A, O, C], "cohortes"], ["periodos", "Periodos", [A, O, C], "periodos"], ["programas", "Programas", [A, O, C], "programas"],
    ["factores", "Factores de riesgo", [A, O, C], "factores"], ["tipos-apoyo", "Tipos de apoyo", [A, O, C], "tipos-apoyo"]] },
  { grupo: "Administración", items: [["parametros", "Parámetros y proyecciones", [A, O, C], "parametros"], ["usuarios", "Usuarios", [A], "usuarios"], ["auditoria", "Auditoría", [A], "auditoria"]] },
];
const NAV_MOVIL = [["inicio", "Inicio"], ["tablero", "Tablero"], ["cola", "Cola"], ["alertas", "Alertas"]];
let pendientesCola = null, abrirNuevo = null, turnoRuta = 0;

function contador() { return pendientesCola ? el("span", { class: "contador", "aria-label": pendientesCola + " casos pendientes" }, pendientesCola) : null; }
function pintarMenu() {
  const nav = $("#menu"); nav.replaceChildren();
  for (const g of VISTAS) {
    const items = g.items.filter(([, , r]) => puede(r));
    if (!items.length) continue;
    if (g.grupo !== "Inicio") nav.append(el("h3", {}, g.grupo));
    for (const [id, t, , ic] of items) nav.append(el("a", { href: "#" + id, "data-vista": id }, icono(ic), el("span", {}, t), id === "cola" ? contador() : null));
  }
  const mov = $("#nav-movil"); mov.replaceChildren();
  for (const [id, t] of NAV_MOVIL) mov.append(el("a", { href: "#" + id, "data-vista": id }, icono(id), el("span", {}, t), id === "cola" ? contador() : null));
  mov.append(el("button", { type: "button", onclick: () => alternarMenu(true), "aria-label": "Más secciones" }, icono("mas"), el("span", {}, "Más")));
}
function alternarMenu(abrir) {
  const m = $("#menu").classList.toggle("abierto", abrir);
  $("#btn-menu").setAttribute("aria-expanded", String(m)); $("#velo").hidden = !m;
}
async function actualizarPendientes() {
  try { const q = await api("/api/bienestar/cola"); pendientesCola = q.casos.length; } catch { pendientesCola = null; }
  pintarMenu(); marcarActual();
}
function marcarActual() {
  const id = (location.hash || "#inicio").slice(1);
  document.querySelectorAll("#menu a, #nav-movil a").forEach((a) => { if (a.dataset.vista === id) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
}

async function router() {
  const id = (location.hash || "#inicio").slice(1);
  const permitido = VISTAS.flatMap((g) => g.items).find(([v]) => v === id);
  marcarActual(); alternarMenu(false); if (!$("#modal").hidden) cerrarModal();
  const real = $("#contenido"), turno = ++turnoRuta; real.replaceChildren(esqueleto());
  // Si el usuario cambia de sección antes de que termine de cargar la anterior, la respuesta vieja se descarta.
  const main = { replaceChildren: (...n) => { if (turno === turnoRuta) real.replaceChildren(...n); }, querySelectorAll: (q) => real.querySelectorAll(q), focus: (o) => real.focus(o), style: real.style, get offsetWidth() { return real.offsetWidth; } };
  main.style.animation = "none"; void main.offsetWidth; main.style.animation = "";
  graficas.forEach((g) => g.destroy()); graficas = [];
  try {
    if (!permitido || !puede(permitido[2])) { main.replaceChildren(el("div", { class: "nota nota-rojo" }, icono("candado"), "Su rol no tiene acceso a esta sección.")); return; }
    if (id === "inicio") await vistaInicio(main);
    else if (id === "tablero") await vistaTablero(main);
    else if (id === "laboratorio") await vistaLaboratorio(main);
    else if (id === "cola") await vistaCola(main);
    else if (id === "reportes") await vistaReportes(main);
    else if (id === "parametros") await vistaParametros(main);
    else await vistaListado(main, id);
  } catch (e) { if (e.status !== 401) main.replaceChildren(el("div", { class: "nota nota-rojo", role: "alert" }, icono("factores"), "No se pudo cargar la sección: " + e.message)); }
  contarValores(main);
  main.focus({ preventScroll: true }); window.scrollTo({ top: 0 });
}

// ------------------------------------------------------------------ inicio: bienvenida, acciones por rol, cómo funciona y glosario
const ROL_INFO = {
  administrador: "Tienes acceso completo: catálogos, usuarios, parámetros del modelo y auditoría.",
  operador: "Puedes registrar matrículas y alertas tempranas y atender la cola de Bienestar.",
  consulta: "Puedes consultar tableros, listados y reportes. No puedes modificar datos.",
};
const ACCIONES = [
  ["alertas", "Registrar una alerta", "Marca a un estudiante en riesgo y recibe el apoyo sugerido.", [A, O], "alertas", true],
  ["cola", "Atender la cola", "Asigna apoyos a los casos en orden de prioridad.", [A, O], "cola"],
  ["tablero", "Ver el tablero", "Compara la deserción real con la simulada.", [A, O, C], "tablero"],
  ["laboratorio", "Explorar escenarios", "Compara las políticas simuladas y su efecto hasta 2030.", [A, O, C], "laboratorio"],
  ["reportes", "Descargar reportes", "Indicadores en CSV o PDF listos para el informe.", [A, O, C], "reportes"],
  ["matriculas", "Registrar una matrícula", "Agrega el resultado de un estudiante en el semestre.", [A, O], "matriculas", true],
  ["estudiantes", "Consultar estudiantes", "Busca por cohorte, estrato o condición laboral.", [C], "estudiantes"],
  ["parametros", "Ajustar el modelo", "Capacidad de Bienestar y proyecciones de la simulación.", [A], "parametros"],
  ["usuarios", "Gestionar usuarios", "Crea cuentas y asigna roles.", [A], "usuarios"],
];
const GLOSARIO = [
  ["Cohorte", "Grupo de estudiantes que ingresa en el mismo semestre; se sigue junto en el tiempo.", "cohortes"],
  ["Deserción", "Cuando un estudiante deja el programa sin graduarse. Aquí se mide por semestre.", "tablero"],
  ["Alerta temprana", "Aviso de que un estudiante tiene riesgo de desertar, para actuar antes de que pase.", "alertas"],
  ["Palanca", "Tipo de apoyo de Bienestar: económico, académico o de adaptación a la vida universitaria.", "tipos-apoyo"],
  ["Semáforo de capacidad", "Verde: hay cupo. Naranja: cerca del límite. Rojo: Bienestar superó lo que puede atender.", "cola"],
  ["Escenario", "Una política simulada (E0 actual, E1, E2, E3) para predecir su efecto sobre la deserción.", "simulacion"],
];

async function vistaInicio(main) {
  const u = sesion.usuario || {};
  const [t, q] = await Promise.all([api("/api/tablero?escenario=E0%20Base").catch(() => null), api("/api/bienestar/cola").catch(() => null)]);
  if (q) pendientesCola = q.casos.length;
  const kpis = [];
  if (t) {
    const des = t.tarjetas.find((x) => x.clave === "desercion_periodo");
    const mat = t.tarjetas.find((x) => x.clave === "matriculados");
    if (des) kpis.push(kpi("kpi-rojo", "alertas", "Deserción último periodo", pct(des.real, 1), des.periodo));
    if (mat) kpis.push(kpi("kpi-verde", "personas", "Estudiantes matriculados", fmt(mat.real, 0), mat.periodo));
  }
  if (q) kpis.push(kpi(pendientesCola ? "kpi-oro" : "kpi-verde", "cola", "Casos esperando atención", fmt(pendientesCola, 0), "Cola de Bienestar · " + q.periodo));
  if (t) kpis.push(tarjetaCapacidad(t.capacidad, t.periodo_en_curso));
  const hora = new Date().getHours(), saludo = hora < 12 ? "Buenos días" : hora < 19 ? "Buenas tardes" : "Buenas noches";
  const nombre = (u.nombre || "").split(" ")[0];
  main.replaceChildren(
    el("section", { class: "bienvenida" },
      el("span", { class: "chip" }, icono("usuario"), "Rol: " + (u.rol || "")),
      el("h1", {}, `${saludo}, `, el("span", {}, nombre || "bienvenido"), "."),
      el("p", {}, "Este sistema ayuda a detectar a tiempo a los estudiantes de Ingeniería de Sistemas y Computación en riesgo de desertar y a organizar la respuesta de Bienestar. " + (ROL_INFO[u.rol] || "")),
      el("div", { class: "bienvenida-acc" },
        el("button", { class: "btn btn-acento", type: "button", onclick: () => recorrido(0) }, icono("ruta"), "Ver recorrido guiado"),
        el("a", { class: "btn btn-sutil", href: "#tablero" }, "Ir al tablero", icono("flecha")))),
    el("div", { class: "rejilla" }, kpis),
    el("h2", { class: "seccion-titulo" }, icono("objetivo"), "¿Qué quieres hacer hoy?"),
    el("div", { class: "acciones-rapidas" }, ACCIONES.filter((a) => puede(a[3])).map(([dest, tit, desc, , ic, nuevo]) =>
      el("a", { class: "accion", href: "#" + dest, onclick: () => { abrirNuevo = nuevo ? dest : null; } },
        el("span", { class: "accion-ic" }, icono(ic)), el("b", {}, tit), el("small", {}, desc), el("span", { class: "ir" }, nuevo ? "Empezar" : "Abrir", icono("flecha"))))),
    el("h2", { class: "seccion-titulo" }, icono("simulacion"), "¿Cómo funciona?"),
    el("section", { class: "tarjeta" }, el("ol", { class: "flujo" },
      [["matriculas", "1. Registrar", "Cada semestre se cargan matrículas y resultados."], ["alertas", "2. Detectar", "Se crean alertas para quienes muestran riesgo."],
        ["apoyos", "3. Atender", "Bienestar asigna apoyos según la prioridad."], ["tablero", "4. Comparar", "Lo real se contrasta con el modelo de simulación."]]
        .map(([ic, b, s]) => el("li", {}, el("span", { class: "flujo-ic" }, icono(ic)), el("b", {}, b.slice(3)), el("small", {}, s))))),
    el("h2", { class: "seccion-titulo" }, icono("libro"), "Glosario rápido"),
    el("dl", { class: "glosario" }, GLOSARIO.map(([t2, d, ic]) => el("div", {}, el("dt", {}, icono(ic), t2), el("dd", {}, d)))));
  animarBarras(main);
  if (!almacen.leer("recorrido-visto")) { almacen.guardar("recorrido-visto", "1"); setTimeout(() => recorrido(0), 400); }
}
function kpi(cls, ic, titulo, valor, sub) {
  return el("section", { class: "tarjeta kpi " + cls }, el("div", { class: "kpi-cab" }, el("span", { class: "kpi-ic" }, icono(ic)), titulo), el("div", { class: "valor" }, valor), sub ? el("div", { class: "sub" }, sub) : null);
}
function animarBarras(raiz) { requestAnimationFrame(() => raiz.querySelectorAll(".barra-prog > span[data-ancho]").forEach((s) => { s.style.width = s.dataset.ancho + "%"; })); }

// ------------------------------------------------------------------ recorrido guiado
const PASOS_TOUR = [
  ["inicio", "Bienvenido a Permanencia UdeC", "Un sistema de alerta temprana para la deserción en Ingeniería de Sistemas y Computación, seccional Fusagasugá. Te mostramos cómo se usa en cuatro pasos."],
  ["alertas", "1. Registra y detecta", "En «Registro» se guardan las matrículas de cada semestre y las alertas tempranas. Al crear una alerta, el sistema sugiere qué apoyo darle al estudiante."],
  ["cola", "2. Atiende en orden", "La «Cola de Bienestar» ordena los casos por prioridad. El semáforo te avisa si Bienestar todavía tiene capacidad."],
  ["laboratorio", "3. Compara y simula", "El «Tablero» pone lo real junto a lo que predijo el modelo, y el «Laboratorio de escenarios» muestra qué pasaría hasta 2030 con cada política."],
  ["teclado", "4. Encuentra todo al instante", "Pulsa Ctrl + K (o la lupa) para buscar cualquier sección o un estudiante por su código y abrir su ficha completa. Cada pantalla trae además un recuadro amarillo de ayuda."],
];
function recorrido(i) {
  const [ic, tit, txt] = PASOS_TOUR[i];
  const ultimo = i === PASOS_TOUR.length - 1;
  abrirModal("Recorrido guiado", el("div", { class: "tour" }, el("div", { class: "tour-ic" }, icono(ic)), el("h3", {}, tit), el("p", {}, txt),
    el("div", { class: "puntos", "aria-label": `Paso ${i + 1} de ${PASOS_TOUR.length}` }, PASOS_TOUR.map((_, j) => el("i", { class: j === i ? "activo" : "" }))),
    el("div", { class: "modal-pie" },
      i > 0 ? el("button", { class: "btn", type: "button", onclick: () => recorrido(i - 1) }, icono("izq"), "Anterior") : el("button", { class: "btn btn-sutil", type: "button", onclick: cerrarModal }, "Saltar"),
      el("button", { class: "btn btn-primario", type: "button", onclick: () => (ultimo ? cerrarModal() : recorrido(i + 1)) }, ultimo ? "¡Empezar!" : "Siguiente", icono(ultimo ? "check" : "der")))));
}

// ------------------------------------------------------------------ listado genérico (búsqueda, filtros, orden y paginación en el servidor)
function valorCelda(c, v, cf) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return el("span", { class: "chip " + (v ? "chip-ok" : "chip-gris") }, v ? "Sí" : "No");
  if (CHIPS[c] && CHIPS[c][v]) return el("span", { class: "chip " + CHIPS[c][v] }, TEXTO_CHIP[v] || v);
  if (c === "estudiante_id") return el("button", { type: "button", class: "btn-enlace", onclick: () => fichaEstudiante(v), title: "Ver ficha del estudiante" }, icono("ficha"), String(v));
  if (cf?.ref) return String(etiquetaRef(cf.ref, v));
  if (c === "periodo_id" || c === "periodo_ingreso_id") return String(nombrePeriodo(v));
  if (c === "fecha") return new Date(v + "Z").toLocaleString("es-CO");
  const crudo = c === "id" || c.endsWith("_id") || c === "anio";
  return crudo && typeof v === "number" ? String(v) : fmt(v, 2);
}
async function vistaListado(main, id) {
  const cfg = ENT[id];
  const estado = { page: 1, size: 20, sort: cfg.compuesta ? "estudiante_id" : "id", order: cfg.compuesta ? "asc" : "desc", q: "", f: {} };
  const tabla = el("div", { class: "tabla-env apilable" }), pag = el("div", { class: "paginacion" });
  const herr = el("form", { class: "barra-herr", role: "search", onsubmit: (e) => { e.preventDefault(); estado.page = 1; cargar(); } });
  if (cfg.buscar) {
    const inp = el("input", { type: "search", id: "q", placeholder: cfg.buscar, maxlength: 80, oninput: (e) => (estado.q = e.target.value) });
    herr.append(el("div", { class: "campo" }, el("label", { for: "q" }, "Buscar"), el("div", { class: "campo-ic" }, el("span", {}, icono("buscar")), inp)));
  }
  for (const f of cfg.filtros || []) {
    const fid = "f-" + f.k; let ctl;
    if (f.ref || f.opciones) {
      ctl = el("select", { id: fid, onchange: (e) => { estado.f[f.k] = e.target.value; estado.page = 1; cargar(); } }, el("option", { value: "" }, "Todos"));
      for (const o of f.ref ? cat[f.ref] : f.opciones) {
        const v = f.ref ? o.id : o;
        const txt = f.ref ? ETIQUETA[f.ref](o) : v === "true" ? "Sí" : v === "false" ? "No" : TEXTO_CHIP[v] || String(v);
        ctl.append(el("option", { value: v }, txt));
      }
    } else ctl = el("input", { id: fid, type: f.tipo || "text", min: f.tipo === "number" ? 1 : null, onchange: (e) => { estado.f[f.k] = e.target.value; estado.page = 1; cargar(); } });
    herr.append(el("div", { class: "campo" }, el("label", { for: fid }, f.l), ctl));
  }
  herr.append(el("button", { class: "btn", type: "submit" }, icono("filtro"), "Aplicar"));
  const nuevo = puede(cfg.escribir) && cfg.campos.length ? el("button", { class: "btn btn-primario", type: "button", onclick: () => formulario(cfg, null, cargar) }, icono("mas1"), "Nuevo registro") : null;
  const herramientas = el("details", { class: "herramientas", open: window.innerWidth > 860 }, el("summary", {}, icono("filtro"), "Buscar y filtrar"), herr);
  main.replaceChildren(cabecera(id, cfg.titulo, cfg.desc, nuevo), ayudaVista(id), herramientas, tabla, pag);

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
    const titulo = (c) => campo(c)?.l || { id: "Id", fecha: "Fecha", usuario_id: "Usuario", entidad: "Entidad", registro_id: "Registro", accion: "Acción", detalle: "Detalle" }[c] || c;
    const th = cols.map((c) => {
      const flecha = estado.sort === c ? (estado.order === "asc" ? " ▲" : " ▼") : "";
      return el("th", { scope: "col", "aria-sort": estado.sort === c ? (estado.order === "asc" ? "ascending" : "descending") : null },
        el("button", { type: "button", onclick: () => { estado.order = estado.sort === c && estado.order === "asc" ? "desc" : "asc"; estado.sort = c; cargar(); } }, titulo(c) + flecha));
    });
    const conFicha = id === "estudiantes";
    const acciones = puede(cfg.escribir) || puede(cfg.borrar) || conFicha;
    if (acciones) th.push(el("th", { scope: "col" }, "Acciones"));
    const filas = items.map((it) => {
      const tds = cols.map((c) => {
        const cf = campo(c);
        return el("td", { class: typeof it[c] === "number" && !cf?.ref ? "num" : "", "data-label": titulo(c) }, valorCelda(c, it[c], cf));
      });
      if (acciones) {
        const td = el("td", { class: "acciones" });
        if (conFicha) td.append(el("button", { class: "btn btn-chico btn-primario", type: "button", onclick: () => fichaEstudiante(it.id) }, icono("ficha"), "Ficha 360"));
        if (puede(cfg.escribir) && cfg.campos.length) td.append(el("button", { class: "btn btn-chico", type: "button", onclick: () => formulario(cfg, it, cargar), "aria-label": "Editar registro" }, icono("editar"), "Editar"));
        if (puede(cfg.borrar)) td.append(el("button", { class: "btn btn-chico btn-peligro", type: "button", onclick: () => confirmarBorrado(cfg, it, cargar), "aria-label": "Eliminar registro" }, icono("borrar"), "Eliminar"));
        tds.push(td);
      }
      return el("tr", {}, tds);
    });
    tabla.replaceChildren(items.length ? el("table", {}, el("caption", { class: "saltar" }, cfg.titulo), el("thead", {}, el("tr", {}, th)), el("tbody", {}, filas))
      : el("div", { class: "vacio tarjeta" }, el("div", { class: "vacio-ic" }, icono("buscar")), el("b", {}, "No hay registros que coincidan"), "Prueba con otro filtro o borra la búsqueda."));
    const paginas = Math.max(1, Math.ceil(datos.total / estado.size));
    const tam = el("select", { "aria-label": "Registros por página", onchange: (e) => { estado.size = +e.target.value; estado.page = 1; cargar(); } },
      [10, 20, 50, 100].map((n) => el("option", { value: n, selected: n === estado.size }, `${n} por página`)));
    pag.replaceChildren(el("span", {}, el("b", {}, datos.total.toLocaleString("es-CO")), ` registros · página ${estado.page} de ${paginas}`),
      el("div", { class: "acciones" }, tam,
        el("button", { class: "btn btn-chico", type: "button", disabled: estado.page <= 1, onclick: () => { estado.page--; cargar(); }, "aria-label": "Página anterior" }, icono("izq")),
        el("button", { class: "btn btn-chico", type: "button", disabled: estado.page >= paginas, onclick: () => { estado.page++; cargar(); }, "aria-label": "Página siguiente" }, icono("der"))));
  }
  await cargar();
  if (abrirNuevo === id && nuevo) { abrirNuevo = null; formulario(cfg, null, cargar); }
}

// ------------------------------------------------------------------ formularios con validación en el cliente
function abrirModal(titulo, ...contenido) {
  $("#modal .modal").classList.remove("modal-ancho");
  $("#modal-titulo").textContent = titulo; $("#modal-cuerpo").replaceChildren(...contenido); $("#modal").hidden = false;
  const primero = $("#modal-cuerpo").querySelector("input,select,textarea") || $("#modal-cuerpo").querySelector(".btn-primario"); if (primero) primero.focus();
}
function cerrarModal() { $("#modal").hidden = true; $("#modal-cuerpo").replaceChildren(); $("#modal .modal").classList.remove("modal-ancho"); }

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
        inp.append(el("option", { value: v, selected: val !== undefined && String(val) === String(v) }, c.ref ? ETIQUETA[c.ref](o) : TEXTO_CHIP[v] || String(o)));
      }
    } else if (c.tipo === "bool") inp = el("input", { id, name: c.k, type: "checkbox", checked: !!val });
    else if (c.tipo === "textarea") { inp = el("textarea", { id, name: c.k, required: c.req, minlength: c.min, maxlength: c.max, rows: 3 }); inp.value = val ?? ""; }
    else {
      const num = c.tipo === "number";
      inp = el("input", { id, name: c.k, type: c.tipo, required: c.req || (c.tipo === "password" && !editando), step: num ? c.paso || "1" : null, inputmode: num ? (c.paso ? "decimal" : "numeric") : null,
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
  form.append(el("p", { class: "ayuda-campo" }, "Los campos con * son obligatorios."), errForm,
    el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
      el("button", { class: "btn btn-primario", type: "submit" }, icono("check"), editando ? "Guardar cambios" : "Crear")));
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
      if (cfg.ruta === "/api/alertas") actualizarPendientes();
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
  abrirModal("¿Eliminar este registro?",
    el("div", { class: "nota nota-rojo" }, icono("factores"), el("div", {}, el("b", {}, `Registro ${ident} de ${cfg.titulo.toLowerCase()}`),
      el("p", {}, cfg.compuesta ? "La relación se borra; la auditoría conserva el registro." : "La eliminación es lógica: el registro deja de aparecer, pero queda guardado en la base y en la auditoría."))),
    el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
      el("button", { class: "btn btn-peligro", type: "button", onclick: async () => {
        try { await api(cfg.ruta + "/" + ident, { metodo: "DELETE" }); cerrarModal(); aviso("Registro eliminado.", "ok"); alBorrar(); }
        catch (e) { cerrarModal(); aviso(e.message, "error"); }
      } }, icono("borrar"), "Sí, eliminar")));
}

// ------------------------------------------------------------------ tablero real frente a simulado
let graficas = [];
const COLOR = { verde: "#007B3E", verdeOsc: "#00482B", oro: "#DAAA00", amarillo: "#FBE122", turquesa: "#00A99D", naranja: "#F7931E", rojo: "#c0262d" };
function grafica(canvas, config) {
  if (!window.Chart || !canvas.isConnected) return;
  Chart.defaults.font.family = "Montserrat, system-ui, sans-serif"; Chart.defaults.color = cssVar("--gris-2");
  graficas.push(new Chart(canvas, config));
}

function tarjetaCapacidad(cap, periodo) {
  const etiqueta = { verde: "Hay capacidad", ambar: "Cerca del límite", rojo: "Capacidad superada" }[cap.semaforo];
  const uso = cap.capacidad ? Math.min(100, Math.round((100 * cap.casos) / cap.capacidad)) : 0;
  return el("section", { class: "tarjeta kpi " + { verde: "kpi-verde", ambar: "kpi-naranja", rojo: "kpi-rojo" }[cap.semaforo] },
    el("div", { class: "kpi-cab" }, el("span", { class: "kpi-ic" }, icono("apoyos")), `Capacidad de Bienestar ${periodo ? "· " + periodo : ""}`),
    el("div", { class: "semaforo" },
      el("span", { class: "luces", role: "img", "aria-label": "Semáforo en " + cap.semaforo },
        ["rojo", "ambar", "verde"].map((c) => el("i", { class: c === cap.semaforo ? "on-" + c : "" }))),
      el("div", {}, el("div", { class: "valor" }, `${cap.casos}`, el("small", {}, ` / ${fmt(cap.capacidad)} casos`)),
        el("span", { class: "chip " + { verde: "chip-ok", ambar: "chip-ambar", rojo: "chip-mal" }[cap.semaforo] }, etiqueta))),
    el("div", { class: "barra-prog " + (cap.semaforo === "verde" ? "" : cap.semaforo) }, el("span", { "data-ancho": uso })),
    el("p", { class: "sub" }, cap.mensaje));
}

async function vistaTablero(main, escenario = "E0 Base") {
  const t = await api("/api/tablero?escenario=" + encodeURIComponent(escenario));
  const sel = el("select", { id: "sel-esc", onchange: (e) => { graficas.forEach((g) => g.destroy()); graficas = []; vistaTablero(main, e.target.value); } },
    t.escenarios.map((e) => el("option", { value: e, selected: e === t.escenario }, e)));
  const tarjetas = t.tarjetas.map((x) => {
    const esPct = x.clave === "desercion_periodo";
    const chip = x.dentro_margen === null ? el("span", { class: "chip chip-gris" }, "Sin proyección")
      : x.dentro_margen ? el("span", { class: "chip chip-ok" }, icono("check"), "Modelo dentro del margen") : el("span", { class: "chip chip-mal" }, icono("factores"), "Fuera del margen: recalibrar");
    const cls = esPct ? "kpi-rojo" : x.clave === "matriculados" ? "kpi-verde" : x.clave === "graduados" ? "kpi-turq" : "kpi-oro";
    const ic = esPct ? "alertas" : x.clave === "matriculados" ? "personas" : x.clave === "graduados" ? "programas" : "tablero";
    return el("section", { class: "tarjeta kpi " + cls }, el("div", { class: "kpi-cab" }, el("span", { class: "kpi-ic" }, icono(ic)), `${x.indicador} · ${x.periodo}`),
      el("div", { class: "valor" }, esPct ? pct(x.real, 2) : fmt(x.real)),
      el("p", { class: "sub" }, `Simulado: ${esPct ? pct(x.simulado, 2) : fmt(x.simulado)} · desviación ${x.desviacion === null ? "—" : pct(x.desviacion)}`), el("div", {}, chip));
  });
  const c1 = el("canvas", { "aria-label": "Deserción por periodo real y simulada", role: "img" });
  const c2 = el("canvas", { "aria-label": "Matriculados reales y simulados", role: "img" });
  main.replaceChildren(
    cabecera("tablero", "Tablero: lo real frente a la simulación", "Compara lo registrado en el sistema con lo que proyecta el modelo para el escenario elegido. Las políticas de E1 y E3 arrancan en 2026-1.",
      el("div", {}, el("label", { for: "sel-esc" }, "Escenario de la simulación"), sel)),
    ayudaVista("tablero"),
    el("div", { class: "rejilla" }, tarjetaCapacidad(t.capacidad, t.periodo_en_curso), ...tarjetas),
    el("div", { class: "dos-col" },
      el("section", { class: "tarjeta" }, el("h2", {}, icono("alertas"), "Deserción por periodo (%)"), el("div", { class: "grafica" }, c1)),
      el("section", { class: "tarjeta" }, el("h2", {}, icono("personas"), "Matriculados"), el("div", { class: "grafica" }, c2))),
    el("p", { class: "nota" }, icono("info"), `Tolerancia: si la desviación supera ${pct(t.tolerancia, 0)} en algún indicador, el modelo debe recalibrarse con los datos nuevos (scripts de simulacion/). Datos sintéticos de desarrollo.`));
  animarBarras(main);
  const labels = t.serie.map((s) => s.periodo);
  const serie = (fuente, k, mult = 1) => t.serie.map((s) => (s[fuente] ? +(s[fuente][k] * mult).toFixed(2) : null));
  const opc = { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
    plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } }, tooltip: { backgroundColor: COLOR.verdeOsc, padding: 10, cornerRadius: 8 } },
    scales: { x: { ticks: { maxTicksLimit: 10 }, grid: { display: false } }, y: { grid: { color: cssVar("--linea") } } } };
  const real = (k, m) => ({ label: "Real (sistema)", data: serie("real", k, m), borderColor: COLOR.verde, backgroundColor: "rgba(0,123,62,.12)", fill: true, tension: .3, pointRadius: 2.5, borderWidth: 2.5 });
  const sim = (k, m) => ({ label: "Simulado · " + t.escenario, data: serie("simulado", k, m), borderColor: COLOR.oro, borderDash: [6, 4], pointRadius: 0, tension: .3, borderWidth: 2.5 });
  grafica(c1, { type: "line", data: { labels, datasets: [real("desercion_periodo", 100), sim("desercion_periodo", 100)] }, options: opc });
  grafica(c2, { type: "line", data: { labels, datasets: [real("matriculados"), sim("matriculados")] }, options: opc });
}

// ------------------------------------------------------------------ cola de Bienestar (ruta de permanencia integral)
async function vistaCola(main) {
  const q = await api("/api/bienestar/cola");
  pendientesCola = q.casos.length; pintarMenu(); marcarActual();
  const atiende = puede([A, O]);
  const maxP = Math.max(1, ...q.casos.map((c) => c.prioridad || 0));
  const cab = ["#", "Prioridad", "Nivel", "Semestre", "Etapa", "Básicas perdidas", "Promedio", "Apoyo sugerido", "Id estudiante"].concat(atiende ? ["Acción"] : []);
  const filas = q.casos.map((c, i) => {
    const vals = [el("b", {}, i + 1),
      el("span", { class: "prioridad" }, el("b", {}, fmt(c.prioridad)), el("span", { class: "barra-prog " + (c.nivel === "alto" ? "rojo" : c.nivel === "medio" ? "ambar" : "") }, el("span", { "data-ancho": Math.round((100 * c.prioridad) / maxP) }))),
      el("span", { class: "chip " + CHIPS.nivel[c.nivel] }, c.nivel), c.nivel_semestre, c.etapa, c.materias_basicas_perdidas, fmt(c.promedio, 2), c.apoyo_sugerido || "—", el("button", { type: "button", class: "btn-enlace", onclick: () => fichaEstudiante(c.estudiante_id) }, icono("ficha"), String(c.estudiante_id))];
    const tds = vals.map((v, j) => el("td", { "data-label": cab[j], class: [0, 3, 5, 6, 8].includes(j) ? "num" : j === 7 ? "ajustar" : "" }, v));
    if (atiende) tds.push(el("td", { class: "acciones" }, el("button", { class: "btn btn-chico btn-primario", type: "button", onclick: () => atender(c, () => vistaCola(main)) }, icono("apoyos"), "Atender")));
    return el("tr", {}, tds);
  });
  main.replaceChildren(
    cabecera("cola", `Cola de Bienestar · ${q.periodo}`, "Casos sin atender ordenados por una regla pública: nivel de la alerta, semestre (los primeros pesan más porque ahí la deserción es mayor) y materias básicas perdidas. La regla no usa estrato ni condición laboral."),
    ayudaVista("cola"),
    el("div", { class: "rejilla" }, tarjetaCapacidad(q.capacidad, q.periodo), kpi(q.casos.length ? "kpi-oro" : "kpi-verde", "cola", "Casos pendientes", String(q.casos.length), q.casos.length ? "Empieza por el primero de la lista" : "¡Todo al día!")),
    q.casos.length ? el("div", { class: "tabla-env apilable" }, el("table", {}, el("thead", {}, el("tr", {}, cab.map((h) => el("th", { scope: "col" }, h)))), el("tbody", {}, filas)))
      : el("div", { class: "vacio tarjeta" }, el("div", { class: "vacio-ic" }, icono("check")), el("b", {}, "No hay casos pendientes"), "Todas las alertas del periodo ya fueron atendidas."));
  animarBarras(main);
}

function atender(caso, alTerminar) {
  const sel = el("select", { id: "tipo-apoyo" }, cat["tipos-apoyo"].map((t) => el("option", { value: t.id, selected: t.id === caso.tipo_apoyo_sugerido_id }, ETIQUETA["tipos-apoyo"](t) + (t.id === caso.tipo_apoyo_sugerido_id ? " (sugerido)" : ""))));
  abrirModal("Atender caso",
    el("div", { class: "rejilla" },
      kpi(caso.nivel === "alto" ? "kpi-rojo" : caso.nivel === "medio" ? "kpi-naranja" : "kpi-verde", "alertas", "Nivel de riesgo", caso.nivel, `Alerta ${caso.alerta_id}`),
      kpi("kpi-turq", "programas", "Semestre", String(caso.nivel_semestre), caso.etapa)),
    el("p", { class: "sub" }, el("b", {}, "Motivo: "), caso.motivo),
    el("label", { for: "tipo-apoyo" }, "Apoyo que se asigna"), sel,
    el("p", { class: "ayuda-campo" }, "La sugerencia sale de los pesos por etapa del modelo de simulación y de los factores de riesgo del estudiante."),
    el("div", { class: "modal-pie" }, el("button", { class: "btn", type: "button", onclick: cerrarModal }, "Cancelar"),
      el("button", { class: "btn btn-primario", type: "button", onclick: async () => {
        try { await api(`/api/bienestar/cola/${caso.alerta_id}/atender?tipo_apoyo_id=${sel.value}`, { metodo: "POST" }); cerrarModal(); aviso("Caso atendido y apoyo asignado.", "ok"); alTerminar(); }
        catch (e) { aviso(e.message, "error"); }
      } }, icono("check"), "Asignar apoyo")));
}

// ------------------------------------------------------------------ reportes y exportación
async function vistaReportes(main, rid) {
  const lista = await api("/api/reportes");
  rid = rid || lista[0].id;
  const rep = await api("/api/reportes/" + rid);
  const sel = el("select", { id: "sel-rep", onchange: (e) => { graficas.forEach((g) => g.destroy()); graficas = []; vistaReportes(main, e.target.value); } },
    lista.map((r) => el("option", { value: r.id, selected: r.id === rid }, r.titulo)));
  const lienzo = el("canvas", { role: "img", "aria-label": "Gráfica del reporte" });
  const clases = ["kpi-verde", "kpi-oro", "kpi-turq", "kpi-naranja"];
  main.replaceChildren(
    cabecera("reportes", "Reportes y exportación", "Indicadores calculados con los datos del sistema. Cada reporte se descarga en CSV o PDF.", el("div", {}, el("label", { for: "sel-rep" }, "Reporte"), sel)),
    ayudaVista("reportes"),
    el("section", { class: "tarjeta" }, el("h2", {}, icono("reportes"), rep.titulo), el("p", { class: "sub" }, rep.descripcion),
      el("ul", { class: "indicadores" }, rep.indicadores.map((i, j) => el("li", { class: "tarjeta kpi " + clases[j % 4] }, el("div", { class: "kpi-cab" }, i.nombre),
        el("div", { class: "valor" }, fmt(i.valor, 2), " ", el("small", {}, i.unidad)), i.detalle ? el("div", { class: "sub" }, i.detalle) : null))),
      el("div", { class: "barra-herr" },
        el("button", { class: "btn btn-primario", type: "button", onclick: () => descargar(`/api/reportes/${rid}?formato=csv`, `reporte_${rid}.csv`) }, icono("descargar"), "Descargar CSV"),
        el("button", { class: "btn", type: "button", onclick: () => descargar(`/api/reportes/${rid}?formato=pdf`, `reporte_${rid}.pdf`) }, icono("descargar"), "Descargar PDF")),
      el("div", { class: "grafica" }, lienzo)),
    el("div", { class: "tabla-env apilable", style: null }, el("table", {}, el("thead", {}, el("tr", {}, rep.columnas.map((c) => el("th", { scope: "col" }, c)))),
      el("tbody", {}, rep.filas.map((f) => el("tr", {}, f.map((v, j) => el("td", { class: typeof v === "number" ? "num" : "", "data-label": rep.columnas[j] }, fmt(v, 2)))))))),
    el("section", { class: "tarjeta", }, el("h2", {}, icono("simulacion"), "Exportación de históricos para la simulación"),
      el("p", { class: "sub" }, "Las cinco series con las que se ajustan las distribuciones del modelo (excluye el periodo en curso). Son idénticas a las de simulacion/datos."),
      el("div", { class: "barra-herr" }, el("button", { class: "btn btn-acento", type: "button", onclick: () => descargar("/api/exportacion/historicos", "historicos_crud.zip") }, icono("descargar"), "Descargar las 5 series (ZIP)"),
        ...["ingresos_por_cohorte", "matriculas_por_periodo", "matriculas_por_nivel", "desercion_sem1_por_cohorte", "alertas_y_apoyos_por_periodo"].map((n) =>
          el("button", { class: "btn btn-chico", type: "button", onclick: () => descargar("/api/exportacion/historicos/" + n, n + ".csv") }, n + ".csv")))));
  const iy = rep.columnas.length - 1;
  const barras = rid === "desercion-nivel";
  grafica(lienzo, { type: barras ? "bar" : "line", data: { labels: rep.filas.map((f) => String(f[0])), datasets: [
    { label: rep.columnas[iy], data: rep.filas.map((f) => (typeof f[iy] === "number" ? f[iy] : null)), borderColor: COLOR.verde, backgroundColor: barras ? COLOR.verde : "rgba(0,123,62,.12)", fill: !barras, tension: .3, borderRadius: 6, borderWidth: 2.5 },
    ...(barras ? [{ label: rep.columnas[4], data: rep.filas.map((f) => f[4]), backgroundColor: COLOR.oro, borderRadius: 6 }] : [])] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } } }, scales: { x: { grid: { display: false } }, y: { grid: { color: cssVar("--linea") } } } } });
}

// ------------------------------------------------------------------ parámetros y carga de proyecciones
async function vistaParametros(main) {
  const params = await api("/api/parametros");
  const esAdmin = rol() === A;
  const cab = ["Clave", "Descripción", "Valor", ""];
  const filas = params.map((p) => {
    const inp = el("input", { type: "number", step: "0.01", min: 0, max: 1000, value: p.valor, disabled: !esAdmin, "aria-label": p.clave, required: true, inputmode: "decimal" });
    return el("tr", {}, el("td", { "data-label": cab[0] }, el("code", {}, p.clave)), el("td", { "data-label": cab[1] }, p.descripcion), el("td", { "data-label": cab[2] }, inp),
      el("td", { class: "acciones" }, esAdmin ? el("button", { class: "btn btn-chico btn-primario", type: "button", onclick: async () => {
        if (!inp.checkValidity()) { aviso("Ingrese un valor entre 0 y 1000.", "error"); return; }
        try { await api(`/api/parametros/${p.clave}?valor=${inp.value}`, { metodo: "PUT" }); aviso("Parámetro actualizado.", "ok"); } catch (e) { aviso(e.message, "error"); }
      } }, icono("check"), "Guardar") : null));
  });
  const archivo = el("input", { type: "file", id: "archivo-proy", accept: ".csv,text/csv" });
  main.replaceChildren(
    cabecera("parametros", "Parámetros y proyecciones", "Valores de operación que vienen de la simulación. La capacidad de Bienestar del escenario recomendado (E3) es 32 casos por semestre."),
    ayudaVista("parametros"),
    el("div", { class: "tabla-env apilable" }, el("table", {}, el("thead", {}, el("tr", {}, cab.map((h) => el("th", { scope: "col" }, h)))), el("tbody", {}, filas))),
    esAdmin ? el("section", { class: "tarjeta" }, el("h2", {}, icono("subir"), "Cargar proyecciones de la simulación"),
      el("p", { class: "sub" }, "Archivo generado por simulacion/scripts/exportar_proyecciones.py. Columnas: escenario, periodo, matriculados, desercion_periodo, graduados, alertas, cobertura_bienestar."),
      el("label", { for: "archivo-proy" }, "Archivo CSV"), archivo,
      el("div", { class: "modal-pie" }, el("button", { class: "btn btn-primario", type: "button", onclick: async () => {
        if (!archivo.files.length) { aviso("Seleccione un archivo CSV.", "error"); return; }
        const fd = new FormData(); fd.append("archivo", archivo.files[0]);
        try { const r = await api("/api/proyecciones", { metodo: "POST", form: fd }); aviso(`Proyecciones cargadas: ${r.escenarios.join(", ")}.`, "ok"); } catch (e) { aviso(e.message, "error"); }
      } }, icono("subir"), "Cargar"))) : el("p", { class: "nota" }, icono("candado"), "Solo el administrador puede cambiar parámetros o cargar proyecciones."));
}

// ------------------------------------------------------------------ logo oficial (opcional) y sesión
function prepararLogos() {
  // Si existe /static/img/logo-udec.png (imagotipo oficial descargado del sitio de la universidad), se muestra; si no, queda el respaldo tipográfico.
  document.querySelectorAll("img.logo-udec").forEach((img) => {
    const mostrar = () => { if (img.naturalWidth > 0) { img.hidden = false; img.parentElement.classList.add("con-logo"); } };
    if (img.complete) mostrar(); else img.addEventListener("load", mostrar, { once: true });
  });
}
function mostrarLogin(msg) {
  $("#vista-app").hidden = true; $("#vista-login").hidden = false; $("#err-login").textContent = msg || "";
  $("#login-email").focus();
}
async function mostrarApp() {
  $("#vista-login").hidden = true; $("#vista-app").hidden = false;
  const u = sesion.usuario;
  $("#usuario-nombre").textContent = u.nombre; $("#usuario-rol").textContent = u.rol;
  $("#usuario-avatar").textContent = (u.nombre || "?").split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  await cargarCatalogos(); pintarMenu(); router(); actualizarPendientes();
}

document.addEventListener("DOMContentLoaded", () => {
  pintarIconosEstaticos(); prepararLogos();
  $("#form-login").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = $("#login-email"), clave = $("#login-clave");
    $("#err-login-email").textContent = email.validity.valueMissing ? "Escriba su correo." : email.validity.typeMismatch ? "El correo no tiene un formato válido." : "";
    $("#err-login-clave").textContent = clave.validity.valueMissing ? "Escriba su contraseña." : clave.validity.tooShort ? "La contraseña tiene al menos 8 caracteres." : "";
    if (!email.checkValidity() || !clave.checkValidity()) return;
    const boton = e.target.querySelector("button[type=submit]"); boton.disabled = true;
    try {
      const fd = new URLSearchParams({ username: email.value.trim(), password: clave.value });
      const r = await fetch("/api/auth/login", { method: "POST", body: fd });
      const j = await r.json();
      if (!r.ok) { $("#err-login").textContent = j.detail || "No fue posible iniciar sesión."; return; }
      sesion.guardar(j.access_token, { nombre: j.nombre, rol: j.rol }); clave.value = "";
      if (!location.hash) location.hash = "#inicio";
      mostrarApp();
    } catch { $("#err-login").textContent = "No hay conexión con el servidor. Si está en Render, espere un minuto mientras despierta."; }
    finally { boton.disabled = false; }
  });
  document.querySelectorAll(".demo-rol").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".demo-rol").forEach((x) => x.classList.toggle("activo", x === b));
    $("#login-email").value = b.dataset.email; $("#login-clave").value = "Cambiar-123"; $("#err-login").textContent = "";
    $("#form-login").querySelector("button[type=submit]").focus();
  }));
  $("#ver-clave").addEventListener("click", (e) => {
    const c = $("#login-clave"), ver = c.type === "password"; c.type = ver ? "text" : "password";
    e.currentTarget.setAttribute("aria-pressed", String(ver)); e.currentTarget.setAttribute("aria-label", ver ? "Ocultar contraseña" : "Mostrar contraseña");
  });
  $("#btn-salir").addEventListener("click", () => { sesion.cerrar(); location.hash = ""; mostrarLogin("Sesión cerrada."); });
  $("#btn-menu").addEventListener("click", () => alternarMenu(!$("#menu").classList.contains("abierto")));
  $("#velo").addEventListener("click", () => alternarMenu(false));
  $("#btn-recorrido").addEventListener("click", () => recorrido(0));
  $("#btn-tema").addEventListener("click", alternarTema); pintarBotonTema();
  $("#btn-paleta").addEventListener("click", abrirPaleta);
  $("#modal-cerrar").addEventListener("click", cerrarModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") cerrarModal(); });
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k" && sesion.token && !$("#vista-app").hidden) { e.preventDefault(); abrirPaleta(); return; }
    if (e.key === "Escape" && $("#paleta")) { cerrarPaleta(); return; }
    if (e.key === "Escape") { if (!$("#modal").hidden) cerrarModal(); else alternarMenu(false); } });
  window.addEventListener("hashchange", () => { if (sesion.token) router(); });
  if (sesion.token) mostrarApp(); else mostrarLogin();
});

// ================================================================== versión 2: animaciones, tema, buscador, ficha 360 y laboratorio
// ------------------------------------------------------------------ cifras que "cuentan" desde cero
function contarValores(raiz) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  raiz.querySelectorAll(".valor, .mini-kpi b, .grande").forEach((nodo) => {
    const t = nodo.firstChild; if (!t || t.nodeType !== 3) return;
    const m = t.textContent.match(/^(-?[\d.]+(?:,\d+)?)(.*)$/); if (!m) return;
    const dec = (m[1].split(",")[1] || "").length;
    const fin = parseFloat(m[1].replace(/\./g, "").replace(",", ".")); if (!isFinite(fin)) return;
    const sufijo = m[2], t0 = performance.now(), dur = 900;
    const paso = (ahora) => {
      const k = Math.min(1, (ahora - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      t.textContent = (fin * e).toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + sufijo;
      if (k < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  });
}

// ------------------------------------------------------------------ modo claro / oscuro
function pintarBotonTema() {
  const oscuro = document.documentElement.dataset.tema === "oscuro", b = $("#btn-tema");
  b.replaceChildren(icono(oscuro ? "sol" : "luna")); b.setAttribute("aria-label", oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
}
function alternarTema() {
  const oscuro = document.documentElement.dataset.tema !== "oscuro";
  if (oscuro) document.documentElement.dataset.tema = "oscuro"; else delete document.documentElement.dataset.tema;
  almacen.guardar("tema", oscuro ? "oscuro" : "claro"); pintarBotonTema();
  if (graficas.length) router(); // las gráficas se vuelven a dibujar con los colores del tema
}

// ------------------------------------------------------------------ buscador universal (Ctrl + K)
const sinTildes = (x) => x.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
function comandosBase() {
  const lista = [];
  for (const g of VISTAS) for (const [id, t, r, ic] of g.items) if (puede(r)) lista.push({ grupo: "Ir a", ic, t, sub: g.grupo, run: () => { location.hash = "#" + id; } });
  if (puede([A, O])) {
    lista.push({ grupo: "Acciones", ic: "alertas", t: "Registrar una alerta temprana", sub: "Abre el formulario", run: () => { abrirNuevo = "alertas"; location.hash === "#alertas" ? router() : (location.hash = "#alertas"); } });
    lista.push({ grupo: "Acciones", ic: "matriculas", t: "Registrar una matrícula", sub: "Abre el formulario", run: () => { abrirNuevo = "matriculas"; location.hash === "#matriculas" ? router() : (location.hash = "#matriculas"); } });
  }
  const oscuro = document.documentElement.dataset.tema === "oscuro";
  lista.push({ grupo: "Acciones", ic: oscuro ? "sol" : "luna", t: oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro", sub: "Apariencia", run: alternarTema });
  lista.push({ grupo: "Acciones", ic: "ruta", t: "Ver el recorrido guiado", sub: "Ayuda", run: () => recorrido(0) });
  lista.push({ grupo: "Acciones", ic: "salir", t: "Cerrar sesión", sub: sesion.usuario?.nombre || "", run: () => $("#btn-salir").click() });
  return lista;
}
function cerrarPaleta() { $("#paleta")?.remove(); }
function abrirPaleta() {
  if ($("#paleta")) return;
  if (!$("#modal").hidden) cerrarModal();
  let activo = 0, visibles = [], extra = [], temporizador;
  const base = comandosBase();
  const entrada = el("input", { type: "search", placeholder: "Busca una sección, una acción o el código de un estudiante…", "aria-label": "Buscar", autocomplete: "off", role: "combobox", "aria-expanded": "true", "aria-controls": "paleta-lista" });
  const lista = el("ul", { class: "paleta-lista", id: "paleta-lista", role: "listbox" });
  const fondo = el("div", { class: "paleta-fondo", id: "paleta", onclick: (e) => { if (e.target === fondo) cerrarPaleta(); } },
    el("div", { class: "paleta", role: "dialog", "aria-modal": "true", "aria-label": "Buscador" },
      el("div", { class: "paleta-entrada" }, icono("buscar"), entrada, el("kbd", {}, "Esc")), lista,
      el("div", { class: "paleta-pie" }, el("span", {}, el("kbd", {}, "↑"), " ", el("kbd", {}, "↓"), " moverse"), el("span", {}, el("kbd", {}, "Enter"), " abrir"), el("span", {}, el("kbd", {}, "Ctrl K"), " abrir el buscador desde cualquier pantalla"))));
  const pintar = () => {
    const q = sinTildes(entrada.value.trim());
    visibles = [...extra, ...base.filter((c) => !q || sinTildes(c.t + " " + c.sub).includes(q))];
    activo = Math.min(activo, Math.max(0, visibles.length - 1));
    lista.replaceChildren();
    let grupo = null;
    visibles.forEach((c, i) => {
      if (c.grupo !== grupo) { grupo = c.grupo; lista.append(el("li", { class: "paleta-grupo", role: "presentation" }, grupo)); }
      lista.append(el("li", { class: "paleta-item" + (i === activo ? " activo" : ""), role: "option", "aria-selected": String(i === activo), onmousemove: () => { if (activo !== i) { activo = i; pintar(); } }, onclick: () => ejecutar(i) },
        el("span", { class: "pi-ic" }, icono(c.ic)), el("div", {}, c.t, el("small", {}, c.sub)), el("span", { class: "pi-flecha" }, icono("flecha"))));
    });
    if (!visibles.length) lista.append(el("li", { class: "vacio" }, "Sin resultados. Prueba con otra palabra."));
    lista.querySelector(".activo")?.scrollIntoView({ block: "nearest" });
  };
  const ejecutar = (i) => { const c = visibles[i]; if (!c) return; cerrarPaleta(); c.run(); };
  const buscarEstudiantes = async () => {
    const q = entrada.value.trim(); extra = [];
    if (/^\d+$/.test(q)) extra.push({ grupo: "Estudiantes", ic: "ficha", t: `Abrir la ficha del estudiante con id ${q}`, sub: "Ficha 360", run: () => fichaEstudiante(+q) });
    if (q.length >= 3 && /^[A-Za-z0-9]+$/.test(q)) {
      try {
        const r = await api("/api/estudiantes?size=6&q=" + encodeURIComponent(q));
        for (const e of r.items) extra.push({ grupo: "Estudiantes", ic: "ficha", t: e.codigo_anonimo, sub: `Id ${e.id} · ${etiquetaRef("cohortes", e.cohorte_id)} · estrato ${e.estrato}`, run: () => fichaEstudiante(e.id) });
      } catch { /* sin resultados */ }
    }
    pintar();
  };
  entrada.addEventListener("input", () => { activo = 0; pintar(); clearTimeout(temporizador); temporizador = setTimeout(buscarEstudiantes, 250); });
  entrada.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); activo = (activo + 1) % Math.max(1, visibles.length); pintar(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); activo = (activo - 1 + visibles.length) % Math.max(1, visibles.length); pintar(); }
    else if (e.key === "Enter") { e.preventDefault(); ejecutar(activo); }
  });
  document.body.append(fondo); pintar(); entrada.focus();
}

// ------------------------------------------------------------------ ficha 360 del estudiante
let graficaFicha = null;
async function fichaEstudiante(id) {
  abrirModal("Ficha del estudiante", el("div", {}, el("div", { class: "esqueleto alto" }), el("div", { class: "esqueleto" }), el("div", { class: "esqueleto alto" })));
  $("#modal .modal").classList.add("modal-ancho");
  let est, mats, apo, fac;
  try {
    [est, mats, apo, fac] = await Promise.all([api("/api/estudiantes/" + id), api(`/api/matriculas?estudiante_id=${id}&size=100&sort=periodo_id&order=asc`),
      api(`/api/apoyos?estudiante_id=${id}&size=100`), api(`/api/estudiante-factores?estudiante_id=${id}&size=100`)]);
  } catch (e) { $("#modal-cuerpo").replaceChildren(el("div", { class: "nota nota-rojo" }, icono("factores"), e.status === 404 ? `No existe un estudiante con id ${id}.` : e.message)); return; }
  const ms = mats.items;
  const alertas = (await Promise.all(ms.map((m) => api(`/api/alertas?matricula_id=${m.id}&size=50`).then((r) => r.items).catch(() => [])))).flat();
  const ultimo = ms[ms.length - 1];
  const estado = !ultimo ? "Sin matrículas" : { CONTINUA: "Activo", DESERTA: "Desertó", GRADUA: "Graduado" }[ultimo.resultado];
  const promedio = ms.length ? ms.reduce((a, m) => a + m.promedio, 0) / ms.length : null;
  const tipoApoyo = (tid) => cat["tipos-apoyo"].find((t) => t.id === tid)?.nombre || "Apoyo " + tid;
  const factor = (fid) => cat.factores.find((f) => f.id === fid);
  const lienzo = el("canvas", { role: "img", "aria-label": "Promedio por semestre" });
  $("#modal-titulo").textContent = "Ficha 360 del estudiante";
  $("#modal-cuerpo").replaceChildren(
    el("div", { class: "ficha-cab" }, el("span", { class: "ficha-avatar" }, icono("usuario")),
      el("div", {}, el("h3", {}, est.codigo_anonimo), el("div", {}, el("span", { class: "chip" }, `Id ${est.id}`), el("span", { class: "chip" }, etiquetaRef("cohortes", est.cohorte_id)),
        el("span", { class: "chip" }, `Estrato ${est.estrato}`), el("span", { class: "chip" }, `Saber 11: ${est.puntaje_saber11}`), el("span", { class: "chip" }, est.trabaja ? "Trabaja" : "No trabaja"))),
      el("div", { class: "ficha-estado" }, el("div", { class: "sub", style: null }, ""), el("span", { class: "chip" }, estado))),
    el("div", { class: "mini-kpis" },
      el("div", { class: "mini-kpi" }, el("span", {}, "Semestres cursados"), el("b", {}, String(ms.length))),
      el("div", { class: "mini-kpi" }, el("span", {}, "Promedio general"), el("b", {}, promedio === null ? "—" : fmt(promedio, 2))),
      el("div", { class: "mini-kpi" }, el("span", {}, "Alertas"), el("b", {}, String(alertas.length))),
      el("div", { class: "mini-kpi" }, el("span", {}, "Apoyos recibidos"), el("b", {}, String(apo.items.length)))),
    el("div", { class: "ficha-rejilla" },
      el("section", {}, el("h3", { class: "seccion-titulo" }, icono("reloj"), "Trayectoria semestre a semestre"),
        ms.length ? el("ol", { class: "linea-tiempo" }, ms.map((m) => el("li", { class: m.resultado === "DESERTA" ? "deserta" : m.resultado === "GRADUA" ? "gradua" : "" },
          el("div", { class: "lt-cab" }, el("b", {}, nombrePeriodo(m.periodo_id)), `Semestre ${m.nivel_semestre}`, el("span", { class: "chip chip-gris" }, `Promedio ${fmt(m.promedio, 2)}`),
            m.materias_basicas_perdidas ? el("span", { class: "chip chip-ambar" }, `${m.materias_basicas_perdidas} básica(s) perdida(s)`) : null, valorCelda("resultado", m.resultado)),
          alertas.filter((a) => a.matricula_id === m.id).map((a) => el("div", { class: "lt-alerta" }, icono("alertas"), el("span", {}, el("b", {}, `Alerta ${a.nivel}: `), a.motivo, a.atendida ? " · atendida" : " · pendiente"))))))
          : el("p", { class: "sub" }, "Este estudiante no tiene matrículas registradas.")),
      el("section", {},
        el("h3", { class: "seccion-titulo" }, icono("tablero"), "Promedio por semestre"), el("div", { class: "grafica", style: null }, lienzo),
        el("h3", { class: "seccion-titulo" }, icono("factores"), "Factores de riesgo"),
        fac.items.length ? el("div", { class: "lista-chips" }, fac.items.map((f) => { const fx = factor(f.factor_id);
          return el("span", { class: "chip " + (CHIPS.tipo[fx?.tipo] || "chip-gris") }, (fx?.nombre || "Factor " + f.factor_id) + " · " + nombrePeriodo(f.periodo_id),
            el("span", { class: "puntos-int", "aria-label": `intensidad ${f.intensidad} de 3` }, [1, 2, 3].map((k) => el("i", { class: k <= f.intensidad ? "on" : "" })))); }))
          : el("p", { class: "sub" }, "Sin factores registrados."),
        el("h3", { class: "seccion-titulo" }, icono("apoyos"), "Apoyos de Bienestar"),
        apo.items.length ? el("div", { class: "lista-chips" }, apo.items.map((a) => el("span", { class: "chip " + (CHIPS.estado[a.estado] || "chip-gris") }, `${tipoApoyo(a.tipo_apoyo_id)} · ${nombrePeriodo(a.periodo_id)} · ${a.estado.replace("_", " ")}`)))
          : el("p", { class: "sub" }, "Todavía no ha recibido apoyos."))),
    el("p", { class: "ayuda-campo" }, "La ficha reúne en una sola vista la información de cinco tablas del sistema. El estudiante se identifica solo con un código anónimo."));
  contarValores($("#modal-cuerpo"));
  if (graficaFicha) graficaFicha.destroy();
  if (window.Chart && ms.length) {
    Chart.defaults.font.family = "Montserrat, system-ui, sans-serif"; Chart.defaults.color = cssVar("--gris-2");
    graficaFicha = new Chart(lienzo, { type: "line", data: { labels: ms.map((m) => nombrePeriodo(m.periodo_id)), datasets: [
      { label: "Promedio", data: ms.map((m) => m.promedio), borderColor: COLOR.verde, backgroundColor: "rgba(0,123,62,.15)", fill: true, tension: .35, pointRadius: 4, pointBackgroundColor: ms.map((m) => (m.promedio < 3 ? COLOR.rojo : COLOR.verde)) },
      { label: "Mínimo aprobatorio (3,0)", data: ms.map(() => 3), borderColor: COLOR.oro, borderDash: [5, 4], pointRadius: 0, borderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } } }, scales: { y: { min: 0, max: 5, grid: { color: cssVar("--linea") } }, x: { grid: { display: false } } } } });
  }
}

// ------------------------------------------------------------------ laboratorio de escenarios
const COLORES_ESC = ["#F7931E", "#00A99D", "#007B3E", "#DAAA00", "#79C000"];
async function vistaLaboratorio(main) {
  const primero = await api("/api/tablero");
  const nombres = primero.escenarios;
  const [series, nivel] = await Promise.all([Promise.all(nombres.map((n) => (n === primero.escenario ? primero : api("/api/tablero?escenario=" + encodeURIComponent(n))))), api("/api/reportes/desercion-nivel")]);
  const periodos = series[0].serie.map((s) => s.periodo);
  const horizonte = periodos.filter((p) => p >= "2026-1" && series[0].serie.find((s) => s.periodo === p)?.simulado);
  const valor = (i, p, k) => series[i].serie.find((s) => s.periodo === p)?.simulado?.[k] ?? null;
  const prom = (arr) => arr.reduce((a, b) => a + b, 0) / Math.max(1, arr.length);
  const resumen = nombres.map((n, i) => ({
    n, color: COLORES_ESC[i % COLORES_ESC.length],
    des: prom(horizonte.map((p) => valor(i, p, "desercion_periodo"))),
    mat: valor(i, horizonte[horizonte.length - 1], "matriculados"),
    gra: horizonte.reduce((a, p) => a + (valor(i, p, "graduados") || 0), 0),
    cob: prom(horizonte.map((p) => valor(i, p, "cobertura_bienestar") ?? 0)),
  }));
  const base = resumen[0], mejor = resumen.reduce((a, b) => (b.des < a.des ? b : a));
  const delta = (v, ref, inv, txt) => { const d = v - ref; if (Math.abs(d) < 1e-9) return el("span", { class: "sub" }, "referencia"); const bien = inv ? d < 0 : d > 0; return el("span", { class: bien ? "delta-bien" : "delta-mal" }, (d > 0 ? "+" : "−") + txt(Math.abs(d))); };
  const tarjetas = resumen.map((r) => {
    const t = el("section", { class: "tarjeta esc-tarjeta" }, r === mejor ? el("span", { class: "cinta" }, icono("trofeo"), "Menor deserción") : null,
      el("h3", {}, el("i", {}), r.n),
      el("div", { class: "esc-fila" }, el("span", {}, "Deserción promedio 2026–2030"), el("span", {}, el("b", {}, pct(r.des, 2)), " ", delta(r.des, base.des, true, (x) => fmt(100 * x, 2) + " pts"))),
      el("div", { class: "esc-fila" }, el("span", {}, `Matriculados en ${horizonte[horizonte.length - 1]}`), el("span", {}, el("b", {}, fmt(r.mat, 0)), " ", delta(r.mat, base.mat, false, (x) => fmt(x, 0) + " est."))),
      el("div", { class: "esc-fila" }, el("span", {}, "Graduados acumulados"), el("span", {}, el("b", {}, fmt(r.gra, 0)), " ", delta(r.gra, base.gra, false, (x) => fmt(x, 0)))),
      el("div", { class: "esc-fila" }, el("span", {}, "Cobertura de Bienestar"), el("b", {}, pct(r.cob, 0))));
    t.style.setProperty("--c", r.color); return t;
  });
  // gráfica comparativa
  const lienzo = el("canvas", { role: "img", "aria-label": "Deserción por periodo en cada escenario" });
  const conm = el("div", { class: "conmutadores", role: "group", "aria-label": "Escenarios visibles" });
  // máquina del tiempo
  const rango = el("input", { type: "range", min: 0, max: horizonte.length - 1, value: horizonte.length - 1, "aria-label": "Semestre proyectado" });
  const salida = el("output", {}, horizonte[horizonte.length - 1]);
  const foto = el("div", { class: "esc-rejilla" });
  const pintarFoto = () => {
    const p = horizonte[+rango.value]; salida.textContent = p;
    foto.replaceChildren(...nombres.map((n, i) => { const c = el("section", { class: "tarjeta esc-tarjeta" }, el("h3", {}, el("i", {}), n),
      el("div", { class: "esc-fila" }, el("span", {}, "Deserción del periodo"), el("b", {}, pct(valor(i, p, "desercion_periodo"), 2))),
      el("div", { class: "esc-fila" }, el("span", {}, "Matriculados"), el("b", {}, fmt(valor(i, p, "matriculados"), 0))),
      el("div", { class: "esc-fila" }, el("span", {}, "Alertas tempranas"), el("b", {}, fmt(valor(i, p, "alertas"), 0))),
      el("div", { class: "esc-fila" }, el("span", {}, "Cobertura de Bienestar"), el("b", {}, pct(valor(i, p, "cobertura_bienestar"), 0))));
    c.style.setProperty("--c", COLORES_ESC[i % COLORES_ESC.length]); return c; }));
  };
  rango.addEventListener("input", pintarFoto);
  // embudo de cohorte con las tasas por semestre
  const filas = nivel.filas.filter((f) => f[0] <= 10 && typeof f[4] === "number");
  let n = 100, nm = 100; const obs = [], mod = [];
  for (const f of filas) { obs.push(+n.toFixed(1)); mod.push(+nm.toFixed(1)); n *= 1 - f[4] / 100; nm *= 1 - (typeof f[5] === "number" ? f[5] : f[4]) / 100; }
  const llegan = obs[obs.length - 1], primerAnio = 100 - (obs[2] ?? n);
  const lienzo2 = el("canvas", { role: "img", "aria-label": "Embudo de permanencia por semestre" });
  main.replaceChildren(
    cabecera("laboratorio", "Laboratorio de escenarios", "¿Qué pasaría con la deserción si la universidad aplica cada política? Proyecciones del modelo de simulación hasta 2030."),
    ayudaVista("laboratorio"),
    el("div", { class: "esc-rejilla" }, tarjetas),
    el("section", { class: "tarjeta" }, el("h2", {}, icono("tablero"), "Deserción por periodo: lo real y cada escenario"), conm, el("div", { class: "grafica" }, lienzo),
      el("p", { class: "sub" }, "La línea gris es lo que pasó de verdad. Desde 2026-1 cada escenario aplica su política; antes de esa fecha todos coinciden.")),
    el("section", { class: "tarjeta", style: null }, el("h2", {}, icono("reloj"), "Máquina del tiempo"),
      el("p", { class: "sub" }, "Mueve el control para ver cómo estaría el programa en cada semestre proyectado."),
      el("div", { class: "maquina" }, el("span", { class: "sub" }, horizonte[0]), rango, el("span", { class: "sub" }, horizonte[horizonte.length - 1]), salida), foto),
    el("section", { class: "tarjeta" }, el("h2", {}, icono("embudo"), "De cada 100 estudiantes que entran, ¿cuántos siguen en cada semestre?"),
      el("div", { class: "embudo-dato" }, el("span", { class: "grande" }, fmt(llegan, 0)), el("div", {}, el("b", {}, "llegan a décimo semestre"),
        el("p", { class: "sub" }, `En el primer año se pierden cerca de ${fmt(primerAnio, 0)} de cada 100: por eso la cola de Bienestar prioriza los primeros semestres.`))),
      el("div", { class: "grafica" }, lienzo2),
      el("p", { class: "ayuda-campo" }, "Aproximación encadenando la tasa de deserción observada en cada semestre (reporte «Deserción por semestre»); no descuenta rezagos ni reingresos.")));
  pintarFoto(); contarValores(main);
  const opc = { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
    plugins: { legend: { display: false }, tooltip: { backgroundColor: COLOR.verdeOsc, padding: 10, cornerRadius: 8 } },
    scales: { x: { ticks: { maxTicksLimit: 10 }, grid: { display: false } }, y: { grid: { color: cssVar("--linea") }, ticks: { callback: (v) => v + " %" } } } };
  const gris = cssVar("--gris-2") || "#6b746f";
  const datasets = [{ label: "Real", data: series[0].serie.map((s) => (s.real ? +(100 * s.real.desercion_periodo).toFixed(2) : null)), borderColor: gris, backgroundColor: gris, pointRadius: 2.5, borderWidth: 2.5, tension: .3 },
    ...nombres.map((nm2, i) => ({ label: nm2, data: series[i].serie.map((s) => (s.simulado ? +(100 * s.simulado.desercion_periodo).toFixed(2) : null)), borderColor: COLORES_ESC[i % COLORES_ESC.length], borderWidth: 2.5, pointRadius: 0, tension: .3, borderDash: i === 0 ? [6, 4] : [] }))];
  grafica(lienzo, { type: "line", data: { labels: periodos, datasets }, options: opc });
  const g = graficas[graficas.length - 1];
  datasets.forEach((d, i) => {
    const b = el("button", { type: "button", class: "conmutador", "aria-pressed": "true" }, el("i", {}), d.label);
    b.style.setProperty("--c", d.borderColor);
    b.addEventListener("click", () => { const vis = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", String(vis)); if (g) { g.setDatasetVisibility(i, vis); g.update(); } });
    conm.append(b);
  });
  grafica(lienzo2, { type: "bar", data: { labels: filas.map((f) => "Sem. " + f[0]), datasets: [
    { type: "bar", label: "Observado en el sistema", data: obs, backgroundColor: obs.map((_, i) => `rgba(0,123,62,${1 - i * 0.06})`), borderRadius: 8 },
    { type: "line", label: "Modelo calibrado", data: mod, borderColor: COLOR.oro, backgroundColor: COLOR.oro, borderWidth: 2.5, pointRadius: 3, tension: .3 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } } },
      scales: { y: { min: 0, max: 100, grid: { color: cssVar("--linea") }, title: { display: true, text: "Estudiantes de cada 100" } }, x: { grid: { display: false } } } } });
}
