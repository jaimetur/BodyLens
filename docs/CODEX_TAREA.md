# Tarea para el agente (Codex / Claude Code)

> Actualizada el 19 nov 2026: multiusuario con invitaciones, cuentas unidas en pareja e imagen en Docker Hub
> (ver `docs/MIGRACION.md` §0). Fases 0 y 1 hechas.

---

Eres el desarrollador de **BodyLens**, la app personal de salud de Jaime. Hoy es un artefacto de claude.ai
(una sola página HTML en `frontend/src/app_a.html` + `app_b.html` + `app_c.html`) que lee una hoja de Google
alimentada por un Google Apps Script (`legacy/apps-script/Codigo.gs`).

**Objetivo:** migrarla a un contenedor Docker que Jaime desplegará en su Synology DS920+, con los datos
**actualizándose solos cada 15 minutos** y el mismo diseño.

Lee primero, en este orden: `AGENTS.md`, `docs/MIGRACION.md` (plan completo, arquitectura, API, fases y criterios
de aceptación) y `docs/DESPLIEGUE.md`. Sigue sus reglas: no rediseñar el frontend, textos en español de España,
ningún secreto ni dato personal en el repo, zona horaria Europe/Madrid.

Haz el trabajo por fases, cada una en su propio PR (o commits claramente separados), con tests:

1. **Fase 0** — `docker/Dockerfile`, `docker/compose.yml`, `docker/compose.dev.yml`, `.env.example` completo y
   `.github/workflows/docker.yml` (tests + build multi-arch amd64/arm64 + push a Docker Hub con etiquetas
   `latest`, `sha-<7>` y `v*`).
2. **Fase 1** — Backend FastAPI + SQLite: cuentas con invitación y pareja (MIGRACION §0), login, almacén de documentos (`/api/docs`), `claude-shim.js` que
   implementa `window.claude.use('user'|'db'|'mcp'|'downloads'|'artifact'|'permissions')` como se describe en
   `docs/MIGRACION.md` §3.2, servir la página con los cambios mínimos (botón Actualizar → `POST /api/sync`,
   librerías sin CDN, sin PACK), `python -m app.seed` para importar `snap.json` o la copia JSON de Ajustes, y el
   planificador cada `SYNC_INTERVAL_MIN` (15) que llama al Apps Script (`?accion=sincronizar`) y exporta la hoja a
   XLSX con la API de Drive (cuenta de servicio). La página abierta debe actualizarse sola cuando cambie el
   workbook (sondeo de `/api/workbook/meta` en el shim).
3. **Fase 2** — Port del Apps Script a Python: Withings (OAuth con refresh token rotatorio, pesadas, composición,
   actividad, entrenos, sueño, SpO2/VO2, ECG; siempre repedir las 3 últimas noches) y Health Auto Export
   (`POST /api/ingest/hae?token=`, un token y un OAuth de Withings **por cuenta**, port completo de `doPost` y de las reglas de sueño: mezcla AutoSleep + Apple
   Watch, desvelos, siestas, reenvíos que corrigen tramos). Tablas SQLite con las mismas columnas que las pestañas
   de la hoja; el workbook se genera desde ellas con las mismas cabeceras. Importador único de la hoja actual.
   Tests de paridad y de las reglas de sueño con fixtures sintéticos (casos listados en `docs/MIGRACION.md` §7.5).
4. **Fase 3** — Estado de las fuentes en la app, copia diaria de la base y documentación actualizada.

Para comprobar el frontend sin navegador puedes adaptar `frontend/tests/snaptest.js` (jsdom) a una prueba
`frontend/tests/smoke.mjs` que cargue la página servida con el shim y un backend de prueba.

Cuando algo no se pueda verificar sin las credenciales reales de Jaime (Withings, Google, Health Auto Export),
déjalo detrás de variables de entorno, con tests que simulen las respuestas (`respx`/fixtures), y anótalo en el PR.

Al terminar cada fase, resume en el PR: qué se ha hecho, cómo probarlo en local con
`docker compose -f docker/compose.dev.yml up`, y qué tiene que hacer Jaime (de `docs/DESPLIEGUE.md`).
