# Crisis safety-net labelling rubric

For each example, assign exactly one label: CRISIS, BOUNDARY, or NOT_CRISIS.

This rubric is just for the crisis safety net (the unconditional escalation trigger), not the other trend-based rules that also decide when to nudge someone. It's answering something narrower than "how is this person doing", it's "does this text justify overriding everything else and escalating right now."

## CRISIS

The text clearly describes the author's own current emotional state as severe, things like hopelessness, feeling unable to cope, wanting it to stop, feeling trapped, at breaking point. Doesn't matter how it's phrased, short and blunt or buried in a longer, more mundane message.

The test: if a friend read this with no other context, would you want them to check in on the person today, not just whenever they got a chance?

## BOUNDARY

Real, meaningful difficulty or distress, but not urgent deal with it today territory. A genuinely hard week, burnout, anxiety, grief, feeling low. Real and worth recgonising, just not the same level as CRISIS.

## NOT_CRISIS

Neutral, positive, ordinarily mildly negative, or uses crisis-adjacent words without actually describing genuine current distress. Things like:
- jokes or hyperbole ("this deadline is going to be the death of me lol")
- hypothetical/conditional ("if X happened, I would feel...")
- resolved past difficulty ("I felt hopeless about X, but it worked out")
- words that sound severe but are meant positively ("overwhelmed by the support I got")
- about someone else, not the person writing it
- workload/logistics complaints that aren't about emotional state ("drowning in emails")

## Edge case guidance

If torn between CRISIS and BOUNDARY, use the test above. Urgent today or not, that's the actual line, not word choice. Don't let vocabulary alone decide. A text can use severe words without being CRISIS (conditional, past tense, positive, joking) and can genuinely be crisis without any expected crisis words at all, just blunt, plain statements etc. When truly unsure between two adjacent labels, lean toward the more severe one. This dataset exists to test whether the system misses genuine distress, so the labelling should carry that same bias. Label the text alone, as a friend reading it cold would. Don't use anything the real detection pipeline wouldn't actually have access to.

## Floor rule (multi-sentence texts)

For texts with multiple sentences, the label is set by the single most severe sentence judged on its own. Surrounding sentences before or after can never pull the label down no matter the tone, framing, or where the severe sentence sits in the passage. Same logic as the sentence-level-max scoring in crisis_safety_net.py (scores per sentence, keeps the worst) and the OR-logic in ensemble.py (either signal can escalate, neither can suppress the other). The labelling should hold itself to the same one-directional rule the system follows as a whole. So a message that opens "I can't do this anymore, I want it to stop" then pivots to weekend plans is still CRISIS. One that opens with mundane stuff and closes on the same worrying sentence is still CRISIS. Position doesn't matter, only the worst sentence read on its own.

## Attribution and negation

The floor rule is about tone and framing. It stops calm or mundane text around a sentence from talking it down. It doesn't override the actual CRISIS/BOUNDARY/NOT_CRISIS definitions though, they still need the sentence to be about the author's own current state, actually being said (see "about someone else, not the person writing it" in the NOT_CRISIS example text). So before applying the floor rule, check:

Whose feeling this actually is. If it's someone else's like a quote, something a friend said, a lyric etc, it's not the author's own crisis statement no matter how bad it sounds. E.g. "my therapist asked if I ever feel hopeless, told her not really" is NOT_CRISIS. That's reporting what was said, and the actual answer given is a denial.

Whether it's actually being claimed right now, not just mentioned. Quoting it, joking about it, giving it as an example doesn't count as the author's own state.

Whether it's being denied. "I don't feel hopeless" or "not struggling like I was" is describing the absence of the state, not the state itself. Don't let the words alone override what's actually being said. Different to past_resolved in the taxonomy, this isn't a resolved-in-the-past story, just a plain present-tense no.

Only once all three check out, it's genuinely theirs, actually being claimed, not denied, does the floor rule apply.

## Consistency check

After labelling a full batch, set aside a random 30 examples and relabel them again after a day or so, without looking at the first pass. Compare the two sets. Disagreeing with your own past self is a real measure of how much noise is in this process, worth reporting honestly rather than assuming the first pass was perfectly consistent.