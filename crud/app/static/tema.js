/* Aplica el tema guardado (claro u oscuro) antes de pintar la página, para evitar un parpadeo. */
try { if (localStorage.getItem("tema") === "oscuro") document.documentElement.dataset.tema = "oscuro"; } catch (e) { /* sin almacenamiento */ }
