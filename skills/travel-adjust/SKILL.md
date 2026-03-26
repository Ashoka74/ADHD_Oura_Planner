---
name: travel-adjust
description: Adjust wellbeing schedule for a new timezone or location — detects jet lag from sleep data, recalculates session times, and creates adjusted calendar events.
argument-hint: "<city or timezone>"
---

# Travel / Timezone Adjustment

Use when arriving somewhere new to recalibrate wellbeing sessions.

## Step 1: Detect Current Location

1. Check sleep data timestamps — what timezone offset do they show?
2. `gcal_list_events` — what timezone does the calendar use?
3. User argument tells us the destination city/timezone

## Step 2: Assess Jet Lag

1. `oura_get_sleep` — last 2-3 nights
2. Compare bedtime/wake time against local timezone
3. If bedtime is >2 hours off from local midnight = jet lag detected

## Step 3: Adjust Recommendations

- **Wind-down time**: recalculate for local timezone
- **Morning session**: based on actual wake time here (not home timezone)
- **If jet lag detected**:
  - Extra BREATH-RESONANT in the morning (HRV recovery)
  - Earlier BREATH-478 wind-down (shift sleep timing)
  - WALK-BRISK midday (reset circadian rhythm with movement + light)

## Step 4: Update Calendar

1. Remove or reschedule any wellbeing events set to wrong timezone
2. Create adjusted sessions for today
3. Report the timezone delta and adjusted schedule
