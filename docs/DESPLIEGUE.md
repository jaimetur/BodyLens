# Despliegue de BodyLens en el NAS (Synology DS920+)

Imagen: `jaimetur/bodylens` en Docker Hub (la construye GitHub Actions en cada push a `main`).
Stack de Dockhand: `/volume1/docker/stacks/bodylens` (`compose.yml` + `.env`).
Datos: `/volume1/docker/data/bodylens` (base SQLite, workbooks de cada cuenta, `secrets/`, `import/`).
Puerto en el NAS: **7280** → 8000 del contenedor. HTTPS: `https://bodylens.jaimetur.cloud` (proxy inverso del NAS).
El servidor corre como `docker_limited:docker_users` (`PUID=1034`, `PGID=65544`): en Synology mandan las ACL y la
carpeta de datos solo da escritura a `docker_users`/`administrators`. Si el contenedor no arranca y el log dice que no
puede escribir en `/data`, revisa PUID/PGID.

## Una vez, antes del primer despliegue

1. **Secreto de Docker Hub en el repo** (GitHub → BodyLens → Settings → Secrets and variables → Actions):
   `DOCKERHUB_TOKEN` (el mismo token de acceso de Docker Hub que usa DriveTestAnalyzer) y, si el usuario de Docker Hub
   no es `jaimetur`, `DOCKERHUB_USERNAME`. Con eso el workflow publica `jaimetur/bodylens:latest`.
2. **Repositorio de Docker Hub**: el primer push crea `jaimetur/bodylens` **público** salvo que lo crees antes como
   privado. La imagen lleva el código (no datos ni secretos). Si la quieres privada, créala privada en Docker Hub y
   haz `docker login` en el NAS para que Dockhand pueda descargarla.
3. **Cuenta de servicio de Google** (solo fase 1, puente con la hoja):
   Google Cloud Console → proyecto → habilita **Google Drive API** → crea una *cuenta de servicio* → descarga su clave
   JSON → guárdala en el NAS como `/volume1/docker/data/bodylens/secrets/google-sa.json`.
   Comparte la hoja «Peso Jaime 2026» con el correo de la cuenta de servicio, como **lector**.

## Primer despliegue (manual, con Dockhand)

1. En Dockhand, stack `bodylens` desde `/volume1/docker/stacks/bodylens` → **Deploy** (descarga la imagen de Docker Hub).
2. **Tu cuenta** se crea sola al arrancar con la base vacía: usuario `BODYLENS_ADMIN_USER` (`jaime`) y contraseña
   provisional `BODYLENS_ADMIN_PASSWORD` (`bodylens` si no se cambia en el `.env`). Al entrar la primera vez la app
   pide tu propia contraseña (mínimo 4 caracteres) y deja cambiar usuario y nombre.
3. **Tus datos**: en `/cuenta` → **Importar datos**, elige `snap.json` (o la «Copia completa (JSON)» de Ajustes →
   Copia de seguridad del artefacto) y en «¿Qué datos de la copia son tuyos?» deja el perfil principal.
   (También por consola: `docker exec bodylens python -m app.seed /data/import/snap.json --usuario jaime`.)
4. Fuentes de tu cuenta (fase 1): en `/cuenta` → Administración → tu cuenta → ID de la hoja y URL del Apps Script.
5. **Laura**: crea una invitación en `/cuenta` (Administración → Crear invitación) y mándale el enlace. Cuando tenga su
   cuenta, ella entra en `/cuenta` → Importar datos con el mismo `snap.json` y elige **Laura Romero**.
   Después, uno de los dos pide **unir las cuentas** en `/cuenta` → Pareja y el otro lo acepta.
6. **Caddy**: añade al `Caddyfile` del stack `caddy` un bloque como los de las otras apps y define el puerto en su `.env`:
   ```
   {$CADDY_HOST}:{$BODYLENS_HTTPS_PORT} {
     import tls_profile
     reverse_proxy {$UPSTREAM_HOST}:7280
   }
   ```
   (o un subdominio propio). Pon esa dirección en `PUBLIC_URL` del `.env` de BodyLens (para los enlaces de invitación).
7. En el iPhone: abre la dirección, entra y **Compartir → Añadir a pantalla de inicio**.

## Despliegues siguientes (los hace el agente)

Cada push a `main` → GitHub Actions (tests + imagen `latest`) → el agente despliega por `ssh nas`:
```
ssh nas 'cd /volume1/docker/stacks/bodylens && sudo -n /usr/local/bin/docker compose -p bodylens pull && sudo -n /usr/local/bin/docker compose -p bodylens up -d'
```
y comprueba que el contenedor `bodylens` queda `healthy`. Para que pueda hacerlo sin contraseña, una vez, como
administrador del NAS, crea `/etc/sudoers.d/bodylens-deploy` (`sudo visudo -f /etc/sudoers.d/bodylens-deploy`):
```
jaimetur_adm ALL=(root) NOPASSWD: /usr/local/bin/docker
```

## Fase 2 (cuando esté el port del Apps Script)

1. **Withings**: en developer.withings.com añade la *callback URL* `https://<bodylens>/oauth/withings/callback`, pon
   `WITHINGS_CLIENT_ID` y `WITHINGS_CLIENT_SECRET` en el `.env`, redepliega y autoriza desde la app (cada cuenta la suya).
2. **Health Auto Export**: cada cuenta tendrá su URL con token (`/api/ingest/hae?token=…`) en «Tu cuenta».
   En la automatización de **sueño sin resumir**, rango **últimos 2–7 días**.
3. Cuando todo cuadre unos días, se desactivan los activadores del Apps Script y la hoja queda como copia.

## Copia de seguridad

Todo lo de la app está en `/volume1/docker/data/bodylens` (incluye `bodylens.db`): basta con incluir esa carpeta en
Hyper Backup. (Fase 3: copia diaria automática dentro de `backups/`.)
