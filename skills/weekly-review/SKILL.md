---
name: weekly-review
description: Weekly effectiveness analysis — reviews all sessions from the past 7 days, identifies best techniques by HR delta and rating, analyzes sleep/stress trends, and suggests adjustments.
argument-hint: ""
---

# Weekly Effectiveness Review

Run on Sundays to analyze what's working.

## Step 1: Gather Week Data

1. `oura_get_session_log` — all entries from past 7 days
2. `oura_get_daily_sleep` — past 7 days
3. `oura_get_daily_readiness` — past 7 days
4. `oura_get_daily_stress` — past 7 days
5. `oura_get_daily_activity` — past 7 days

## Step 2: Analyze Sessions

- **Best technique by HR delta**: which technique consistently drops HR the most?
- **Best technique by user rating**: which does the user prefer?
- **Completion rate**: what % of sessions were completed vs skipped?
- **Most skipped**: any technique consistently skipped? (maybe remove it)
- **Untried techniques**: what haven't we tested yet?

## Step 3: Analyze Trends

- **Sleep scores**: improving / stable / declining over the week?
- **Readiness scores**: same trend analysis
- **Stress minutes**: is stress_high decreasing over the week?
- **Activity**: are step counts recovering?
- **Sleep timing**: is the timing contributor improving?

## Step 4: Present Weekly Summary

```
## Weekly Wellbeing Review — [date range]

### Session Effectiveness
| Technique | Sessions | Avg HR Delta | Avg Rating | Completion |
|-----------|----------|-------------|------------|------------|

Best performer: [technique] (avg -X bpm, rating X/5)
Most skipped: [technique] — consider removing?
Not yet tried: [list] — try these next week

### Trend Dashboard
| Day | Sleep | Readiness | Stress (min) | Steps |
|-----|-------|-----------|-------------|-------|

Overall trajectory: [improving / stable / declining]

### Recommendations for Next Week
- [specific adjustments based on data]
```
