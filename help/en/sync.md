# Sync

BodyLens does not ask you to type your data: it receives it from your scale, your phone and your watch. You only
need to connect each service once. Everything is set up in **Your account → Data sources**, and each source shows
its status there.

Which ones do you need?

| You have… | Connect |
|---|---|
| A Withings scale (or a Withings watch) | **Withings** |
| An iPhone (and maybe an Apple Watch, AutoSleep…) | **Apple Health** with the app Health Auto Export |
| An Android phone (Samsung, Pixel, a Wear OS watch, Fitbit…) | **Android** with the BodyLens app for Health Connect |

You can connect several: Apple Health or Android are the main source for sleep, activity and heart; Withings brings
your weigh-ins and body composition and fills the gaps.

If your account gets data **both from Apple Health and from Android**, one of them rules and the other one only fills
the days and kinds of data the first one is missing (sleep: whole nights; workouts: the same session is not
duplicated). Choose it in **Your account → Data sources → Main source**: **Automatic** (the default: Android, unless
most of your data comes from Apple Health), **Apple Health** or **Android (Health Connect)**. The choice applies to the
data that arrives from then on.

## Withings, step by step

1. Open BodyLens and go to **Your account → Data sources**.
2. In the **Withings** box, press **Connect Withings**.
   - If the button is not there, the server is not set up for Withings yet: ask the administrator (it is done once in
     **Administration → Withings**).
