import numpy as np

from harness.dataset_building.run_holdout_evaluation import load_rows, score_rows, rows_matching, count_triggered

# recall and both false positive rates come from small samples too, not just prevalence, so treating them as fixed numbers and only worrying about uncertainty in prevalence would make this look more precise than it actually is. instead of using the flat rate for each one, I draw 500,000 plausible values for what the true rate could be, based on how many successes and failures were actually observed (a beta distribution, starting neutral, so any rate is equally likely before seeing the data) and run every combination through, carrying all three uncertainties into the final range together, not just one

SAMPLES = 500_000
SEED = 42 # fixed so this reproduces the same numbers every run, same reasoning as build_holdout_queue.py's fixed seed

def beta_samples(successes, n, rng):
    return rng.beta(successes + 1, n - successes + 1, SAMPLES)

def precision_at_prevalence(recall_samples, fpr_samples, prevalence): # Bayes' rule. of everyone who'd actually get flagged at this prevalence, how many would really be in crisis
    return (recall_samples * prevalence) / (recall_samples * prevalence + fpr_samples * (1 - prevalence))

def report_prevalence(prevalence_percent, recall_samples, fpr_samples):
    prevalence = prevalence_percent / 100
    precision_samples = precision_at_prevalence(recall_samples, fpr_samples, prevalence)
    low, high = np.percentile(precision_samples, [2.5, 97.5])
    median = np.median(precision_samples)
    print(f"  prevalence {prevalence_percent}%: median {median * 100:.1f}%, 95% credible interval {low * 100:.1f}%-{high * 100:.1f}%")
    return low, high

def run_simulation(recall_successes, recall_n, fpr_successes, fpr_n, label):
    rng = np.random.default_rng(SEED)
    recall_samples = beta_samples(recall_successes, recall_n, rng)
    fpr_samples = beta_samples(fpr_successes, fpr_n, rng)

    print(f"using the {label} false positive rate")
    range_low = []
    range_high = []
    for prevalence_percent in [1, 2, 3, 4, 5]: # a plausible illustrative range, not derived from a specific prevalence estimate
        low, high = report_prevalence(prevalence_percent, recall_samples, fpr_samples)
        range_low.append(low)
        range_high.append(high)
    print(f"combined range across 1-5% prevalence: {min(range_low) * 100:.1f}%-{max(range_high) * 100:.1f}%\n")

def main():
    rows = load_rows()
    score_rows(rows)

    crisis_rows = rows_matching(rows, label = "CRISIS")
    recall_successes = count_triggered(crisis_rows)
    recall_n = len(crisis_rows)

    ordinary_rows = rows_matching(rows, label = "NOT_CRISIS", category = "ordinary")
    ordinary_successes = count_triggered(ordinary_rows)
    ordinary_n = len(ordinary_rows)

    not_crisis_rows = rows_matching(rows, label = "NOT_CRISIS")
    adversarial_rows = []
    for row in not_crisis_rows:
        if row["category"] not in ("ordinary", "anchor"):
            adversarial_rows.append(row)
    adversarial_successes = count_triggered(adversarial_rows)
    adversarial_n = len(adversarial_rows)

    print(f"recall: {recall_successes}/{recall_n}, ordinary FPR: {ordinary_successes}/{ordinary_n}, adversarial FPR: {adversarial_successes}/{adversarial_n}\n")

    run_simulation(recall_successes, recall_n, ordinary_successes, ordinary_n, "ordinary")
    run_simulation(recall_successes, recall_n, adversarial_successes, adversarial_n, "adversarial")

if __name__ == "__main__":
    main()
