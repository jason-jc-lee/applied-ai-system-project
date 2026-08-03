"""
test_guardrail_demo.py

THROWAWAY / DEMO SCRIPT -- not part of the main app.

This deliberately reintroduces the original Module 1 bug (hints
swapped: "Too High" and "Too Low" reversed) into a *local copy* of
check_guess, then runs the agent against it. This proves the
guardrail actually catches bad hints instead of just being present
but never triggered.

Do NOT import this into app.py. Run it standalone:
    python test_guardrail_demo.py
"""

from agent import GuessAgent
from logic_utils import update_score


def broken_check_guess(guess, secret):
    """
    Reproduction of the original Module 1 bug: hints are swapped.
    (Copied from app.py's commented-out original buggy version.)

    NOTE: this version swaps EVERY time, which is consistently
    wrong but never self-contradictory -- the guardrail (which only
    checks for self-contradiction, not correctness) won't catch it.
    See intermittent_check_guess below for a version it does catch.
    """
    if guess == secret:
        return "Win", "Correct!"
    if guess > secret:
        return "Too Low", "Go LOWER!"   # WRONG: should be "Too High"
    else:
        return "Too High", "Go HIGHER!"  # WRONG: should be "Too Low"


_call_count = {"n": 0}


def intermittent_check_guess(guess, secret):
    """
    Reproduction of the OTHER original Module 1 bug (the FIXME in
    app.py): secret gets mishandled on every other attempt. Here
    we simulate that by swapping the hint direction only on
    even-numbered calls. This creates real self-contradictions the
    guardrail can catch: attempt N narrows the range one way,
    attempt N+1 gives a hint that's impossible given that range.
    """
    _call_count["n"] += 1
    is_odd_attempt = _call_count["n"] % 2 == 1

    if guess == secret:
        return "Win", "Correct!"

    correct_outcome = "Too High" if guess > secret else "Too Low"

    if is_odd_attempt:
        return correct_outcome, "hint"
    else:
        swapped = "Too Low" if correct_outcome == "Too High" else "Too High"
        return swapped, "corrupted hint"


def run_case(label, broken_fn, secret):
    import agent as agent_module

    original_check_guess = agent_module.check_guess
    agent_module.check_guess = broken_fn
    _call_count["n"] = 0

    try:
        print(f"=== {label} (secret={secret}) ===")
        guesser = GuessAgent(low=1, high=100, max_attempts=8)
        result = guesser.play(secret)

        for entry in result.log:
            flag = " <-- FLAGGED BY GUARDRAIL" if not entry.consistent else ""
            print(
                f"Attempt {entry.attempt}: guessed {entry.guess} -> "
                f"{entry.outcome} (range {entry.bounds_before} -> "
                f"{entry.bounds_after}){flag}"
            )

        print(f"Won: {result.won} | Anomalies detected: {len(result.anomalies)}")
        for a in result.anomalies:
            print(" -", a)
        print()

    finally:
        agent_module.check_guess = original_check_guess


if __name__ == "__main__":
    run_case("Case 1: consistently swapped hints (bug present, guardrail blind to it)",
              broken_check_guess, secret=13)
    run_case("Case 2: intermittently corrupted hints (guardrail catches it)",
              intermittent_check_guess, secret=13)
