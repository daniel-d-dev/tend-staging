from sentence_transformers import SentenceTransformer
import numpy as np

LOW_ENERGY_REFERENCE = [
    "tired", "drained", "exhausted", "burnt out", "stressed",
    "anxious", "overwhelmed", "down", "flat", "heavy",
    "rough", "rubbish", "grim", "awful", "low", "horrible",
    "dead", "cooked", "done", "wiped out", "zonked", "shattered",
    "drained", "empty", "depleted", "defeated", "hopeless",
    "struggling", "broken", "numb", "lost", "suffocating",
    "can't be bothered", "going through it", "not myself", "struggling today", "dead inside",
    "uninspired", "apathetic", "indifferent", "disengaged", "whatever", "unmotivated"
]

HIGH_ENERGY_REFERENCE = [
    "energetic", "active", "lively", "vibrant", "alert",
    "refreshed", "invigorated", "pumped", "ready", "sprightly",
    "good", "great", "fine", "well", "brilliant",
    "thriving", "flourishing", "buzzing", "fired up", "alive",
    "positive", "upbeat", "cheerful", "confident", "strong",
    "productive", "focused", "clear", "light", "free",
    "nailing it", "crushing it", "on fire", "smashing it", "killing it",
    "decent", "blessed", "content", "pleased", "satisfied", "motivated",
    "relaxed", "chill", "peaceful", "calm", "hopeful", "supported", "loved"
]

# loaded once at startup so each call only encodes the input word
model = SentenceTransformer("all-mpnet-base-v2")
low_ref = model.encode(LOW_ENERGY_REFERENCE)
high_ref = model.encode(HIGH_ENERGY_REFERENCE)

def score_low_energy(word: str) -> float:
    embedding = model.encode([word])
    low_score = (embedding @ low_ref.T).max() # similarity to the closest low energy word, not an average across all of them
    high_score = (embedding @ high_ref.T).max() # same applies here but for high energy words
    return float(low_score - high_score)