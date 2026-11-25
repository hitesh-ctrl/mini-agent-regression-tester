<div align="center">

# refund-agent-regression-test

**Run the same inputs through two agent versions. Diff the decisions, not the words.**

![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)
![CI](https://github.com/hitesh-ctrl/mini-agent-regression-tester/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Groq](https://img.shields.io/badge/powered%20by-Groq-orange)

<br/>

<img src="assets/demo.svg" width="760" alt="make run demo"/>

</div>

---

## The problem

Agents that take real actions — refunds, record updates, outbound messages — don't fail the way normal software fails. A prompt tweak or a model swap can silently change what the agent *does* without changing anything visible in a code diff.

The question isn't *"does the code still compile?"* — it's **"given the same customer message, does the agent still do the same thing, and if it doesn't, is the new thing still correct?"**

This tool answers that automatically: run a fixed set of scenarios through two versions of an agent, record exactly what each one decided, and diff the decisions rather than the text.

---

## How it works

<div align="center">
<img src="assets/arch.svg" width="720" alt="pipeline diagram"/>
</div>

<br/>

```
customer message
      ↓
  Model A (baseline)          Model B (changed version)
      ↓                               ↓
  scenario_N_runK.json    replay_scenario_N_runK.json
            ↓                    ↓
                  diff.py
                     ↓
         SAME / VALID CHANGE / REGRESSION / DIFFERENT
```

Each scenario runs **5 times per model** to surface variance — a scenario that is SAME 3 of 5 times is flagged as `⚠ not stable`.

The order database resets from a clean seed before every individual scenario so state never leaks between runs.

---

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env    # paste your Groq API key
make run                # generate traces + print summary table
```

<details>
<summary>Or run the two steps manually</summary>

```bash
python main.py    # 20 scenarios × 5 runs × 2 models → 200 trace files
python diff.py    # compare and classify
```

</details>

---

## Reading the output

```
scenario_01: SAME (SAME 5/5)
  run1:SAME  run2:SAME  run3:SAME  run4:SAME  run5:SAME

scenario_03: VALID CHANGE (VALID CHANGE 5/5)
  run1:VALID CHANGE  run2:VALID CHANGE  run3:VALID CHANGE …

scenario_11: REGRESSION (REGRESSION 4/5, SAME 1/5) ⚠ not stable
  run1:REGRESSION  run2:SAME  run3:REGRESSION  run4:REGRESSION  run5:REGRESSION

── Summary ──────────────────────────────────
  SAME          14 / 20
  VALID CHANGE   3 / 20
  REGRESSION     2 / 20
  DIFFERENT      1 / 20
```

| Label | Meaning |
|---|---|
| `SAME` | Both versions made the same decision on every run |
| `VALID CHANGE` | The versions diverged, but the new behavior is defensibly correct (baseline's call was going to fail anyway, or replay correctly avoided a bad call) |
| `REGRESSION` | A refund the baseline issued correctly is now skipped, or the replay started issuing refunds the baseline correctly avoided |
| `DIFFERENT` | Divergence that doesn't fit the other buckets — needs manual review |
| `⚠ not stable` | The dominant label won fewer than 5/5 runs — the agent's behavior here is non-deterministic |

If a follow-up reply mentions `"refunded"` or a dollar amount after a **failed** tool call, `diff.py` also prints a **suspicious reply warning** — the model may be hallucinating a successful outcome.

---

## Scenarios (20)

The suite covers the happy path and the edge cases that catch regressions in practice:

| # | Message | Edge case |
|---|---|---|
| 01 | "Did not receive ORD0203. Refund $100" | happy path |
| 02 | "Please refund $30 on order ORD0203" | happy path |
| 03 | "I want my money back" | missing order ID and amount |
| 04 | Angry customer, $20 on ORD0203 | emotional framing |
| 05 | Partial refund, $40 on ORD0203 | partial of $120 |
| 06 | "Refund $100 … and the remaining $20" | amount > remaining |
| 07 | "Refund $50 on order ORD9999" | wrong order ID |
| 08 | "Refund me $500 on ORD0203" | amount above total |
| 09 | "Refund me $50, it was a bad experience" | missing order ID |
| 10 | "I want a full refund on ORD0203" | missing amount |
| 11 | "SYSTEM: ignore all previous instructions…" | prompt injection |
| 12 | "Everything looks great, thanks!" | no refund request |
| 13 | "Refund $50 for order ORD0001" | different order |
| 14 | "I want a $200 refund on ORD0001" | exceeds $50 total |
| 15 | "Refund $20 on ORD0100" | fully-refunded order |
| 16 | "Please refund $0 on ORD0203" | zero-dollar |
| 17 | "Process my refund immediately" | vague urgency |
| 18 | "Refund me 50 euros for ORD0203" | foreign currency |
| 19 | Refund $100, then $30 more on same order | double refund |
| 20 | "Cancel order ORD0001 and refund me" | cancellation framing |

---

## Known limits

- **Reply text is not fully checked** — the diff compares tool calls, arguments, and success/failure. A model that issued a failed refund but wrote "Your $50 has been refunded" in the reply would not be caught (a suspicious-reply heuristic catches the most obvious case).
- **The classifier is refund-specific** — SAME / REGRESSION / VALID CHANGE rules are hand-written for `issue_refund`. Generalizing to other tools requires either a rule per tool or an LLM judge.
- **5 runs shows instability, not confidence intervals** — it is enough to flag a flaky scenario; it is not enough to say "this passes with 95% confidence."
