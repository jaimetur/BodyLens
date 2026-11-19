# Sleep

Use it to see how you sleep: last night, your sleep balance, progress, schedule and analysis. It includes naps, sleep stages and comparisons with your weight.

## Source of the data and rules for nights

- Sleep comes mainly from **Apple Health** (iPhone, through Health Auto Export) or **Android** (Health Connect, through the BodyLens app): nights from AutoSleep or the Apple Watch (iPhone) or from your Android health app, and naps. **Withings** fills in the nights that Health does not have.
- **Night window**: the night of a given day is the one that ends between 17:00 the day before and 17:00 of that day. It must end after 03:00; anything that ends earlier is treated as a nap. Each night is assigned to the day you wake up.
- **Episodes**: two bouts of sleep separated by more than 90 minutes are different episodes. Two night episodes separated by 4 hours or less are merged and the gap counts as a sleepless spell.
- **Sleepless spells**: gaps of at least 10 minutes within the night.
- **Source of the night**: schedule, time asleep and sleepless spells from AutoSleep if available; if not, from the Apple Watch; if not, from the source with the most sleep. If the Watch clearly records more sleep than AutoSleep, the Watch takes precedence. Stages (deep and REM) come from the Watch.
- **Naps**: episodes of at least 10 minutes outside the night. On the naps card, the day runs from 20:00 the day before to 20:00.
- If Health resends a night (for example, AutoSleep redoes it when you wake up), the latest version replaces the previous one.

## Tabs

- **Night**, **Balance**, **Progress**, **Schedule** and **Analysis**. The app remembers the last one you opened.

## Period

- The floating selector (1 wk to All) is shared with the other sections. With **1 wk** you navigate week by week with arrows; with longer periods, nights are shown as bars or a calendar.

## Night

- **Last night** (or the one chosen in the week strip, or in the period's bars or calendar): time asleep in large type, efficiency (percentage of time in bed that you sleep) and time in bed.
- **View** switch: colours the nights by **Score** (default) or by **Hours**.
- **Sleep clock**: arc with your bedtime and wake-up time, your usual schedule dashed and the sleepless spells. Tapping it enlarges it.
- **Score** (0 to 100): sum of four parts.
  - 50 points for duration compared with your hours goal.
  - 20 for efficiency (0 if it is 70 % or less, full at 95 %).
  - 15 for deep sleep (full with 15 % or more of the time asleep).
  - 15 for regularity of your bedtime compared with your median of the last 90 days (no penalty up to 45 minutes of difference).
  - Colour: green from 75, amber from 50, red below. In Hours mode: green if you reach the goal, amber if you are less than 1 hour short, red if more.
- **Stages**: bar and legend with Deep, Light, REM and Awake for the night.
- **Overnight Apple Health / Android data** (if it arrived): overnight SpO2 with its minimum, overnight HRV and respiratory rate.
- **Figures for the night**: sleeping heart rate (with its minimum), awakenings and time awake, and your bedtime and wake-up time compared with the goal in Goals, plan and meals (with how many minutes earlier or later).
- **Sleep balance**: link to the Balance section with your current balance.
- **Note for the day**: box to add a comment (up to 300 characters).
- **Naps**: list of the day's naps with time, duration and heart rate, and a strip that places them next to the night. Naps add to the sleep balance.
- **Wellbeing from last night**: gauge-style indicators for the night (time asleep, preparation, sleeping heart rate, consistency, efficiency, deep sleep, awakenings and recommended bedtime for tonight). They are calculated from your last few weeks and need at least 3 nights.
  - **Preparation** (0 to 100): 45 % night score, 30 % balance of the last week and 25 % sleeping heart rate compared with your last nights. Labels: Low, Fair, Good, Excellent.

## Balance

- **Sleep balance**: what you have slept in the last 7 nights, plus naps, compared with your goal per night. Nights without data do not count (nor does their goal). Positive is a surplus; negative, a debt. The ring shows the percentage and the text says how much you slept out of how much you needed. It also shows 7- and 14-night plans to pay off the debt.
- **Balance progress**: each point is the balance of the previous 7 nights; the bands and the red dots are weekends.
- **Night by night**: what each night adds or subtracts (naps included). On nights without data, **Add** appears: you can log by hand the time you went to bed and got up (the night must last between 30 minutes and 20 hours). If the real night from Withings or Apple Health arrives later, it replaces it. Nights logged by hand can be edited or deleted.
- **In numbers**: average slept, nights on goal, current streak, days in debt, worst balance and naps contributed.
- **Which nights put you in debt**: average balance by day of the week.
- **How debt affects you**: compares your days with a lot of debt with the days when you are up to date in HRV, resting heart rate, steps, meal score and score (needs at least 5 days of each type).
- **Plan to pay off the debt**: if there is debt, a table with how much to sleep each night and what time to go to bed to pay it off in 3, 5, 7, 10 or 14 nights. It uses your average efficiency of the last month.
- Tapping the balance card opens the report, with the target bedtime and wake-up time.

## Progress

- **Historical**: tabs **Score**, **Quality** (deep plus REM), **Sleep** (hours), **Deep**, **When you go to bed** and **Heart rate**. It shows bars for the period and a calendar of up to 18 weeks; tapping a day selects it.
- **Figures for the period**: time asleep, time in bed and efficiency, median time you fall asleep and wake up, regularity of your bedtime, nights that reach the goal and breakdown of deep, REM and light.
- **Hours of sleep** per night with the goal line.
- **What your sleep says**: sentences with your own data.
- **Trend**: monthly median of how much you sleep and its 3-month average, using your whole history.
- **What time you sleep**: monthly median time you fall asleep and wake up.

## Schedule

- **Schedule**: from when you fall asleep until you wake up, night by night. In green, what you slept up to your target wake-up time; in red, what you slept after it (the weekend is measured with its own schedule). Dashed lines: your usual time; solid lines: the moving average.
- **Sleep stages**: hours of each stage per night (Apple Watch).
- **By night of the week**: average hours slept according to the day you go to bed.

## Analysis

- **Sleep calendar**: hours for the last 16 weeks, more intense the more you sleep.
- **How much you sleep**: breakdown of the period's nights by hours slept.
- **Weekdays and weekends**: Sunday to Thursday nights compared with Friday and Saturday.
- **Quality: deep and REM sleep**: share of each week in deep and in REM.
- **Sleep and weight**: how much you weigh in the morning compared with the surrounding days, according to how you slept that night (using your whole history).

## Goals

The goal for hours per night (7 h by default, between 4 and 12) and the target schedule for going to bed and waking up (weekdays and weekends; 00:00 and 07:00 by default) are changed in Goals, plan and meals → Goals and plan.
