# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · [Italiano](README_IT.md) ·
**Deutsch** · [Português](README_PT.md) · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** ist eine selbst gehostete persönliche Gesundheits-Webanwendung für mehrere Nutzer. Sie vereint das
Gewicht und die Körperzusammensetzung deiner **Withings**-Waage mit dem, was dein Handy und deine Uhr aufzeichnen
(Schlaf, Aktivität, Herzfrequenz, HRV, SpO2, VO2max, EKG, Zyklus, Stimmung…) – aus **Apple Health** oder **Android
Health Connect**. Sie läuft in Docker auf deinem eigenen Server, die Daten kommen von selbst an und jede Person sieht
nur ihre eigenen.

## Funktionen

- **Übersicht:** Trendgewicht, Planfortschritt, „heute auf einen Blick“ (Bereitschaft, Schlaf, Schlafbilanz, HRV,
  Schritte) sowie automatische Erkenntnisse und Hinweise.
- **Gewicht:** geglätteter Trend, Plan mit Zielraten, Prognose, Wochen, Kalender und Meilensteine; Gewichtsverlauf
  über die Jahre, Abnehmversuche und Rückfälle.
- **Körper:** Zusammensetzung (Fett, Muskeln, Wasser, Knochen), BMI/FFMI mit Bereichen nach Alter und Geschlecht,
  Maßband-Messungen, Herz (Ruheherzfrequenz, HRV, SpO2, VO2max, EKG, Herzfrequenz-Warnungen) und Wohlbefinden.
- **Aktivität:** Schritte, Kalorien und Trainingsminuten mit Ringen und Zielen, Workouts und ihr Zusammenhang mit dem
  Gewicht.
- **Schlaf:** die letzte Nacht mit Phasen, Schlafbilanz über 7 Nächte, Nickerchen, Zielzeiten und Analyse. Die Daten
  von AutoSleep und Apple Watch werden mit eigenen Regeln zusammengeführt (Fenster von 17:00 bis 17:00 Uhr,
  Aufwachphasen, Nickerchen).
- **Mahlzeiten:** ein Tageswert für das, was du isst, trinkst und an Bewegung machst, und seine geschätzte Wirkung
  auf dein Gewicht.
- **Intim:** Zyklus (mit Prognose), sexuelle Aktivität und Stimmung, geschützt durch eine private PIN.
- **Hilfe** in der App: die Hilfe jedes Moduls, diese README und das Änderungsprotokoll in deiner Sprache.
- **PDF-Bericht** für den gewählten Zeitraum und **vollständige Backups** als JSON und CSV.
- **Oberfläche:** helles und dunkles Design, fürs Handy gemacht (lässt sich im Browser als App installieren),
  Wischgesten, Layout für breite Bildschirme bis 1600 px.
- **Sprachen:** Englisch (Standard), Spanisch, Katalanisch, Französisch, Italienisch, Deutsch, Portugiesisch,
  Niederländisch, Chinesisch und Japanisch. Jedes Konto wählt seine eigene; E-Mails kommen in der Sprache des
  Empfängers an.

### Konten

- **Mehrere Konten**, jedes mit eigenen Daten, Anmeldung mit Benutzername und Passwort.
- **Registrierung:** Zugangsanfragen auf der Anmeldeseite, von einem Administrator genehmigt (mit
  E-Mail-Benachrichtigungen), oder Einladungslinks zur einmaligen Verwendung.
- **Paare:** Zwei Konten können verknüpft werden, um Zyklus- und Intimitätseinträge gemeinsam zu teilen und zu
  bearbeiten.
- **Profile:** Jedes Konto kann mehrere Profile haben (mit optionaler PIN), verwaltet unter *Dein Konto*.
- **Administration:** Benutzer (Benutzername, Name, E-Mail, Passwort, Aktiv-Schalter, Administratorrolle),
  Zugangsanfragen, Einladungen, E-Mail (SMTP), Zugangsdaten der Withings-App, Backups und Datenquellen.

### Daten, die von selbst ankommen

- **Withings:** Jedes Konto verbindet sich per OAuth; Wiegungen, Zusammensetzung, Aktivität, Workouts, Schlaf, SpO2,
  VO2max und EKG werden alle paar Minuten abgerufen, und sofort, wenn Withings eine neue Messung meldet.
- **Apple Health:** Die iPhone-App *Health Auto Export* sendet die Daten an eine persönliche Adresse jedes Kontos.
- **Android:** Die BodyLens-Android-App (in `android/`) liest Health Connect und sendet stündlich im selben Format.
- **Tägliches Backup** der Datenbank um 03:30 Uhr (die letzten 30 bleiben erhalten).

