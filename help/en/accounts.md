# Accounts and access

Each person has their own BodyLens account, with their data kept separate from everyone else's. You sign in with your username (or your email) and your password.

## Signing in
- **Sign-in screen** (`/login`): your username or the email of your account, and your password. If you fail several times in a row, you have to wait a few minutes.
- **Session**: lasts 90 days in that browser. To sign out, go to "Your account" → **Sign out** (this also deletes the data stored in that browser).
- **Initial account of a new deployment**: while the `admin` account keeps its default password (`admin123`), the sign-in screen shows it with a **Use** button. It disappears once you change the password.

## Creating an account with a subscription
- On the sign-in screen (website and Android app), the **Create my account** card opens the sign-up; on the website, the home page (`/`) shows what BodyLens does and its prices, and **Start free** opens it too (`/alta`).
- **Plans**: €1.49 per month or €12 per year (€1 per month), both with a **7-day free trial**. On the website you pay by card, Google Pay or Apple Pay (on Stripe's secure page); in the Android app, through Google Play.
- **Information requested**: full name, email, username and password, an **invitation code** if you have one, and accepting the [terms](/terms) and the [privacy policy](/privacy). The account is created as soon as the payment page confirms the subscription, and you are signed in.
- **Invitation code**: with a valid code the account is **free** and is created at once, without paying, for the time the code gives (1, 3 or 6 months, a year, until a given date or for life); an administrator can change the end date later. Capitals, accents and spaces do not matter.
- If a subscription ends (you cancelled it, a payment failed or your free time is over), the account becomes **read-only for 30 days**: you can sign in and see and download your data, but you cannot add new data, and synchronisation and the data sent by your sources (Withings, Apple Health, Health Connect) stop. A red bar at the bottom of the app says so and shows the day the account will be deleted, with **Renew** (`/alta`). You are warned by email three times (when it ends, a week before the deletion and the day before); if after 30 days it has not been renewed, the account and its data are deleted.

## Requesting an account
- Accounts are no longer requested: they are created with a subscription or an invitation code. Requests made before are still in Administration → Access requests.

## Signing up with an invitation
- A `/registro?c=…` link created by the administration. It works for **one** account and expires after a few days.
- It asks for the same information as the request, but the account is active immediately.

## First sign-in with a temporary password
- If your account was created with a temporary password, you are asked for **your own password** when you sign in, and you can change your username and name. The app does not open until you do.

## Your account (`/cuenta`)
Open it from the profile menu (top left) → **Your account**.
- **Full name** and **email**: the email receives all notifications.
- **Language**: the language of the whole app and of the emails you receive. Before signing in, choose it with the 🌐 selector on the sign-in screen. New accounts start in English (or in the language chosen when requesting the account).
- **Text size**: Small, Normal, Large or Extra large, for the whole app.
- **Theme**: the colours of the app and of these pages. **Automatic** follows your device (light by day, dark at night if your device does so); **Daytime** is always light, **Night-time** always dark, and there are also **Sepia** (warm light), **Ocean** (deep blue), **Forest** (dark green), **High contrast** (black and white, for reading more easily), **Rose**, **Lavender** and **Mint** (soft light colours), **Sunset** (warm dark) and **Graphite** (neutral dark grey).
- **Lock profiles with a PIN after**: the minutes without activity (1, 2, 5, 10, 15 or 30; 1 by default) after which a profile with a PIN locks itself.
- **Password**: asks for the current one; changing it signs you out on your other devices.
- **Partner** and **Sync**: see [partner](couples.md) and [sync](sync.md). Importing backups is in Your account → Data and backups ([import](import.md)).
- **Administration**: only for administrator accounts; see [administration](administration.md).
- **Subscription** (accounts with a subscription): the plan and until when it is active. Paid on the website, you can **switch between monthly and yearly** (the new price applies from the next renewal; nothing is charged now), **Cancel my subscription** without deleting the account (it stays active until the end of the paid period, then read-only for 30 days), **Keep my subscription** to undo a cancellation, and **Card and invoices** (Stripe's page). Paid in the app, the change of plan is made in Google Play and **Cancel my subscription** works the same. When the subscription is over it shows the day the account will be deleted, with **Renew**.
- **Privacy and terms**: links to the [privacy policy](/privacy), the [terms of use](/terms) and [how to delete an account](/delete-account).
- **Delete my account**: type your password and confirm. Your account and all its data are deleted at once and any subscription is cancelled. It cannot be undone: download a copy first in Data and backups if you want to keep your data.

## Privacy
- The [privacy policy](/privacy) explains in detail what is kept and why.
- Only you can see your data. **Cycle** and intimacy data is also visible to your partner if you have linked your accounts.
- Passwords are stored encrypted (argon2); nobody can read them.
