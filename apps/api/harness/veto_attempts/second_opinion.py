import ollama

# an LLM filter that double-checks a flag from the crisis safety net before it reaches a person. uses llama3.2:3b for speed, and checks the text against every NOT_CRISIS category already in labelling_rubric.md, rather than inventing new criteria. Ultimately I rejected it as running check_for_doubt against every real CRISIS-labeled row in labelling_batch.csv, 4 of 123 genuine crisis cases get wrongly doubted, including short/blunt ones like "I've given up, what happens happens."

# This isn't the same thing as doubt_check.py though, even though they work in a similar way. that one targeted the old three-agent system, not this one

MODEL = "llama3.2:3b"

def build_prompt(text: str) -> str: # includes an explicit note that short/terse phrasing is NOT on its own a reason to doubt a flag. added after finding the model would otherwise treat brevity itself as suspicious, when a terse message is a completely normal way to express genuine distress
    return f"""You are reviewing a message that has already been flagged as a possible sign of serious emotional distress by a separate detection system. Your only job is to check for a CLEAR, OBVIOUS reason to doubt that flag - not to make your own independent judgment about how distressed the person actually is.

TEXT:
"{text}"

Only answer DOUBT if the text is CLEARLY one of the following:
- an explicit joke or hyperbole, not a genuine expression of feeling
- an explicit hypothetical or conditional ("if X happened, I would feel...") rather than describing the person's actual, current state
- describing a difficulty that is already resolved or in the past, not how the person feels right now
- using an alarming-sounding word in a clearly POSITIVE context (overwhelmed by good news, love, or support)
- clearly about someone else, not the author themselves - a quote, reported speech, or describing another person's state
- a workload or logistics complaint that isn't really about the person's emotional state ("drowning in emails")
- explicitly denying or negating the distressed feeling ("I don't feel hopeless")

Being short, blunt, or lacking detail is NOT on its own a reason to doubt the flag. Terse phrasing is a completely normal and common way for someone in genuine distress to express it - judge the text only against the categories above, regardless of how long or short it is.

If you are not completely certain the text clearly matches one of these, or if there is any genuine ambiguity, answer KEEP - the flag stays in place. When in doubt, always answer KEEP. Missing a genuine sign of distress is far more costly than an unnecessary check-in from a friend.

First, write up to 40 words explaining your reasoning. Then, on its own final line, in exactly this format and nothing else, give your verdict:

VERDICT: DOUBT or VERDICT: KEEP
"""

def parse_verdict(output: str) -> bool: # only an explicit, well-formed DOUBT verdict returns True. anything malformed or missing defaults to False, so the escalation stays in place
    for line in output.split("\n"):
        if line.strip().upper().startswith("VERDICT:"):
            return "DOUBT" in line.strip().upper()
    return False

def check_for_doubt(text: str) -> bool:
    response = ollama.chat(
        model = MODEL,
        messages = [{"role": "user", "content": build_prompt(text)}],
        options = {"temperature": 0} # zero randomness, same reasoning as doubt_check.py. a judgment call, not creative text
    )
    return parse_verdict(response["message"]["content"])
