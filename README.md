# refund-agent-regression-test

Tests whether an AI agent's decisions stay correct after you change its prompt or model, by running the same inputs through both versions and diffing what actually happened.

## Example

Four scenarios, run through `openai/gpt-oss-20b` vs `openai/gpt-oss-safeguard-20b`:

```
$ python diff.py
scenario_01: SAME
scenario_02: SAME
scenario_03: VALID CHANGE
scenario_04: SAME
```

scenario_03: "I want my money back," no order ID given. The base model called `issue_refund` anyway with a blank order ID, which only failed because the tool rejected an order that doesn't exist. The safety-tuned model just asked for the missing details instead. Different decisions, but not a regression, the base model's attempt only worked out because a guardrail caught a bad guess. The diff checks whether the differing attempt actually succeeded before calling it broken, so it classified this correctly instead of leaving the judgment to a human.

## How it works

```
issue_refund(order_id, amount)
    -> loads the order from a JSON file
    -> checks it's not already fully refunded
    -> checks the amount doesn't exceed what's left
    -> writes the change back, or rejects with a reason
```

Every scenario gets traced: what the customer said, what got called, what happened, including the cases where the agent correctly called nothing. Database resets from a clean seed before every scenario, so results can't leak between runs.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # add your Groq key
python main.py         # runs both models through all scenarios
python diff.py          # compares them
```

## Limits

Only diffs tool calls, not reply text, so a model can hallucinate a fake refund history in its reply and still pass. Classifier logic is hand-written for this one tool, wouldn't scale to more without more rules.
