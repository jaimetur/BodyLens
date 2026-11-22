# Weight

Use it to follow the progress of your weight against the weight-loss plan: trend, pace, weeks, days of the week, weigh-in calendar and milestones. Weigh-ins come from the **Withings** scale; you can also add manual weigh-ins.

## Tabs

- **Progress**, **Weeks** and **Calendar**. The app remembers the last one you opened, until the PIN lock shows: then it starts again from the first.
- On phones, the explanation of a chart card is behind the ⓘ next to its title: tap the title to show it.

## Period

- The **floating selector** (1 wk to All) is shared with the other sections.
- The "Weight progress" card also has its own selector (4 wk, 3 months, 1 year, All) and "Weight per week" has its own (12 wk, 6 months, 1 year, All).

## Progress

- **Top panel**:
  - **Trend weight**, last weigh-in and its change, and a pill showing how many kg you are ahead of, behind or exactly on the plan (with the estimated weeks of delay, if applicable).
  - **Rings and progress bar**: your progress (green) against the progress expected by the plan (grey), with marks at the milestones and your position between the starting weight and the goal.
  - **Changes**: 7 days, 30 days, the chosen period (90 days if it is shorter) and the total since the start of the plan.
  - **Mini chart**: the trend of the last weeks with the plan line.
  - **Key figures**: lost so far, left to go, next milestone (with an estimated date at your pace), 4-week pace, BMI and body fat if there is data.
- **Weight progress** (chart):
  - **Daily weigh-in**: one dot per weigh-in (hollow if manual).
  - **Trend**: the smoothed line. It is calculated with exponential smoothing (factor 0.2) that gives more weight to recent weigh-ins.
  - **Weekly plan**: dashed line with the weight expected by the plan.
  - **Projection**: if you are losing, it extends the trend at the pace of the last 4 weeks.
  - **Weight-loss attempts**: green bands over the periods detected as attempts.
  - Tapping a legend item hides or shows it. Hovering or swiping over the chart shows the detail for the day (and the note for the day, if there is one).
- **New manual weigh-in**: each field shows your last value as a reference (empty if there is none). On a phone, tapping a number opens a wheel (only a deliberate tap: touching it while you scroll does not open it): slide it up or down to change the value and press **Done** (or **Keyboard** to type it). With no earlier value, the wheel starts at a typical value for your sex, age and height (Your account → Personal data). Date, weight and, if you want, fat, muscle, water and bone, for days without a scale weigh-in (or if you have no Withings scale). If a scale weigh-in arrives for that day later, the scale's one takes precedence. Below, the manual weigh-ins are listed with **Edit** and **Remove**. Without any weigh-in yet, Weight shows only this card and a short note. On phones this card goes to the end of the tab.
- **Figure cards**: **4-week pace** and **2-week pace** (regression of the weigh-ins), **Compared with the plan**, **Pace needed** to reach the goal by the plan's date, **Next milestone**, **Final goal** (date at your pace and the plan's), **Daily noise** (typical swing from one day to the next) and **Streak** of weeks going down.

## Weeks

- **Weight per week**: each dot is the median of your weigh-ins for the week (Monday to Sunday) and the bar goes from the lowest to the highest weight. Green if it went down compared with the previous week; red if it went up.
- **Week by week**: change of each week compared with the previous one since the start of the plan.
  - Choose the week: **Mon–Sun** or **Sat–Fri**.
  - Choose the metric: **Trend** (trend weight at the end of the week), **Median** or **P20** (20th percentile of the week's weigh-ins).
- **Day-of-week effect**: average difference of each day compared with the days around it, using your whole history. Positive: you usually weigh more that day. A few weeks of data are needed.
- **Weekly control**: table by week (control Friday) with weekly weight (P20), difference, cumulative, plan target, difference from the target, number of weigh-ins and notes. The current week is marked "in progress".

## Calendar

- **Weigh-in calendar**: last 16 weeks. The colour shows the change from the previous weigh-in (green down, red up, up to ±1 kg). Friday is marked in the header as the control day. On the right, the change for each week; below, the total and the average for each day of the week.
  - A sentence summarises which day goes down the most and which goes up the most (only with at least 4 weigh-ins per day).
- **Plan milestones**: intermediate goals with the date expected by the plan and the one given by your actual pace. Each milestone appears as **Achieved**, **On time** or with the weeks of delay. The achieved ones and the next six are shown.

## Notes

- The notes for the day (the ones you write on the Activity and Sleep cards) appear on the weight chart and in the weekly control table.
