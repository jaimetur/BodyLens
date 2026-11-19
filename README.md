# BodyLens

**BodyLens** es una app web de salud personal y multiusuario. Reúne en un solo sitio el peso y la composición
corporal de la báscula **Withings** y lo que registra el iPhone y el Apple Watch en **Apple Salud** (sueño,
actividad, pulso, VFC, SpO2, VO2 máx, ECG, ciclo, ánimo…). Se instala con Docker en un servidor propio, los datos se
actualizan solos cada 15 minutos y cada persona ve solo los suyos.

Nació como un artefacto de claude.ai alimentado por una hoja de Google; este repositorio es su versión autoalojada,
con el mismo diseño.

## Qué hace

- **Resumen**: peso de tendencia, progreso del plan, «hoy de un vistazo» (preparación, sueño, saldo de sueño, VFC,
  pasos) y avisos y conclusiones automáticas.
- **Peso**: tendencia suavizada, plan con ritmos objetivo, proyección, semanas, calendario e hitos.
- **Cuerpo**: composición (grasa, músculo, agua, hueso), IMC/FFMI con rangos por edad y sexo, medidas con cinta,
  corazón (pulso en reposo, VFC, SpO2, VO2 máx, ECG, avisos de frecuencia) y bienestar.
- **Actividad**: pasos, calorías, minutos de ejercicio con anillos y objetivos, entrenamientos y su relación con el peso.
- **Sueño**: última noche con fases, saldo de sueño de 7 noches, siestas, horario objetivo y análisis. Mezcla AutoSleep
  y Apple Watch con reglas propias (ventana 17:00→17:00, desvelos, siestas).
- **Comidas**: nota diaria de lo que comes y su efecto estimado en el peso.
- **Íntimo**: ciclo (con previsión), sexualidad y ánimo, protegidos con un PIN privado.
- **Historial**: años de pesadas, intentos de pérdida de peso y rebotes.
- **PDF**: informe del periodo elegido; **copias** completas en JSON y CSV.
- **Interfaz**: claro y oscuro, pensada para el iPhone (se instala como app desde Safari), gestos y periodo sincronizado.

### Cuentas
- **Varias cuentas**, cada una con sus datos. Se entra con usuario y contraseña (cookie de sesión segura).
- **Alta**: petición desde la pantalla de entrar que aprueba la administración (con avisos por correo) o enlace de
  invitación de un solo uso.
- **Pareja**: dos cuentas pueden unirse para compartir y editar juntas los registros de ciclo e intimidad.
- **Importar**: el `snap.json` o la copia completa de la versión anterior, desde «Tu cuenta».
- **Perfiles**: dentro de una cuenta se mantienen los perfiles de la app (con PIN).

### Datos que llegan solos
- **Ahora (fase 1)**: cada 15 minutos el servidor dispara el Apps Script de la hoja de Google de cada cuenta (que trae
  Withings y Health Auto Export) y descarga la hoja; la página abierta se refresca sola.
- **Siguiente (fase 2)**: Withings (OAuth por cuenta) y Health Auto Export directos al servidor, sin Google.

## Cómo está hecho

```
navegador / iPhone (PWA) ── HTTPS (proxy inverso del NAS) ──► contenedor BodyLens
                                                              FastAPI + SQLite + planificador cada 15 min
                                                              │
                                     fase 1: Apps Script + Google Drive (cuenta de servicio)
```

- **Frontend**: la misma página del artefacto (`src/frontend/app/`), servida sin cambios en sus ficheros. El servidor
  le añade una capa (`src/frontend/compat/claude-shim.js`) que imita lo que la página pedía a claude.ai (`db`, `user`,
  `mcp`, `downloads`) contra la API propia, y aplica unas pocas sustituciones exactas (librerías sin CDN, botón de
  sincronizar, textos).
- **Backend**: Python 3.12, FastAPI, SQLite (WAL) en `/data`, un solo proceso con el planificador dentro.
- **Seguridad**: contraseñas argon2, sesiones en servidor (cookie HttpOnly/Secure/SameSite), cabecera anti-CSRF en
  toda escritura, límites de intentos, cada cuenta aislada; secretos solo en variables de entorno.

## Estructura del repositorio

```
src/backend/app/        servidor (paquete «app»), un subpaquete por módulo:
  core/                 configuración, SQLite, seguridad, dependencias de las rutas
  accounts/             cuentas, sesiones, invitaciones, peticiones de acceso, CLI de administración
  couples/              pareja
  data/                 documentos de cada cuenta e importación de copias
  sync/                 sincronización, libro XLSX y planificador
  mail/                 correo SMTP
  web/                  montaje de la página y ficheros estáticos
src/frontend/
  app/                  la app (app_a: estilos y vistas, app_b: núcleo, app_c: interfaz)
  compat/               capa window.claude
  accounts/ common/     páginas de entrar, pedir cuenta, registro y «Tu cuenta»
assets/branding/        iconos y logo
tests/<módulo>/         tests (pytest) y tests/frontend/smoke.mjs (arranque de la página)
help/                   ayuda de uso, un fichero por módulo
docker/                 Dockerfile, compose del NAS y de desarrollo
docs/                   plan de migración, despliegue y traspaso
legacy/                 Apps Script y scripts de Salud (referencia de la lógica de datos)
```

## Desarrollo

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'
```
```bash
.venv/bin/python -m pytest -q
```
```bash
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs
```
```bash
docker compose -f docker/compose.dev.yml up --build
```
La última orden levanta http://localhost:8000 con recarga automática del backend y la página servida desde `src/`.

## Despliegue

Cada push a `main` pasa los tests y publica la imagen `jaimetur/bodylens` (amd64 y arm64) en Docker Hub. En el
servidor: `docker/compose.yml` + `.env` (a partir de `.env.example`). Pasos completos en
[`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).

## Documentación

- Ayuda de uso: [`help/`](help/README.md)
- Plan de migración y arquitectura: [`docs/MIGRACION.md`](docs/MIGRACION.md)
- Instrucciones para agentes de código: [`AGENTS.md`](AGENTS.md)

Los datos personales nunca van al repositorio: bases de datos, copias JSON y `.env` están en `.gitignore`.
