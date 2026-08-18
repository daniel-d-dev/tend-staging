import csv
import sys
from pathlib import Path
from math import sqrt

from app.services.ensemble import evaluate_checkin

# ties together all of the numbers used for the dissertation's crisis safety net evaluation, so the whole thing can be rerun from one place. only reads from holdout_evaluation_set.csv, never labelling_batch.csv, as that's the file the two thresholds were actually tuned against

# holdout_evaluation_set.csv mixes three batches of text with different labelling histories, tracked in the source column, original_blind_holdout and sealed_slab rows were generated aiming at specific constructs, then read and labelled blind, without knowing which construct each one was written for. confirmed rows were written with a specific construct or technique already in mind and then confirmed directly, not blind labelled, because the original crisis and adversarial samples were too small on their own to support a real number

# the same underlying limitation applies to both kinds though, since I designed the crisis constructs and adversarial techniques myself, a genuinely naive labeller who knows nothing about what's being tested doesn't exist for either one

HARNESS_DIR = Path(__file__).resolve().parent

def confidence_interval(successes, n, z = 1.96): # 95% confidence interval for a proportion, given how much a small n should actually be trusted. the plain success/n rate on its own hides how easily a small sample could have landed somewhere else. Wilson interval, more accurate than the standard formula when n is small or the rate sits near 0% or 100%, both true here
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denominator = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * sqrt((p * (1 - p) / n) + (z * z / (4 * n * n)))
    return ((centre - margin) / denominator, (centre + margin) / denominator)

def load_rows():
    with open(HARNESS_DIR / "holdout_evaluation_set.csv", newline = "") as f:
        return list(csv.DictReader(f))

def score_rows(rows):
    for row in rows:
        result = evaluate_checkin(row["text"])
        row["triggered"] = result["safety_net_triggered"]

def rows_matching(rows, label = None, category = None):
    matched = []
    for row in rows:
        if label is not None and row["label"] != label:
            continue
        if category is not None and row["category"] != category:
            continue
        matched.append(row)
    return matched

def count_triggered(rows):
    triggered = 0
    for row in rows:
        if row["triggered"]:
            triggered += 1
    return triggered

def report(name, rows):
    triggered = count_triggered(rows)
    n = len(rows)
    lo, hi = confidence_interval(triggered, n)
    rate = triggered / n if n else 0.0
    print(f"{name}: {triggered}/{n} = {rate * 100:.1f}% (95% range: {lo * 100:.1f}%-{hi * 100:.1f}%)")

def main():
    print("Scoring everything against the live deployed ensemble, takes a few minutes\n", file = sys.stderr)

    rows = load_rows()
    score_rows(rows)

    crisis_rows = rows_matching(rows, label = "CRISIS")
    report("Crisis recall", crisis_rows)

    ordinary_rows = rows_matching(rows, label = "NOT_CRISIS", category = "ordinary")
    report("Ordinary false positives", ordinary_rows)

    not_crisis_rows = rows_matching(rows, label = "NOT_CRISIS")
    adversarial_rows = []
    for row in not_crisis_rows:
        if row["category"] not in ("ordinary", "anchor"):
            adversarial_rows.append(row)
    report("Adversarial false positives", adversarial_rows)

    print()
    print("Adversarial false positives, broken down by technique:")
    categories = set()
    for row in adversarial_rows:
        categories.add(row["category"])
    for category in sorted(categories):
        matching = rows_matching(rows, category = category)
        print(f"  {category}: {count_triggered(matching)}/{len(matching)}")

    # boundary is reported as-is, deliberately not grown, since it's a description of what happened rather than a claim needing statistical confidence
    boundary_rows = rows_matching(rows, label = "BOUNDARY")
    print(f"\nBoundary cases (descriptive only, not a pass/fail number): {count_triggered(boundary_rows)}/{len(boundary_rows)}")

if __name__ == "__main__":
    main()
