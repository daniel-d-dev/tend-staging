import numpy as np
from sentence_transformers import CrossEncoder

from app.services.crisis_safety_net import split_sentences

# this file checks a check in's text against many specific hypotheses, which are descriptions of distress, such as "the author is having thoughts of self-harm". It asks a small language model whether the text genuinely supports each one being true (entailment), not just whether it sounds similar

# label order for cross-encoder/nli-deberta-v3-* models is [contradiction, entailment, neutral]

# fires as a false positive on some mundane but negatively-toned text that describes soreness, mild frustration etc. rewording this hypothesis to rule out physical language was tried and rejected, since it also suppressed real crisis cases that had no physical language in them at all. This is the most tested hypothesis in the project, and when a different model was tried it broke badly. The soreness false positives are handled instead by checking against a second hypothesis, below
HYPOTHESIS = "The author is currently, genuinely feeling hopeless or that things are too much to cope with."

# several hypotheses instead of one, each aimed at a specific kind of distress, seeing as statements that imply burden-relief, not belonging, self-harm etc don't logically entail hopelessness specifically, even though they're serious warning signs in their own right. Takes the highest entailment score across all of them.
CONSTRUCT_HYPOTHESES = {
    "hopelessness": HYPOTHESIS, # the original hypothesis catches direct hopelessness well but misses a related belief that things will never change or improve, which check-ins could express as part of ordinary narrative rather than as a direct statement. these two rephrasings turned out to be complementary rather than redundant, each catching different genuine examples, so both are kept
    "hopelessness_change_2": "The author believes things will never be different or get better.",
    "hopelessness_change_3": "The author cannot see things ever changing.",
    "burden_relief": "The author believes the people around them would be better off without them, or that they are a burden to the people in their life.", # a second version of this hypothesis, added because the first one missed some of the ways people would actually phrase this. The shorter, plainer wording below covers all three ways this shows up across the test cases checked against. A reworded version was tried to fix the complaint-stacking issue described below, but it missed two-thirds of the test cases the original used to catch and was considered not worth the trade
    "burden_relief_2": "The author feels like a burden to the people who care about them.",
    "belongingness": "The author feels that no one would notice or care if they were gone, or that they are completely alone and disconnected from everyone around them.", # a second version of this hypothesis is below. The original scored close to zero on every test case it was checked against which is a real structural failure not just a wording issue. The shorter, more literal version catches most of the ways this shows up. The most indirect one is still missed, and that's covered by the cosine fallback instead
    "belongingness_2": "The author feels like nobody would notice or care if they were gone.",
    "self_harm": "The author is having thoughts of self-harm.", # self harm went through a couple of rewordings before getting here. It previously mentioned an "urge to physically harm themselves", but this ended up latching onto generic pain and body language, firing on ordinary things like the soreness you feel after a workout. Switching to the specific clinical term instead of a paraphrase fixed it as the model recognises self harm as a clear, specific idea 
    "defeat": "The author has stopped fighting or resisting their difficulties and feels completely defeated.",
    "defeat_2": "The author has given up and stopped trying.",
    "no_future": "The author cannot picture or imagine having any future at all.",
    "no_future_2": "When the author tries to imagine their life going forward, there is nothing there.",
    "passive_ideation": "The author wishes they would not wake up or would stop existing.",
    "disappear": "The author wants to disappear or cease to exist.",
    "masking": "The author is exhausted from pretending to be okay when they genuinely are not.",
    "worthlessness": "The author believes they are worthless or hates who they are.", # two extra versions of this hypothesis, neither alone caught enough of the ways this shows up, but together with the original they cover everything we've seen. worthlessness_3 specifically tells real self-blame apart from nearly identical but harmless phrasing
    "worthlessness_2": "The author feels worthless and like a failure.",
    "worthlessness_3": "The author believes they mess everything up.",
    "shame_guilt": "The author is consumed by unbearable guilt or shame they cannot live with.", # Two extra versions of this hypothesis, same idea as worthlessness above. v2 catches guilt over one specific thing that happened, v3 catches broader shame with no particular incident behind it
    "shame_guilt_2": "The author feels unbearable guilt that they cannot let go of.",
    "shame_guilt_3": "The author feels deeply ashamed of themselves.",
}

# farewell and escape aren't included as their own hypotheses here as neither has a single phrase that reliably captures it (farewell is more about how someone tells a story than a specific thing they say), and every version tried for both scored close to zero on the test cases checked against. both are caught entirely by the cosine similarity check instead

# stacking several ordinary complaints in one message (like a moan about a commute, a minor argument, something about being tired etc) can wrongly trigger a hypothesis, even though none of it is really about that hypothesis's construct on its own. It affects three hypotheses: burden_relief_2 defeat, and worthlessness_3, roughly a third of the time on this kind of deliberately stacked text
# tried requiring a keyword match before letting the NLI check escalate on its own, but rejected it, since it would have blocked genuine, unambiguous crisis statements that just don't happen to contain the expected words. real crisis language is too varied for a fixed keyword list to reliably back it up
# accepted the complaint-stacking as a known gap rather than chasing it further. even if this misses something, the baseline-deviation signal still catches it independently, and a wrong nudge here is soft, rate-limited, and doesn't reveal what was actually said, the cost of getting it wrong is low
# the same contrastive trick used for hopelessness (see PHYSICAL_HYPOTHESIS) was also tried on burden_relief_2, since casual hyperbole like "drowning in emails, this is gonna kill me lol" fires it. unlike physical soreness, a contrastive hypothesis about workload stress fired just as strongly on genuine crisis text, since "overwhelmed by work" and "overwhelmed by a real crisis" share too much of the same wording. no working contrastive hypothesis found, left as part of the same accepted gap above

