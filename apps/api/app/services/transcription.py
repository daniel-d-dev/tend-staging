import whisper
import os

model = whisper.load_model("base")

def transcribe_audio(path: str) -> str:
    result = model.transcribe(path)
    return result["text"].strip()