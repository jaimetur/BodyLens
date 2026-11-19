# Deploying BodyLens on the NAS (Synology DS920+)

Image: `jaimetur/bodylens` on Docker Hub (built by GitHub Actions on every push to `main`).
Dockhand stack: `/volume1/docker/stacks/bodylens` (`compose.yml` + `.env`).
Data: `/volume1/docker/data/bodylens` (SQLite database, each account's workbooks, `secrets/`, `import/`).
Port on the NAS: **7280** → 8000 of the container. HTTPS: `https://bodylens.jaimetur.cloud` (the NAS reverse proxy).
The server runs as `docker_limited:docker_users` (`PUID=1034`, `PGID=65544`): on Synology the ACLs rule, and the
data folder only grants write access to `docker_users`/`administrators`. If the container does not start and the log says it
cannot write to `/data`, check PUID/PGID.

## Once, before the first deployment

1. **Docker Hub secret in the repo** (GitHub → BodyLens → Settings → Secrets and variables → Actions):
   `DOCKERHUB_TOKEN` (the same Docker Hub access token that DriveTestAnalyzer uses) and, if the Docker Hub user
   is not `jaimetur`, `DOCKERHUB_USERNAME`. With that the workflow publishes `jaimetur/bodylens:latest`.
2. **Docker Hub repository**: the first push creates `jaimetur/bodylens` as **public** unless you create it beforehand as
   private. The image carries the code (no data or secrets). If you want it private, create it private on Docker Hub and
   run `docker login` on the NAS so that Dockhand can pull it.
3. **Google service account** (phase 1 only, bridge with the sheet):
   Google Cloud Console → project → enable **Google Drive API** → create a *service account* → download its JSON
   key → save it on the NAS as `/volume1/docker/data/bodylens/secrets/google-sa.json`.
   Share the "Peso Jaime 2026" sheet with the service account's email, as **viewer**.

## First deployment (manual, with Dockhand)

1. In Dockhand, stack `bodylens` from `/volume1/docker/stacks/bodylens` → **Deploy** (pulls the image from Docker Hub).
2. **`admin` account**: the first start creates `admin` / `admin123` once, and the sign-in screen shows it
   while it keeps that password. Sign in with it or with your own and change it.
   **Your account** is created automatically on start-up with an empty database: username `BODYLENS_ADMIN_USER` (`jaimetur`) and
   temporary password `BODYLENS_ADMIN_PASSWORD` (`bodylens` if not changed in the `.env`). On first sign-in the app
   asks for your own password (minimum 4 characters) and lets you change username and name.
3. **Your data**: in `/cuenta` → **Import data**, choose `snap.json` (or the "Full backup (JSON)" from Settings →
   Backup of the artifact) and under "Which data in the backup is yours?" leave the main profile.
   (Also from the console: `docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario jaimetur`.)
4. **Access requests**: on the sign-in screen, "Don't have an account? Request one" creates the inactive account and notifies
   by email the administrator accounts that have an email (yours: `BODYLENS_ADMIN_EMAIL` or "Your account"). They are approved
   or rejected in `/cuenta` → Administration → Access requests, and the person receives an email.
   Outgoing email: `SMTP_*` variables in the `.env` (`bodylens@jaimetur.cloud`, `jaimetur.cloud:465` SSL); the
   password only in the NAS `.env`. "Send me a test email" in Administration checks it.
5. Your account's sources (phase 1): in `/cuenta` → Administration → your account → sheet ID and Apps Script URL.
6. **Laura**: create an invitation in `/cuenta` (Administration → Create invitation) and send her the link. Once she has her
   account, she goes to `/cuenta` → Import data with the same `snap.json` and chooses **Laura Romero**.
   After that, one of you requests to **link the accounts** in `/cuenta` → Partner and the other accepts.
7. **Caddy**: add to the `Caddyfile` of the `caddy` stack a block like those of the other apps and define the port in its `.env`:
   ```
   {$CADDY_HOST}:{$BODYLENS_HTTPS_PORT} {
     import tls_profile
     reverse_proxy {$UPSTREAM_HOST}:7280
   }
   ```
   (or a subdomain of its own). Put that address in `PUBLIC_URL` of BodyLens' `.env` (for the invitation links).
8. On the iPhone: open the address, sign in and **Share → Add to Home Screen**.

## Subsequent deployments (done by the agent)

The NAS stack mounts the code from `/volume1/docker/stacks/bodylens/code` (`docker/compose.hot.yml`), so
**changes show up in seconds, without waiting for a new image**:

```bash
tools/deploy.sh
```

- Copies the current commit (only what is in git) to `code/` over SSH and writes `code/REVISION`.
- If the backend changes, it restarts the container (a few seconds); if only the page changes, not even that.
- If dependencies (`pyproject.toml`), the Dockerfile or the page's libraries (`package*.json`) change, it waits
  for the new GitHub Actions image and pulls it (`docker compose pull` + `up -d`). `tools/deploy.sh --imagen` forces it.
- Open pages show "BodyLens has been updated" with a button to reload.

It needs, once, a sudo rule on the NAS so that the SSH user can use Docker without a password
(`/etc/sudoers.d/bodylens-deploy`: `jaimetur_adm ALL=(root) NOPASSWD: /usr/local/bin/docker`, permissions 440).

## Phase 2: direct Withings and Apple Health (without the Google sheet)

1. **Withings** (once, as administrator): at developer.withings.com, in your application, add the *callback URL*
   `https://<bodylens>/oauth/withings/callback`. Copy its *Client ID* and *Client secret* into BodyLens → Administration →
   Withings (or `WITHINGS_CLIENT_ID` / `WITHINGS_CLIENT_SECRET` in the `.env`).
2. **Each account**: Your account → Data sources → **Connect Withings**. The first time, the account starts having its data
   on the server: its Google sheet is first imported in full (if it had one) so no history is lost.
3. **Each account**: Your account → Data sources → **Create my upload address** and put it in all the Health Auto Export
   automations (sleep not summarised: last 2–7 days).
4. Once everything has arrived fine for a few days, the Apps Script triggers, the Google service account
   and the sheet can be deleted (it stays as a copy).

## Android app (Health Connect)

The code is in `android/` (Kotlin + Jetpack Compose). It reads Health Connect and posts to the same Health Auto
Export address (`/api/ingest/hae/<token>`) with the same JSON format, so the server cannot tell where it comes from.

- Every push that changes `android/` is built by GitHub Actions (`.github/workflows/android.yml`) and the APK is left in the
  repository's `android-latest` release.
- `tools/deploy-android.sh` waits for that build, downloads the APK and leaves it on the NAS at
  `/volume1/docker/data/bodylens/downloads/bodylens-android.apk`; the app serves it at `/android.apk` (when signed in).
- Signing: without secrets it is signed with a debug key (fine to install it, but each CI build has a different key and
  you would have to uninstall to update). To always sign the same way, store in the repository secrets
  `ANDROID_KEYSTORE_B64` (the `.jks` in base64), `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` and `ANDROID_KEY_PASSWORD`.

## Backup

Everything of the app is in `/volume1/docker/data/bodylens` (including `bodylens.db`): just include that folder in
Hyper Backup. (Phase 3: automatic daily backup inside `backups/`.)

## Help and automatic translation

The Help section of the app shows `help/en/`, `README.md` and `CHANGELOG.md`, translated automatically into each
account's language with the Claude API. Set the Anthropic API key in **Administration → Translator** (stored
encrypted in the database) or as `ANTHROPIC_API_KEY` in the `.env`. Translations are kept in
`/data/translations/<lang>/` and made again only when the English text changes. Without a key, the help is shown in
English. The documents are read from `DOCS_DIR` (`/app/docs` in the image, `/app/code` with hot deployment).