model = CrossEncoder("cross-encoder/nli-deberta-v3-small")
# tried two bigger, differently-trained models, hoping to catch some of the more indirect phrasing several hypotheses were still missing. both looked like real wins on small, narrow tests, but one of them failed a fuller test against the actual held out queue. Mundane false positives on ordinary, harmless check-ins roughly tripled, for barely any improvement in recall gain. reverted to this smaller model, which is the one that's actually been fully tested and validated

def entailment_for_hypothesis(text: str, hypothesis: str) -> float:
    logits = model.predict([(text, hypothesis)])[0]
    probs = np.exp(logits) / np.exp(logits).sum() # turns the three raw scores into probabilities that sum to 1 (softmax)
    return float(probs[1]) # entailment probability

def entailment_score(text: str) -> float:
    # single hypothesis - only used by the harness's labeling/calibration scripts now, not the deployed ensemble, which uses nli_triggered_score and the full battery below
    return entailment_for_hypothesis(text, HYPOTHESIS)

def all_construct_scores(text: str) -> tuple[list[float], list[str]]: # scored per sentence and not the whole text. scoring the whole text missed a significant amount of test cases labeled crisis, where the alarming sentence was diluted by surrounding mundane text, the same dilution problem the per-sentence cosine design already exists to prevent. every sentence-hypothesis pair is batched into one model.predict() call rather than looping through them one at a time, to avoid the overhead of many separate calls
    sentences = split_sentences(text) or [text]
    pairs = [(s, h) for s in sentences for h in CONSTRUCT_HYPOTHESES.values()]
    labels = [name for _ in sentences for name in CONSTRUCT_HYPOTHESES.keys()] # built the same way, in the same order, so pairs[i] and labels[i] always line up
    logits = model.predict(pairs)
    probs = np.exp(logits) / np.exp(logits).sum(axis = 1, keepdims = True) # same softmax as above, just row by row over the whole batch
    return list(probs[:, 1]), labels

# the default threshold for construct hypotheses. used as the fallback whenever a hypothesis doesn't have its own override below. calibrated to not lose any real cases. it should catch against the labeled test set, while giving up one false positive that would be otherwise avoidable. went no higher, since missing a real crisis is far more costly than sending an unwarranted nudge
NLI_TRIGGER_THRESHOLD = 0.7

# a per-hypothesis threshold override, not a blanket exception, needs its own justification each time, based on whether a safe gap actually exists between real cases and false positives. worthlessness_3 was one of the three hypotheses affected by the complaint-stacking issue above. checked whether that kind of gap exists for each of the three, and only this one did. for the other two, stacked-complaint false alarms score as high or higher than the real cases they're meant to catch, so no threshold could separate them, that option just doesn't exist for those. raised this one comfortably inside its gap and verified it costs nothing against the labeled test set. this is based on very little data for this specific hypothesis though, worth re-checking if more ever exists
NLI_TRIGGER_THRESHOLD_OVERRIDES = {
    "worthlessness_3": 0.90,
}

# not one of the hypotheses above, since it's not a warning sign in its own right, it's only used to double check hopelessness. exaggerated soreness language like "my legs are killing me after that run" was firing hopelessness almost every time, because the model weighs the word "killing" heavily regardless of the context around it. hopelessness now only counts as triggered if it also outscores this hypothesis on the same sentence. tested against the labeled set: real crisis cases beat this comfortably (the closest was still 0.07 clear), and it fixed the soreness false positives with no other cost
PHYSICAL_HYPOTHESIS = "The author is complaining about sore muscles or tiredness after exercise or physical exertion."

def nli_triggered_score(text: str) -> tuple[bool, float, str]: # the real trigger decision used by the deployed ensemble. each hypothesis gets checked against its own threshold, not the single highest score compared against one shared threshold. otherwise a per-hypothesis override like worthlessness_3's wouldn't actually do anything, since there'd be no way to know which hypothesis's threshold to compare the top score against
    sentences = split_sentences(text) or [text]
    entail_probs, labels = all_construct_scores(text)
    hypotheses_per_sentence = len(CONSTRUCT_HYPOTHESES)
    physical_probs = [entailment_for_hypothesis(s, PHYSICAL_HYPOTHESIS) for s in sentences]

    triggered = []
    for i, (p, name) in enumerate(zip(entail_probs, labels)):
        if p <= NLI_TRIGGER_THRESHOLD_OVERRIDES.get(name, NLI_TRIGGER_THRESHOLD):
            continue
        if name == "hopelessness" and p <= physical_probs[i // hypotheses_per_sentence]:
            continue
        triggered.append(i)

    if triggered:
        best_i = max(triggered, key=lambda i: entail_probs[i])
        return True, float(entail_probs[best_i]), labels[best_i]
    return False, 0.0, ""