# Accounts and access

Each person has their own BodyLens account, with their data kept separate from everyone else's. You sign in with your username (or your email) and your password.

## Signing in
- **Sign-in screen** (`/login`): your username or the email of your account, and your password. If you fail several times in a row, you have to wait a few minutes.
- **Session**: lasts 90 days in that browser. To sign out, go to "Your account" → **Sign out** (this also deletes the data stored in that browser).
- **Pending account**: if your request is not approved yet, signing in tells you that you will get an email once it is.
- **Initial account of a new deployment**: while the `admin` account keeps its default password (`admin123`), the sign-in screen shows it with a **Use** button. It disappears once you change the password.

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
- **Password**: asks for the current one; changing it signs you out on your other devices.
- **Partner** and **Sync**: see [partner](couples.md) and [sync](sync.md). Importing backups is in Settings → Data and backups ([import](import.md)).
- **Administration**: only for administrator accounts; see [administration](administration.md).

## Privacy
- Only you can see your data. **Cycle** and intimacy data is also visible to your partner if you have linked your accounts.
- Passwords are stored encrypted (argon2); nobody can read them.
