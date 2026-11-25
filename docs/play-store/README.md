# Google Play: store listing and forms

Everything Play Console asks for BodyLens (`app.bodylens.android`), ready to paste. Every image is made with the
synthetic demo account (`tools/demo_data.py`), never with real data. The store files are in `assets/play-store/`:

| File | Where it goes in Play Console | Size |
|---|---|---|
| `icon-512.png` | Store listing → App icon | 512×512 PNG (full square: Play rounds the corners) |
| `feature-1024x500-es.png`, `feature-1024x500-en.png` | Store listing → Feature graphic (Spanish listings / the rest) | 1024×500 PNG |
| `listings/<locale>.json` | Store listing texts of each store language (name, short and full description) | ≤ 30 / 80 / 4000 characters |
| `screenshots/<lang>/phone/*.png` | Phone screenshots, in this order | 7 × 1080×1920 PNG (9:16) |
| `screenshots/<lang>/tablet/*.png` | 7-inch and 10-inch tablet screenshots (the same images for both) | 7 × 1620×2880 PNG (9:16) |
| `screenshots/<lang>/chromebook/*.png` | Chromebook screenshots | 7 × 2880×1620 PNG (16:9) |

**Screenshots in the shopper's language.** Google Play shows each person the listing of their language, with its own
texts and screenshots, and the default one (English, `en-US`) when there is none. So every language of the app has
its own listing: `listings/` has the texts (`es-419` uses the Spanish one and `pt-BR` the Portuguese one) and
`screenshots/<lang>/` the app shown in that language.

**Always up to date.** The screenshots are not in the repository: GitHub Actions takes them again whenever the app's
layout changes (`.github/workflows/play-store.yml`, `tools/store_capture.py`) and leaves them in the
`play-store-media` release. `tools/play-store-media.sh` downloads them to `assets/play-store/screenshots/`.

**Publishing without Play Console** (`tools/play_publish.py`, with the service account in the
`PLAY_SERVICE_ACCOUNT_JSON` secret, see `docs/DEPLOYMENT.md`):
- every Android build of the version branch goes to the **internal test** by itself (`.github/workflows/android.yml`);
- the texts of every language and the phone and tablet screenshots are sent by running the *🛍️ Google Play
  screenshots* workflow by hand with **publish** ticked (or `tools/play_publish.py listing --images
  assets/play-store/screenshots`). Chromebook screenshots cannot be sent through the API: upload them by hand.

## 1. Create the app

- App name: **BodyLens**
- Default language: **English (United States) – en-US**; the other languages are translations of the listing.
- App or game: **App** · Free or paid: **Free** (subscriptions are in-app products).
- Category (Store settings): **Health & Fitness**. Tags: *Fitness tracking*, *Sleep*, *Weight management*.
- Contact details (Store settings): email `bodylens@jtgcloud.com`, website `https://bodylens.jtgcloud.com`.

## 2. Store listing texts

The texts of every language are in `assets/play-store/listings/`; Spanish and English here for reference.

### Spanish (es-ES)

**Name** (30): BodyLens

**Short description** (80):

```
Tu peso, sueño, actividad y corazón en un solo lugar, desde báscula y móvil
```

**Full description** (4000):

```
BodyLens reúne en un solo lugar los datos de tu báscula, tu móvil y tu reloj, y te los enseña de forma clara para que veas cómo evolucionas día a día.

QUÉ PUEDES VER
• Peso y composición corporal: peso de tendencia (sin los altibajos del día a día), grasa, músculo, agua y hueso, con tu plan y tu objetivo.
• Sueño: cada noche con sus fases, despertares y siestas, tu puntuación de sueño, el saldo de horas de la semana y tus horarios.
• Actividad: pasos, distancia, pisos, calorías y minutos de ejercicio, con anillos diarios y tus entrenamientos.
• Corazón y forma física: pulso en reposo, variabilidad (VFC), frecuencia respiratoria, oxígeno en sangre y VO2 máx, comparados con tus últimos 30 días.
• Comidas: registra lo que comes y ve su análisis.
• Ciclo y bienestar: registro del ciclo menstrual, del estado de ánimo y de la intimidad, que puedes compartir con tu pareja si los dos lo decidís.
• Historial: tu evolución año a año y todos tus intentos y etapas.
• Informe en PDF y copia de seguridad de tus datos cuando quieras.

DE DÓNDE VIENEN TUS DATOS
• Android: la app lee tus datos de Health Connect (Samsung Health, Google Fit, Fitbit, relojes Wear OS…) y los envía a tu cuenta cada hora, también en segundo plano.
• Básculas y relojes Withings: se conectan una vez y BodyLens recibe cada pesada al momento.
• iPhone: con Health Auto Export desde Apple Salud.
Si recibes datos de varias fuentes, tú eliges cuál manda y las demás solo rellenan los huecos.

TUS DATOS SON TUYOS
• Sin anuncios, sin rastreadores y sin vender ni compartir tus datos.
• La app solo lee de Health Connect: nunca escribe ni borra nada allí.
• Tus datos viajan cifrados a tu cuenta y puedes descargarlos o borrar tu cuenta cuando quieras.

BodyLens no es un dispositivo médico ni sustituye el consejo de un profesional sanitario.

Necesitas una cuenta de BodyLens. Suscripción de 1,50 € al mes o 12 € al año, con 7 días de prueba gratis.
```

