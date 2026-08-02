# Model Card: Glitchy Guesser Autonomous Agent

This document reflects on the limitations, risks, and AI-collaboration process
behind the `GuessAgent` built for this project. It is separate from
`README.md`, which covers what the system does and how to run it.

## Limitations and Biases

The agent's guardrail is designed to catch **logical inconsistency**, not
**correctness**. During testing, a version of `check_guess` was created that
swapped "Too High" and "Too Low" on every single call. Because the swap was
applied consistently, every hint stayed internally consistent with the last —
the agent's tracked range never contradicted itself, it just steadily narrowed
in the wrong direction until it ran out of attempts. The guardrail only
detected a problem once the range became mathematically invalid
(`low > high`), and even then, only after several attempts had already passed
with confidently wrong guesses.

This means the guardrail is better at catching **intermittent or partial**
corruption than a **fully systematic** bias. A hint source that is wrong in
exactly the same way every time can look trustworthy for a surprisingly long
time. This is a real limitation, not just a hypothetical one: it directly
mirrors how a subtly biased AI system can seem reliable if its errors are
consistent rather than random.

The agent's strategy (binary search) also assumes the *underlying game* is
well-behaved — a range that can be cleanly bisected. It would not generalize
to a fundamentally different kind of game logic without rework.

## Potential Misuse and Mitigation

This is a low-stakes educational project, so the direct misuse risk is small.
That said, the general pattern is worth naming: an agent could be presented as
"guardrail-verified" or "reliability-tested" based on a suite that only checks
for one narrow failure mode (self-contradiction), which could create false
confidence in a system that still has a systematic, undetected bias. The
mitigation used here is running the agent against **deliberately reintroduced
bugs** (see `test_guardrail_demo.py`), not just clean runs — a reliability
claim is only meaningful if you've also tried to make it fail.

## What Surprised Me During Reliability Testing

The first version of the guardrail passed all 20 clean-run trials with zero
anomalies, which looked like strong evidence it worked. It was only when a
known-broken version of `check_guess` was deliberately substituted in as a
test that a real gap showed up: a systematically wrong hint pattern produced
**zero flagged anomalies** on the first guardrail design, even though the
agent never won a single game against it. Passing all your tests only shows
your guardrail didn't fire on the inputs you happened to test — it does not
show it would catch every kind of failure. That distinction was the biggest
surprise of the reliability testing process.

## AI Collaboration

**A flawed suggestion:** the first guardrail design (built with AI assistance)
only checked whether a single hint was individually plausible given the
agent's current tracked range. This looked reasonable and passed all initial
clean-run tests, but it failed to catch a real bug pattern — a consistently
swapped hint direction — because that pattern never produced a hint that was
implausible *on its own*, only a range that became invalid after several
guesses accumulated. I verified this by running the agent against a
deliberately broken `check_guess` and observing zero anomalies where there
clearly should have been some.

**A helpful correction:** once that gap was identified, the fix — checking
whether the range became invalid (`low > high`) after narrowing, rather than
only checking each hint in isolation — was suggested and correctly resolved
the issue. Re-running both the clean 20-trial suite and the deliberately
broken test cases confirmed the fix worked without introducing false
positives on legitimate games.

The overall lesson: AI-suggested guardrails and tests can look sufficient
while quietly missing an entire failure mode, and the only way to find that
out is to deliberately test against known-bad inputs rather than trusting a
clean run.
