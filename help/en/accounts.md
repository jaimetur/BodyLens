# Accounts and access

Each person has their own BodyLens account, with their data kept separate from everyone else's. You sign in with your username (or your email) and your password.

## Signing in
- **Sign-in screen** (`/login`): your username or the email of your account, and your password. If you fail several times in a row, you have to wait a few minutes.
- **Session**: lasts 90 days in that browser. To sign out, go to "Your account" → **Sign out** (this also deletes the data stored in that browser).
- **Pending account**: if your request is not approved yet, signing in tells you that you will get an email once it is.
- **Initial account of a new deployment**: while the `admin` account keeps its default password (`admin123`), the sign-in screen shows it with a **Use** button. It disappears once you change the password.

## Creating an account with a subscription
- On the website: the home page (`/`) shows what BodyLens does and its prices; **Start free** opens the sign-up (`/alta`). In the Android app: on the sign-in screen, **create it with a subscription**.
- **Plans**: €1.49 per month or €12 per year (€1 per month), both with a **7-day free trial**. On the website you pay by card, Google Pay or Apple Pay (on Stripe's secure page); in the Android app, through Google Play.
- **Information requested**: full name, email, username and password, and accepting the [terms](/terms) and the [privacy policy](/privacy). The account is created as soon as the payment page confirms the subscription, and you are signed in.
- If a subscription ends or a payment fails, the app asks you to renew it (`/alta`) and you are warned by email three times, a week apart; seven days after the third warning, the account and its data are deleted.

## Requesting an account
- On the sign-in screen, **Don't have an account? Ask for one**.
- **Information requested**: username (lowercase letters, numbers, dot, hyphen), full name, a valid email (it cannot already belong to another account), password (at least 4 characters) and an optional message.
- **What happens next**: the account stays pending; the administration receives an email and approves or rejects it. You get one email when you request it and another when it is decided.

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
- **Subscription** (accounts with a subscription): the plan, until when it is active and **Manage**: on the website, Stripe's page to change the card, download invoices or cancel; in the app, Google Play's subscriptions. If you have been warned of a missed payment, it says how many warnings you have had, with **Renew**.
- **Privacy and terms**: links to the [privacy policy](/privacy), the [terms of use](/terms) and [how to delete an account](/delete-account).
- **Delete my account**: type your password and confirm. Your account and all its data are deleted at once and any subscription is cancelled. It cannot be undone: download a copy first in Data and backups if you want to keep your data.

## Privacy
- The [privacy policy](/privacy) explains in detail what is kept and why.
- Only you can see your data. **Cycle** and intimacy data is also visible to your partner if you have linked your accounts.
- Passwords are stored encrypted (argon2); nobody can read them.
