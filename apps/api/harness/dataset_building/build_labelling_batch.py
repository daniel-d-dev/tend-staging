import csv
import sys
from pathlib import Path

from harness.dataset_building.generate_candidates import FAILURE_MODE_PROMPTS, REGISTERS, generate_grid_candidate, generate_contrast_pair, splice_sentence
from app.services.crisis_safety_net import score_crisis_language_per_sentence, CRISIS_THRESHOLD
from app.services.nli_reranker import entailment_score, NLI_TRIGGER_THRESHOLD
from harness.dataset_building.group_ids import assign_group_id, CONTRAST_SEEDS, SPLICE_SENTENCES

def truthy(value): # a row generated just now has a real True/False, but a row read back from the csv only has the text "True" or "False", and bool("False") is actually True in python since it's a non-empty string, this just handles both cases the same way
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"

def get_source(row):
    return row["source"]

def build_batch():
    out_path = Path(__file__).resolve().parent / "labelling_batch.csv" # the csv sits in the same folder as this script, so this always finds it no matter where the script gets run from

    existing_rows = []
    if out_path.exists():
        with open(out_path, newline = "") as f: # load what's already been generated and labelled, so this can be re-run to keep growing the dataset instead of starting over each time
            existing_rows = list(csv.DictReader(f))

    existing_texts = set() # just the text of every row already generated, so the deduplicate check below can spot a repeat
    for row in existing_rows:
        existing_texts.add(row["text"])

    labeled_count = 0
    for row in existing_rows:
        if row["label"]:
            labeled_count += 1
    print(f"Loaded {len(existing_rows)} existing rows ({labeled_count} labeled) from {out_path.name}", file = sys.stderr)

    rows = [] # every candidate generated below goes in here as a dict, "source" just says how and where it came from eg. "grid:crisis_direct"

    print("Generating grid candidates", file = sys.stderr)
    for failure_mode in FAILURE_MODE_PROMPTS: # every failure_mode/register combination gets its own fresh generation
        for register in REGISTERS:
            text = generate_grid_candidate(failure_mode, register)
            rows.append({"source": f"grid:{failure_mode}", "text": text})
            print(f"  {failure_mode} / {register}", file = sys.stderr)

    print("Generating contrast pairs", file = sys.stderr)
    for seed_id, seed in CONTRAST_SEEDS.items(): # the seed itself gets added as its own row too, so each rewrite can be compared back against the original wording it came from
        rows.append({"source": "contrast:seed", "text": seed, "known_group_id": seed_id})
        for transform in ["conditional", "past_resolved", "positive_valence", "terse"]:
            text = generate_contrast_pair(seed, transform)
            rows.append({"source": f"contrast:{transform}", "text": text, "known_group_id": seed_id}) # known_group_id remembers which seed this came from, so it can still be linked back to it later
            print(f"  {transform} of seed", file = sys.stderr)

    print("Generating spliced (dilution) candidates", file = sys.stderr)
    for splice_id, sentence in SPLICE_SENTENCES.items(): # buries the sentence in filler at 3 different positions, to check it still gets caught once it's not the only thing in the message
        for position in ["start", "middle", "end"]:
            text = splice_sentence(sentence, position)
            rows.append({"source": f"spliced:{position}", "text": text, "known_group_id": splice_id})

    before_dedup = len(rows)
    new_rows = [] # drop anything that's an exact match for text already in the file
    for row in rows:
        if row["text"] not in existing_texts:
            new_rows.append(row)
    rows = new_rows
    skipped = before_dedup - len(rows)

    print("Scoring new candidates", file = sys.stderr)
    for row in rows: # scored with the real live detector, not a mock, so this matches what the actual app would do
        cosine = score_crisis_language_per_sentence(row["text"]) # cosine and nli are the app's two separate ways of checking if text sounds like a crisis
        nli = entailment_score(row["text"])
        row["cosine_score"] = round(cosine, 3)
        row["nli_score"] = round(nli, 3)
        row["cosine_triggered"] = cosine > CRISIS_THRESHOLD
        row["nli_triggered"] = nli > NLI_TRIGGER_THRESHOLD
        row["signals_disagree"] = row["cosine_triggered"] != row["nli_triggered"]
        near_boundary = abs(cosine) < 0.1 or (0.15 < nli < 0.85)
        row["interesting"] = row["signals_disagree"] or near_boundary # signals disagree, or either one is close to its own threshold, these are the examples most worth spending review time on
        row["label"] = "" # for me to fill in: CRISIS / BOUNDARY / NOT_CRISIS
        row["group_id"] = assign_group_id(row["source"], row["text"], row.pop("known_group_id", None)) # pass along the group_id from above if we already know it (contrast/spliced rows), otherwise let assign_group_id work it out itself

    all_rows = existing_rows + rows

    interesting_rows = [] # split into interesting and not, so interesting rows can be put first once both are sorted and put back together below
    other_rows = []
    for row in all_rows:
        if truthy(row["interesting"]):
            interesting_rows.append(row)
        else:
            other_rows.append(row)
    interesting_rows.sort(key = get_source)
    other_rows.sort(key = get_source)
    all_rows = interesting_rows + other_rows

    with open(out_path, "w", newline = "") as f:
        writer = csv.DictWriter(f, fieldnames = [ # this list sets the column order in the actual csv file
            "label", "interesting", "source", "text", "cosine_score", "nli_score",
            "cosine_triggered", "nli_triggered", "signals_disagree", "group_id",
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    unlabeled_count = 0
    for row in all_rows:
        if not row["label"]:
            unlabeled_count += 1

    interesting_count = 0
    for row in rows:
        if truthy(row["interesting"]):
            interesting_count += 1

    print(f"\nAppended {len(rows)} new candidates ({skipped} duplicates skipped) to {out_path}", file = sys.stderr)
    print(f"{len(all_rows)} total rows, {unlabeled_count} unlabeled", file = sys.stderr)
    print(f"{interesting_count} of the new rows flagged as especially worth reviewing (disagreement or near-boundary)", file = sys.stderr)

if __name__ == "__main__": # this only runs when the file is executed directly (python3 build_labelling_batch.py), not when something else imports functions from it
    build_batch()
