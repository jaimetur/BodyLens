# 🗓️ CHANGELOG
[Changelog](/CHANGELOG.md) for the past releases

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Breaking Changes:
- **From a claude.ai artifact to a server of its own:** BodyLens no longer lives in claude.ai and moves to a Docker container on the NAS (`https://bodylens.jaimetur.cloud`). The data is in a SQLite database on the server, not in the artifact's data space. You sign in with a BodyLens username and password, not with your Claude account.
- **The Google sheet is no longer needed:** Withings and Apple Health send the data straight to the server. The sheet and its Apps Script remain only as a temporary bridge, for the accounts that have not been moved yet.
- **Default language: English.** New accounts start in English; existing ones keep Spanish.

#### 🌟 New Features:
- **Docker deployment (Synology NAS):**
  - `jaimetur/bodylens` image on Docker Hub, built by GitHub Actions on every push to the version branch.
  - The Dockhand stack runs as `docker_limited:docker_users`, behind an HTTPS reverse proxy.
  - Health check (`/healthz`) and a warning if `/data` cannot be written to.
- **Hot deployment:** `tools/deploy.sh` copies the code to the NAS and the container uses it without waiting for a new image. Open pages show a "BodyLens has been updated" notice with a button to reload.
- **Several accounts, each with its own data:**
  - You sign in with username and password; passwords are stored with argon2 and sessions on the server.
  - Each account has a username, first and last name, a valid and unique email and a password of at least 4 characters, typed twice.
- **Account sign-up:**
  - Account request from the sign-in screen, approved by the administration; notices go by email.
  - Single-use invitation links.
  - Initial `admin`/`admin123` account, which the sign-in screen shows while it keeps the default password.
- **Outgoing email (SMTP)** for requests, approvals, temporary passwords and notices, configurable from Administration.
- **Couples:** two accounts can be linked to share and edit the cycle and intimacy records together. You invite your partner with their username or email from Your account → Account → Partner; they get an email with the invitation (you are told at once if no account has that username or email), and you get one when they accept. An app profile can be moved to that person's own account.
- **Your account:**
  - **Account:** profile, email, language and password, partner, data sources, synchronisation and import.
  - **Profiles:** access levels over your account's data (all profiles see the same data), explained on the panel itself. Each profile, the main one included, can be given only the modules you choose, with chips like in DriveTest Analyzer; it only sees those in the menu. The modules include Goals, plan and meals, Your account and, for administrators, Administration; at least one profile must keep those, the rest can have any modules. Profiles no longer have their own partner or cycle.
  - **The PIN decides the profile:** the PIN typed on the lock screen opens the profile that has it; if several profiles share a PIN, entering with it shows the modules of all of them (the panel warns when you set a PIN another profile already uses). The separate private PIN for Cycle and intimacy is gone: Intimate is a module like the others, and a profile only exports to PDF the modules it has.
  - **Personal data** (height, sex, date of birth) is a panel of the **Account** tab, under Password.
  - **Data and backups:** where your phone data comes from, data source, full backup and CSV export.
- **Administration** (administrator accounts), with these tabs:
  - **Users:** edit username, name, email and password; activate or deactivate with a switch; grant or remove admin; reset the password; delete.
  - **Access requests** and **Invitations**.
  - **Mail:** SMTP settings and test email.
  - **Withings:** developer application data.
  - **Backups** and **Data sources**.
  - The server never ends up without an active administration account.
- **Direct Withings:**
  - OAuth connection per account, with the token stored encrypted.
  - Synchronisation every few minutes and at once when Withings notifies (webhook).
  - Fetches weigh-ins and composition, activity, workouts, sleep, SpO2, VO2 max and ECG.
- **Direct Apple Health:** Health Auto Export posts to a personal address of each account. It is a full port of the Apps Script logic:
  - Sleep by segments (AutoSleep plus Apple Watch, wake-ups and naps, night from 5 pm to 5 pm).
  - Daily activity, workouts, ECG, alerts and records (cycle, mood, symptoms…).
  - Health takes precedence over Withings, which only fills gaps.
- **Android app (Health Connect):**
  - Sends hourly steps, distance, floors, energy, heart rate, HRV, SpO2, respiration, VO2 max, sleep with stages, workouts, cycle and sexual activity.
  - Uses the same format as Health Auto Export.
  - The APK is built by GitHub Actions and downloaded from Your account (`/android.apk`).
- **Data on the server:**
  - The sheet's tabs become tables on the server, and the workbook the page reads is generated from them.
  - Parity with the original sheet checked on all 16 tabs.
  - The first Withings connection or the first Health upload imports the sheet beforehand, so no history is lost.
- **Daily database backup** at 03:30, in `/data/backups`. The last 30 are kept and can be downloaded from Administration.
- **Multi-language:** English, Spanish, Catalan, French, Italian, German, Portuguese, Dutch, Chinese and Japanese.
  - Each account picks its own, and emails arrive in the language of whoever receives them.
  - The base catalog is in English (`src/frontend/i18n/`), with a guide for contributing translations.
  - The language is chosen in the access request and invitation forms too.
- **Help:** a Help section in the app with the help of every module, the README and the changelog, without leaving the tool. It is public: it can be read without signing in (link on the sign-in screen, with its own language picker).
  - The documents are written only in English and translated automatically into each account's language with LibreTranslate, a free translator running on the server next to BodyLens (the Claude API can be set as an optional, paid alternative in Administration → **Translator**); each translation is kept until the English text changes.
  - Spanish comes already translated with the app (`help/i18n/es/`), so it needs no translator.
  - Every document is translated in advance into every language when the server starts, and checked again every 10 minutes: only documents whose English text changed (their fingerprint) are translated again, so the help opens already translated.
