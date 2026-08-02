"""
agent.py

An autonomous agent that plays the number-guessing game from
Module 1 (Game Glitch Investigator). It extends the original
project with:

  1. An agentic workflow: PLAN (pick a guess) -> ACT (submit it)
     -> CHECK (validate the hint before trusting it).
  2. A guardrail / reliability layer: every hint returned by
     check_guess() is checked against the agent's own tracked
     bounds. If a hint contradicts what the agent has already
     learned, it's flagged as an ANOMALY instead of blindly
     followed.
  3. A structured log of every decision, so the whole run can be
     reviewed afterwards (this becomes your reliability-testing
     evidence for the README).

This module does not replace logic_utils.py -- it calls into it,
the same way a human player would use check_guess() and
update_score(). The agent is a new *consumer* of that logic, not
a duplicate of it.
"""

from dataclasses import dataclass, field
from typing import Optional
from logic_utils import check_guess, update_score


@dataclass
class GuessLogEntry:
    attempt: int
    guess: int
    outcome: str
    message: str
    bounds_before: tuple
    bounds_after: tuple
    consistent: bool
    note: str = ""


@dataclass
class AgentResult:
    won: bool
    final_score: int
    attempts_used: int
    secret: int
    log: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)


class GuessAgent:
    """
    Plays the guessing game using a binary-search strategy and
    guards against inconsistent hints.

    Strategy (PLAN step):
        Always guess the midpoint of the current known range
        [low, high]. This is the optimal strategy for this kind
        of game -- it guarantees finding the secret in
        log2(range) guesses if the hints are trustworthy.

    Guardrail (CHECK step):
        Before trusting a hint, the agent checks whether the
        outcome is even *possible* given what it already knows.
        For example: if the agent already knows the secret must
        be <= 40 (because a previous "Too High" hint said so),
        and it guesses 20 and is told "Too High" again, that's a
        contradiction -- the secret can't be both <= 40 and > 20
        AND < 20 at the same time in a way that matches its own
        prior hint. Contradictions are logged as anomalies rather
        than acted upon naively.
    """

    def __init__(self, low: int, high: int, max_attempts: int):
        self.low = low
        self.high = high
        self.max_attempts = max_attempts

    def _next_guess(self) -> int:
        # PLAN: bisect the current known range
        return (self.low + self.high) // 2

    def _check_consistency(self, guess: int, outcome: str) -> tuple[bool, str]:
        """
        CHECK: does this hint make sense given the range the
        agent has already narrowed down to?

        Returns (is_consistent, note).
        """
        if outcome == "Too High":
            # Hint claims secret < guess. That's only sensible if
            # guess is still within the agent's believed range.
            if guess < self.low:
                return False, (
                    f"Told secret is below {guess}, but agent already "
                    f"knew secret >= {self.low}. Contradiction."
                )
        elif outcome == "Too Low":
            # Hint claims secret > guess.
            if guess > self.high:
                return False, (
                    f"Told secret is above {guess}, but agent already "
                    f"knew secret <= {self.high}. Contradiction."
                )
        return True, ""

    def play(self, secret: int, starting_score: int = 0) -> AgentResult:
        score = starting_score
        log = []
        anomalies = []
        attempt = 0
        won = False

        while attempt < self.max_attempts:
            attempt += 1
            guess = self._next_guess()
            bounds_before = (self.low, self.high)

            outcome, message = check_guess(guess, secret)

            consistent, note = self._check_consistency(guess, outcome)
            if not consistent:
                anomalies.append(
                    f"Attempt {attempt}: guess={guess} outcome={outcome} -> {note}"
                )

            # ACT: update score the same way a human playthrough would
            score = update_score(
                current_score=score,
                outcome=outcome,
                attempt_number=attempt,
            )

            # Narrow the range for the next guess (only if consistent;
            # an inconsistent hint is logged but not allowed to corrupt
            # the agent's bounds).
            if outcome == "Win":
                won = True
            elif outcome == "Too High" and consistent:
                self.high = guess - 1
            elif outcome == "Too Low" and consistent:
                self.low = guess + 1

            # Second guardrail check: even if this single hint looked
            # plausible on its own, narrowing the range using it might
            # have produced an impossible state (low > high). That is
            # definitive proof a hint was wrong somewhere along the
            # way, even if no single hint looked contradictory in
            # isolation.
            if consistent and self.low > self.high:
                consistent = False
                note = (
                    f"After narrowing, range became invalid "
                    f"({self.low} > {self.high}). A prior hint must "
                    f"have been wrong."
                )
                anomalies.append(f"Attempt {attempt}: guess={guess} outcome={outcome} -> {note}")

            log.append(GuessLogEntry(
                attempt=attempt,
                guess=guess,
                outcome=outcome,
                message=message,
                bounds_before=bounds_before,
                bounds_after=(self.low, self.high),
                consistent=consistent,
                note=note,
            ))

            if won:
                break

        return AgentResult(
            won=won,
            final_score=score,
            attempts_used=attempt,
            secret=secret,
            log=log,
            anomalies=anomalies,
        )


def run_reliability_suite(low: int, high: int, max_attempts: int, trials: int = 20):
    """
    Runs the agent against `trials` random secrets and summarizes
    win rate + any anomalies. This is the "structured experiment"
    the rubric asks for -- use its output directly in your
    README's Testing Summary / reliability section.
    """
    import random

    results = []
    for _ in range(trials):
        secret = random.randint(low, high)
        agent = GuessAgent(low, high, max_attempts)
        result = agent.play(secret)
        results.append(result)

    wins = sum(1 for r in results if r.won)
    total_anomalies = sum(len(r.anomalies) for r in results)
    avg_attempts = sum(r.attempts_used for r in results) / len(results)

    summary = {
        "trials": trials,
        "wins": wins,
        "win_rate": wins / trials,
        "avg_attempts": avg_attempts,
        "total_anomalies": total_anomalies,
    }
    return summary, results


if __name__ == "__main__":
    # Quick manual smoke test: run the reliability suite on Normal
    # difficulty (1-100, 8 attempts) and print a summary.
    summary, results = run_reliability_suite(low=1, high=100, max_attempts=8, trials=20)
    print("Reliability suite summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    if summary["total_anomalies"] > 0:
        print("\nAnomalies found:")
        for r in results:
            for a in r.anomalies:
                print(" -", a)
