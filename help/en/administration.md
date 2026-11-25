# Administration

Only for administrator accounts. It is in "Your account" → **Administration**.

## Users
- All the accounts on the server. The **switch** on each row enables or disables the account (a disabled account cannot sign in, but its data is kept). You cannot disable your own.
- Next to each name, how the account was made: the **invitation code** it used (or "Free from the administration") with the end of its free time, or its **subscription**: on the website (monthly or yearly, and how it is paid: card brand and last digits, Google Pay or Apple Pay) or in Google Play (monthly or yearly).
- **Edit**: username, full name, email and, if you want, a new password (typed twice; empty = unchanged). Changing the password signs out that account's open sessions.
- **Reset password**: sets a temporary one, emails it to the person and asks them to change it when they sign in.
- **Make admin / Remove admin** and **Delete** (deletes the account and all its data).

## Business
The figures of the service and, below them, its settings (payments, subscriptions, API keys, email and legal details), which used to have their own tabs.

- **Period**: 7 days, 30 days, 12 months or since the beginning. **Refresh** asks Stripe and Google Play again (otherwise their figures are kept for a few minutes). Each box says where its figures come from and when they were taken; a service that is not set up says **Not configured** and links to its setting, and one that fails shows its error without affecting the rest.
- **Users**: accounts and couples, sign-ups in the period (with a chart per day or per month) and accounts active in the last 7 and 30 days (counted since this version was installed).
- **Subscriptions**: paying, in trial, cancelled or expired and read-only; per plan (monthly or yearly) and per channel (website or Google Play); free access (for life or given by the administration); invitation codes used and places left in the launch offer. Google Play does not say whether a subscription is in its trial, so it counts as paying.
- **Revenue**: the monthly recurring revenue at list prices (yearly plans count ÷ 12), split by channel. From **Stripe**: collected and refunded in the period, net revenue per month, trials that became paying and cancellations. From **Google Play**: its monthly earnings reports (net of Google's fee), which Google publishes around the 5th of the next month.
- **Downloads**: downloads of the BodyLens and BodyLens Bridge APKs from this server, and, from Google Play's statistics reports, installs, users who have installed it and devices with the app (Google publishes them a few days late).
- **Versions in Google Play**: the version on each track (internal test, closed test, production).
- **Health**: last backup, whether outgoing email is set up and free disk space.
- Saved keys are kept encrypted on the server and are never shown whole: only that they are configured and their last characters.

### Payments · Stripe
- For accounts paid on the website (card, Google Pay, Apple Pay), at €1.50 per month or €12 per year with a 7-day free trial.
- Paste your Stripe **secret key**: the server creates the BodyLens product and its two prices in Stripe if they do not exist yet. Then create a webhook in Stripe (Developers → Webhooks) with the address shown here and the events `checkout.session.completed` and `customer.subscription.*`, and paste its **signing secret**. **Test connection** checks the key.
- A test key (`sk_test_…`) lets you try everything with Stripe's test cards; switch to the live key to charge for real.
- Accounts that stop paying get three emails, a week apart, and are deleted seven days after the third one; the administrators are never deleted this way.

### Google Play
- For accounts paid with a subscription in the Android app. Paste the **JSON key of a service account** with access to the Play Console; the server uses it to check each purchase with Google and to cancel the subscription of an account that is deleted. The package (`app.bodylens.android`) and the subscription ID (`bodylens`) come filled in. While it is not set, the app does not offer to subscribe. **Test connection** checks that Google lets the service account reach the app.
- **Google Play reports bucket**: Google Play's downloads and earnings come from the reports Google leaves every month in a Google Cloud Storage bucket. In Play Console, go to "Manage account > Play apps reports", choose "Statistics", click "Copy Cloud Storage URI" next to the section header and paste it here (it starts with `pubsite_prod_rev`). The service account needs, for the whole account, permission to view app information and to view financial data. **Test the reports** checks that it can read them.

### Subscriptions
- BodyLens has a single subscription, with a monthly and a yearly plan and a free trial. The website's plans and prices are created in Stripe by the server; Google Play's are those of the `bodylens` subscription in Play Console. Free access is given in Users → Edit, and the promotion codes and the launch offer are in Invitations.

### Withings
- BodyLens connects to Withings through a free developer application, created once at developer.withings.com (a public API application), with the **return address (callback URL)** shown in this block.
- Withings then gives two values: the **Client ID**, which identifies the application, and the **Client secret**, its password (do not share it). Copy them here and press **Save**; then each account connects its scale in Your account → Data sources.

### Translator
- The help, the README and the changelog are translated automatically into each account's language with LibreTranslate, which runs on this server; optionally, an Anthropic API key is used when LibreTranslate is not available.

### Email
- Email is sent from the mailbox configured here or on the server (`SMTP_*` variables). **Send me a test email** checks that it works.

### Legal details
- The controller of the data (your name or your brand), a contact email for privacy and, optionally, a postal address. They appear at the top of the public pages [privacy policy](/privacy), [terms of use](/terms) and [deleting an account](/delete-account), which Google Play asks for to publish the app.

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
- In the Invitations tab, **Invitation codes**: each code with its **duration**: 1 month, 3 months, 6 months, 1 year, for life or until a date you choose. `INVITACION_AMIGOS`, for life, by default. Whoever signs up with one gets a free account, without paying, for that time counted from the sign-up day, or until that date (to the end of the last day); you can change its end date later in Users → Edit. A code can also have an **expiry date** and a **maximum of accounts** (both optional, e.g. the first 100 for a promotion): it can be used until the end of that day, or until that many accounts have used it; then it is deleted and is no longer valid, while the accounts already made with it keep their free time. Under the maximum you see how many places are left. **Announce on the website** shows the code on the landing page as a promotion, with its free time and a counter of the places left. A code can have **aliases**, in its **Alias** field, separated by commas (e.g. `LAUNCH` for `LANZAMIENTO`): other names for the same code that share its duration, dates and places; the landing page shows the first alias in every language but Spanish. Capitals, accents and spaces do not matter. **Add code** adds a row, **Remove** takes one away, and **Save** keeps the list.
- **Users → Edit → Free access**: none, **For life** or **Until a date** (the end of that day). When it is over, the account is treated like an unpaid subscription: it can only renew, download its data or delete itself, it gets three warnings a week apart and is deleted seven days after the third one. The list shows each account's free access and subscription.

## Default `admin` account
- Every new deployment creates the `admin` account once, with the password `admin123`, which appears on the sign-in screen until it is changed. **Change it** right after deploying; if you delete it, it is not created again.

## From the console
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
