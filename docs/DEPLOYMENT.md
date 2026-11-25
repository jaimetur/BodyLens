# Deploying BodyLens on the NAS (Synology DS920+)

Image: `jaimetur/bodylens` on Docker Hub (built by GitHub Actions on every push to `main`).
Dockhand stack: `/volume1/docker/stacks/bodylens` (`compose.yml` + `.env`).
Data: `/volume1/docker/data/bodylens` (SQLite database, each account's workbooks, `secrets/`, `import/`).
Port on the NAS: **7280** → 8000 of the container. HTTPS: `https://bodylens.jtgcloud.com` (the NAS reverse proxy).
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
   Outgoing email: `SMTP_*` variables in the `.env` (`bodylens@jtgcloud.com`, server `mail.jtgcloud.com:465` SSL); the
   password only in the NAS `.env`. "Send me a test email" in Administration checks it.
5. **Laura**: create an invitation in `/cuenta` (Administration → Create invitation) and send her the link. Once she has her
   account, she goes to `/cuenta` → Import data with the same `snap.json` and chooses **Laura Romero**.
   After that, one of you requests to **link the accounts** in `/cuenta` → Partner and the other accepts.
6. **Caddy**: add to the `Caddyfile` of the `caddy` stack a block like those of the other apps and define the port in its `.env`:
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

## Releases

Each version lives in a branch named after it (`0.1.0`, `0.2.0`…); every push to that branch builds
`jaimetur/bodylens:<version>` and `:latest`, the image the NAS runs. To start a new version, from the current version
branch:

```
python3 tools/CreateUpdateRelease.py            # window: Create New Release / Update Current Release
python3 tools/CreateUpdateRelease.py --create 0.2.0 2026-12-01 [--dirty commit|carry|discard]
python3 tools/CreateUpdateRelease.py --update 0.1.0 2026-11-20
```

- **Create New Release** checks that the branch does not exist (locally or on GitHub), then creates it, sets the
  version in `pyproject.toml` and the Android app's `versionName` (Play shows it as `X.Y.Z (<build>)`), adds an empty
  `## Release: vX.Y.Z` block on top of `CHANGELOG.md` and of `help/i18n/es/changelog.md` (stamped again), commits and
  pushes it. If there is uncommitted work it asks first: commit and push it to the current branch, carry it to the new
  one, or discard it (from the command line, `--dirty`; without it, it stops).
- **Update Current Release** only rewrites the version and date of the current release (no branch, no commit).
- After pushing, GitHub Actions builds the image; deploy it as usual with `tools/deploy.sh`.
- **Publishing a version on GitHub** (Releases), when it is finished: run the **🚀 Release** workflow on the version
  branch (Actions → 🚀 Release → Run workflow, or `gh workflow run release.yml --ref 0.1.0`), or push a tag `vX.Y.Z`.
  It creates the `vX.Y.Z` release with the notes of that version's block in `CHANGELOG.md`, the source code and the
  Android APK of the version; "final" makes it the latest release, otherwise it is a pre-release. Running it again
  recreates it on the current commit.
- The **Android app (rolling build)** pre-release (`android-latest`) is not a version: it is the APK rebuilt on every
  change in `android/`, which `tools/deploy-android.sh` copies to the NAS.
- If the Python has no Tk (Homebrew's, without `brew install python-tk@3.12`), it asks the same questions in the
  terminal instead of opening the window.

## Data sources: Withings, Apple Health and Android

1. **Withings** (once, as administrator): at developer.withings.com, in your application, add the *callback URL*
   `https://<bodylens>/oauth/withings/callback`. Copy its *Client ID* and *Client secret* into BodyLens → Administration →
   Withings (or `WITHINGS_CLIENT_ID` / `WITHINGS_CLIENT_SECRET` in the `.env`).
2. **Each account** connects its own sources in Your account → Data sources: step by step in the help, section
   *Sync* (also inside the app, in Help).

## Android app

The code is in `android/` (Kotlin). It is the whole of BodyLens: a native shell that shows the server's web app (so
every server deployment updates the app too), plus Health Connect (it posts to the account's Health Auto Export
address, `/api/ingest/hae/<token>`, in the same JSON format), downloads, the file picker, Android's back button and
Google Play subscriptions. It asks for the server address the first time (`https://bodylens.jtgcloud.com` by default).

- Two apps come from the same code (Gradle flavours): `full` is BodyLens (`app.bodylens.android`) and `bridge` is
  BodyLens Bridge (`app.bodylens.bridge`), which only sends Health Connect data; the server serves them at
  `/android.apk` and `/android-bridge.apk`.
- Every push that changes `android/` is built by GitHub Actions (`.github/workflows/android.yml`) and the APKs are left in the
  repository's `android-latest` release. A version release (`🚀 Release`) attaches the APK and the AAB (for Google Play).
- `tools/deploy-android.sh` waits for that build, downloads the APK and leaves it on the NAS at
  `/volume1/docker/data/bodylens/downloads/bodylens-android.apk`; the server serves it at `/android.apk`.
- **Signing**: Google Play needs every version signed with the same key. Run `tools/android-keystore.sh` once on your
  computer: it creates the key (`~/bodylens-upload.jks`) and stores it in the repository secrets
  (`ANDROID_KEYSTORE_B64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`). Keep the `.jks`
  and its password safe. Without the secrets, CI signs with a throwaway debug key (fine to try the APK, not for Play).
- **Google Play without uploading by hand**: with the secret `PLAY_SERVICE_ACCOUNT_JSON` (the JSON key of a Play
  Console service account with "Release apps to testing tracks" and "Manage store presence"), every build of a
  version branch also goes to Play (`tools/play_publish.py bundle`), named `X.Y.Z (<build>)`, to the track of the
  repository variable `PLAY_TRACK` (`alpha`, the closed test, by default; if your closed test is a track you created,
  its name). `gh secret set PLAY_SERVICE_ACCOUNT_JSON < key.json` stores it. If versionName is not the branch, the
  upload fails; without the secret, the workflow warns and uploads nothing. Mam-IA, BodyLens and MeetGo upload the
  same way.
- **Going to production**: a personal developer account needs a closed test with at least 12 testers for 14 days in a
  row, then Play Console → **Dashboard → Apply for production**. Once Google grants it:
  1. Play Console → **Users and permissions** → the service account → **App permissions → BodyLens**: add "Release
     to production, exclude devices, and use Play App Signing".
  2. Play Console → **Test and release → Production → Countries/regions**: add the countries (without them the upload
     to production fails).
  3. Switch the track: `gh variable set PLAY_TRACK --body production -R jaimetur/BodyLens`; the three apps at once:
     `for r in Mam-IA BodyLens MeetGo; do gh variable set PLAY_TRACK --body production -R jaimetur/$r; done`.
  4. Try it: **Actions → 🤖 Android app → Run workflow** on the version branch; the log ends with
     "X.Y.Z (N) uploaded to the production track".

  From then on every build of a version branch goes to production, to every user as soon as Google approves it (no
  staged rollout: with few users it adds nothing and the percentage would have to be raised by hand). The closed test
  needs no upload of its own: Play gives each person the highest version of the tracks they can use, so testers get
  the production one too. To try a version before everyone gets it, go back to the closed test
  (`gh variable delete PLAY_TRACK -R jaimetur/BodyLens`) and promote it by hand in Play Console.
- **Store listing**: texts per language in `assets/play-store/listings/`; screenshots of every language, phone, tablet
  and Chromebook, taken again by GitHub Actions whenever the app changes (`play-store-media` release,
  `tools/play-store-media.sh` downloads them) and, on version branches with the secret, sent to Play with the texts.
  See `docs/play-store/README.md`.

## Subscriptions, payments and legal pages

- **Legal pages** (public): `/privacy`, `/terms` and `/delete-account`. Their texts are `help/en/legal/*.md`, with
  reviewed translations in `help/i18n/<lang>/`. Who is responsible for the data is set in Administration → Legal
  details.
- **Google Play** (subscriptions in the app): in the Play Console create the subscription `bodylens` with the base
  plans `monthly` (€1.50) and `yearly` (€12), each with a 7-day free-trial offer. Create a service account in Google
  Cloud, give it access in Play Console → Users and permissions (view financial data, manage orders and
  subscriptions) and paste its JSON key in Administration → Google Play.
- **Stripe** (subscriptions on the website): paste the secret key in Administration → Web payments (Stripe); the server
  creates the product and the prices (€1.50/month, €12/year). Create the webhook with the address shown there and the
  events `checkout.session.completed` and `customer.subscription.*`, and paste its signing secret. Enable Google Pay
  and Apple Pay in Stripe → Settings → Payment methods (Stripe's own checkout page is used, so no domain needs
  verifying for Apple Pay).
- **Unpaid accounts**: every 6 hours the server checks paid accounts and those free for a time; one whose subscription
  is over is read-only for 30 days (no new data, no synchronisation, Health Auto Export / Health Connect posts
  refused), gets three emails (at once, a week before and the day before) and is then deleted (administrators never).
- **Landing page**: visitors who are not signed in see `src/frontend/landing/index.html` at `/`. Its screenshots and
  videos are made from a synthetic demo account with `tools/demo_data.py` and `tools/landing_capture.py` (Playwright
  and ffmpeg, not in the image): one phone video per tab of each module (`--tabs`, which also writes `manifest.json`,
  the modules and tabs the landing page shows, read from the app), plus the hero, desktop and theme media (without
  `--tabs`), in Spanish and English (`--lang`). The workflow **🎬 Landing media** (`.github/workflows/landing-media.yml`)
  records them all again whenever the app's page, its translations or themes change (or by hand from Actions) and
  leaves them in the `landing-media` release; `tools/deploy.sh` then copies them to `<DATA_DIR>/landing-media` on the
  NAS (`tools/deploy-landing-media.sh`, only when their build changed), which the server serves before the copy in
  `src/frontend/landing/media/`.

## Backup

Everything of the app is in `/volume1/docker/data/bodylens` (including `bodylens.db`): just include that folder in
Hyper Backup. (Phase 3: automatic daily backup inside `backups/`.)

## Help and automatic translation

The Help section of the app shows `help/en/`, `README.md` and `CHANGELOG.md`, translated automatically into each
account's language with the Claude API. Set the Anthropic API key in **Administration → Translator** (stored
encrypted in the database) or as `ANTHROPIC_API_KEY` in the `.env`. Translations are kept in
`/data/translations/<lang>/` and made again only when the English text changes. Without a key, the help is shown in
English. The documents are read from `DOCS_DIR` (`/app/docs` in the image, `/app/code` with hot deployment).
