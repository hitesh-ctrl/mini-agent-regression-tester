"""
diff.py  —  compare baseline vs replay traces and report labels per scenario.

Labels
------
SAME          Both versions made the same decision (both called the tool with the
              same arguments and got the same success/failure, or both skipped it).
VALID CHANGE  The versions diverged, but the new behavior is defensibly correct:
              the baseline's tool call was going to fail anyway, or the replay's
              failed safely where the baseline did not call it.
REGRESSION    The versions diverged in a way that looks like a step back: a refund
              that the baseline issued correctly is now skipped, or the replay
              started issuing refunds that the baseline (correctly) did not.
DIFFERENT     The divergence does not fit the other buckets; needs manual review.

Variance
--------
Each scenario is run N_RUNS times.  diff.py reports a per-run label and then a
summary: "SAME 4/5, REGRESSION 1/5".  An agent that is SAME 3 of 5 times is NOT
reliably the same — this is noted in the summary when the dominant label wins
fewer than N_RUNS times.

Reply-text check
----------------
When a tool call failed (result.success == False) but the agent's follow-up reply
contains the word "refunded" or a dollar amount ("$<digits>"), that is flagged as
a suspicious reply: the model may be hallucinating a successful outcome.
"""

import glob
import json
import os
import re
import sys

N_RUNS = 5


# ---------------------------------------------------------------------------
# Core classifier (also imported by tests/test_diff.py)
# ---------------------------------------------------------------------------

def classify(baseline: dict, replay: dict) -> str:
    """Return a label string for one baseline/replay trace pair."""
    b_tool = baseline.get("tool_called")
    r_tool = replay.get("tool_called")

    if b_tool != r_tool:
        if b_tool == "issue_refund" and r_tool is None:
            if baseline.get("result", {}).get("success"):
                return "REGRESSION"
            else:
                return "VALID CHANGE"
        elif b_tool is None and r_tool == "issue_refund":
            if replay.get("result", {}).get("success"):
                return "REGRESSION"
            else:
                return "VALID CHANGE"
        else:
            return "DIFFERENT"

    if b_tool is None:
        return "SAME"

    # Both called the tool — compare arguments and success flags
    b_args = baseline.get("arguments", {})
    r_args = replay.get("arguments", {})
    b_ok = baseline.get("result", {}).get("success")
    r_ok = replay.get("result", {}).get("success")

    if b_args == r_args and b_ok == r_ok:
        return "SAME"
    return "DIFFERENT"


_MONEY_RE = re.compile(r"\$\s*\d")


def suspicious_reply(trace: dict):
    """
    Return a warning string if the agent's reply looks wrong after a failed tool
    call, or None if everything looks fine.
    """
    if trace.get("tool_called") != "issue_refund":
        return None
    if trace.get("result", {}).get("success"):
        return None  # tool succeeded; mentioning a refund is expected
    reply = (trace.get("agent_reply") or "").lower()
    if "refunded" in reply or _MONEY_RE.search(reply):
        return (
            "reply mentions 'refunded' or a dollar amount after a failed tool call "
            f"(result: {trace['result'].get('reason', '?')})"
        )
    return None


# ---------------------------------------------------------------------------
# Discover scenario IDs from trace files on disk
# ---------------------------------------------------------------------------

def discover_scenario_ids():
    files = glob.glob("scenario_*.json") + glob.glob("scenario_*_run*.json")
    ids = set()
    for f in files:
        name = f.removesuffix(".json")
        name = re.sub(r"_run\d+$", "", name)
        ids.add(name)
    return sorted(ids)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

LABEL_ORDER = ["SAME", "VALID CHANGE", "REGRESSION", "DIFFERENT"]


def main():
    scenario_ids = discover_scenario_ids()
    if not scenario_ids:
        print("No trace files found. Run main.py first.")
        sys.exit(1)

    grand_counts = {k: 0 for k in LABEL_ORDER}
    warnings = []

    print()
    for sid in scenario_ids:
        run_labels = []
        for run in range(1, N_RUNS + 1):
            b_path = f"{sid}_run{run}.json"
            r_path = f"replay_{sid}_run{run}.json"
            # fall back to legacy single-run filenames
            if not os.path.exists(b_path):
                b_path = f"{sid}.json"
            if not os.path.exists(r_path):
                r_path = f"replay_{sid}.json"

            if not os.path.exists(b_path) or not os.path.exists(r_path):
                break

            baseline = _load(b_path)
            replay = _load(r_path)
            label = classify(baseline, replay)
            run_labels.append(label)

            for t, tag in [(baseline, "baseline"), (replay, "replay")]:
                w = suspicious_reply(t)
                if w:
                    warnings.append(f"  {sid}/run{run}/{tag}: {w}")

        if not run_labels:
            print(f"{sid}: no traces found")
            continue

        counts = {k: run_labels.count(k) for k in LABEL_ORDER if run_labels.count(k)}
        dominant = max(counts, key=lambda k: counts[k])
        grand_counts[dominant] += 1

        per_run = "  ".join(f"run{i+1}:{l}" for i, l in enumerate(run_labels))
        summary_parts = [f"{l} {n}/{len(run_labels)}" for l, n in counts.items() if n]
        summary = ", ".join(summary_parts)
        stable = " ⚠ not stable" if counts.get(dominant, 0) < len(run_labels) else ""
        print(f"{sid}: {dominant} ({summary}){stable}")
        print(f"  {per_run}")

    total = sum(grand_counts.values())
    print()
    print("── Summary ──────────────────────────────────")
    for label in LABEL_ORDER:
        n = grand_counts[label]
        if n:
            print(f"  {label:12s} {n:3d} / {total}")

    if warnings:
        print()
        print("── Suspicious reply warnings ────────────────")
        for w in warnings:
            print(w)


def _load(path):
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    main()
