import random
import ollama

MODEL = "llama3.2:3b" # as this is for generation only and I am labelling all of them myself, speed is the most important thing here, nothing is being scored

REGISTERS = [
    "very short and blunt, like a quick text message, under 10 words",
    "a longer, rambling, conversational message that touches on a couple of different things",
    "a single plain sentence, casually written",
]

RAMBLING_REGISTER = REGISTERS[1] # this register is never generated directly, as asking the model for a long rambling message came out overly flowery. instead generate_rambling_candidate gets one short plain sentence from the model and buries it inside a few random filler sentences, which reads as rambling without the model ever writing a long message
SHORT_FRAGMENT_REGISTER = REGISTERS[2]

FAILURE_MODE_PROMPTS = { # one prompt per way real crisis-adjacent text could actually fool a naive detector. Things like hypotheticals, resolved pasts, quoting someone else, joking hyperbole, positive-context reuse of alarming words, and so on. Used to generate systematically varied test candidates covering each failure mode rather than picking tricky examples ad hoc
    "crisis_direct": "Write a short, first-person daily check-in response that directly and clearly describes the person currently feeling hopeless, unable to cope, or at breaking point. Do not soften it. Write it the way a real person would actually type it - casual, maybe lowercase, not a textbook example.",
    "crisis_terse": "Write a very short, blunt, first-person message where someone is clearly at breaking point or can't cope, but without using words like 'hopeless' or 'overwhelmed' explicitly - just a plain, terse statement a real person might type.",
    "conditional": "Write a first-person daily check-in response where the person describes a hypothetical or conditional situation (\"if X happened, I would feel...\") using emotionally heavy language, but is NOT describing their actual current state.",
    "past_resolved": "Write a first-person daily check-in response describing a difficulty from the past that has since been resolved or improved - use emotionally heavy language for the past feeling, but make clear it's resolved now.",
    "positive_valence": "Write a first-person daily check-in response using a word like \"overwhelmed\" or \"can't cope\" but in a clearly POSITIVE context (overwhelmed by good news, love, or support, for example).",
    "workload_hyperbole": "Write a first-person daily check-in response about being busy or stressed with workload or logistics, using hyperbolic or joking language (\"drowning in emails\", \"this is going to kill me lol\") that is NOT describing genuine emotional crisis.",
    "boundary_difficult": "Write a first-person daily check-in response describing a genuinely hard time - burnout, anxiety, grief, feeling low - real and significant, but NOT describing wanting to give up or being unable to cope.",
    "ordinary_negative": "Write a first-person daily check-in response about an ordinary, mildly negative day - traffic, a small argument, feeling a bit bored or tired. Nothing serious.",
    "ordinary_positive": "Write a first-person daily check-in response about a good or neutral day.",
    "reported_speech": "Write a first-person daily check-in response where the person reports or quotes someone else using severe, crisis-sounding language toward them - for example a therapist, doctor, friend, or family member asking if they feel hopeless or at breaking point, or the person quoting something someone else said. The author is NOT describing their own current state, just relaying the question or quote, and should make their own actual state clear (e.g. answering the question, or brushing it off).",
    "other_experiencer": "Write a first-person daily check-in response describing someone else's severe emotional state - a friend, partner, or family member who is hopeless, unable to cope, or at breaking point - using strong, unambiguous language for THEIR state. Make clear through phrasing (e.g. 'she said', 'I'm worried about him') that the author is describing another person, not themselves.",
    "negated_distress": "Write a first-person daily check-in response where the person explicitly and directly denies currently feeling a severe emotional state, using present-tense negation (e.g. \"I don't feel hopeless\", \"I'm not struggling like I was\", \"not gonna lie and say I can't cope, because I can\"). Do not frame it as a past difficulty that has been resolved - it should read as a plain, present-tense denial, not a resolution story.",
    "ironic_hyperbole": "Write a first-person daily check-in response using sarcastic, joking, or meme-style hyperbole that borrows crisis-adjacent language (e.g. \"literally deceased\", \"I would die for this\", \"not me almost crying over\") to describe something clearly trivial, funny, or positive - not about workload or being busy specifically, could be about a TV show, food, a joke, the weather, anything mundane. Write it the way someone would actually type a joke online, not describing genuine emotional distress.",
}

