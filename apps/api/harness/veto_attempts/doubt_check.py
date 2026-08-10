import ollama

# my first attempt at using an LLM to double-check a flagged check-in, tested against the old three-agent system, before the crisis safety net (cosine/NLI) even existed. Rejected it as llama3.1 took over 8 minutes per call, and it suppressed a crisis case that absolutely should have stayed flagged
MODEL = "llama3.1"

def build_prompt(text: str) -> str: # asks the model to explain its reasoning before giving a verdict, rather than just answering bare. Tried a bare-answer version first and it defaulted to the "safe" answer without actually engaging with the criteria. Giving it room to reason first fixed that
    return f"""You are reviewing a message that has already been flagged as a possible sign of serious emotional distress by a separate detection system. Your only job is to check for a CLEAR, OBVIOUS reason to doubt that flag - not to make your own independent judgment about how distressed the person actually is.

TEXT:
"{text}"

Only answer DOUBT if the text is CLEARLY one of the following:
- an explicit joke or hyperbole, not a genuine expression of feeling
- an explicit hypothetical or conditional ("if X happened, I would feel...") rather than describing the person's actual, current state
- clearly about someone else, not the author themselves
- clearly describing something already resolved or in the past, not how the person feels right now

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
        options = {"temperature": 0} # zero randomness on purpose here, opposite of generate_candidates.py's temperature. This should give the same answer every time, not varied creative text
    )
    return parse_verdict(response["message"]["content"])
