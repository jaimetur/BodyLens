# 🗓️ CHANGELOG
[Changelog](/CHANGELOG.md) for the past releases

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Breaking Changes:
- **From a claude.ai artifact to a server of its own:** BodyLens no longer lives in claude.ai and moves to a Docker container on the NAS (`https://bodylens.jtgcloud.com`). The data is in a SQLite database on the server, not in the artifact's data space. You sign in with a BodyLens username and password, not with your Claude account.
- **The Google sheet is no longer needed:** Withings, Apple Health and Android send the data straight to the server, and every account keeps its data there; the sheet and its Apps Script are no longer used.
- **Default language: English.** New accounts start in English; existing ones keep Spanish.

#### 🌟 New Features:
- **Docker deployment (Synology NAS):**
  - `jaimetur/bodylens` image on Docker Hub, built by GitHub Actions on every push to the version branch.
  - The Dockhand stack runs as `docker_limited:docker_users`, behind an HTTPS reverse proxy.
  - Health check (`/healthz`) and a warning if `/data` cannot be written to.
- **Hot deployment:** `tools/deploy.sh` copies the code to the NAS and the container uses it without waiting for a new image. Open pages show a "BodyLens has been updated" notice with a button to reload.
- **Several accounts, each with its own data:**
  - You sign in with your username or your email and a password; passwords are stored with argon2 and sessions on the server.
  - Each account has a username, first and last name, a valid and unique email and a password of at least 4 characters, typed twice.
- **Account sign-up:**
  - Account request from the sign-in screen, approved by the administration; notices go by email.
  - Single-use invitation links.
  - Initial `admin`/`admin123` account, which the sign-in screen shows while it keeps the default password.
- **Outgoing email (SMTP)** for requests, approvals, temporary passwords, partner invitations and notices, configurable from Administration. The server greets the mail server with its public name, and the test email reads like a real notice; Administration → Mail explains what to do if it lands in spam.
- **Couples:** two accounts can be linked to share and edit the cycle and intimacy records together. You invite your partner with their username or email from Your account → Account → Partner; they get an email with the invitation (you are told at once if no account has that username or email), and you get one when they accept. An app profile can be moved to that person's own account.
- **Your account:**
  - **Account:** profile, email, language, text size (Small, Normal, Large, Extra large; the new Normal is slightly bigger than before), theme (Automatic as the device, Daytime, Night-time, Sepia, Ocean, Forest, High contrast, Rose, Lavender, Mint, Sunset or Graphite, for the app and the server pages), minutes without activity before a profile with a PIN locks itself (1 by default), password, personal data (height, sex, date of birth), partner and data sources.
  - **Profiles** and **Data and backups** (where your phone data comes from, data source, full backup and import, CSV export).
- **Profiles** (Your account → Profiles):
  - Access levels over the account's data: every profile sees the same data, and each one, the main one included, sees only the modules chosen with chips (as in DriveTest Analyzer), Goals, plan and meals, Your account and Administration included. At least one profile must keep those three. A profile only exports to PDF the modules it has, and on mobile the bottom bar shows fewer sections bigger.
  - The PIN decides the profile: typed on the lock screen, it opens the profile that has it; profiles that share a PIN open together, with all their modules (the panel warns when a PIN is already in use). Intimate is a module like the others, with no separate private PIN.
  - Profiles are reordered by dragging their ⋮⋮ handle, and the first one is the main profile. Opening the app enters it directly if it has no PIN; otherwise the PIN is asked for and decides the profile. A profile with a PIN locks itself after the minutes without activity chosen in Your account.
  - Each profile reopens the section and tabs it had open, also after a restart or on another device (kept in the account on the server).
- **Administration** (administrator accounts), with these tabs:
  - **Users:** edit username, name, email and password; activate or deactivate with a switch; grant or remove admin; reset the password; delete.
  - **Access requests** and **Invitations**.
  - **Mail:** SMTP settings and test email.
  - **Withings:** developer application data.
  - **Backups** and **Translator**.
  - The server never ends up without an active administration account.
- **Direct Withings:**
  - OAuth connection per account, with the token stored encrypted.
  - Synchronisation every few minutes and at once when Withings notifies (webhook).
  - Fetches weigh-ins and composition, activity, workouts, sleep, SpO2, VO2 max and ECG.
- **Direct Apple Health:** Health Auto Export posts to a personal address of each account. It is a full port of the Apps Script logic:
  - Sleep by segments (AutoSleep plus Apple Watch, wake-ups and naps, night from 5 pm to 5 pm).
  - Daily activity, workouts, ECG, alerts and records (cycle, mood, symptoms…).
  - Health takes precedence over Withings, which only fills gaps.