CONTRAST_TRANSFORMS = { # rewrites, not fresh generations. Takes a real crisis-shaped seed sentence and asks the model to keep as much of the original wording as possible while changing just one thing (framing, tense, context, or length), producing a near-identical pair that tests whether the detector is tracking meaning or just reacting to vocabulary. only these 4 modes work as a pure rewrite of an existing sentence, the rest need a different subject or genuinely new content
    "conditional": "Rewrite this sentence so it describes a hypothetical/conditional situation instead of the person's actual current state, using an \"if... I would feel\" structure, keeping as much of the original wording as possible: \"{seed}\"",
    "past_resolved": "Rewrite this sentence so it describes the same feeling but in the past, now resolved or improved, keeping as much of the original wording as possible: \"{seed}\"",
    "positive_valence": "Rewrite this sentence so a similar-sounding word is used in a clearly POSITIVE context instead, keeping the sentence structure similar: \"{seed}\"",
    "terse": "Rewrite this sentence as a very short, blunt, under-8-word version that keeps the same core meaning: \"{seed}\"",
}

MUNDANE_FILLERS = [ # hand-written and always the same, not generated by the model because this way the filler sentences around a spliced fragment are always boring and never accidentally sound crisis-related themselves
    "Work has been pretty busy this week, lots of meetings back to back.",
    "Been trying to get through my reading list but keep getting distracted.",
    "The weather's been all over the place, hard to plan anything outdoors.",
    "Caught up with a friend over coffee yesterday which was nice.",
    "Still haven't sorted out that thing I've been putting off.",
    "Watched a couple of episodes of something last night, nothing special.",
    "Had a pretty standard commute today, nothing much to report.",
    "Been meaning to go for a run but haven't got round to it.",
]

def generate_from_prompt(prompt: str) -> str:
    response = ollama.chat(
        model = MODEL,
        messages = [{"role": "user", "content": f"{prompt} Only output the text itself, nothing else - no preamble, no quotation marks."}], # sometimes ignores the no quotation marks part, so included the strip below
        options = {"temperature": 1.0} # high randomness on purpose seeing as the goal here is varied natural-sounding candidates, not one best answer
    )
    return response["message"]["content"].strip().strip('"') # backup cleanup for when it ignores the no-quotation-marks instruction anyway

def generate_grid_candidate(failure_mode: str, register: str) -> str: # generates one test message for a given failure mode written in a given style except the rambling style, which is built separately by splicing
    if register == RAMBLING_REGISTER:
        return generate_rambling_candidate(failure_mode)
    prompt = f"{FAILURE_MODE_PROMPTS[failure_mode]} Write it in this style: {register}."
    return generate_from_prompt(prompt)

def generate_contrast_pair(seed_crisis_text: str, transform: str) -> str: # rewrites the seed sentence using the given transform and returns just the rewritten version
    prompt = CONTRAST_TRANSFORMS[transform].format(seed = seed_crisis_text)
    return generate_from_prompt(prompt)

def ensure_terminal_punctuation(sentence: str) -> str: # the model doesn't always end a fragment with punctuation, and without this a spliced-in fragment can run straight into the next filler sentence with no break between them
    sentence = sentence.strip()
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence

def splice_sentence(sentence: str, position: str = "end") -> str: # mixes the given sentence in with 2 to 3 random filler sentences to make it look like part of a longer message. position decides where the sentence goes, either at the start, in the middle, or at the end, with filler sentences on either side. used for the rambling register and also called directly by build_labelling_batch.py
    sentence = ensure_terminal_punctuation(sentence)
    filler = random.sample(MUNDANE_FILLERS, k = random.randint(2, 3))
    if position == "start":
        parts = [sentence] + filler
    elif position == "middle":
        mid = len(filler) // 2
        parts = filler[:mid] + [sentence] + filler[mid:]
    else:
        parts = filler + [sentence]
    return " ".join(parts)

def generate_rambling_candidate(failure_mode: str) -> str:
    fragment_prompt = (
        f"{FAILURE_MODE_PROMPTS[failure_mode]} Write it in this style: {SHORT_FRAGMENT_REGISTER}. "
        "Avoid metaphors, imagery, or literary language (for example, don't write things like \"an invisible anchor tightening around my chest\" or \"drowning in an ocean of\") - keep the wording plain and literal, the way someone would actually type it into a phone, not the way a short story would describe it." # those two examples were actually produced by the model before this instruction was added
    )
    fragment = generate_from_prompt(fragment_prompt)
    position = random.choice(["start", "middle", "end"])
    return splice_sentence(fragment, position)
