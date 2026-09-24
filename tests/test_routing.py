"""Routing policy, model-free: each case edits the saved answers and checks
the decision code, not a model."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import cog_core      # noqa: E402


def bundle(**brief):
    value = json.loads((ROOT / "examples" / "sample-bundle.json").read_text())
    value["brief"].update(brief)
    return value


def result(implementation=None, confidence=0.7, **nouls):
    value = json.loads((ROOT / "examples" / "sample-result.json").read_text())
    if implementation:
        probabilities = {k: 0.1 for k in ("code", "context", "decision")}
        probabilities[implementation] = 0.8
        value["answers"]["implementation"].update(choice=implementation, probabilities=probabilities)
    value["answers"]["implementation"]["confidence"] = confidence
    for name, probability in nouls.items():
        value["answers"][name]["noul"] = probability
    return value


def decide(b, r):
    envelope = cog_core.finish(b, r, {"kind": "test"})
    assert envelope["ok"], envelope
    return envelope["payload"]["decision"], envelope["problems"]


class RoutingTests(unittest.TestCase):
    def test_sample_brief_is_a_decision_the_designer_called_context(self):
        decision, problems = decide(bundle(), result())
        self.assertEqual(problems, [])
        self.assertEqual(decision["recommendation"], "decision")
        self.assertTrue(decision["agrees_with_designer"])
        self.assertIn("consider-decision-class", decision["flags"])

    def test_low_confidence_goes_to_review(self):
        decision, _ = decide(bundle(), result(confidence=0.3))
        self.assertEqual(decision["recommendation"], "needs-review")
        self.assertIn("low-confidence", decision["flags"])
        self.assertIsNone(decision["agrees_with_designer"])

    def test_code_without_rules_is_a_contradiction(self):
        decision, _ = decide(bundle(cog_kind="code"), result("code", rules_suffice=0.1))
        self.assertEqual(decision["recommendation"], "needs-review")
        self.assertIn("signals-disagree", decision["flags"])

    def test_decision_with_open_ended_output_is_a_contradiction(self):
        decision, _ = decide(bundle(), result("decision", open_ended_output=0.9))
        self.assertEqual(decision["recommendation"], "needs-review")

    def test_context_for_a_bounded_answer_space_is_questioned(self):
        decision, _ = decide(bundle(), result("context", bounded_answer_space=0.95, open_ended_output=0.05))
        self.assertEqual(decision["recommendation"], "needs-review")
        self.assertIn("signals-disagree", decision["flags"])

    def test_disagreement_with_the_designer_is_reported(self):
        decision, _ = decide(bundle(cog_kind="code"), result("context", bounded_answer_space=0.2, open_ended_output=0.9))
        self.assertEqual(decision["recommendation"], "context")
        self.assertFalse(decision["agrees_with_designer"])
        self.assertIn("designer proposed code", decision["reasons"])

    def test_no_designer_kind_means_no_agreement_claim(self):
        b = bundle()
        del b["brief"]["cog_kind"]
        decision, _ = decide(b, result())
        self.assertIsNone(decision["designer_kind"])
        self.assertIsNone(decision["agrees_with_designer"])

    def test_underspecified_brief_is_flagged_without_changing_the_kind(self):
        r = result()
        spec = r["answers"]["specification_clarity"]
        spec.update(score=0.3, probabilities={"0": 0.7, "1": 0.3, "2": 0.0})
        decision, _ = decide(bundle(), r)
        self.assertEqual(decision["recommendation"], "decision")
        self.assertIn("underspecified-brief", decision["flags"])

    def test_the_designer_kind_is_not_sent_to_the_model(self):
        task = cog_core.prepare(bundle())["task"]
        self.assertEqual(set(task["state"]), {"name", "brief", "prohibits"})


if __name__ == "__main__":
    unittest.main()
