---
name: session-followup
description: Process a completed wellbeing session — collects HR before/after, calculates delta, logs effectiveness, and interprets the result.
argument-hint: "<technique>, <completed yes/partially/skipped>, <rating 1-5>, [notes]"
---

# Session Follow-Up

Process feedback after completing a wellbeing technique session.

## Parse Arguments

Extract from user input:
- **Technique**: which technique was done (e.g., "resonance breathing" → BREATH-RESONANT)
- **Completed**: yes / partially / skipped
- **Rating**: 1-5 (5 = very helpful)
- **Notes**: optional free text

Be flexible with parsing — "resonance, yes, 4" should work fine.

## Step 1: Collect HR Data

1. `oura_get_heart_rate` for 10 min before the session started
2. `oura_get_heart_rate` for 10 min after the session ended
3. Calculate average HR for both windows
4. Compute delta (after - before)

## Step 2: Log to Session Log

Call `oura_log_session` with:
- technique ID
- trigger (what caused this session)
- duration
- hr_before (avg)
- hr_after (avg)
- completed (yes/partially/skipped)
- user_rating (1-5)

## Step 3: Interpret and Report

| HR Delta | Interpretation |
|----------|---------------|
| Drop > 10 bpm | "Excellent — this technique works great for you" |
| Drop 5-10 bpm | "Good — measurable calming effect" |
| Drop 0-5 bpm | "Mild — may need longer duration or different technique" |
| HR increased | "Not ideal — let's try something different next time" |

## Step 4: Comparative Data

If this is the 3rd+ logged session, show a comparison:
- Best technique by avg HR delta
- Best technique by avg user rating
- Techniques not yet tried
