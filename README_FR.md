# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · **Français** · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** est une application web de santé personnelle, auto-hébergée et multi-utilisateur. Elle réunit le poids
et la composition corporelle d'une balance **Withings** et ce qu'enregistrent ton téléphone et ta montre (sommeil,
activité, fréquence cardiaque, VFC, SpO2, VO2 max, ECG, cycle, humeur…) depuis **Apple Santé** ou **Health Connect
d'Android**. Elle tourne dans Docker sur ton propre serveur, les données arrivent toutes seules et chaque personne ne
voit que les siennes.

## Fonctionnalités

- **Résumé :** poids de tendance, progression du plan, « aujourd'hui en un coup d'œil » (préparation, sommeil, solde
  de sommeil, VFC, pas) et conclusions et alertes automatiques.
- **Poids :** tendance lissée, plan avec rythmes cibles, projection, semaines, calendrier et jalons ; historique des
  poids au fil des années, tentatives de perte de poids et rebonds.
- **Corps :** composition (graisse, muscle, eau, os), IMC/FFMI avec plages par âge et par sexe, mensurations au mètre
  ruban, cœur (fréquence cardiaque au repos, VFC, SpO2, VO2 max, ECG, alertes de fréquence cardiaque) et bien-être.
- **Activité :** pas, calories et minutes d'exercice avec anneaux et objectifs, entraînements et leur lien avec le poids.
- **Sommeil :** la dernière nuit avec ses phases, solde de sommeil sur 7 nuits, siestes, horaire cible et analyse. Les
  données d'AutoSleep et d'Apple Watch sont fusionnées selon des règles propres (fenêtre de 17 h à 17 h, réveils
  nocturnes, siestes).
- **Repas :** un score quotidien de ce que tu manges, bois et de l'exercice que tu fais, et son effet estimé sur ton poids.
- **Intime :** cycle (avec prévision), activité sexuelle et humeur, protégés par un code PIN privé.
- **Aide** dans l'app : l'aide de chaque module, ce README et le journal des modifications, dans ta langue.
- **Rapport PDF** de la période choisie et **sauvegardes complètes** en JSON et CSV.
- **Interface :** thèmes clair et sombre, pensée pour le téléphone (s'installe comme une app depuis le navigateur),
  gestes de balayage, mise en page pour écrans larges jusqu'à 1600 px.
- **Langues :** anglais (par défaut), espagnol, catalan, français, italien, allemand, portugais, néerlandais, chinois
  et japonais. Chaque compte choisit la sienne ; les e-mails arrivent dans la langue de leur destinataire.

### Comptes

- **Plusieurs comptes**, chacun avec ses données, avec connexion par identifiant et mot de passe.
- **Inscription :** demandes d'accès depuis la page de connexion, approuvées par un administrateur (avec notifications
  par e-mail), ou liens d'invitation à usage unique.
- **Couples :** deux comptes peuvent être liés pour partager et modifier ensemble les enregistrements du cycle et de
  l'intimité.
- **Profils :** chaque compte peut avoir plusieurs profils (avec un code PIN facultatif), gérés dans *Ton compte*.
- **Administration :** utilisateurs (identifiant, nom, e-mail, mot de passe, interrupteur d'activation, rôle
  d'administrateur), demandes d'accès, invitations, e-mail (SMTP), identifiants de l'application Withings,
  sauvegardes et sources de données.

### Données qui arrivent toutes seules

- **Withings :** chaque compte se connecte avec OAuth ; les pesées, la composition, l'activité, les entraînements, le
  sommeil, la SpO2, le VO2 max et l'ECG sont récupérés toutes les quelques minutes, et immédiatement quand Withings
  signale une nouvelle mesure.
- **Apple Santé :** l'app iPhone *Health Auto Export* envoie les données à une adresse personnelle de chaque compte.
- **Android :** l'app BodyLens pour Android (dans `android/`) lit Health Connect et envoie toutes les heures dans le
  même format.
- **Sauvegarde quotidienne** de la base de données à 03 h 30 (les 30 dernières sont conservées).

## Comment c'est construit

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend :** une seule page (`src/frontend/app/`), née comme artefact de claude.ai, servie avec une petite couche
  (`src/frontend/compat/claude-shim.js`) qui implémente, via l'API du serveur, ce que la page demandait auparavant à
  claude.ai (`db`, `user`, `downloads`…).
- **Backend :** Python 3.12, FastAPI, SQLite (WAL) dans `/data`, un seul processus avec le planificateur intégré.
- **Traductions :** le catalogue est en anglais (`src/frontend/i18n/catalog.json`) et chaque langue est
  `src/frontend/i18n/locales/<lang>.json`. La page est traduite dans le navigateur par `src/frontend/i18n/i18n.js`,
  qui formate aussi les nombres et les dates ; le serveur utilise les mêmes fichiers pour les e-mails. L'aide (`help/en/`), ce README et le
  journal des modifications sont écrits en anglais et traduits automatiquement dans la langue de chaque compte avec
  l'API Claude (la clé se renseigne dans Administration → Traducteur) ; chaque traduction est conservée jusqu'à ce que
  le texte anglais change.
- **Sécurité :** mots de passe argon2, sessions côté serveur (cookie HttpOnly/Secure/SameSite), en-tête anti-CSRF sur
  chaque écriture, limites de fréquence, chaque compte isolé, jetons OAuth chiffrés ; secrets uniquement dans des
  variables d'environnement ou dans la base de données du serveur.

## Structure du dépôt

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

## Développement

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
La dernière commande démarre http://localhost:8000 avec rechargement à chaud : la page est servie telle quelle depuis
`src/` (il suffit de recharger) et le backend redémarre à l'enregistrement. `tools/dev-data.sh` copie les données du
serveur dans `data-dev/` (les modifications faites en développement ne remontent jamais). Il existe aussi
`docker compose -f docker/compose.dev.yml up --build`.

## Déploiement

Chaque push sur la branche de la version en cours (p. ex. `0.1.0`) lance les tests et publie l'image
`jaimetur/bodylens:latest` (amd64 et arm64) sur Docker Hub ; `main` publie `jaimetur/bodylens:main`. Sur le
serveur : `docker/compose.yml` plus un fichier `.env`. Le NAS monte le code depuis le dossier du stack, donc
`tools/deploy.sh` déploie un commit en quelques secondes sans attendre une nouvelle image. Étapes complètes :
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) (en anglais).

## Contribuer aux traductions

Il te suffit de connaître l'anglais : consulte [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (en
anglais) pour ajouter une langue ou en améliorer une. L'aide, le README et le journal des modifications sont traduits automatiquement : tu ne modifies que les fichiers
anglais.

## Documentation

- Aide d'utilisation : [`help/`](help/en/README.md) (en anglais ; aussi dans l'app, dans *Aide*)
- Modifications de chaque version : [`CHANGELOG.md`](CHANGELOG.md)
- Instructions pour les agents de code : [`AGENTS.md`](AGENTS.md)

Les données personnelles n'entrent jamais dans le dépôt : les bases de données, les sauvegardes JSON et `.env` sont
dans `.gitignore`.
