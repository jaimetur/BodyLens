# Settings

Use it to configure the app: profiles and PIN, personal data, goals and weight-loss plan, Meals formula, backups and export to PDF.

## How to open it

- On the computer, in the sidebar: **Settings** (general settings) and **Your account**, which brings together the account and profiles in tabs: **Account**, **Profiles** and **Personal data**.
- On mobile, with the settings icon in the top bar. You can also reach both from the profile button.
- The **✕** button in the top bar closes Settings and returns you to the section and the point of the page where you were.

## Tabs

Settings has two groups of tabs. The last one opened in each group is remembered.

- **Profiles**: Profiles and Personal data.
- **General settings**: Goals and plan, Meals and Data and backups.

---

## Profiles

- Each person has their own data. You switch profile with the profile button (initials and name) next to the title in the top bar, which also offers **Settings**, **Your account** (where profiles are managed), **Administration** (if you are an administrator), **Lock profile** (if the profile has a PIN) and **Sign out**.
- Each profile row lets you set:
  - **Name** and **colour** (the colour and initials identify the profile).
  - **Cycle**: marks which profile receives the menstrual cycle data that arrives from Apple Health. Only one can be marked.
  - **Partner**: links two profiles to each other. When linked, "since" appears to indicate the start date of the relationship; sexual activity of the partner before that date is not counted.
  - **Set PIN** / **Change PIN** / **Remove PIN**: 4-digit PIN for the profile.
  - **Private PIN**: 4-digit PIN for Cycle and intimacy (see below).
  - **Delete** (asks for confirmation with "Sure?"): removes the profile from the list. Its data stays saved in case you create it again with the same name. The main profile cannot be deleted.
- **Add profile**: type a name and press **Add profile**. Switch to it with the profile button.

### Profile PIN
- It is a 4-digit screen lock with a numeric keypad. It **does not encrypt the data.**
- When you open the app or switch to a profile with a PIN, it is asked for. After 5 failed attempts you have to wait 30 seconds.
- The lock screen lets you **Sign in with another profile**.
- **Lock profile** (in the profile menu) asks for the PIN again.
- Signing in with the **normal PIN** opens the profile without Cycle and intimacy; signing in with the **private PIN** opens everything.

### Private PIN
- It protects the Cycle and intimacy section. Until you change it, it is **0000**.
- To change it you must enter the current private PIN and a new 4-digit one other than 0000. **Back to 0000** resets it.
- If the profile has a normal PIN and its own private PIN, when you sign in with the normal PIN the Cycle and intimacy section does not even appear.

### Personal data
- **Height (cm)**: between 120 and 230. It is used for BMI, lean mass index, reference zones and the tape measurement formulas.
- **Sex for the formulas**: Not specified, Male or Female. It is used for fat zones, lean mass index, VO2 max and the tape measurement formulas.
- **Date of birth**: refines the fat and VO2 max ranges to your age band.
- Press **Save profile**.

---

## Goals and plan

### Daily goals
They set the goal lines on the bars and count the days and nights on which you meet them (Activity and Sleep).

- **Steps per day** (1,000 to 50,000; default 8,000).
- **Minutes of exercise per day** (5 to 300; default 30).
- **Active calories per day** (50 to 3,000 kcal; default 400).
- **Sleep per night** in hours (4 to 12; default 7).
- **Target schedule**: bedtime and wake-up time on weekdays and at weekends (default 00:00 and 07:00).
- **Save targets** saves the changes; **Default values** resets them.

### Weight-loss plan
- **Starting weight**, **Final target** (lower than the starting weight) and **Plan start**.
- **Three weekly paces** (kg per week, greater than zero): the plan drops that much each week while you are above 1.35 times the target (first pace), above 1.2 times (second) and above the target (final pace). Defaults: 1, 0.75 and 0.5 kg per week.
- With this, the plan line, the milestones and the comparison in Summary and Weight are drawn.
- **Save plan**. What you change here is kept even if other values arrive.

---

## Meals

- **Meals · your dishes**: all the dishes you have logged, from most to least used.
  - Rename a dish, delete it, merge several into one (select several and press **Merge**) or add new dishes so they appear in the suggestions. There is a search box.
- **Meal score and estimated loss**: the weights of the score for the day and of the estimated loss.
  - **Weights** for breakfast, lunch, dinner, water and sport.
  - **Penalty** for food and drink indulgences.
  - **Default score** for an unscored meal (0 to 5; default 3).
  - **Estimated loss factor** (greater than 0 and up to 5).
  - Checkboxes: a normal day keeps your weight (neutral model); count all days even if you do not weigh yourself (using your last weigh-in); and count days without meals logged with the default score.
  - Formula: estimated loss for the day = factor × (goal − weight) ÷ goal × score for the day.
  - A preview shows the breakdown in % of each item.
  - **Save formula**, **Default values** (neutral model) and **Sheet model** (the reference values the formula was first tuned with).

---

## Data and backups

### Apple Health
- It explains how to set up the **Health Auto Export** app on the iPhone to send the app resting heart rate, HRV, oxygen saturation, respiratory rate, VO2 max, wrist temperature, ECGs and Apple Watch alerts. The data is shown in Body → Heart and in Sleep.
- Summary of the steps: create an automation of type REST API with JSON format, and choose the data (health metrics, ECG and heart rate notifications) and the sending frequency. For history, use Health Auto Export's manual upload.

### Source of the data
- Check figures: **days saved**, **last weigh-in** and when the data was last read.
- Weigh-ins and composition come from the **Withings** scale; sleep, activity and workouts mainly from **Apple Health**.

### Backup
- **Download full copy**: saves a JSON file with everything (weigh-ins, composition, measurements, activity, sleep, workouts, meals, Health data and settings of the current profile). Its name includes the date.
- **Import a backup…**: choose a backup file. A summary is shown (date of the backup and number of days of each type) and two options:
  - **Merge with the current data**: adds what is missing and, if a day is in both places, the backup's version is kept.
  - **Replace all**: leaves your data exactly as in the backup. It asks for an extra confirmation ("Yes, replace all").
  - You can also **Cancel**. If the file is not a backup from this app, you are told.
- **History (CSV)** and **Measurements (CSV)**: export your weight history and your tape measurements as CSV for spreadsheets.

---

## Export to PDF

- It is opened with the **PDF** icon in the top bar (in Settings it offers to export everything).
- Options:
  - **Period**: 1 wk, 1 month, 3 months, 6 months, 1 year or All; it starts with the one of the section you are in.
  - **Orientation**: Portrait or Landscape.
  - **What to export**: **This tab**, **Choose** (a grid by modules and sections, with **Select all** and **Remove all**) or **All**.
- Press **See preview**: A4 pages are generated with the charts as you see them in the app, with the profile name and the period in the header. Tap a page to enlarge it.
- **Download PDF** saves the file; **Change options** goes back.
- The PDF is always made with the light theme.
- The Cycle and intimacy section can only be exported if you have signed in with the private PIN.
