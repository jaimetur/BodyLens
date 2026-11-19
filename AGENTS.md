# AGENTS.md — BodyLens

Instrucciones para agentes de código (Codex, Claude Code…) que trabajen en este repositorio.

## Qué es

BodyLens es una app de salud multiusuario: peso y composición (báscula Withings), actividad, sueño, corazón,
comidas, ciclo, ánimo… Cada cuenta tiene sus datos; las cuentas se crean por invitación o por petición aprobada por
la administración, y dos cuentas pueden unirse en pareja para compartir y editar juntas el ciclo y la intimidad.

Corre en un contenedor Docker en el NAS de Jaime (Synology DS920+). Withings, Apple Salud (Health Auto Export) y
Android (Health Connect, app en `android/`) mandan los datos directamente al servidor. La página es la del antiguo
artefacto de claude.ai, servida con una capa de compatibilidad (`window.claude`) contra la API propia. El puente con
la hoja de Google (Apps Script) queda solo para cuentas que aún no se han pasado y se retirará.

## Estructura

```
src/backend/app/            servidor FastAPI (paquete `app`), un subpaquete por módulo:
  main.py                   arranque, seguridad común y registro de las rutas de cada módulo
  core/                     configuración, SQLite, seguridad, idiomas, copias de seguridad, dependencias
  accounts/                 cuentas, sesiones, invitaciones, peticiones de acceso, «Tu cuenta», CLI de admin
  admin/                    panel de Administración
  couples/                  unir y separar cuentas en pareja
  data/                     documentos de cada cuenta (el «db» de la app, con lo compartido en pareja) e importación
  sheets/                   las pestañas de datos en tablas del servidor y el libro XLSX que lee la página
  sources/                  Withings (OAuth) y Apple Salud / Android (envíos en formato Health Auto Export)
  sync/                     sincronización, puente con Google y planificador
  mail/                     correo saliente por SMTP
  web/                      montaje de la página de la app y ficheros estáticos
src/frontend/
  app/app_a|b|c.html        la app (el HTML del artefacto: estilos+vistas, núcleo, interfaz)
  compat/claude-shim.js     capa window.claude contra la API del servidor
  accounts/ admin/ common/  páginas de entrar, pedir cuenta, registro, «Tu cuenta» y Administración
  i18n/                     traductor, catálogo en inglés y un fichero por idioma
  package.json              librerías servidas sin CDN (xlsx, jspdf, html2canvas-pro) y jsdom para la prueba
android/                    app de Android (Health Connect → servidor)
assets/branding/            iconos y logo (no cambian)
tests/<módulo>/             tests de cada módulo (pytest) y tests/frontend/*.mjs (página y traductor en jsdom)
help/                       ayuda de uso, un fichero por módulo
docker/                     Dockerfile, compose.yml (NAS), compose.hot.yml, compose.dev.yml, entrypoint
docs/DESPLIEGUE.md          despliegue en el NAS
tools/                      despliegue, servidor de desarrollo y herramientas de traducción
```

## Trabajo pendiente

- Estado de las fuentes en «Tu cuenta»: último dato de cada tipo (pesada, noche, envío de Salud por tipo), última
  sincronización y errores.
- Retirar el puente con Google (Apps Script, cuenta de servicio, hoja) cuando Jaime lo confirme.

## Reglas

1. **El diseño no se toca.** La interfaz de `src/frontend/app/` debe verse y comportarse igual. Los cambios en el
   frontend se limitan a lo imprescindible para funcionar fuera de claude.ai: sustituciones exactas en
   `src/backend/app/web/page.py` y la capa `src/frontend/compat/claude-shim.js`.
   Nada de reescribir la app en React/Vue ni de «limpiar» el código. Los cambios de diseño que pida Jaime sí se
   hacen, con el mínimo cambio en `src/frontend/app/`.
2. **Paridad de datos antes que mejoras.** La lógica de datos viene del Apps Script original (`Codigo.gs`, ya fuera del
   repositorio) y está portada en `src/backend/app/sources/` y `src/backend/app/sheets/rules.py`, con sus tests. No se
   cambia sin motivo. Reglas que hay que conservar:
   - **Noche del día k**: la que acaba entre las 17:00 del día k-1 y las 17:00 del día k, y después de las 03:00 del
     día k; lo que acabe antes es siesta.
   - **Episodios**: ratos de sueño separados por más de 90 min son episodios distintos; dos episodios nocturnos
     (19:00–12:00) separados por ≤ 4 h se unen y el hueco cuenta como desvelo.
   - **Mezcla de la noche**: horario, tiempo dormido y desvelos de AutoSleep si lo hay; si no, del Apple Watch; si
     no, de la fuente con más sueño. Si el Watch registra claramente más (> 1,2 × AutoSleep + 15 min), manda el
     Watch. Profundo y REM salen del Watch.
   - **Reenvíos**: cada envío manda en el tramo de tiempo que cubre por fuente (lo que esa fuente ya no envía en ese
     intervalo se borra).
   - **Siestas**: episodios ≥ 10 min fuera de la noche. **Desvelos**: huecos ≥ 10 min dentro de la noche.
   - **Fuentes**: Apple Salud manda; Withings solo para peso y composición y para rellenar huecos.
