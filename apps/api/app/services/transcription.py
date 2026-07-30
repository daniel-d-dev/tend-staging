import whisper
import ffmpeg

model = whisper.load_model("base") # chose the smallest deliberately, not the most accurate option. Found transcription latency to be a problem so speed was prioritised

def get_audio_duration(path: str) -> float:
    return float(ffmpeg.probe(path)["format"]["duration"])

def transcribe_audio(path: str) -> str:
    result = model.transcribe(path)
    return result["text"].strip()