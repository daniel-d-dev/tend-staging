import ollama

BANDS = [
    (0.10, "Clearly settled"),
    (0.25, "Broadly okay"),
    (0.45, "Mild tension"),
    (0.60, "Moderate difficulty"),
    (0.75, "Significant difficulty"),
    (1.01, "High distress") # slightly above the maximum possible score as some formulas can produce exactly 1.0 and the loop uses strict less than. By setting this to 1.01, the loop always finds a match
]

BAND_ORDER = [b[1] for b in BANDS]

def get_band(score: float) -> str:
    for threshold, label in BANDS:
        if score < threshold:
            return label
    return BANDS[-1][1]

FORMULA_DESCRIPTIONS = {
    "A": "sadness only",
    "B": "average of sadness and fear",
    "C": "average of sadness, fear and anger",
    "D": "average of sadness, fear, anger and disgust",
    "E": "1 minus joy (fires whenever joy is low, regardless of which negative emotion is present)",
    "F": "average of sadness and fear, scaled down by how much joy is present",
    "G": "a weighted blend of all six emotions, clamped to zero"
}

def compute_formulas(scores: dict[str, float]) -> dict:
    joy = scores.get("joy", 0)
    sadness = scores.get("sadness", 0)
    anger = scores.get("anger", 0)
    fear = scores.get("fear", 0)
    disgust = scores.get("disgust", 0)
    neutral = scores.get("neutral", 0)

    raw = {
        "A": sadness,
        "B": (sadness + fear) / 2,
        "C": (sadness + fear + anger) / 3,
        "D": (sadness + fear + anger + disgust) / 4,
        "E": 1 - joy,
        "F": ((sadness + fear) / 2) * (1 - joy),
        "G": max(0.0, (sadness * 0.4) + (fear * 0.3) + (anger * 0.2) + (disgust * 0.1) + (joy * -0.3) + (neutral * -0.1)), # the formula selected from the evaluation study. The score is stored as sentiment_score and used by the inference engine to detect when someone drops below their personal baseline
    }

    return {
        name: {"score": round(value, 4), "band": get_band(value)}
        for name, value in raw.items()
    }

CONSENSUS_THRESHOLD = 6 # 6 out of the 7 formulas must agree to skip the llm pipeline

def consensus_band(formula_results: dict) -> str | None:
    counts = {}
    for data in formula_results.values():
        band = data["band"]
        counts[band] = counts.get(band, 0) + 1 # increment this band's count, start from 0 if it hasn't been seen yet
    best_band = max(counts, key = counts.get)
    best_count = counts[best_band]
    if best_count >= CONSENSUS_THRESHOLD:
        return best_band
    return None

def format_formula_block(formula_results: dict) -> str:
    lines = []
    for name, data in formula_results.items():
        desc = FORMULA_DESCRIPTIONS.get(name, "")
        lines.append(f"- Formula {name} ({desc}): score {data["score"]} -> \"{data["band"]}\"")
    return "\n".join(lines)

MODEL = "llama3.1"

# Advocate Agent
def advocate(text: str, formula_results: dict) -> str:
    formula_block = format_formula_block(formula_results)
    bands = ", ".join(BAND_ORDER)
    prompt = f"""You are assessing the emotional distress expressed in a short piece of text written by someone describing how they feel in a particular situation.

TEXT:
"{text}"

Seven scoring formulas have analysed this text using an emotion classification model. Each formula combines the model's emotion scores differently:

{formula_block}

The possible distress bands, from lowest to highest, are: {bands}.

Your task: argue for which single distress band best reflects what this person is actually expressing, using both the formula scores above AND your own reading of the text itself. Pay close attention to things the formulas might miss, such as:
- whether the person is speaking about themselves directly, or in a conditional/hypothetical way ("I would feel...")
- whether the person is intellectualising, generalising, or giving advice rather than expressing their own feelings
- whether the emotional language used matches the distress level the formulas suggest

Give a clear, direct argument. State your chosen band explicitly. Do not ask follow-up questions. Keep your answer under 150 words.
"""

    response = ollama.chat(
        model = MODEL,
        messages = [{"role": "user", "content": prompt}],
        options = {"temperature": 0} # temperature 0 means deterministic output so the same input always produces the same response
    )
    return response["message"]["content"]

