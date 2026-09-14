# refund-agent-regression-test

Tests whether an AI agent's decisions stay correct after you change its prompt or model, by running the same inputs through both versions and diffing what actually happened, not just what got said.

## The problem

An agent that takes real actions, refunds, record updates, outbound messages, doesn't fail the way normal software fails. You can run the same test suite a hundred times and it can still make a different call on the hundred-and-first, because the decision comes from a model, not from deterministic code. And a prompt tweak or a model swap can change that decision-making without changing anything that shows up in a code diff.

So the actual question isn't "does the code still compile," it's "given the same customer message, does the agent still do the same thing, and if it doesn't, is the new thing still correct." Reading a few sample outputs by hand doesn't scale and doesn't catch the edge cases. This is a small, working version of a system built to answer that question automatically: run a fixed set of scenarios through two versions of an agent, record exactly what each one decided, and diff the decisions rather than the text.

## Example

Four customer messages, run through two versions of the same refund agent, `openai/gpt-oss-20b` as the base and `openai/gpt-oss-safeguard-20b`, a safety-tuned variant of it, as the change being tested:

```
$ python diff.py
scenario_01: SAME
scenario_02: SAME
scenario_03: VALID CHANGE
scenario_04: SAME
```

scenario_03's message was "I want my money back," no order ID attached. Here's what each version actually did, pulled straight from the trace files:

```json
// scenario_03.json (base model)
{
  "user_message": "I want my money back",
  "tool_called": "issue_refund",
  "arguments": { "amount": 0, "order_id": "" },
  "result": { "success": false, "reason": "Order  not found" }
}

// replay_scenario_03.json (safety-tuned model)
{
  "user_message": "I want my money back",
  "tool_called": null,
  "agent_reply": "Sure, I can help with that. Could you please provide your order ID and the amount you'd like refunded?"
}
```

The base model called `issue_refund` anyway, with a blank order ID, and only failed because the tool itself rejected an order that doesn't exist. The safety-tuned model didn't attempt the call at all, it asked for the missing details first.

Those are two different decisions, `tool_called` is `"issue_refund"` in one trace and `null` in the other, so a naive diff would just flag this as changed and stop there. But it isn't a regression: the base model's attempt only avoided doing something wrong because a guardrail happened to catch it, not because the decision itself was sound. `diff.py` checks whether the differing attempt actually succeeded before it decides anything broke, so it classifies this as a valid change, arguably an improvement, instead of leaving that judgment call to whoever's reading the diff.

## How it works

```
customer message
      |
      v
  agent decides: call issue_refund, or reply in text
      |
      v
  issue_refund(order_id, amount)
      -> loads the order from a JSON file standing in for a database
      -> checks it's not already fully refunded
      -> checks the amount doesn't exceed what's left
      -> writes the change back, or rejects with a reason
      |
      v
  recorder logs: message, decision, arguments, result, DB state before/after
      |
      v
  same message replayed through the changed agent version
      |
      v
  diff.py compares the two traces and classifies: SAME / VALID CHANGE / REGRESSION
```

Every scenario produces its own trace file, including the ones where the correct behavior is calling nothing, those get recorded too, with `tool_called: null` and the agent's actual reply, so "correctly did nothing" is a checkable state and not just a silent absence of data.

The order database resets from a clean seed before every individual scenario, not once at the start of the run. Early on it wasn't doing this, and a successful refund in one scenario was silently changing the starting balance the next scenario read, which made two model versions look like they disagreed when they were actually just working off different numbers. Worth mentioning because it's exactly the kind of bug that would produce false positives in a real version of this: a "regression" that isn't one, caused by test contamination rather than the agent itself.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # add your Groq API key
python main.py         # runs both model versions through all scenarios, writes traces
python diff.py          # compares the two sets of traces, prints a verdict per scenario
```

## Where it stops short

The diff only compares tool calls, order_id, amount, success or failure, not the text the agent actually says to the customer. At one point during testing, a model got a failed refund back from the tool and wrote a reply describing a refund history that didn't exist, specific dollar figures included, none of it matching the real order. The tool call itself got classified correctly by the diff. The fabricated sentence sitting right next to it would sail through completely unchecked. Catching that would mean also diffing reply content for factual consistency against the trace, not just the function call.

The classifier logic is also specific to refunds, it knows how to check a refund amount against an order total because that rule is hand-written into `diff.py`. Extending this to more tools means either a hand-written rule per tool, which doesn't scale past a handful, or some other way to judge correctness that isn't hardcoded per action.
