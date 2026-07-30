def compute_sentence_score(emotion_scores: dict[str, float]) -> float: # kept formula g's original weights from the evaluation study, just removed the llm debate around it but added surprise at weight 0.1 as the classifier reads overwhelmed as mostly surprise, which the original formula missed entirely. It's not a full fix, and doesn't touch the crisis safety net just improves the trend signal
    joy = emotion_scores.get("joy", 0)
    sadness = emotion_scores.get("sadness", 0)
    anger = emotion_scores.get("anger", 0)
    fear = emotion_scores.get("fear", 0)
    disgust = emotion_scores.get("disgust", 0)
    neutral = emotion_scores.get("neutral", 0)
    surprise = emotion_scores.get("surprise", 0)
    return max(0.0, (sadness * 0.4) + (fear * 0.3) + (anger * 0.2) + (disgust * 0.1) + (joy * -0.3) + (neutral * -0.1) + (surprise * 0.1))

def aggregate_sentence_scores(scores: list[float]) -> dict: # plain average backfired as one bad sentence buried in filler scored lower than no bad sentence at all. Top two mean fixes this and still just uses the one sentence when there's only one
    top_two = sorted(scores, reverse = True)[:2]
    mean_score = sum(top_two) / len(top_two)
    return {
        "mean_score": round(mean_score, 4), # the day's overall tone, feeds trend detection
    }

def score_checkin(sentence_emotion_scores: list[dict[str, float]]) -> dict: # scored per sentence not the whole passage. Same reason as the crisis safety net, a bad sentence shouldn't get averaged away
    scores = [compute_sentence_score(es) for es in sentence_emotion_scores]
    return aggregate_sentence_scores(scores)