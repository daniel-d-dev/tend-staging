import re
import spacy

# a different kind of veto attempt to the ones from before. Deterministic grammatical pattern matching instead of LLM judgment, tried after second_opinion.py proved unstable on short text. I'd diagnosed the root cause as cosine similarity getting fooled by wording that's grammatically conditional or past-tense. As this is just a grammar thing and there is no judgment needed there was no model involved meaning the same input always gives the same output. The plan was to only use this when cosine flags something but NLI doesn't agree, this would get asked to confirm whether that disagreement looks like a genuine false alarm before letting the flag through. it never actually got built into the real app as even in this narrow form it still wrongly suppressed at least one genuine crisis case when tested which I deemed not acceptable, same as every other veto attempt so ensemble.py just goes on cosine or NLI alone.

nlp = spacy.load("en_core_web_sm") # spaCy's small English model, the tool doing the grammar parsing that the functions below rely on

RESOLUTION_MARKERS = [ # phrases that, combined with a past-tense verb, suggest the distress being described is over, not current. a fixed, hand-picked list rather than something inferred, so the behaviour stays easy to inspect and debug
    "now", "anymore", "these days", "finally", "found a way", "worked out", "got through", "moved on", "resolved", "better now", "learned to cope", "not anymore", "back then",
]

def has_conditional_construction(text: str) -> bool: # true if the text has both an "if" clause and a modal verb (would/could/might/'d) - the grammatical shape of a hypothetical, regardless of what it's actually about
    doc = nlp(text)
    has_if = False
    has_modal = False
    for tok in doc:
        if tok.lower_ == "if" and tok.dep_ == "mark":
            has_if = True
        if tok.tag_ == "MD":
            has_modal = True
    return has_if and has_modal

def contains_marker(text_lower: str, marker: str) -> bool: # word-boundary match, not substring. a plain substring check let "now" match inside "know"/"known", wrongly flagging "I do not know how" as a resolution marker
    return re.search(rf"\b{re.escape(marker)}\b", text_lower) is not None

def has_past_tense_resolution(text: str) -> bool: # true if the text says "used to", or if it has a past-tense verb alongside one of the resolution markers above. either way suggests the distress described is in the past, not now
    doc = nlp(text)
    text_lower = text.lower()
    has_used_to = contains_marker(text_lower, "used to")

    has_past_verb = False
    for tok in doc:
        if tok.pos_ == "VERB" and "Tense=Past" in tok.morph:
            has_past_verb = True

    has_resolution_marker = False
    for marker in RESOLUTION_MARKERS:
        if contains_marker(text_lower, marker):
            has_resolution_marker = True

    return has_used_to or (has_past_verb and has_resolution_marker)

def has_negated_distress(text: str) -> bool: # not used in syntactic_doubt() below. I tried this and it's unreliable, since checking for "any negation anywhere" has no concept of scope. It wrongly fires on negations that have nothing to do with distress ("I don't KNOW how..."), and worse, on negations that are themselves crisis language ("I don't SEE THE POINT" is hopelessness, not a denial of it). A real fix would need to check the negation is actually attached to a distress-relevant word, not just present somewhere in the sentence. I never built that but I've kept this here as a documented dead end
    doc = nlp(text)
    for tok in doc:
        if tok.dep_ == "neg":
            return True
    return False

def syntactic_doubt(text: str) -> bool: # only combines the two checks that actually worked
    return has_conditional_construction(text) or has_past_tense_resolution(text)