### English (en-GB)

**Name**: BodyLens

**Short description**:

```
Your weight, sleep, activity and heart in one place, from scale and phone
```

**Full description**:

```
BodyLens brings together the data from your scale, your phone and your watch in one place, and shows it clearly so you can see how you are doing day by day.

WHAT YOU CAN SEE
• Weight and body composition: trend weight (without the daily ups and downs), fat, muscle, water and bone, with your plan and your goal.
• Sleep: every night with its stages, wake-ups and naps, your sleep score, the weekly sleep balance and your schedule.
• Activity: steps, distance, floors, calories and exercise minutes, with daily rings and your workouts.
• Heart and fitness: resting heart rate, heart rate variability (HRV), respiratory rate, blood oxygen and VO2 max, compared with your last 30 days.
• Meals: log what you eat and see its analysis.
• Cycle and wellbeing: menstrual cycle, mood and intimacy logs, which you can share with your partner if you both decide to.
• History: your progress year by year and all your attempts and stages.
• PDF report and a backup of your data whenever you want.

WHERE YOUR DATA COMES FROM
• Android: the app reads your data from Health Connect (Samsung Health, Google Fit, Fitbit, Wear OS watches…) and sends it to your account every hour, also in the background.
• Withings scales and watches: connect them once and BodyLens gets every weigh-in at once.
• iPhone: with Health Auto Export from Apple Health.
If you get data from several sources, you choose which one rules and the others only fill the gaps.

YOUR DATA IS YOURS
• No ads, no trackers, and your data is never sold or shared.
• The app only reads from Health Connect: it never writes or deletes anything there.
• Your data travels encrypted to your account, and you can download it or delete your account at any time.

BodyLens is not a medical device and does not replace the advice of a health professional.

You need a BodyLens account. Subscription: €1.50 per month or €12 per year, with a 7-day free trial.
```

**Release notes for the first version** (es / en):

```
<es-ES>
Primera versión de BodyLens para Android: toda la app y la sincronización con Health Connect.
</es-ES>
<en-GB>
First version of BodyLens for Android: the whole app and syncing with Health Connect.
</en-GB>
```

## 3. App content (Policy → App content)

| Section | Answer |
|---|---|
| Privacy policy | `https://bodylens.jtgcloud.com/privacy` |
| Ads | **No**, the app does not contain ads |
| App access | **All or some functionality is restricted** → add instructions: a username and password of a reviewer account with synthetic data (see section 6). Never your own account. |
| Content rating | See section 4 |
| Target audience | **18 and over** only (the privacy policy says it is not intended for people under 16; intimacy logging makes 18+ the safe choice). Not designed for children. |
| News app | No |
| COVID-19 / Government / Financial features | No / No / **My app doesn't provide any financial features** |
| Health apps | Declare it: **Health & fitness** → *Activity and fitness tracking*, *Sleep tracking*, *Nutrition and weight management*, *Period tracking / menstrual health*, *Heart and vital signs monitoring* (tick the ones the form offers). Not a medical device. |
| Data safety | See section 5 |
| Health Connect | See section 7 (declaration form for each permission) |
| Account deletion | Yes, in the app (Your account → Delete my account) and on the web: `https://bodylens.jtgcloud.com/delete-account` |

## 4. Content rating questionnaire (IARC)

- Email: `bodylens@jtgcloud.com`. Category: **All other app types** (not a game, not social media).
- Violence, fear, sexuality (sexual content or nudity), language, controlled substances, crude humour, gambling: **No**.
  The app lets users log their own sexual activity as health data, but it shows no sexual content or imagery.