- **Text size** per account (Small, Normal, Large, Extra large) in *Your account*, like the language; the new Normal is slightly bigger than before.

#### 🚀 Enhancements:
- **A single importer** (Your account → Data and backups) for the full backup and for the previous version's `snap.json`. If the backup has several profiles, you choose which one to import.
- **Meals:**
  - Each score sits on its meal's row, with large buttons, and Water has its own row.
  - The day's log comes before the estimated loss.
  - The day's log shows the last 4 weeks (Monday to Sunday) at the top instead of just one; the arrows jump 4 weeks.
- **Email:** the server greets the mail server with its public name instead of the container's private address, which spam filters penalise.
- **Profiles panel:** each row adapts to the width of the panel, so the PIN buttons no longer end up out of view.
- **Android at the same level as the iPhone:** every screen, empty state and notice that spoke only of Apple Health / Health Auto Export now also explains the Android path (Health Connect with the BodyLens app), with the same sending address for both.
- **Mood:** past moods can be recorded, with date and time or by tapping the day in the calendar.
- **History** is now called **Weight history**.
- **Wide screens:** the app reaches 1600 px, and Your account and Administration use the width with columns.
- **Sidebar:**
  - Your account and Administration (administrators only) are sections of the app, with the sidebar.
  - "Manage profiles" moves to Your account.
  - **Settings** is now called **Goals, plan and meals**; its **Data and backups** tab moves to Your account.
- **Avatar menu:** shows the full name and includes Your account, Administration and **Sign out**, in red.
- **Administration command line** (`python -m app.accounts.cli`): create accounts with a temporary password, invitations, passwords, users, sources and move profiles.

#### 🐛 Bug fixes:
- **Security:** the access log no longer stores the Apple Health upload address, OAuth codes or invitations.
- **Withings:** the callback address accepts Withings' tests and notices (POST and HEAD).
- **Browser:**
  - Pages and their styles are revalidated on every deployment, so no stale copies stay in the cache.
  - Your account and Administration can be shown inside the app.

#### 📚 Documentation:
- **English is the official language of the project:** code, documentation and commit messages. Complete `README.md`; the README, the help and the changelog are written only in English and shown translated in the app.
- Usage help per module in `help/en/` (shown in the app's Help in each language).
- `docs/DEPLOYMENT.md` (NAS, Dockhand, hot deployment, Withings, Apple Health, Android).
- No longer used material moved out of the repository: the original migration plan, brief and handover (`docs/`) and the Apps Script and Health scripts (`legacy/`); the data rules that must be kept move to `AGENTS.md`.
- `AGENTS.md` with the repository rules (design untouched, data parity, secrets and personal data kept out, working language, texts and languages).
- `src/frontend/i18n/README.md`: how to add or improve a translation.

---

## Release: v0.0.1
### Release Date: 2026-11-01
Starting version: the app as it was published as a claude.ai artifact (page version 144) when Claude Work handed it over to Claude Code.

#### ⚠️ Breaking Changes:

#### 🌟 New Features:
- **Single-page web app**, published as a claude.ai artifact. The data was in the artifact's data space (`bascula` collection), and the page carried a copy inside for whoever opened it without a session.
- **Summary:** trend weight, plan progress, "today at a glance" (readiness, sleep, sleep balance, HRV, steps) and automatic alerts and insights.
- **Weight:** smoothed trend, plan with target rates, projection, weeks, calendar and milestones.
- **Body:**
  - **Scale:** fat, muscle, water and bone; BMI and FFMI with ranges by age and sex.
  - **Measurements** with a tape.
  - **Heart:** resting heart rate, HRV, SpO2, VO2 max, ECG and heart-rate alerts.
  - **Wellbeing.**
- **Activity:** steps, calories and exercise minutes with rings and goals; workouts and their relation to weight.
- **Sleep:** last night with stages, 7-night sleep balance, naps, target schedule and analysis.
- **Meals:** a daily note of what you eat (meals, water, exercise and "sins") and its estimated effect on weight.
- **Intimate:** cycle with forecast, sexuality and mood, protected by a private PIN.
- **History:** years of weigh-ins (since 2009), weight-loss attempts and rebounds.
- **Profiles** inside the app, each with its own data and, if wanted, a PIN. The Apple Health cycle goes automatically to the profile marked as "cycle".
- **PDF report** of the chosen period and full **backups** in JSON and CSV.
- **Data sources through a Google sheet** ("Peso Jaime 2026") with its Apps Script:
  - Withings: weigh-ins, composition, activity, sleep, workouts, SpO2, VO2 and ECG.
  - Health Auto Export from the iPhone: Apple Health, which takes precedence over Withings.
  - Own sleep rules: mix of AutoSleep and Apple Watch, 5 pm to 5 pm window, wake-ups and naps.
- **Interface:**
  - Light and dark theme and **BodyLens** brand, with icon and logo.
  - Designed for the iPhone: installs as an app from Safari, swipe gestures between sections, bottom bar and floating period selector.
  - All in Spanish.

#### 🚀 Enhancements:

#### 🐛 Bug fixes:

#### 📚 Documentation:
- Handover document from Claude Work with what had been done, how it was set up and what was left to build.
