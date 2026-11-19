# AGENTS.md — BodyLens

Instrucciones para agentes de código (Codex, Claude Code…) que trabajen en este repositorio.
Lee también `docs/MIGRACION.md` (el plan completo) antes de tocar nada.

## Qué es

BodyLens es la app personal de salud de Jaime: peso y composición (báscula Withings), actividad, sueño,
corazón, comidas, ciclo, ánimo… Hoy vive como **artefacto de claude.ai** (una sola página HTML) alimentado por
una **hoja de Google** que rellena un **Google Apps Script** (Withings + Health Auto Export desde el iPhone).

El objetivo de este repo es **pasarla a un contenedor Docker en el servidor de Jaime** (Synology DS920+, x86_64),
con los datos **actualizándose solos cada 15 minutos**, sin tener que pulsar «Actualizar».

## Estructura

```
frontend/src/app_a.html   estilos + HTML de todas las vistas
frontend/src/app_b.html   núcleo: parseo de la hoja (XLSX), modelo, métricas
frontend/src/app_c.html   interfaz: vistas, gráficas SVG, sincronización, ajustes
frontend/build_artifact.py  une a+b+c (versión artefacto; solo referencia)
frontend/tests/snaptest.js  arranque de la página en jsdom (referencia)
legacy/apps-script/Codigo.gs  el Apps Script en producción hoy (REFERENCIA de toda la lógica de datos)
legacy/salud-scripts/       scripts sueltos de importación de Apple Salud (referencia)
branding/                   iconos y logo
docs/                       plan de migración, despliegue, tarea y traspaso original
```

Lo que hay que crear está descrito en `docs/MIGRACION.md` (backend FastAPI, capa `window.claude`, Docker, CI).

## Reglas

1. **El diseño no se toca.** La interfaz de `frontend/src/` debe verse y comportarse igual. Los cambios en el
   frontend se limitan a lo imprescindible para funcionar fuera de claude.ai (ver «capa de compatibilidad»).
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
pytest -q                                              # tests del backend
node frontend/tests/smoke.mjs                          # la página arranca con la capa de compatibilidad
```

## Definición de terminado (para cualquier PR)

- `pytest` en verde y la prueba de arranque del frontend sin errores.
- La imagen se construye (`docker build -f docker/Dockerfile .`).
- Ningún secreto ni dato personal añadido al repo.
- Si cambia el comportamiento, actualizado `docs/MIGRACION.md` o `docs/DESPLIEGUE.md`.
