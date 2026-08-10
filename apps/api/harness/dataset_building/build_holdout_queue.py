import csv
import random
import sys
from pathlib import Path

from harness.dataset_building.generate_candidates import generate_from_prompt, REGISTERS, FAILURE_MODE_PROMPTS, generate_grid_candidate
from app.services.crisis_safety_net import score_crisis_language_per_sentence, CRISIS_THRESHOLD
from app.services.nli_reranker import nli_triggered_score

BLIND_SPOT_PROMPTS = { # 5 fresh prompts, one for each construct that used to be a recall blind spot. deliberately worded differently from group_ids.py's CONTRAST_SEEDS, so this is a genuinely new test of whether the fix worked, not just re-testing the exact sentences it was tuned on
    "sudden_calm": "Write a first-person daily check-in message where the person describes feeling suddenly, unusually calm or at peace after a period of real difficulty, as if something has been decided or resolved for them - the kind of calm that can be a warning sign after a hard time, not just genuine relief. Write it the way a real person would actually type it - casual, maybe lowercase, not dramatic.",
    "burden_relief": "Write a first-person daily check-in message where the person expresses that the people close to them would be better off, less stressed, or less burdened if they weren't around - framed around relieving others of a burden, not about their own suffering directly. Write it casually, the way someone would actually type it.",
    "belongingness": "Write a first-person daily check-in message where the person describes feeling like no one would notice or care if they weren't around, or that they're completely disconnected from everyone in their life. Write it casually, the way someone would actually type it.",
    "no_future": "Write a first-person daily check-in message where the person describes being completely unable to picture or imagine having any future at all - not just uncertainty, a total blank when they try. Write it casually, the way someone would actually type it.",
    "passive_ideation": "Write a first-person daily check-in message where the person expresses wishing they wouldn't wake up, or wishing they could just stop existing, without describing any plan or intent to act - a passive wish, not active intent. Write it casually, the way someone would actually type it.",
}

SELF_HARM_ADVERSARIAL_PROMPT = ( # self_harm has a known weak spot, it scored 0.48 on "Acting in the school play tonight, pretending to be a pirate," a completely mundane sentence so this generates fresh benign text using similar hurting/pain/urge language to check that weak spot properly
    "Write a short, first-person, completely ordinary and benign daily check-in message that happens to use words or phrases associated with hurting, pain, urges, or physical sensation in a totally non-crisis, everyday context (for example: sore muscles from exercise, a craving for food, an urge to buy something, a minor accidental injury, a competitive urge in a game or sport). It must NOT express any real self-harm intent or distress. Write it casually, the way someone would actually type it."
)

def score(text: str) -> dict: # calls the same nli_triggered_score the real deployed detector uses, rather than a simplified copy of it. that function already handles per-sentence scoring, per-hypothesis threshold overrides, and the hopelessness/physical-exertion correction, so none of that needs repeating here
    cosine = score_crisis_language_per_sentence(text)
    nli_triggered, nli_score, nli_hypothesis = nli_triggered_score(text)
    return {
        "cosine_score": round(cosine, 3),
        "cosine_triggered": cosine > CRISIS_THRESHOLD,
        "nli_score": round(nli_score, 3),
        "nli_hypothesis": nli_hypothesis,
        "nli_triggered": nli_triggered,
    }

def build_rows(): # 3 sources of held-out text: fresh crisis text for the constructs listed in BLIND_SPOT_PROMPTS, fresh adversarial benign text for self_harm's known weak spot, and ordinary mundane check-ins to check the false-positive rate on realistic text
    rows = []

    print("Generating fresh crisis text for the 5 former blind-spot constructs", file = sys.stderr)
    for construct, prompt in BLIND_SPOT_PROMPTS.items():
        for register in REGISTERS:
            text = generate_from_prompt(f"{prompt} Write it in this style: {register}.")
            rows.append({"source": f"holdout_crisis:{construct}", "text": text, "expect": "CRISIS_FAMILY"})
            print(f"  {construct} / {register}", file = sys.stderr)

    print("Generating fresh adversarial benign text for self_harm", file = sys.stderr)
    for i in range(15):
        register = REGISTERS[i % len(REGISTERS)]
        text = generate_from_prompt(f"{SELF_HARM_ADVERSARIAL_PROMPT} Write it in this style: {register}.")
        rows.append({"source": "holdout_adversarial:self_harm", "text": text, "expect": "BENIGN"})
        print(f"  self_harm adversarial {i + 1} of 15", file = sys.stderr)

    print("Generating mundane check-ins", file = sys.stderr)
    for i in range(20):
        mode = "ordinary_negative" if i % 2 == 0 else "ordinary_positive"
        register = REGISTERS[i % len(REGISTERS)]
        text = generate_grid_candidate(mode, register)
        rows.append({"source": f"holdout_mundane:{mode}", "text": text, "expect": "BENIGN"})
        print(f"  mundane {i + 1} of 20", file = sys.stderr)

    return rows

