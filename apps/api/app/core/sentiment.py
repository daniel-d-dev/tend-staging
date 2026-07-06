from transformers import pipeline
from app.services.scoring import score_checkin

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
        results = _sentiment_pipeline(text)[0]
        emotion_scores = {r["label"]: r["score"] for r in results}
        return score_checkin(text, emotion_scores)
    except Exception:
        return None