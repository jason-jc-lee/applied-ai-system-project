# Glitchy Guesser: Autonomous Agent Edition

## Base Project

This project extends **Game Glitch Investigator** (Module 1), a Streamlit-based
number-guessing game that was originally delivered with several AI-generated
bugs — swapped hint directions, a secret value that intermittently got
converted to a string, and a scoring function that awarded points on wrong
guesses. The original project's goal was to practice diagnosing, explaining,
and repairing AI-generated code using an AI coding assistant. All three bugs
were identified and fixed in that submission.

## Title and Summary

**Glitchy Guesser: Autonomous Agent Edition** adds an autonomous AI agent that
plays the guessing game on its own, using a binary-search strategy, and
verifies every hint it receives against its own internal guardrail before
trusting it. This matters because it turns a simple bug-fixing exercise into a
demonstration of **trustworthy AI behavior**: an agent that not only acts, but
checks whether the information it's given is even logically possible before
acting on it — and reports when it isn't.

## Architecture Overview

See [`diagrams/architecture.mmd`](diagrams/architecture.mmd) for the full
Mermaid source.

The system has four main parts:

- **Streamlit UI (`app.py`)** — the game interface, unchanged from Module 1
  except for one new button: "Let AI Agent Play."
- **Agent (`agent.py`)** — a `GuessAgent` class that plans its next guess by
  bisecting the current known range, submits it through the existing
  `check_guess()` function, and checks the resulting hint for consistency
  before updating its internal bounds.
- **Guardrail** — before trusting any hint, the agent checks two things: (1)
  is this hint even possible given the range it already knows about, and (2)
  does narrowing the range using this hint produce an impossible state (i.e.
  `low > high`)? Either failure is logged as an anomaly instead of silently
  trusted.
- **Reliability log** — every guess, hint, and any anomalies are recorded in a
  structured log (`GuessLogEntry`), which is what both the UI and the
  reliability test suite read from.

Data flow: **UI → Agent (plan) → `logic_utils.check_guess()` (act) → Guardrail
(check) → updated range → back to Agent for the next guess**, until a win or
the attempt limit is reached.

## Setup Instructions

```bash
git clone https://github.com/jason-jc-lee/applied-ai-system-project.git
cd applied-ai-system-project
pip install -r requirements.txt
python -m streamlit run app.py
```

Then click **"Let AI Agent Play"** to watch the agent play a full game
automatically, or play manually as in the original Module 1 version.

To run the automated reliability suite (20 trials) directly from the command
line:

```bash
python agent.py
```

## Sample Interactions

**Run 1 — 6 attempts, win, no anomalies:**
```
Attempt 1: guessed 50 → Too High (range was (1, 100) → (1, 49))
Attempt 2: guessed 25 → Too Low (range was (1, 49) → (26, 49))
Attempt 3: guessed 37 → Too Low (range was (26, 49) → (38, 49))
Attempt 4: guessed 43 → Too High (range was (38, 49) → (38, 42))
Attempt 5: guessed 40 → Too High (range was (38, 42) → (38, 39))
Attempt 6: guessed 38 → Win (range was (38, 39) → (38, 39))
✅ No guardrail anomalies — all hints were consistent
```

**Run 2 — 7 attempts, win, no anomalies:**
```
Attempt 1: guessed 50 → Too High (range was (1, 100) → (1, 49))
Attempt 2: guessed 25 → Too High (range was (1, 49) → (1, 24))
Attempt 3: guessed 12 → Too Low (range was (1, 24) → (13, 24))
Attempt 4: guessed 18 → Too High (range was (13, 24) → (13, 17))
Attempt 5: guessed 15 → Too Low (range was (13, 17) → (16, 17))
Attempt 6: guessed 16 → Too Low (range was (16, 17) → (17, 17))
Attempt 7: guessed 17 → Win (range was (17, 17) → (17, 17))
✅ No guardrail anomalies — all hints were consistent
```

**Run 3 — guardrail catching a deliberately reintroduced bug**
(see `test_guardrail_demo.py`; this is not part of normal gameplay, it's a
reliability test):
```
=== Case 2: intermittently corrupted hints (guardrail catches it) (secret=13) ===
Attempt 1: guessed 50 -> Too High (range (1, 100) -> (1, 49))
Attempt 2: guessed 25 -> Too Low (range (1, 49) -> (26, 49))
Attempt 3: guessed 37 -> Too High (range (26, 49) -> (26, 36))
Attempt 4: guessed 31 -> Too Low (range (26, 36) -> (32, 36))
Attempt 5: guessed 34 -> Too High (range (32, 36) -> (32, 33))
Attempt 6: guessed 32 -> Too Low (range (32, 33) -> (33, 33))
Attempt 7: guessed 33 -> Too High (range (33, 33) -> (33, 32)) <-- FLAGGED BY GUARDRAIL
Attempt 8: guessed 32 -> Too Low (range (33, 32) -> (33, 32)) <-- FLAGGED BY GUARDRAIL
Won: False | Anomalies detected: 2
 - Attempt 7: guess=33 outcome=Too High -> After narrowing, range became invalid (33 > 32). A prior hint must have been wrong.
 - Attempt 8: guess=32 outcome=Too Low -> After narrowing, range became invalid (33 > 32). A prior hint must have been wrong.
```

## Design Decisions

- **Binary search over random/naive guessing**: guarantees the fastest
  possible convergence given consistent hints, and makes any deviation from
  expected narrowing easy to notice and test.
- **Guardrail checks bound validity, not just single-hint plausibility**:
  the first version of the guardrail only checked whether a single hint was
  individually possible. Testing showed this missed cases where a hint
  looked fine on its own but made the tracked range logically impossible
  once combined with earlier hints. Adding a check for `low > high` after
  narrowing closed that gap. Trade-off: this means an anomaly is sometimes
  detected one attempt *after* the actual bad hint occurred, rather than
  the instant it happens — catching it early would require re-deriving the
  "true" hint from the actual secret, which the agent isn't given access to
  (it only sees what a human player would see).
- **Reusing `logic_utils.py` unchanged**: the agent calls the same
  `check_guess`, `parse_guess`, and `update_score` functions a human player
  uses, rather than reimplementing game logic. This keeps a single source of
  truth for game rules and means any future bug fix to `logic_utils.py`
  automatically applies to both manual and agent play.

## Testing Summary

Automated reliability suite (`python agent.py`, 20 trials, Normal difficulty,
1–100, 8 attempts):

```
trials: 20
wins: 20
win_rate: 1.0
avg_attempts: 6.05
total_anomalies: 0
```

All 20 trials passed with zero guardrail anomalies, confirming the current
`logic_utils.py` gives consistent, non-contradictory hints. Separately, the
guardrail was validated against two deliberately reintroduced bug patterns
(see `test_guardrail_demo.py`): a systematically swapped hint direction and
an intermittently corrupted hint. Both were eventually caught by the
invalid-range check, though the systematic swap wasn't caught until the range
had nearly collapsed — a known limitation noted above and in
`model_card.md`.
