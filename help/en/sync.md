# Sync

Data from your scale and watch arrives in your account on its own. It is set up in **Your account → Data sources**.

## Withings (scale, and whatever Withings has from the watch)
- **Connect Withings** takes you to Withings to grant permission; when you return, the server fetches your data and from then on reads it by itself every few minutes.
- It brings weigh-ins and composition, activity, workouts, sleep (the last 3 nights are always requested again, because they sometimes close late), SpO2, VO2 max and ECG.
- Withings never overwrites what arrives from Apple Health: it only fills the gaps (for example light and vigorous activity or awakenings).

## Apple Health (Health Auto Export on the iPhone)
- **Create my sending address** gives you a personal address; set it as the URL in each Health Auto Export automation (type **REST API**, format **JSON version 2**).
- For **unsummarised sleep**, the date range is **last 2–7 days** (so that nights that the watch or AutoSleep close late are picked up). For everything else, "Since last sync".
- Apple Health is the main source of sleep, naps, activity, workouts, heart rate, HRV, SpO2, ECG, alerts, cycle, mood and symptoms.
- Sleep rules: night from 17:00 to 17:00, AutoSleep decides the schedule if present (unless the watch clearly records more), deep and REM from the watch, awakenings of 10 min or more, naps of 10 min or more. A new submission corrects what that app no longer has in the period it covers.
- **Change the address** invalidates the previous one.

## Android (Health Connect)
- Install the BodyLens app for Android: in **Your account → Data sources** there is a link to download it (`/android.apk`). Android will ask for permission to install apps from outside Google Play.
- In the app: paste the same **sending address** as above, press **Grant Health Connect permissions** (and also accept "read data in the background") and **Send now**.
- The first time it sends the last 30 days; after that, every hour, whatever is new (sleep from the last 3 days is always resent, in case a night arrives late).
- It sends: steps, distance, floors, active energy and heart rate by the hour; resting heart rate, HRV, SpO2, breathing and VO2 max; sleep with stages; workouts; cycle and sexual activity. The server treats them the same as what arrives from the iPhone.

## How you find out
- The open page updates itself when data arrives (it checks every minute and when you return to the tab).
- **Sync now** (or the cloud button at the top) asks Withings for the latest data immediately.

## Previously (bridge with the Google Sheet)
While an account has not connected Withings or received direct submissions, the server keeps reading its Google Sheet every few minutes. The first time something arrives directly, the account switches to keeping its data on the server: its whole sheet is imported first so that no history is lost.