## Wie es aufgebaut ist

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** eine einzelne Seite (`src/frontend/app/`), entstanden als claude.ai-Artefakt, ausgeliefert mit einer
  kleinen Schicht (`src/frontend/compat/claude-shim.js`), die über die Server-API das umsetzt, was die Seite früher
  bei claude.ai angefragt hat (`db`, `user`, `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) in `/data`, ein einziger Prozess mit dem Scheduler darin.
- **Übersetzungen:** Der Katalog ist englisch (`src/frontend/i18n/catalog.json`) und jede Sprache ist
  `src/frontend/i18n/locales/<lang>.json`. Die Seite wird im Browser von `src/frontend/i18n/i18n.js` übersetzt, das
  auch Zahlen und Datumsangaben formatiert; der Server nutzt dieselben Dateien für E-Mails. Die Hilfe (`help/en/`), diese README und das
  Änderungsprotokoll sind auf Englisch geschrieben und werden mit der Claude-API automatisch in die Sprache jedes Kontos
  übersetzt (den Schlüssel gibst du unter Verwaltung → Übersetzer ein); jede Übersetzung bleibt bestehen, bis sich der
  englische Text ändert.
- **Sicherheit:** argon2-Passwörter, serverseitige Sitzungen (HttpOnly/Secure/SameSite-Cookie), Anti-CSRF-Header bei
  jedem Schreibzugriff, Ratenbegrenzungen, jedes Konto isoliert, OAuth-Tokens verschlüsselt; Geheimnisse nur in
  Umgebungsvariablen oder in der Server-Datenbank.

## Struktur des Repositorys

```
src/backend/app/        server (package "app"), one subpackage per module:
  core/                 settings, SQLite, security, languages, backups, route dependencies
  accounts/             accounts, sessions, invitations, access requests, admin CLI
  admin/                Administration panel
  couples/              couples
  data/                 documents of each account and backup import
  help/                 the Help module (help, README and changelog, translated automatically)
  sheets/               the data tables and the XLSX workbook the page reads
  sources/              Withings and Apple Health / Android ingestion
  sync/                 synchronisation and scheduler
  mail/                 SMTP email
  web/                  page assembly and static files
src/frontend/
  app/                  the app (app_a: styles and views, app_b: core, app_c: interface)
  compat/               window.claude layer
  accounts/ admin/ common/   sign-in, request, registration, Your account and Administration pages
  i18n/                 translator, English catalog and one file per language
android/                Android app (Health Connect → server)
assets/branding/        icons and logo
tests/<module>/         tests (pytest) and tests/frontend/*.mjs (page and translator in jsdom)
help/en/                user help, one file per module (English; translated automatically in the app)
docker/                 Dockerfile and compose files (NAS, hot reload, development)
docs/DEPLOYMENT.md      deployment on a Synology NAS
tools/                  deployment, development server and translation tools
```

## Entwicklung

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'
```
```bash
.venv/bin/python -m pytest -q
```
```bash
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs && node tests/frontend/i18n.mjs
```
```bash
tools/dev-data.sh && tools/dev.sh
```
Der letzte Befehl startet http://localhost:8000 mit Hot Reload: Die Seite wird unverändert aus `src/` ausgeliefert
(einfach neu laden) und das Backend startet beim Speichern neu. `tools/dev-data.sh` kopiert die Serverdaten nach
`data-dev/` (in der Entwicklung gemachte Änderungen gehen nie zurück). Außerdem gibt es
`docker compose -f docker/compose.dev.yml up --build`.

## Bereitstellung

Jeder Push auf den Branch der aktuellen Version (z. B. `0.1.0`) führt die Tests aus und veröffentlicht das Image
`jaimetur/bodylens:latest` (amd64 und arm64) auf Docker Hub; `main` veröffentlicht `jaimetur/bodylens:main`. Auf dem
Server: `docker/compose.yml` plus eine `.env`-Datei. Das NAS bindet den Code aus dem Stack-Ordner ein, daher
bringt `tools/deploy.sh` einen Commit in Sekunden live, ohne auf ein neues Image zu warten. Vollständige Schritte:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) (auf Englisch).

## Zu den Übersetzungen beitragen

Du brauchst nur Englisch: Siehe [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (auf Englisch), um eine
Sprache hinzuzufügen oder eine zu verbessern. Hilfe, README und Änderungsprotokoll werden automatisch übersetzt: Du bearbeitest nur die englischen Dateien.

## Dokumentation

- Benutzerhilfe: [`help/`](help/en/README.md) (auf Englisch; auch in der App unter *Hilfe*)
- Änderungen jeder Version: [`CHANGELOG.md`](CHANGELOG.md)
- Anweisungen für Coding-Agenten: [`AGENTS.md`](AGENTS.md)

Persönliche Daten gelangen nie ins Repository: Datenbanken, JSON-Backups und `.env` stehen in `.gitignore`.
