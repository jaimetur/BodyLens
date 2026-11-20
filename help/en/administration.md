# Administration

Only for administrator accounts. It is in "Your account" → **Administration**.

## Users
- All the accounts on the server. The **switch** on each row enables or disables the account (a disabled account cannot sign in, but its data is kept). You cannot disable your own.
- **Edit**: username, full name, email and, if you want, a new password (typed twice; empty = unchanged). Changing the password signs out that account's open sessions.
- **Reset password**: sets a temporary one, emails it to the person and asks them to change it when they sign in.
- **Make admin / Remove admin** and **Delete** (deletes the account and all its data).

## Access requests
- Requests made before accounts were created with a subscription or an invitation code (no new ones arrive).
- List of accounts requested from the sign-in screen, with name, username, email, date and message.
- **Approve**: the account is activated and the person receives an email with the link to sign in.
- **Reject**: the request is deleted and the person receives an email.
- Each new request is emailed to the administrator accounts that have an email.

## Invitations
- **Create invitation**: generates a single-use sign-up link (optional: a note to remember who it is for). The link is shown only once: copy it.
- The list shows whether each invitation is pending, used (and by whom) or expired.

## Invitation codes
- In the Invitations tab, **Invitation codes**: one per line (`INVITACION_AMIGOS` by default). Whoever signs up with one gets a free account for life, without paying; capitals, accents and spaces do not matter.
- **Users → Edit → Free access**: none, **For life** or **Until a date** (the end of that day). When it is over, the account is treated like an unpaid subscription: it can only renew, download its data or delete itself, it gets three warnings a week apart and is deleted seven days after the third one. The list shows each account's free access and subscription.

## Email
- Email is sent from the mailbox configured on the server (`SMTP_*` variables). **Send me a test email** checks that it works.

## Legal details
- The controller of the data (your name or your brand), a contact email for privacy and, optionally, a postal address. They appear at the top of the public pages [privacy policy](/privacy), [terms of use](/terms) and [deleting an account](/delete-account), which Google Play asks for to publish the app.

## Google Play
- For accounts paid with a subscription in the Android app. Paste the **JSON key of a service account** with access to the Play Console; the server uses it to check each purchase with Google and to cancel the subscription of an account that is deleted. The package (`app.bodylens.android`) and the subscription ID (`bodylens`) come filled in.
- While it is not set, the app does not offer to subscribe.

## Web payments (Stripe)
- For accounts paid on the website (card, Google Pay, Apple Pay), at €1.49 per month or €12 per year with a 7-day free trial.
- Paste your Stripe **secret key**: the server creates the BodyLens product and its two prices in Stripe if they do not exist yet. Then create a webhook in Stripe (Developers → Webhooks) with the address shown here and the events `checkout.session.completed` and `customer.subscription.*`, and paste its **signing secret**.
- A test key (`sk_test_…`) lets you try everything with Stripe's test cards; switch to the live key to charge for real.
- Accounts that stop paying get three emails, a week apart, and are deleted seven days after the third one; the administrators are never deleted this way.

## Default `admin` account
- Every new deployment creates the `admin` account once, with the password `admin123`, which appears on the sign-in screen until it is changed. **Change it** right after deploying; if you delete it, it is not created again.

## From the console
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
