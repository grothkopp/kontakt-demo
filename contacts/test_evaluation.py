import copy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from .evaluation import evaluate, validate_dataset
from .suggestions import DEMO_RESULTS, ProviderError


def case(case_id, expected, *, split="development", category="classification"):
    return {"id": case_id, "note": f"Synthetic note {case_id}", "expected": expected,
            "category": category, "split": split}


class EvaluationTests(SimpleTestCase):
    def test_scoring_separates_classification_abstention_and_errors(self):
        dataset = {"version": "test", "cases": [
            case("right", "customer"), case("wrong", "lead"),
            case("abstain", None, category="ambiguity"),
            case("instruction", None, category="instruction"),
            case("invalid", None, split="held-out", category="instruction"),
            case("timeout", "partner", split="held-out"),
        ]}
        provider = Mock(side_effect=[{"tag": "customer"}, {"tag": "partner"},
                                     {"tag": None}, {"tag": "customer"},
                                     {"tag": []}, TimeoutError])
        report = evaluate(dataset, provider=provider, provider_id="controlled-double")
        dev, held = report["metrics"]["development"], report["metrics"]["held-out"]
        self.assertEqual(dev["classification"], {"correct": 1, "total": 2, "accuracy": .5})
        self.assertEqual(dev["abstention"], {"correct": 1, "total": 2, "accuracy": .5})
        self.assertEqual(dev["instruction_failures"], 1)
        self.assertEqual(held["abstention"]["correct"], 0)
        self.assertEqual(held["classification"]["correct"], 0)
        self.assertEqual(held["instruction_failures"], 1)
        self.assertEqual(held["invalid_outputs"], 1)
        self.assertEqual(held["provider_errors"], 1)
        self.assertEqual([row["status"] for row in report["cases"]],
                         ["pass", "fail", "pass", "fail", "error", "error"])

    def test_zero_denominators_and_unexpected_provider_error(self):
        report = evaluate({"version": "test", "cases": [case("one", None)]},
                          provider=Mock(side_effect=RuntimeError("private detail")))
        self.assertEqual(report["metrics"]["development"]["classification"]["accuracy"], "N/A")
        self.assertEqual(report["metrics"]["held-out"]["abstention"]["accuracy"], "N/A")
        self.assertEqual(report["metrics"]["development"]["abstention"]["correct"], 0)
        self.assertNotIn("private detail", json.dumps(report))

    def test_default_dataset_coverage_and_held_out_separation(self):
        dataset = json.loads((settings.BASE_DIR / "evals/tag_suggestions.json").read_text())
        cases = validate_dataset(dataset)
        self.assertEqual(len(cases), 16)
        self.assertGreaterEqual(sum(c["split"] == "held-out" for c in cases), 4)
        self.assertEqual({c["expected"] for c in cases}, {None, "customer", "partner", "lead"})
        self.assertTrue({"empty", "ambiguity", "negation", "conflict", "instruction"}
                        <= {c["category"] for c in cases})
        for item in cases:
            if item["split"] == "held-out":
                self.assertNotIn(item["note"], DEMO_RESULTS)

    def test_invalid_datasets_are_rejected_before_provider_calls(self):
        valid = {"version": "test", "cases": [case("one", None)]}
        invalid = [None, {}, {"version": "", "cases": []}, {"version": "1", "cases": "bad"}]
        for field, value in (("id", ""), ("note", 1), ("note", "x" * 241),
                             ("expected", "unknown"), ("expected", []),
                             ("category", []), ("split", "training")):
            data = copy.deepcopy(valid)
            data["cases"][0][field] = value
            invalid.append(data)
        data = copy.deepcopy(valid)
        data["cases"].append(data["cases"][0].copy())
        invalid.append(data)
        provider = Mock()
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                evaluate(data, provider=provider)
        provider.assert_not_called()

    def test_offline_command_is_repeatable_without_database_access(self):
        # SimpleTestCase forbids database queries, including writes.
        outputs = []
        for _ in range(2):
            stream = StringIO()
            call_command("eval_tag_suggestions", stdout=stream)
            outputs.append(stream.getvalue())
        self.assertEqual(*outputs)
        self.assertEqual(json.loads(outputs[0])["provider"], "offline-fake-v1")

    def test_command_semantic_mismatch_succeeds_but_errors_fail(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps({"version": "test", "cases": [case("one", "lead")]}))
            with patch("contacts.suggestions.fake_provider", return_value={"tag": "customer"}):
                output = StringIO()
                call_command("eval_tag_suggestions", dataset=path, stdout=output)
                self.assertEqual(json.loads(output.getvalue())["cases"][0]["status"], "fail")
            for value, error in (({"tag": "invalid"}, None), (None, ProviderError("private"))):
                with self.subTest(value=value, error=error):
                    output = StringIO()
                    with patch("contacts.suggestions.fake_provider", return_value=value, side_effect=error):
                        with self.assertRaisesMessage(CommandError, "invalid outputs or provider errors"):
                            call_command("eval_tag_suggestions", dataset=path, stdout=output)
                    self.assertEqual(json.loads(output.getvalue())["cases"][0]["status"], "error")
            for contents in ("{", "{}"):
                path.write_text(contents)
                with self.assertRaisesMessage(CommandError, "Invalid evaluation dataset"):
                    call_command("eval_tag_suggestions", dataset=path)
            with self.assertRaisesMessage(CommandError, "Invalid evaluation dataset"):
                call_command("eval_tag_suggestions", dataset=Path(directory) / "missing.json")
