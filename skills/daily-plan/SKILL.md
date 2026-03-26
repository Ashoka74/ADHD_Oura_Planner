---
name: daily-plan
description: Full daily wellbeing assessment — pulls Oura data (sleep, readiness, stress, activity, HR), checks calendar, scores each dimension, selects recovery techniques, and schedules sessions + follow-up checks.
argument-hint: "[date]"
---

# Daily Wellbeing Plan

Run the full daily planning workflow. Default to today if no date argument.

## Step 1: Gather Oura Data (in parallel)

Pull for today and the past 3 days:
1. `oura_get_daily_sleep` — score, contributors (timing, deep, REM, total)
2. `oura_get_sleep` — detailed sleep periods (HR, HRV, duration, stages)
3. `oura_get_daily_readiness` — score, HRV balance, temperature, recovery index
4. `oura_get_daily_stress` — stress_high minutes, recovery minutes
5. `oura_get_daily_activity` — steps, calories, active minutes
6. `oura_get_heart_rate` — last 24h
7. `oura_get_session_log` with `last_n: 20` — past effectiveness data

## Step 2: Assess Current State

Score each dimension as Green / Yellow / Red:

| Dimension | Green | Yellow | Red |
|-----------|-------|--------|-----|
| Sleep | score >= 85 | 70-84 | < 70 |
| Readiness | score >= 85 | 70-84 | < 70 |
| Stress | high < 60 min | 60-120 min | > 120 min |
| Activity | 7K-15K steps | 4K-7K or >15K | < 4K or >20K+low readiness |

**Overall:** Any Red = Recovery Mode. Two+ Yellow = Easy Day. Else = Full Capacity.

## Step 3: Check Calendar

1. `gcal_list_events` for today
2. `gcal_list_events` with `q="[Recovery]"` and `q="[Wellbeing]"` to find existing blocks
3. `gcal_find_my_free_time` for today with `minDuration: 10`

If wellbeing blocks already exist, offer to update/replace — don't duplicate.

## Step 4: Select Techniques

Read CLAUDE.md for technique library and selection logic. Choose based on:
1. State-based selection (what does assessment say user needs?)
2. Calendar gaps (only propose events in free slots)
3. Effectiveness history (prefer techniques with proven HR reduction)
4. Rotation (don't repeat same technique consecutively)

### Templates by State

**Recovery Mode:**
- Morning: BREATH-RESONANT 10 min
- Post-meeting gaps: BOX-BREATH 5 min
- Afternoon: BODY-SCAN or PMR 10 min
- Movement: WALK-MINDFUL 15 min (gentle, not brisk)
- Evening: BREATH-478 5 min + Wind Down

**Easy Day:**
- Morning: BOX-BREATH or STRETCH-DESK 5 min
- Midday: WALK-BRISK 10 min
- Afternoon: Breathing if stress accumulates
- Evening: Wind Down if sleep timing poor

**Full Capacity:**
- Minimal: one WALK-BRISK + one STRETCH-DESK
- Good day for challenging work — say so explicitly

## Step 5: Present Report

```
## Wellbeing Report — [Date]
### Status: [Overall State]

| Dimension | Score | Status | Trend | Key Insight |
|-----------|-------|--------|-------|-------------|

### Effectiveness Data
Best technique so far: [technique] (avg HR delta)
Techniques not yet tried: [list]

### Proposed Calendar Changes
| Time | Session | Technique | Why |
```

## Step 6: Execute (after user approval)

For each session, create TWO calendar events:

**Session event:**
- Title: `[Recovery] Technique Name` or `[Wellbeing] Technique Name`
- Color: Sage (`colorId: "2"`)
- Reminder: 5 min before (popup)
- Description: Full step-by-step guide from CLAUDE.md

**Follow-up check (5 min after session ends):**
- Title: `[Check-in] How was your [Technique]?`
- Color: Banana (`colorId: "5"`)
- Reminder: at event time (popup, 0 min)
- Duration: 5 min
- Description: Completion + rating questions

After creating events, log each to `oura_log_session`.
