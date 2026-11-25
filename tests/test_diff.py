"""
Unit tests for diff.py's classify() and suspicious_reply() functions.

One test per label: SAME, VALID CHANGE, REGRESSION, DIFFERENT.
Tests use hand-built trace dicts — no file I/O, no live API calls.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from diff import classify, suspicious_reply


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def refund_trace(order_id="ORD0203", amount=50, success=True, agent_reply=None):
    result = (
        {"success": True, "amount_refunded": amount, "total_refunded_so_far": amount}
        if success
        else {"success": False, "reason": f"Order {order_id} not found"}
    )
    return {
        "user_message": "Refund me",
        "tool_called": "issue_refund",
        "arguments": {"order_id": order_id, "amount": amount},
        "result": result,
        "agent_reply": agent_reply,
    }


def no_call_trace(agent_reply="Could you provide your order ID?"):
    return {
        "user_message": "I want my money back",
        "tool_called": None,
        "agent_reply": agent_reply,
    }


# ---------------------------------------------------------------------------
# classify() — one test per label
# ---------------------------------------------------------------------------

class TestClassifySame:
    def test_both_called_same_args_success(self):
        b = refund_trace(order_id="ORD0203", amount=30, success=True)
        r = refund_trace(order_id="ORD0203", amount=30, success=True)
        assert classify(b, r) == "SAME"

    def test_both_called_same_args_failure(self):
        b = refund_trace(order_id="ORD9999", amount=50, success=False)
        r = refund_trace(order_id="ORD9999", amount=50, success=False)
        assert classify(b, r) == "SAME"

    def test_neither_called(self):
        b = no_call_trace()
        r = no_call_trace("Please share your order number.")
        assert classify(b, r) == "SAME"


class TestClassifyValidChange:
    def test_baseline_failed_replay_skipped(self):
        # baseline attempted the tool but it failed; replay didn't call it at all
        b = refund_trace(order_id="ORD9999", amount=50, success=False)
        r = no_call_trace()
        assert classify(b, r) == "VALID CHANGE"

    def test_replay_attempted_failed_safely(self):
        # baseline didn't call; replay tried but failed
        b = no_call_trace()
        r = refund_trace(order_id="ORD0203", amount=200, success=False)
        assert classify(b, r) == "VALID CHANGE"


class TestClassifyRegression:
    def test_baseline_succeeded_replay_skipped(self):
        # baseline issued a valid refund; replay skipped the tool entirely
        b = refund_trace(order_id="ORD0203", amount=50, success=True)
        r = no_call_trace()
        assert classify(b, r) == "REGRESSION"

    def test_baseline_skipped_replay_succeeded(self):
        # baseline correctly did not call the tool; replay called it and succeeded
        b = no_call_trace()
        r = refund_trace(order_id="ORD0203", amount=50, success=True)
        assert classify(b, r) == "REGRESSION"


class TestClassifyDifferent:
    def test_same_tool_different_args(self):
        b = refund_trace(order_id="ORD0203", amount=30, success=True)
        r = refund_trace(order_id="ORD0203", amount=100, success=True)
        assert classify(b, r) == "DIFFERENT"

    def test_same_tool_different_success(self):
        b = refund_trace(order_id="ORD0203", amount=30, success=True)
        r = refund_trace(order_id="ORD0203", amount=30, success=False)
        assert classify(b, r) == "DIFFERENT"


# ---------------------------------------------------------------------------
# suspicious_reply()
# ---------------------------------------------------------------------------

class TestSuspiciousReply:
    def test_no_warning_on_success(self):
        # tool succeeded; reply mentioning dollars is expected
        t = refund_trace(success=True, agent_reply="Your $50 refund has been processed.")
        assert suspicious_reply(t) is None

    def test_no_warning_on_no_call(self):
        t = no_call_trace("I can help with that.")
        assert suspicious_reply(t) is None

    def test_flags_refunded_in_reply_after_failure(self):
        t = refund_trace(
            order_id="ORD9999",
            success=False,
            agent_reply="Your order has been refunded successfully.",
        )
        result = suspicious_reply(t)
        assert result is not None
        assert "refunded" in result.lower() or "suspicious" in result.lower() or "reply" in result.lower()

    def test_flags_dollar_amount_in_reply_after_failure(self):
        t = refund_trace(
            order_id="ORD9999",
            success=False,
            agent_reply="We have processed $50 back to your account.",
        )
        result = suspicious_reply(t)
        assert result is not None

    def test_clean_reply_after_failure(self):
        t = refund_trace(
            order_id="ORD9999",
            success=False,
            agent_reply="I'm sorry, I could not locate that order. Please check the order ID.",
        )
        assert suspicious_reply(t) is None