def pick_anchors(labeled_path: Path, n_each: int = 2) -> list[dict]: # anchors are real, already-labelled rows mixed into the queue as a sanity check. if labelling later disagrees with a label that's already trusted, that's worth noticing. n_each = 2 picks 2 per label, so all 3 ground-truth categories get at least some overlap check
    with open(labeled_path, newline = "") as f:
        labeled = list(csv.DictReader(f))

    anchors = []
    for label in ["CRISIS", "NOT_CRISIS", "BOUNDARY"]:
        candidates = []
        for row in labeled:
            if row["label"] == label and len(row["text"]) < 200:
                candidates.append(row)
        anchors.extend(random.sample(candidates, min(n_each, len(candidates))))
    return anchors

def main():
    random.seed(2026) # fixed seed so the shuffle below is reproducible, the same queue comes out every time this is run
    harness_dir = Path(__file__).resolve().parent # the folder this script lives in, used below to find labelling_batch.csv and to write both output files next to it, regardless of where the script is actually run from
    out_path = harness_dir / "holdout_queue.csv"

    rows = build_rows()
    for row in rows:
        row.update(score(row["text"])) # merges cosine_score/cosine_triggered/nli_score/nli_hypothesis/nli_triggered straight into this row's dict
        row["label"] = ""
        row["is_anchor"] = False

    anchors_raw = pick_anchors(harness_dir / "labelling_batch.csv")
    anchor_rows = []
    for anchor in anchors_raw:
        anchor_rows.append({
            "source": "anchor", "text": anchor["text"], "expect": "", "label": anchor["label"],
            "is_anchor": True, "cosine_score": anchor.get("cosine_score", ""),
            "cosine_triggered": anchor.get("cosine_triggered", ""), "nli_score": anchor.get("nli_score", ""),
            "nli_hypothesis": "", "nli_triggered": anchor.get("nli_triggered", ""), # nli_hypothesis stays blank - labelling_batch.csv doesn't record which hypothesis triggered, only whether one did
        })

    random.shuffle(rows)
    midpoint = len(rows) // 2
    queue = anchor_rows[:len(anchor_rows) // 2] + rows[:midpoint] + anchor_rows[len(anchor_rows) // 2:] + rows[midpoint:] # half the anchors near the start, half near the end, fresh rows shuffled in between

    with open(out_path, "w", newline = "") as f: # blind columns only - the true label/expect is withheld here and kept in the separate answer key below, so labelling is genuinely blind
        writer = csv.DictWriter(f, fieldnames = ["blind_id", "text", "your_label"])
        writer.writeheader()
        for i, row in enumerate(queue):
            writer.writerow({"blind_id": i, "text": row["text"], "your_label": ""})

    answer_key_path = harness_dir / "holdout_answer_key.csv"
    with open(answer_key_path, "w", newline = "") as f:
        writer = csv.DictWriter(f, fieldnames = [
            "blind_id", "source", "expect", "true_label_if_anchor", "is_anchor",
            "cosine_score", "cosine_triggered", "nli_score", "nli_hypothesis", "nli_triggered",
        ])
        writer.writeheader()
        for i, row in enumerate(queue):
            writer.writerow({
                "blind_id": i,
                "source": row["source"],
                "expect": row.get("expect", ""),
                "true_label_if_anchor": row["label"] if row["is_anchor"] else "",
                "is_anchor": row["is_anchor"],
                "cosine_score": row["cosine_score"],
                "cosine_triggered": row["cosine_triggered"],
                "nli_score": row["nli_score"],
                "nli_hypothesis": row["nli_hypothesis"],
                "nli_triggered": row["nli_triggered"],
            })

    print(f"\n{len(queue)} rows written to {out_path.name} ({len(rows)} fresh + {len(anchor_rows)} anchor repeats)", file = sys.stderr)
    print(f"Answer key (do not open until labelling is done): {answer_key_path.name}", file = sys.stderr)

if __name__ == "__main__": # only runs when this file is executed directly, not when something imports functions from it
    main()