# Devil's Advocate Agent
def devils_advocate(text: str, formula_results: dict, advocate_argument: str) -> str:
    formula_block = format_formula_block(formula_results)
    bands = ", ".join(BAND_ORDER)

    prompt = f"""You are critically reviewing someone else's assessment of emotional distress in a piece of text. Your job is to challenge it, not to agree with it by default.

TEXT:
"{text}"

Seven scoring formulas have analysed this text:

{formula_block}

The possible distress bands, from lowest to highest, are: {bands}.

THE ASSESSMENT YOU ARE REVIEWING:
"{advocate_argument}"

Critically challenge this assessment. Specifically check:
- Does the conclusion match what the majority of the formulas suggest? If the assessment landed on a band that most formulas disagree with, ask why. Formula agreement is one form of evidence, but it is not automatically correct — the formulas can only detect a fixed, limited set of named emotions, so a genuine feeling that doesn't map cleanly onto sadness, fear, anger, disgust, or joy may be invisible to most of them while still being clearly present in the text itself. Weigh the formula majority and your own independent reading of the text as comparably important sources of evidence, and judge evenhandedly whether the assessment is too low, too high, or correctly justified.
- Did the assessment correctly read whether the person was speaking directly about their own feelings, hypothetically, or in a generalising/advisory way — and does that reading point toward higher or lower distress?

Write up to 100 words of reasoning. Then, on their own final two lines, in exactly this format and nothing else, give your verdict. These two lines are mandatory and must always be included, with no other text after them:

VERDICT: AGREE or DISAGREE
BAND: <one band name from the list above>

The BAND line is your final position, not the one you are reviewing.
"""

    response = ollama.chat(
        model = MODEL,
        messages = [{"role": "user", "content": prompt}],
        options = {"temperature": 0}
    )
    return response["message"]["content"]

# Judge Agent
def judge(text: str, formula_results: dict, advocate_argument: str, devils_advocate_response: str) -> str:
    formula_block = format_formula_block(formula_results)
    bands = ", ".join(BAND_ORDER)

    prompt = f"""You are making the final determination of the emotional distress expressed in a piece of text. Two reviewers have already given their assessments, and they may disagree with each other. Your job is to weigh both and decide — you are not required to side with either one, and may reach a different conclusion than both if that is what the evidence supports.

TEXT:
"{text}"

Seven scoring formulas have analysed this text:

{formula_block}

The possible distress bands, from lowest to highest, are: {bands}.

FIRST ASSESSMENT:
"{advocate_argument}"

SECOND ASSESSMENT (a critical review of the first):
"{devils_advocate_response}"

Before deciding, check which band the majority of the seven formulas actually point to. Treat that majority as meaningful evidence, but remember that the formulas can only detect a fixed, limited set of named emotions — a genuine feeling that doesn't map cleanly onto sadness, fear, anger, disgust, or joy may be invisible to most formulas while still being clearly present in the text itself. Weigh the formula majority and an independent reading of the text as comparably important sources of evidence — neither should be a default that only gets overridden in exceptional cases, and neither should be dismissed just because one assessment frames its argument more persuasively than the other.

Weigh both assessments against the formula majority and the text itself, then decide.

Write up to 60 words of reasoning — be concise. Only the final two lines below are read by the scoring system; your reasoning above them is never seen by anyone else, so it is far more important that those two lines are present than that the reasoning is long. No matter how much you have already written, no matter how complex the case, you must end your response with exactly these two lines and nothing after them:

FINAL BAND: <one band name from the list above>
REASON: <one short sentence>
"""

    response = ollama.chat(
        model = MODEL,
        messages = [{"role": "user", "content": prompt}],
        options = {"temperature": 0}
    )
    return response["message"]["content"]

def parse_final_band(judge_output: str) -> str | None:
    for line in judge_output.split("\n"):
        if line.strip().upper().startswith("FINAL BAND:"):
            return line.split(":", 1)[1].strip() # split once and take everything after the first colon as the band name
    return None

def score_checkin(text: str, emotion_scores: dict[str, float]) -> dict:
    formula_results = compute_formulas(emotion_scores)
    band = consensus_band(formula_results)
    if band is None:
        argument = advocate(text, formula_results)
        challenge = devils_advocate(text, formula_results, argument)
        verdict = judge(text, formula_results, argument, challenge)
        band = parse_final_band(verdict)
    return {
        "formula_g": formula_results["G"]["score"], # stored as sentiment_score for baseline comparison
        "band": band # stored for internal use only and not shown to users
    }