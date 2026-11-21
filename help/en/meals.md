# Meals

Use it to record what you eat each day and score it, and to see how much it should affect your weight according to a formula, compared with what the scale shows the next day. Weights come from the **Withings** scale; you write the meals yourself.

## Tabs

- **Today**, **Log** and **Analysis**. The app remembers the last one you opened, until the PIN lock shows: then it starts again from the first.
- On a phone, the explanation of a chart card waits behind the **ⓘ** next to its title (tap the title to show or hide it).

## Period

- The floating selector (1 wk to All) is shared with the other sections and controls the figures, bars and lists.

## Today

### Log for the day
- Choose the day in the strip of the last 4 weeks, Monday to Sunday (the arrows jump 4 weeks), with the date picker or with **Today**. Days with entries have the colour of their score.
- **Breakfast**, **Lunch** and **Dinner**: add several dishes by typing and pressing Enter. The dishes you have typed most are suggested. The dishes of one meal can be moved to another.
- **Food indulgences** and **Drink indulgences**: each indulgence has a quantity. They count automatically up to a cap of −5.
- **Sport** and **Note**: free text.
- **Scores**: press a value for each item; pressing it again removes it.
  - Breakfast, Lunch, Dinner, Water and Sport: from 0 to 5.
  - Food and drink indulgences: from −5 to 0. They are calculated automatically from what you have entered; if you press a value you set it by hand and, if you press it again, they count automatically again.
- Next to the day, the weight for the day, steps, sleep and workouts are shown as context. Changes are saved immediately.

### Estimated loss
- Ring with the **score for the day** (in %), split into what adds (green) and what subtracts (red).
- **Estimated and actual**: the loss estimated by the formula for the day and, next to it, the actual change on the scale between that day's morning and the next one's (only if you weigh yourself on both days). What you eat one day shows up on the scale the next morning, which is why the week strips are organised by weigh-in day.
- **Perfect day**: what the formula would estimate with a score of 100 %.
- **Week strips**: one with the estimated loss and one with the actual loss, with arrows to move between weeks and the **Today** button to go back.
- **Figures**: estimated and actual for the week, since the start of the plan, estimated pace over the last 14 days and the date you would reach the goal at that pace.
- With periods longer than a week, the panel summarises the period and you can navigate by period.

## Log

- **Your log**: days logged, average score, days with a score of 70 % or more and days with indulgences. Bars of the score per day (goal line at 70 %). Tap a day to view or change it.
- Table for the period with day, weight, breakfast, lunch, dinner, indulgences, sport, score and estimated loss (there is also a list version).
- **What you repeat most**: the dishes and indulgences you have logged most often in the period, by meal.

## Analysis

- **Estimated and actual loss**: chart since the start of the plan with three lines: **Actual**, **Estimated** and **Estimated without switching to the actual one** (the cumulative estimate is not allowed to get ahead of the actual one). It needs your plan (starting weight, goal and start date) and at least two weigh-ins. Below it, the formula in use and a link to adjust it.
- **What you eat and your weight**: median weight change the next day according to the score for the day (under 40 %, 40 to 69 % and 70 % or more). At least 8 days with a score and with a weight the next day are needed.

## How it is calculated

- **Score for the day**: weighted average of the scores. Unscored meals count as the default score (3, adjustable); water, sport and unscored indulgences count as 0. Indulgences subtract with their own penalty. The result is expressed as a % of the maximum possible, rounded.
- **Estimated loss for the day** = factor × (goal − weight) ÷ goal × score for the day. With the "neutral" model, a normal day (breakfast, lunch and dinner at 3, with no water, sport or indulgences) keeps your weight: it only estimates loss if you do better and gain if you do worse.
- The formula weights, the penalties, the factor and several options (count days without a weigh-in, count days without meals logged, use the classic model) are changed in Goals, plan and meals → Meals.
