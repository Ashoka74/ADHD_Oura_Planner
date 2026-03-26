---
name: anomaly-check
description: Quick Oura anomaly scan — checks last hour of heart rate and activity for stress spikes, sedentary alerts, or evening activation. Schedules interventions if needed.
argument-hint: ""
---

# Anomaly Check

Quick scan for physiological anomalies. Designed for recurring use (every 15-30 min via Dispatch).

## Step 1: Quick Data Pull

Pull only:
1. `oura_get_heart_rate` — last 1 hour
2. `oura_get_daily_activity` — today only (for step count)
3. `oura_get_daily_stress` — today only

## Step 2: Detect Anomalies

Check against these patterns:

| Pattern | Detection | Intervention |
|---------|-----------|-------------|
| Stress spike | HR > resting+20 for 15+ min, <50 steps | BOX-BREATH 5 min |
| Sustained elevated HR | Avg HR last hour > resting+15, no workout | BODY-SCAN 10 min |
| Post-meeting spike | HR jumps >10 bpm after calendar event | BOX-BREATH or PMR |
| Sedentary alert | <250 steps in 2 hours (9am-9pm) | WALK-BRISK 10 min |
| Evening activation | HR > resting+10 after 8pm, no workout | BREATH-478 5 min |
| Recovery deficit | stress_high > recovery for 2+ days | Morning BREATH-RESONANT |

## Step 3: Calendar Context

Before intervening, check:
- Is user in a meeting? → Queue for after
- Next event in <10 min? → Quick technique only (5 min)
- Free slot available? → Full intervention
- No free slots? → Log anomaly, skip intervention

## Step 4: Intervene or Report

**If anomaly detected AND free slot exists:**
1. Create session event (with step-by-step guide from CLAUDE.md)
2. Create 5-min follow-up check
3. Log to `oura_log_session`
4. Tell user: "Detected [pattern]. Scheduled [technique] at [time]."

**If no anomaly:**
Report: "All clear — HR: [X] bpm, Steps: [X] today"
