from transformers import pipeline
from app.services.scoring import score_checkin
from app.services.crisis_safety_net import split_sentences

_sentiment_pipeline = None

def load_model():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "text-classification",
            model = "j-hartmann/emotion-english-distilroberta-base",
            top_k = None
        )

def score_text(text: str) -> dict | None:
    if _sentiment_pipeline is None:
        return None
    try:
        sentences = split_sentences(text) or [text] # split_sentences can return an empty list for empty/whitespace-only text, fall back to the raw text rather than crash on an empty list
        sentence_emotion_scores = []
        for sentence in sentences:
            results = _sentiment_pipeline(sentence)[0]
            sentence_emotion_scores.append({r["label"]: r["score"] for r in results})
        return score_checkin(sentence_emotion_scores)
    except Exception:
        return None