from app.services.crisis_safety_net import score_crisis_language_per_sentence, CRISIS_THRESHOLD
from app.services.nli_reranker import nli_triggered_score

# the threshold and per-hypothesis override table live in nli_reranker.py, see that file for the calibration history

def evaluate_checkin(text: str) -> dict: # this function's job is to simply answer whether or not the crisis floor fired, and app/services/inference.py decides what that means for nudging. still escalate-only in that either signal can raise the alarm on its own, but neither can cancel the other one out. Cosine similarity and nli have complementary blind spots, and this is something that has been tested: cosine catches the short and blunt statements that nli misses, whereas nli catches conditional/past-tense/positive-valence phrasing that cosine can't distinguish. a requiring of both signals to agree before triggering was tried and rejected. it cut down on the odd unwarranted nudge, but at the cost of missing real crises it used to catch, the wrong direction given a missed crisis is far more costly than an awkward nudge
    crisis_score = score_crisis_language_per_sentence(text)
    nli_triggered, nli_score, nli_hypothesis = nli_triggered_score(text)
    cosine_triggered = crisis_score > CRISIS_THRESHOLD
    triggered = cosine_triggered or nli_triggered

    return {
        "safety_net_triggered": triggered,
        "cosine_triggered": cosine_triggered,
        "nli_triggered": nli_triggered,
        "crisis_score": crisis_score,
        "nli_score": nli_score,
        "nli_hypothesis": nli_hypothesis, # which hypothesis actually triggered, empty if none did. not read anywhere yet, the trigger decision only needs the yes/no
    }
