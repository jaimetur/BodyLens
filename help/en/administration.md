# Administration

Only for administrator accounts. It is in "Your account" → **Administration**.

## Users
- All the accounts on the server. The **switch** on each row enables or disables the account (a disabled account cannot sign in, but its data is kept). You cannot disable your own.
- **Edit**: username, full name, email and, if you want, a new password (typed twice; empty = unchanged). Changing the password signs out that account's open sessions.
- **Reset password**: sets a temporary one, emails it to the person and asks them to change it when they sign in.
- **Make admin / Remove admin** and **Delete** (deletes the account and all its data).

## Access requests
- List of accounts requested from the sign-in screen, with name, username, email, date and message.
- **Approve**: the account is activated and the person receives an email with the link to sign in.
- **Reject**: the request is deleted and the person receives an email.
- Each new request is emailed to the administrator accounts that have an email.

## Invitations
- **Create invitation**: generates a single-use sign-up link (optional: a note to remember who it is for). The link is shown only once: copy it.
- The list shows whether each invitation is pending, used (and by whom) or expired.

## Accounts and sources (phase 1)
- For each account: **Google Sheet ID** (shared as a reader with the server's service account) and **Apps Script URL** (`https://script.google.com/…/exec`).
- Only the administration can change them, so that nobody can read another person's sheet.

## Email
- Email is sent from the mailbox configured on the server (`SMTP_*` variables). **Send me a test email** checks that it works.

## Default `admin` account
- Every new deployment creates the `admin` account once, with the password `admin123`, which appears on the sign-in screen until it is changed. **Change it** right after deploying; if you delete it, it is not created again.

## From the console
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
