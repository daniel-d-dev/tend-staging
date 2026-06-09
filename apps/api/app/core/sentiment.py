from transformers import pipeline

_sentiment_pipeline = None

def load_model():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "text-classification",
            model = "j-hartmann/emotion-english-distilroberta-base",
            top_k = None
        )

def score_text(text: str) -> float | None:
    if _sentiment_pipeline is None:
        return None
    
    try:
        results = _sentiment_pipeline(text)[0]
        scores = {r["label"]: r["score"] for r in results}
        return scores.get("sadness", 0) + scores.get("fear", 0) # primary distress signals, may change
    except Exception:
        return None