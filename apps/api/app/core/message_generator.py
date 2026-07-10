import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
AGENT_NAME = "Thread"

def mood_summary(signals: dict) -> str:
    parts = []
    if signals["avg_sentiment"] is not None:
        if signals["avg_sentiment"] > 0.35:
            parts.append("several members are struggling")
        elif signals["avg_sentiment"] > 0.15:
            parts.append("the group is having a mixed week")
        else:
            parts.append("the group is broadly doing well")
    if signals["temperature_words"]:
        words = ", ".join(signals["temperature_words"])
        parts.append(f"this week members described themselves as: {words}")
    if signals["has_recent_flag"]:
        parts.append("at least one member has been flagged for distress recently")
    return ". ".join(parts) if parts else "no strong signals this week"

def build_prompt(mode: str, category: str | None, mood: str, last_post_summary: str | None) -> str:
    base = (
        f"You are {AGENT_NAME}, a warm presence in a friend group's peer support app. "
        "You are not a member of the group but you have a presence in their shared feed. "
        "Write in a casual, warm, non-clinical tone. Keep it to 2 to 3 sentences maximum. "
        "You are not a participant in activities — you suggest them for the group, not yourself. "
        "Do not describe your own feelings, reactions, or experiences. "
        "Do not start with 'Hey' or 'Hi'. Do not mention scores, data, or anything technical. " # LLMs tend to use this language without being told to
        "Do not suggest specific times or dates. "
        "Do not use exclamation marks. "
        "Warm and calm in tone, not energetic or hype. "
        "Do not use phrases like 'I would love', 'I hope', or 'I think'. "
        "Use British English spelling and phrasing. Avoid American cultural references. "
        f"Current mood of the group: {mood}."
    )
    if last_post_summary:
        base += f" Your last message was: {last_post_summary}. Do not repeat yourself."
    if mode == "urgent":
        return base + " Someone in the group may be having a hard time. Write a short, gentle message to the whole group letting them know you're thinking of them. Do not identify anyone."
    if mode == "supportive":
        return base + " The group is having a tough week. Write a warm, supportive message. No activity suggestion, just warmth and presence."
    if mode == "connective":
        return base + " It has been a mixed week. Acknowledge that and suggest something low-effort and social the group could do together."
    return base + f" The group is doing well. Suggest a {category} activity for them to do together. Be specific and natural."

def generate_message(mode: str, category: str | None, signals: dict, last_post_summary: str | None = None) -> str:
    mood = mood_summary(signals)
    prompt = build_prompt(mode, category, mood, last_post_summary)
    response = httpx.post(OLLAMA_URL, json = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout = 30.0)
    response.raise_for_status()
    return response.json()["response"].strip()