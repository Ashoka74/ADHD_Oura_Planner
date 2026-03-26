---
name: evening-winddown
description: Evening check — reviews stress accumulation, current HR, and sleep timing to schedule a wind-down breathing session and recommend a target bedtime.
argument-hint: ""
---

# Evening Wind-Down Check

Use around 9-10pm local time to prepare for sleep.

## Step 1: Evening Data Pull

1. `oura_get_daily_stress` — today's stress_high vs recovery minutes
2. `oura_get_heart_rate` — last 30 min (is HR winding down?)
3. `oura_get_daily_sleep` — last 3 days (for sleep timing trend)
4. `gcal_list_events` with `q="[Recovery]"` — any wind-down already scheduled?
5. `gcal_list_events` for tomorrow — when is first event? (to calc target wake time)

## Step 2: Assess Evening State

- **HR elevated?** Current HR > resting + 10 bpm = still activated
- **Stress accumulated?** stress_high > recovery = unresolved stress
- **Wind-down exists?** Check for existing [Recovery] blocks tonight
- **Sleep timing trend?** Look at timing contributor from sleep scores

## Step 3: Intervene if Needed

If HR still elevated OR no wind-down scheduled:
1. Schedule BREATH-478 (5 min) for 30 min from now
2. Add follow-up check
3. Recommend target bedtime:
   - Tomorrow's first event minus 8 hours minus 30 min buffer
   - But no later than midnight if sleep timing has been poor

## Step 4: Report

```
Evening Check — [time]

Stress today: [X] min high / [X] min recovery
Current HR: [X] bpm ([elevated/normal])
Wind-down: [scheduled at X / already exists / not needed]
Target bedtime: [time] (first event tomorrow: [time])
```