- **Android app:**
  - The whole BodyLens on the phone: the server's web app in a native shell, so every change on the server shows in it at once, with what a web page cannot do by itself: the server address on first start, a start screen and an offline screen, downloads of PDF and backups, choosing files to import, Android's back button (it first closes what is open), the system edges kept for swiping, and the bars in the colour of the theme.
  - Signing in links the app to the account on its own and opens its Health Connect screen: it sends you to Google Play when Health Connect is missing or out of date and asks for the permissions (again when you come back from installing it), reading in the background included, and then Android's permission to run in the background without battery limits; it reminds you at most once a week while something is missing, and the screen shows both with a button for whatever is missing and has a **Close** button. Your account → Data sources shows Health Connect's state with **Send now**, **Health Connect permissions** and **Change the server**.
  - **Main health source** per account (Your account → Data sources): when an account gets data both from Apple Health and from Android, the main one rules and the other one only fills the days and kinds of data it is missing, without adding up or duplicating anything. **Automatic** by default (Android, unless most of the data comes from Apple Health), **Apple Health** or **Android**. The box shows whether the data comes from Apple Health, Android or both, with the last sending of each and how many values were not used.
  - Sends hourly steps, distance, floors, energy, heart rate, HRV, SpO2, respiration, VO2 max, sleep with stages, workouts, cycle and sexual activity, to the same sending address as Health Auto Export and in the same format.
  - **BodyLens Bridge**, a second app from the same code, only sends Health Connect data (for those who use BodyLens in the browser); both can be installed together, and Your account → Data sources → **Set up BodyLens Bridge** opens it already linked (`/android-bridge.apk`).
  - The APK and the AAB for Google Play are built by GitHub Actions; the APK is also downloaded from the server (`/android.apk`, linked from the landing page and Your account). `tools/android-keystore.sh` creates the signing key Google Play needs.
  - Every screen, empty state and help page explains the Android path at the same level as the iPhone's.
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
- **Releases** (adapted from DriveTest Analyzer): `tools/CreateUpdateRelease.py` creates the next version's branch with its version, Android version and empty changelog release (English and Spanish), commits and pushes it, or updates the current release's version and date; the **🚀 Release** workflow publishes a version on GitHub with the notes of its changelog block, the source code and the Android APK. The rolling Android APK is published as "Android app (rolling build)".
- **Paid accounts:** besides invitations and approved requests, an account can be created with a subscription of €1.50 per month or €12 per year (€1 per month), with a 7-day free trial: on the website through Stripe (card, Google Pay or Apple Pay; the account is made when the payment page confirms the subscription) or in the Android app through Google Play. Your account → Subscription shows the plan, and the subscription can be switched between monthly and yearly (from the next renewal) or cancelled without deleting the account. An account whose subscription ends (cancelled, unpaid or free time over) is read-only for 30 days, with a red bar in the app showing the day it will be deleted: its data can be seen and downloaded, but nothing new can be added and synchronisation and the data sent by its sources stop; it is warned by email three times and is deleted with its data if it is not renewed. Administration has the Google Play and Stripe settings. The deployment's own administrator accounts (the default `admin` and `BODYLENS_ADMIN_USER`) are free for life.
- **Landing page** at `/` for visitors, in English or Spanish (by the browser's language, with an EN | ES switch): what each module does, with an endless carousel per module holding one video per tab that scrolls the whole tab (from a demo account with synthetic data; recorded again automatically by GitHub Actions whenever the app changes, so new modules and tabs appear by themselves), a colour-themes section, the website on a large screen, the launch promotion, sources, downloading the Android app (and its Google Play link once published, set in Administration → Google Play), prices, questions and sign-up.
- **Delete my account** in Your account (with the password): deletes the account and all its data and cancels its subscription.
- **Legal pages** (public, in every language): privacy policy (`/privacy`), terms of use (`/terms`) and how to delete an account (`/delete-account`), with the controller's details set in Administration → Legal details; linked from the sign-in page, Your account and the app.
- **Invitation codes:** signing up with a code (`INVITACION_AMIGOS`, for life, by default, set in Administration → Invitations; capitals, accents and spaces do not matter) makes a free account at once, for the code's duration (1, 3 or 6 months, 1 year, until a given date or for life, chosen per code, an optional expiry date and an optional maximum of accounts, e.g. the first 100, after which the code is deleted, aliases such as `LAUNCH` for `LANZAMIENTO` that share its places, and an option to announce it on the landing page as a promotion with a counter of the places left. The list of users in Administration shows how each account was made: the code it used, or its subscription with its plan and payment method (card, Google Pay or Apple Pay) while the accounts made with it keep their time), unless an administrator changes the end date in Users → Edit → Free access. Accounts are no longer requested: the sign-in page has, instead of "Ask for one", a large **Create my account** card that opens the sign-up in a dialog, with the plans and the invitation code.

#### 🚀 Enhancements:
- **A single importer** (Your account → Data and backups) for the full backup and for the previous version's `snap.json`. If the backup has several profiles, you choose which one to import.
- **Meals:**
  - Each score sits on its meal's row, with large buttons, and Water has its own row.
  - The day's log comes before the estimated loss.
  - The day's log shows the last 4 weeks (Monday to Sunday) at the top instead of just one; the arrows jump 4 weeks.
- **Manual entry in every module**, for those without a watch or a connected phone:
  - The manual weigh-in card is in Weight (also when there is no weigh-in yet, instead of an empty page); Activity has cards for the day's activity (steps, exercise minutes, active calories) and for workouts; Sleep, one for any night; and Body → Heart, one for resting heart rate, HRV, oxygen saturation and VO2 max. Data from your sources for the same day takes precedence.
  - Each field shows the account's last value as a reference (empty when there is none). On a phone, tapping a number opens a wheel to slide the value, with Keyboard to type it; without an earlier value, the wheel starts at a typical value for the profile's sex, age and height.
- **Mood:** past moods can be recorded, with date and time or by tapping the day in the calendar.
- **History** is now called **Weight history**.
- **Wide screens:** the app reaches 1600 px, and Your account and Administration use the width with columns.
- **Sidebar:**
  - Your account, Administration (administrators only) and Help are sections of the app, with the sidebar.
  - "Manage profiles" moves to Your account.
  - **Settings** is now called **Goals, plan and meals**; its **Data and backups** tab moves to Your account.
- **Avatar menu:** shows the full name and includes Your account, Administration, Help and **Sign out**, in red.
- **Administration command line** (`python -m app.accounts.cli`): create accounts with a temporary password, invitations, passwords, users, sources and move profiles.
- **Sleep clock (enlarged):** shows only the chosen night, as a thick ring coloured by phase (deep, light, REM, awake) when the watch records phases, with the average of the 14 earlier nights as a grey bar inside, the target schedule for that day (weekday or weekend) dashed outside and a larger time asleep in the centre.
- **Phones:** every tab shows a chart or a full set of figures without scrolling: the explanation of each chart card waits behind an ⓘ by its title (tap the title), the cards to enter data by hand go to the end of the tab, the figure tiles (also Activity's records and streaks) have colours and mini charts, and the profile avatar is bigger.
- **Enlarged cards:** a sideways swipe on phones and tablets, or the arrows at each side on a computer, goes to the previous or next day.
- **Swiping between tabs:** on touch screens a sideways swipe moves to the next or previous tab of the module (the parts of Body count as its tabs); past the last tab it goes on to the next module, and before the first, back to the last tab of the previous one.
- **No zoom on phones:** the app and its pages (sign-in, Your account, Administration, Help) no longer zoom when pinched, when tapping twice (the PIN pad included) or when a field gets the focus; a page that a browser zooms anyway (Brave, for example) goes back to its normal size and can be pinched back out.
- **Tabs start from the first after the lock:** when the PIN lock shows (the app is opened again, after the idle time or when locking the profile), every module opens again on its first tab; the module in use is kept.
- **PIN screen:** it fits on the screen without scrolling bars (the keys are bigger and further apart, grow with the free space and shrink only on very short screens) and has **Sign in with another user**, which signs out and goes back to the sign-in page.
- **Help, Your account and Administration inside the app scroll as one page:** on phones the page shown inside the app no longer scrolls on its own, so a swipe always moves the content.
- **Easier navigation on phones:** the bottom bar shows 4 modules of your choice and **More**, which opens every module with its tabs to go straight to any of them (it closes with its ✕ button or by swiping it down); the tabs of each module, with their icons, are at the bottom, in a strip just above the bottom bar, tinted with the colour of the module so the two read apart; when you scroll down, a thin bar at the top keeps the module's name (and Administration's tabs, now in a single sliding row); the period shows only the one in use and opens with a tap; dots show where you are when changing tab, and a hint the first time explains the sideways swipe. The close and arrow buttons of the panels are bigger and clearer, and the close button is red-orange and lines up with the arrows.
- **Manual-entry fields on phones no longer open by mistake:** the value wheel opens only with a deliberate tap, not when the finger touches a field while scrolling, slides on it or lands while the page is still moving.
#### 🐛 Bug fixes:
- **Security:** the access log no longer stores the Apple Health upload address, OAuth codes or invitations.
- **Withings:** the callback address accepts Withings' tests and notices (POST and HEAD).
- **Browser:**
  - Pages and their styles are revalidated on every deployment, so no stale copies stay in the cache.
  - Your account and Administration can be shown inside the app.
  - The enlarged cards fit the screen and their close button stays visible while scrolling, also with a larger text size on phones.
- **Weigh-in and sleep calendars on phones:** each day shows its whole figure (for example 110,9) instead of cutting it, and the table fits the screen, so a swipe on it changes tab.
- **Translations:** texts that still showed in Spanish in the other languages are translated: the weekday initials of the calendars and the meal initials, BMI and range labels, sleep phases and their tooltips, the captions of the rings and the charts' legends, the mood list (emotions and what they relate to) and its relationships, counts such as "21 of 30", the placeholder of the notes and several sentences of the insights. In Spanish, dates keep their «de» («viernes 20 de noviembre»).

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
