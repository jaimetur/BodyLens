# AGENTS.md — BodyLens

Instrucciones para agentes de código (Codex, Claude Code…) que trabajen en este repositorio.
Lee también `docs/MIGRACION.md` (el plan completo) antes de tocar nada.

## Qué es

BodyLens es la app de salud de Jaime (multiusuario: cada cuenta con sus datos, alta por invitación, cuentas unidas en
pareja que comparten ciclo e intimidad; ver `docs/MIGRACION.md` §0): peso y composición (báscula Withings), actividad, sueño,
corazón, comidas, ciclo, ánimo… Hoy vive como **artefacto de claude.ai** (una sola página HTML) alimentado por
una **hoja de Google** que rellena un **Google Apps Script** (Withings + Health Auto Export desde el iPhone).

El objetivo de este repo es **pasarla a un contenedor Docker en el servidor de Jaime** (Synology DS920+, x86_64),
con los datos **actualizándose solos cada 15 minutos**, sin tener que pulsar «Actualizar».

## Estructura

```
src/backend/app/            servidor FastAPI (paquete `app`), un subpaquete por módulo:
  main.py                   arranque, seguridad común y registro de las rutas de cada módulo
  core/                     configuración, SQLite, seguridad, dependencias de las rutas (sesión, admin)
  accounts/                 cuentas, sesiones, invitaciones, peticiones de acceso, «Tu cuenta», CLI de admin
  couples/                  unir y separar cuentas en pareja
  data/                     documentos de cada cuenta (el «db» de la app, con lo compartido en pareja) e importación
  sync/                     sincronización (fase 1: Apps Script + hoja de Google), libro XLSX y planificador
  mail/                     correo saliente por SMTP
  web/                      montaje de la página de la app y ficheros estáticos
src/frontend/
  app/app_a|b|c.html        la app (el mismo HTML que el artefacto: estilos+vistas, núcleo, interfaz) — no se edita
  compat/claude-shim.js     capa window.claude contra la API del servidor
  accounts/                 páginas de entrar, pedir cuenta, registro por invitación y «Tu cuenta»
  common/                   estilos y utilidades de esas páginas
  package.json              librerías servidas sin CDN (xlsx, jspdf, html2canvas-pro) y jsdom para la prueba
assets/branding/            iconos y logo (no cambian)
tests/<módulo>/             tests de cada módulo (pytest) y tests/frontend/smoke.mjs (arranque de la página en jsdom)
help/                       ayuda de uso, un fichero por módulo
docker/                     Dockerfile, compose.yml (NAS), compose.dev.yml (desarrollo), entrypoint
docs/                       plan de migración, despliegue, tarea y traspaso original
legacy/                     Apps Script en producción y scripts de Salud (REFERENCIA de la lógica de datos)
```

Lo que hay que crear está descrito en `docs/MIGRACION.md` (backend FastAPI, capa `window.claude`, Docker, CI).

## Reglas

1. **El diseño no se toca.** La interfaz de `src/frontend/app/` debe verse y comportarse igual. Los cambios en el
   frontend se limitan a lo imprescindible para funcionar fuera de claude.ai: sustituciones exactas en
   `src/backend/app/web/page.py` y la capa `src/frontend/compat/claude-shim.js`.
   Nada de reescribir la app en React/Vue ni de «limpiar» el código.
2. **Paridad de datos antes que mejoras.** Cada pieza portada del Apps Script debe producir los mismos
   resultados que el original (mismas filas, mismas reglas). Las reglas de sueño (mezcla AutoSleep + Apple Watch,
   desvelos, siestas, ventana de 17:00 a 17:00, etc.) están en `Codigo.gs` y se portan tal cual.
3. **Textos de la app en español de España.** Mensajes de error y de interfaz también.
4. **Secretos fuera del código.** Withings (client id/secret, tokens), token de Health Auto Export, contraseña,
   credenciales de Google: solo por variables de entorno o en la base de datos del servidor. Nunca en el frontend,
   nunca en el repositorio, nunca en logs.
5. **Datos personales fuera del repositorio.** `data/`, `*.db`, `snap.json`, copias JSON y exportaciones de Salud
   están en `.gitignore`. Los fixtures de tests deben ser sintéticos o mínimos.
6. **Zona horaria `Europe/Madrid`** para todo cálculo de días y noches (igual que la hoja).
7. Trabaja por fases (las de `docs/MIGRACION.md`), con commits pequeños y tests en cada una.

## Comandos (cuando existan)

```
docker compose -f docker/compose.dev.yml up --build    # desarrollo con recarga automática
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'   # entorno local (PyCharm usa .venv)
.venv/bin/python -m pytest -q                          # tests del backend
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs   # arranque de la página
```

## Definición de terminado (para cualquier PR)

- `pytest` en verde y la prueba de arranque del frontend sin errores.
- La imagen se construye (`docker build -f docker/Dockerfile .`).
- Se trabaja en la **rama de la versión actual** (p. ej. `0.1.0`), nunca directamente en `main` (Jaime la pone al día).
  Cada push a esa rama construye `jaimetur/bodylens:latest`. Tras el push y el build verde, desplegar en el NAS (ver `docs/DESPLIEGUE.md`, «Despliegues siguientes»)
  y comprobar que el contenedor `bodylens` queda `healthy`.
- Ningún secreto ni dato personal añadido al repo.
- Si cambia el comportamiento, actualizado `docs/MIGRACION.md` o `docs/DESPLIEGUE.md`.
