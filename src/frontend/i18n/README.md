# BodyLens translations

BodyLens is translated with a simple English catalog. You do not need to know Spanish or read any code.

## Files

| File | What it is |
|---|---|
| `catalog.json` | Every message of the app in English (the base language). |
| `locales/<lang>.json` | One file per language: `{"English message": "translation"}`. |
| `locales/es.json` | Spanish. Special: the app code itself is written in Spanish, so these values must match the code exactly. Do not edit it to change wording. |
| `i18n.js` | The translator that runs in the browser. |

## Add a language

1. Copy any existing locale (for example `locales/fr.json`) to `locales/<code>.json`, where `<code>` is the
   two-letter ISO 639-1 code (`pl`, `sv`, `ko`…).
2. Replace every value with your translation. Keep the keys (the English messages) unchanged.
3. Add the language to `LANGS` in `src/backend/app/core/i18n.py` (with its own name, e.g. `"pl": "Polski"`) and to
   `LOCALES` in `i18n.js` (its locale for numbers and dates, e.g. `pl: 'pl-PL'`).
4. Run `python3 tools/i18n_check.py <code>` until it prints `OK`.

## Rules

- `{0}`, `{1}`… are placeholders for numbers, dates, names or other pieces of text. Keep every one; you may
  change their order.
- Many messages are fragments of a sentence (text cut around a number or a bold word). Translate them so they read
  well in place, and keep leading or trailing punctuation.
- Keep units (kg, km, kcal, h, min, %), emoji and product names (BodyLens, Withings, Health Connect, Apple Watch…).
- Address the user informally if your language distinguishes (like German *du*, French *tu*).
- A missing translation is shown in English, so a partial file still works.

## Improve a translation

Edit the value in `locales/<lang>.json` and run `python3 tools/i18n_check.py <lang>`.