3. **Textos de la app en español de España** (es el idioma de origen; se traducen a los demás). Mensajes de error y de
   interfaz también. Ver «Textos e idiomas».
4. **Secretos fuera del código.** Withings (client id/secret, tokens), token de Health Auto Export, contraseña,
   credenciales de Google: solo por variables de entorno o en la base de datos del servidor. Nunca en el frontend,
   nunca en el repositorio, nunca en logs.
5. **Datos personales fuera del repositorio.** `data/`, `*.db`, `snap.json`, copias JSON y exportaciones de Salud
   están en `.gitignore`. Los fixtures de tests deben ser sintéticos o mínimos.
6. **Zona horaria `Europe/Madrid`** para todo cálculo de días y noches (igual que la hoja).
7. Commits pequeños y con tests.
8. **Idioma del trabajo.** Con Jaime se habla **siempre en español** (mensajes, resúmenes, preguntas, informes).
   Los **comentarios del código** y los docstrings nuevos van **en inglés**; los que ya existen en español se dejan
   como están salvo que se reescriba ese código. Los textos que ve quien usa la app siguen la regla 3.

## Textos e idiomas

El **idioma base de las traducciones es el inglés**: `src/frontend/i18n/catalog.json` tiene todos los mensajes en
inglés y cada idioma es `src/frontend/i18n/locales/<idioma>.json` = `{"mensaje en inglés": "traducción"}` (las
partes variables son `{0}`, `{1}`…). Quien traduce solo necesita el inglés: ver `src/frontend/i18n/README.md`.

El código de la página está escrito en español, así que `locales/es.json` hace de puente: a cada mensaje inglés le
corresponde el texto español **tal cual está en el código** (o una lista, si varios textos españoles comparten el
mismo mensaje). El servidor compone con eso el diccionario del navegador (texto español → idioma elegido; si falta
una traducción, sale en inglés) y lo usa también para los correos. Idioma predeterminado de las cuentas: inglés.

Al añadir o cambiar textos visibles (página, páginas del servidor, mensajes de error, correos):
1. `python3 tools/i18n_extract.py` lista los textos del código que aún no tienen mensaje inglés (`i18n/new.json`).
2. Para cada uno, el mensaje inglés en `locales/es.json` (`{"English": "texto del código"}`) y
   `python3 tools/i18n_catalog.py` para rehacer `catalog.json`.
3. Las traducciones en todos los `locales/` (mismo tono y términos que el resto).
4. `python3 tools/i18n_check.py` tiene que dar OK (lo comprueba también `pytest`).

## Comandos (cuando existan)

```
tools/dev-data.sh && tools/dev.sh                      # desarrollo en caliente (http://localhost:8000) con copia de los datos del NAS
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'   # entorno local (PyCharm usa .venv)
.venv/bin/python -m pytest -q                          # tests del backend
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs   # arranque de la página
```

## Definición de terminado (para cualquier PR)

- `pytest` en verde y la prueba de arranque del frontend sin errores.
- La imagen se construye (`docker build -f docker/Dockerfile .`).
- Se trabaja en la **rama de la versión actual** (p. ej. `0.1.0`), nunca directamente en `main` (Jaime la pone al día).
  Cada push a esa rama construye `jaimetur/bodylens:latest`. Tras el push, desplegar en el NAS con `tools/deploy.sh`
  (en caliente; solo espera a la imagen si cambian dependencias o el Dockerfile) (ver `docs/DESPLIEGUE.md`, «Despliegues siguientes»)
  y comprobar que el contenedor `bodylens` queda `healthy`.
- Ningún secreto ni dato personal añadido al repo.
- Si cambia el despliegue, actualizado `docs/DESPLIEGUE.md`; si cambia el uso, la ayuda de `help/`.
- `CHANGELOG.md` al día: cada cambio que se note en la app, el servidor o el despliegue va en la versión actual
  (la de la rama), en su apartado (Breaking Changes, New Features, Enhancements, Bug fixes, Documentation), con el
  formato de las entradas que ya hay.
