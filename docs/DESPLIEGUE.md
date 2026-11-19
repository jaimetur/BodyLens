# Despliegue de BodyLens en el Synology (pasos para Jaime)

Lo que tienes que hacer tú, fuera del código. El agente prepara el resto.

## Antes de empezar (una vez)

1. **Crear el repositorio privado** en GitHub (p. ej. `bodylens`) y subir este paquete tal cual
   (sin el zip de datos privados).
2. **Copia fresca de tus datos**: abre BodyLens en claude.ai → **Ajustes → Copia de seguridad → Copia completa (JSON)**.
   Guárdala junto a `snap.json` del zip de datos privados. **No los subas a GitHub.**
3. **Cuenta de servicio de Google** (solo para la fase 1):
   - Google Cloud Console → crea un proyecto → habilita **Google Drive API** → crea una *cuenta de servicio* →
     descarga su clave JSON.
   - Comparte la hoja «Peso Jaime 2026» con el correo de la cuenta de servicio, como **lector**.
   - Ese JSON irá en el NAS en `/volume1/docker/bodylens/data/secrets/google-sa.json`.

## En el Synology

1. Carpeta `/volume1/docker/bodylens/` con `compose.yml` (lo genera el agente en `docker/compose.yml`),
   `.env` (a partir de `.env.example`) y la carpeta `data/`.
2. Container Manager → **Proyecto** → crear desde esa carpeta (o `docker compose up -d` por SSH).
   La imagen se descarga de `ghcr.io/<tu-usuario>/bodylens:latest`. Como el repo es privado, antes haz
   `docker login ghcr.io` con un token de GitHub con permiso `read:packages`.
3. Sembrar los datos (una vez), con los ficheros copiados en `data/import/`:
   `docker compose exec bodylens python -m app.seed /data/import/snap.json`
   `docker compose exec bodylens python -m app.seed /data/import/Bascula-copia-AAAA-MM-DD.json`
4. **Proxy inverso**: Panel de control → Portal de inicio de sesión → Avanzado → Proxy inverso →
   origen `https://bodylens.<tu-dominio>:443` → destino `http://localhost:8000`. Certificado de Let's Encrypt
   para ese dominio.
5. Abre `https://bodylens.<tu-dominio>`, entra con tu contraseña y, en el iPhone, **Compartir → Añadir a pantalla
   de inicio** para tenerla como app.

## Fase 2 (cuando el agente tenga listo el port del Apps Script)

1. **Withings**: en developer.withings.com, en tu aplicación, añade la *callback URL*
   `https://bodylens.<tu-dominio>/oauth/withings/callback`. Pon `WITHINGS_CLIENT_ID` y `WITHINGS_CLIENT_SECRET`
   en el `.env` del NAS, reinicia y entra en `https://bodylens.<tu-dominio>/oauth/withings/start` para autorizar.
2. **Health Auto Export**: en cada automatización cambia la URL a
   `https://bodylens.<tu-dominio>/api/ingest/hae?token=<HAE_TOKEN>`.
   En la de **sueño sin resumir**, deja el rango de fechas en **últimos 2–7 días** (no «desde la última
   sincronización»), para que lleguen las noches que el Watch o AutoSleep guardan tarde.
3. Comprueba en el estado de las fuentes que llegan pesadas y envíos de Salud. Cuando todo cuadre unos días,
   borra los activadores del Apps Script y deja la hoja como copia.

## Actualizar la app

Cada push a `main` genera una imagen nueva. En el NAS: Container Manager → Proyecto → **Acción → Compilar**
(o `docker compose pull && docker compose up -d`). Con Watchtower se actualiza sola.