- Users can interact or exchange content: **Yes**, only between two accounts that link as a couple (they share the
  cycle and intimacy logs). No public content, no chat with strangers.
- Shares the user's location: **No**. Digital purchases: **Yes** (subscriptions).
- Expected result: PEGI 3 / Everyone, with the "Users interact" and "In-app purchases" notes.

## 5. Data safety form

- Does the app collect or share any of the required user data types? **Yes**
- Is all of the user data collected by the app encrypted in transit? **Yes**
- Which of the following methods of account creation does the app support? **Username and password** (accounts are
  created by invitation or approved request; there is no sign-in with Google).
- Can users request that their data is deleted? **Yes** (`https://bodylens.jtgcloud.com/delete-account`)

Data types (all: **Collected** = yes, **Shared** = no, **Processed ephemerally** = no):

| Category → type | Required or optional | Purposes |
|---|---|---|
| Personal info → **Name** | Required | App functionality, Account management |
| Personal info → **Email address** | Required | App functionality, Account management |
| Personal info → **User IDs** (username) | Required | App functionality, Account management |
| Personal info → **Other info** (date of birth, height, sex for the formulas) | Optional | App functionality |
| Health and fitness → **Health info** (heart rate, HRV, blood oxygen, respiratory rate, sleep, menstrual cycle, sexual activity, mood, weight and body composition) | Optional | App functionality |
| Health and fitness → **Fitness info** (steps, distance, floors, calories, exercise, workouts, VO2 max) | Optional | App functionality |
| Financial info → **Purchase history** (subscription plan and state) | Optional | App functionality, Account management |

Not collected: location, contacts, messages, photos, audio, files, calendar, web history, app interactions or
diagnostics, device IDs, and no card details (Google Play handles the payments).

"Shared" is **No**: Google Play (payments) acts as a service provider, and the data never goes to anyone else. The
couple link is chosen by the user between two BodyLens accounts.

## 6. Reviewer account (App access)

Google's reviewers need to sign in. The server has an account only for them: username **`playreview`** (Alex García,
synthetic data made with `tools/demo_data.py`, English, free access for life). Its password is not in the repository;
give it, with the username, in **App access**. Instructions to
paste:

```
Sign in with the username and password above at the first screen (server: https://bodylens.jtgcloud.com).
The account has sample data. Health Connect sync is in Your account → Data sources → Health Connect.
```

## 7. Health Connect permissions declaration

Play Console → **App content → Health Connect permissions**. For every permission, the purpose is the same: the user
sees their own data in their BodyLens account. Justifications to paste:

| Permission | Justification |
|---|---|
| Steps, Distance, Floors climbed, Active and Total calories burned | Show the user's daily activity (steps, distance, floors, calories) and activity rings in the Activity module. |
| Exercise | Show the user's workouts (type, duration, distance, calories) in Activity → Workouts. |
| Sleep | Show each night with its stages, wake-ups and naps, and the sleep score, in the Sleep module. |
| Heart rate, Resting heart rate, Heart rate variability | Show the user's heart rate, resting heart rate and HRV trends in Body → Heart. |
| Oxygen saturation, Respiratory rate, VO2 max | Show blood oxygen, respiratory rate and VO2 max trends in Body → Heart and fitness. |
| Menstruation | Show the menstrual cycle log in the Cycle module (optionally shared with the user's linked partner). |
| Sexual activity | Show the intimacy log in the Intimate module (optionally shared with the user's linked partner). |
| Read health data in the background | Send new data to the user's account every hour while the app is closed, so the dashboards stay up to date. |

The app only reads; it does not write or delete Health Connect data, does not use it for ads and does not sell or
transfer it (as the privacy policy states). Google may ask for a short video of the permission flow.

## 8. Before the first upload

- **Battery exemption** (`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`): Google Play only allows it for a few kinds of apps
  and may reject the release. Remove it from the Play build if Google objects.
- **App signing**: Play App Signing with a key generated by Google; `bodylens-upload.jks` is only the upload key. The
  app from Google Play and the APK from the server are signed differently, so one cannot update the other: uninstall
  first to switch.
- **Android developer verification**: register the package name `app.bodylens.android` in
  Settings → Android developer verification.
- **Trader status**: declared as trader; the public contact email is `bodylens@jtgcloud.com`.
