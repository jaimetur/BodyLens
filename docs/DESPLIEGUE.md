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
2. **Cuenta `admin`**: el primer arranque crea una vez `admin` / `admin123`, y la pantalla de entrar la muestra
   mientras conserve esa contraseña. Entra con ella o con la tuya y cámbiala.
   **Tu cuenta** se crea sola al arrancar con la base vacía: usuario `BODYLENS_ADMIN_USER` (`jaimetur`) y contraseña
   provisional `BODYLENS_ADMIN_PASSWORD` (`bodylens` si no se cambia en el `.env`). Al entrar la primera vez la app
   pide tu propia contraseña (mínimo 4 caracteres) y deja cambiar usuario y nombre.
3. **Tus datos**: en `/cuenta` → **Importar datos**, elige `snap.json` (o la «Copia completa (JSON)» de Ajustes →
   Copia de seguridad del artefacto) y en «¿Qué datos de la copia son tuyos?» deja el perfil principal.
   (También por consola: `docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario jaimetur`.)
4. **Peticiones de acceso**: en la pantalla de entrar, «¿No tienes cuenta? Pide una» crea la cuenta inactiva y avisa
   por correo a las cuentas administradoras con correo (el tuyo: `BODYLENS_ADMIN_EMAIL` o «Tu cuenta»). Se aprueban
   o rechazan en `/cuenta` → Administración → Peticiones de acceso, y la persona recibe un correo.
   Correo saliente: variables `SMTP_*` del `.env` (`bodylens@jaimetur.cloud`, `jaimetur.cloud:465` SSL); la
   contraseña solo en el `.env` del NAS. «Enviarme un correo de prueba» en Administración lo comprueba.
5. Fuentes de tu cuenta (fase 1): en `/cuenta` → Administración → tu cuenta → ID de la hoja y URL del Apps Script.
6. **Laura**: crea una invitación en `/cuenta` (Administración → Crear invitación) y mándale el enlace. Cuando tenga su
   cuenta, ella entra en `/cuenta` → Importar datos con el mismo `snap.json` y elige **Laura Romero**.
   Después, uno de los dos pide **unir las cuentas** en `/cuenta` → Pareja y el otro lo acepta.
7. **Caddy**: añade al `Caddyfile` del stack `caddy` un bloque como los de las otras apps y define el puerto en su `.env`:
   ```
   {$CADDY_HOST}:{$BODYLENS_HTTPS_PORT} {
     import tls_profile
     reverse_proxy {$UPSTREAM_HOST}:7280
   }
   ```
   (o un subdominio propio). Pon esa dirección en `PUBLIC_URL` del `.env` de BodyLens (para los enlaces de invitación).
8. En el iPhone: abre la dirección, entra y **Compartir → Añadir a pantalla de inicio**.

## Despliegues siguientes (los hace el agente)

El stack del NAS monta el código desde `/volume1/docker/stacks/bodylens/code` (`docker/compose.hot.yml`), así que
**los cambios se ven en segundos, sin esperar a una imagen nueva**:

```bash
tools/deploy.sh
```

- Copia el commit actual (solo lo que está en git) a `code/` por SSH y escribe `code/REVISION`.
- Si cambia el backend, reinicia el contenedor (unos segundos); si solo cambia la página, ni eso.
- Si cambian dependencias (`pyproject.toml`), el Dockerfile o las librerías de la página (`package*.json`), espera
  a la imagen nueva de GitHub Actions y la baja (`docker compose pull` + `up -d`). `tools/deploy.sh --imagen` lo fuerza.
- Las páginas abiertas avisan «BodyLens se ha actualizado» con un botón para recargar.

Necesita, una vez, una regla de sudo en el NAS para que el usuario de SSH pueda usar Docker sin contraseña
(`/etc/sudoers.d/bodylens-deploy`: `jaimetur_adm ALL=(root) NOPASSWD: /usr/local/bin/docker`, permisos 440).

## Fase 2: Withings y Apple Salud directos (sin la hoja de Google)

1. **Withings** (una vez, como administrador): en developer.withings.com, en tu aplicación, añade la *callback URL*
   `https://<bodylens>/oauth/withings/callback`. Copia su *Client ID* y *Client secret* en BodyLens → Administración →
   Withings (o `WITHINGS_CLIENT_ID` / `WITHINGS_CLIENT_SECRET` en el `.env`).
2. **Cada cuenta**: Tu cuenta → Fuentes de datos → **Conectar Withings**. La primera vez, la cuenta pasa a tener sus datos
   en el servidor: antes se importa entera su hoja de Google (si tenía) para no perder historial.
3. **Cada cuenta**: Tu cuenta → Fuentes de datos → **Crear mi dirección de envío** y ponerla en todas las automatizaciones de
   Health Auto Export (sueño sin resumir: últimos 2–7 días).
4. Cuando todo llegue bien unos días, se pueden borrar los activadores del Apps Script, la cuenta de servicio de Google
   y la hoja (queda como copia).

## App de Android (Health Connect)

El código está en `android/` (Kotlin + Jetpack Compose). Lee Health Connect y envía a la misma dirección de Health Auto
Export (`/api/ingest/hae/<token>`) con el mismo formato JSON, así que el servidor no distingue de dónde viene.

- Cada push que cambia `android/` lo compila GitHub Actions (`.github/workflows/android.yml`) y deja el APK en la release
  `android-latest` del repositorio.
- `tools/deploy-android.sh` espera a ese build, baja el APK y lo deja en el NAS en
  `/volume1/docker/data/bodylens/downloads/bodylens-android.apk`; la app lo sirve en `/android.apk` (con sesión iniciada).
- Firma: sin secretos se firma con una clave de depuración (vale para instalarla, pero cada build de CI tiene una clave distinta y
  habría que desinstalar para actualizar). Para firmar siempre igual, guarda en los secretos del repositorio
  `ANDROID_KEYSTORE_B64` (el `.jks` en base64), `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` y `ANDROID_KEY_PASSWORD`.

## Copia de seguridad

Todo lo de la app está en `/volume1/docker/data/bodylens` (incluye `bodylens.db`): basta con incluir esa carpeta en
Hyper Backup. (Fase 3: copia diaria automática dentro de `backups/`.)
