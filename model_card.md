# Model Card: Glitchy Guesser Autonomous Agent

This document talks about the limitations, risks, and AI-collaboration process
for the `GuessAgent` class in this project. It covers the limitations, risks, and how AI
assistance was used during development.

## Limitations and Biases

The guardrail is designed to catch inconsistencies. During testing, a version of `check_guess` was created that
swapped "Too High" and "Too Low" on every single call. Because the swap was
applied consistently, every hint stayed internally consistent, and steadily narrowed
in the wrong direction until it ran out of attempts. The guardrail only
detected a problem once the range became invalid
(`low > high`). The guardrail only caught the problem after several attempts had already passed with confidently wrong guesses.

This means the guardrail is better at catching hints that sometimes contradict each other, but
it struggles to catch bugs that are wrong every single time. This is due to consistent lies never 
contradicting themselves. A hint source that is wrong in
exactly the same way every time can look trustworthy for a long
time. This is a limitation that shows how an AI system can seem reliable if its errors are
consistent rather than random.

Testing also allowed me to notice and fix two bugs, being status and score not being reset when starting a new game, which caused score inaccuracies and blocked further play.

In addition, the agent is incapable of playing where the manual plays left off. Instead, the agent will do all the guesswork from scratch and will not take the manual guesses into account. A completed version would track the ranges across both manual and agent guesses.

The agent's strategy (binary search) only works well for the number-guessing game. If this logic
was applied to a different game, it would not work well.

## Potential Misuse and Mitigation

The possibility of misuse is small, and the pattern that the AI uses is designed to check for 
one specific kind of error, the error of hints contradicting each other.
This means that a hint that may be wrong could be interpreted as right by the system, leading into wrong answers. 
The mitigation here is the results that may be a failure. So, claiming the system is "reliable" may not be true as
it might have not accounted for countless other cases.

The mitigation is that the version of the game was given a known bug to determine if 
the guardrail would actually check. This led to cases where it worked and didn't work, 
which is a more honest test.

## What Surprised Me During Reliability Testing

The first version of the guardrail passed all 20 trials with zero
anomalies, which looked like strong evidence it worked. It was only when a
known broken version of `check_guess` was deliberately substituted in that it showed a 
wrong hint pattern producing zero flagged anomalies, even though the
agent never won a single game against it. Passing all the tests only shows
the guardrail didn't fire on the inputs that were being tested; it does not
show it would catch every kind of failure.

## AI Collaboration

**Flawed suggestion:** the first guardrail design was built with the assistance of AI. It
only checked whether a single hint was individually plausible given the
agent's current tracked range. This looked reasonable and passed all initial
clean-run tests, but it failed to catch a consistently
swapped hint direction because that pattern never produced a hint that was
implausible on its own, only that range became invalid after several
guesses accumulated. I verified this by running the agent against a
deliberately broken `check_guess` and observing zero anomalies where there
clearly should have been some.

**Helpful suggestion:** once that gap was identified, the fix was to check whether the range became invalid (low > high) after narrowing, rather than only checking each hint in isolation. This correctly resolved the issue. Re-running both the clean runs and the deliberately broken test cases confirmed the fix worked without introducing false
positives on legitimate games.

AI-suggested guardrails and tests can look sufficient while quietly missing a real failure. The only way to find out is to deliberately test against bad inputs rather than trust a clean run.

## Future Improvements

A future version of this guardrail could work by comparing hints against the secret value directly rather than checking for contradiction. While this would catch wrong hint patterns immediately rather than later on, it would only be possible during a test run, rather than an actual run since the agent isn't supposed to cheat. Another improvement would be to track the count of consecutive same-direction (constantly going higher/lower) hints, as scenarios like these are usually signs of errors. Additionally, the agent may take into account of where manual plays have left off and work from there.