3. Withings opens. Sign in with your Withings account (the same one as in the Withings app: [App Store](https://apps.apple.com/app/id542701020), [Google Play](https://play.google.com/store/apps/details?id=com.withings.wiscale2); or create one on the [Withings website](https://account.withings.com/)).
4. Withings asks whether BodyLens can read your data: press **Allow**.
5. You return to BodyLens and the box shows **connected**. The first time, BodyLens fetches your recent data; it can
   take a minute.

From then on BodyLens reads Withings every few minutes, and at once when your scale sends a new weigh-in.
To stop it, press **Disconnect** in the same box.

What it brings: weigh-ins and body composition (fat, muscle, water, bone), activity, workouts, sleep, SpO2, VO2 max
and ECG. Withings never overwrites what arrives from Apple Health or Android: it only fills the gaps.

## Apple Health (iPhone), step by step

The iPhone keeps your health data on the phone only, so an app has to send it to BodyLens. BodyLens uses
**Health Auto Export**, from the App Store. Its automatic sending (**automations**) needs its Premium version.

### 1. Create your sending address in BodyLens

1. In BodyLens, go to **Your account → Data sources**, box **Apple Health / Android**.
2. Press **Create my sending address**. A long address appears (`https://…/api/ingest/hae/…`).
3. Press **Copy the address**. Open BodyLens on the iPhone itself, so you can copy it there and paste it in the app.

The address is personal: whoever has it can send data to your account. Do not share it. If you think someone has
it, press **Change the address** and put the new one in your automations (the old one stops working).

### 2. Install Health Auto Export and give it access to Health

1. Install [Health Auto Export – JSON+CSV](https://apps.apple.com/app/id1115567069) from the App Store and open it.
2. When it asks for access to Health, allow **all** the data types (you can change it later in the iPhone's
   **Settings → Health → Data Access & Devices**).
3. Get the Premium version, which is needed for automations.

### 3. Create the automations

Health Auto Export sends one kind of data per automation, so create one automation for each kind you want (at least
the first two). For each one:

1. Open the **Automations** tab and create a new automation.
2. Type: **REST API**.
3. URL: paste your **sending address**.
4. Format: **JSON**, version **2**.
5. Choose the data (see the table) and the date range.
6. Turn the automation on and save it.

| Automation | Data to choose | Date range | Notes |
|---|---|---|---|
| Health metrics | **Health Metrics**, all of them | Since the last sync | Summarise (group) by **hour** |
| Sleep | **Health Metrics**, only **Sleep Analysis** | **Last 2–7 days** | Turn **off** summarising, so the stages arrive |
| Workouts | **Workouts** | Since the last sync | |
| ECG | **ECG** | Since the last sync | If you have an Apple Watch with ECG |
| Heart alerts | **Heart Rate Notifications** | Since the last sync | High, low and irregular rhythm alerts |
| Cycle | **Cycle Tracking** | Since the last sync | If you log your cycle in Health |
| Mood, symptoms, medications | **State of Mind**, **Symptoms**, **Medications** | Since the last sync | Optional |

The sleep automation looks back several days because AutoSleep and the watch sometimes close a night late; sending a
night again corrects it, it never duplicates it.

### 4. Check that it works

1. In each automation, use its button to send now (manual export).
2. In BodyLens, **Your account → Data sources**: the box changes from **waiting for data** to **receiving**, with the
   time of the last submission. Your sleep, steps and heart rate appear in the app within a minute.

Health Auto Export sends in the background, but iOS only lets it when the phone is unlocked from time to time. If
your data stops arriving, open Health Auto Export for a moment.

### Optional: AutoSleep, for better sleep data

[AutoSleep](https://apps.apple.com/app/id1164801111) (App Store, one-off purchase) is an iPhone app that works out
your sleep from the Apple Watch, even if you do not start any sleep mode: when you fall asleep, the wake-ups in the
night and when you get up. Many people find its times more accurate than the watch's own sleep tracking. You do
not need it: without AutoSleep, BodyLens uses the sleep recorded by the Apple Watch.

BodyLens does not connect to AutoSleep directly: AutoSleep writes each night into Apple Health, and Health Auto
Export sends it to BodyLens with the rest of your sleep. To set it up:

1. Install AutoSleep and open it once. Its first-time setup asks how you use the watch at night; follow it.
2. When it asks for access to Health, allow it to **write sleep** (Sleep Analysis). You can check it later in the
   iPhone's **Settings → Health → Data Access & Devices → AutoSleep**.
3. Wear the watch at night and charge it at some other time of the day (AutoSleep needs it on your wrist all night).
4. In the morning, open AutoSleep once, so it closes the night and writes it into Health (it usually does it on its
   own a little after you get up).
5. Nothing else: the **Sleep** automation of Health Auto Export already sends it (that is why it looks back 2–7 days:
   AutoSleep sometimes closes a night late).

How BodyLens uses it: when a night has data from AutoSleep, its bedtime, wake-up time, time asleep and wake-ups come
from AutoSleep, and the sleep stages (deep, REM) from the Apple Watch. If the watch clearly records more sleep than
AutoSleep (for example, if AutoSleep missed part of the night), the watch wins. The source of each night is shown in
**Sleep**.

## Android (Health Connect), step by step

On Android, health apps (Samsung Health, Google Fit, Fitbit, a Wear OS watch…) keep their data in **Health
Connect**, Android's health data store (the equivalent of Apple Health on the iPhone). Health Connect only keeps the
data on the phone; the **BodyLens app for Android** reads it there and sends it to your account every hour (the
equivalent of Health Auto Export on the iPhone, but already set up for BodyLens: no automations to create).

The BodyLens app is the whole of BodyLens on your phone: it shows the same app as the browser (every change on the
server appears in it at once) and adds Health Connect, downloads of your PDF and backups, Android's back button and a
start screen.

### 1. Make sure your data reaches Health Connect

1. Health Connect is built into Android 14 and later (in **Settings → Security & privacy → Privacy → Health
   Connect**, or search for "Health Connect" in Settings). On older versions, install
   [Health Connect](https://play.google.com/store/apps/details?id=com.google.android.apps.healthdata) from Google Play.
2. In the app that records your health (Samsung Health, Fitbit, Google Fit, your watch's app…), turn on syncing
   with Health Connect. In Samsung Health, for example: **Settings → Health Connect**.

### 2. Install the BodyLens app

- From **Google Play**, once it is published there; or
- from your server: open BodyLens in the phone's browser, go to **Your account → Data sources** and tap the link to
  download **the BodyLens app** (`/android.apk`). Android warns that it comes from outside Google Play: allow
  installing apps from your browser.

### 3. Open it and sign in

1. The first time, the app asks for your **server address** (the one you open BodyLens at in the browser; it comes
   filled in). Press **Continue**.
2. Sign in with your BodyLens username and password (or create an account: see [Accounts](accounts.md)).
3. The app links itself to your account and opens its Health Connect screen on its own. If Health Connect is missing
   or out of date, the screen tells you and **Open Health Connect in Google Play** installs it; when you come back,
   the app asks for the permissions. Allow all the data types, and also **read data in the background**, so it can
   send with the app closed. If you leave it without permissions, the app reminds you at most once a week.
4. That's all: it sends your data at once, and then every hour on its own.

Inside the app, **Your account → Data sources** shows the state of Health Connect (permissions allowed and the last
sending) with **Send now**, **Health Connect permissions** and **Change the server**. The Health Connect screen has a
**Close** button to go back to the app.

**BodyLens Bridge** is a second, smaller app for those who use BodyLens in the browser: it only sends your Health
Connect data (`/android-bridge.apk`). Install it, open **Your account → Data sources** in the phone's browser and press
**Set up BodyLens Bridge**: it opens already linked and asks for the permissions. Or copy the address with **Copy the
address** and paste it in the app. You do not need it if you use the BodyLens app.

The first time it sends the last 30 days; then, every hour, whatever is new. The app shows the time and the result of
the last submission, and in BodyLens the box changes to **receiving**.

## How you see that your data is arriving

- **Your account → Data sources** shows each source: **connected** / **not connected** for Withings, and
  **receiving** / **waiting for data** for Apple Health and Android, with the time of the last data.
- The open page updates itself when data arrives (it checks every minute and when you come back to the tab).
- **Sync now** (or the cloud button at the top of the app) asks Withings for the latest data at once.

## If your data does not arrive

| Problem | What to do |
|---|---|
| No **Connect Withings** button | The administrator has to set up Withings once (Administration → Withings). |
| Withings shows **not connected** after allowing | Press **Connect Withings** again and make sure you press **Allow** on the Withings page. |
| Apple Health stays in **waiting for data** | Check that the URL of each automation is exactly your sending address, the format is JSON version 2, and the automation is on; then send it manually. |
| Sleep arrives without stages | In the sleep automation, turn off summarising and use the last 2–7 days. |
| Data stops arriving from the iPhone | Open Health Auto Export for a moment; iOS pauses background apps. |
| You changed your sending address | Put the new address in every automation (iPhone) or in the BodyLens app (Android). |
| Android sends nothing | Check that your health app syncs with Health Connect and that the BodyLens app has every permission, including reading in the background. |
