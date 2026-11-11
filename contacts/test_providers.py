import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase
from django.core.management import call_command, CommandError
from .providers import LabelProvider
from .suggestions import suggest_tag

class ProviderTests(SimpleTestCase):
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-not-a-secret"})
    @patch("openai.OpenAI")
    def test_live_boundary_sends_only_note_and_validates_result(self, factory):
        client = factory.return_value.__enter__.return_value
        client.responses.create.return_value = SimpleNamespace(
            output_text='{"tag":"lead"}', model="test-snapshot", id="test-response", usage=None)
        provider = LabelProvider("openai", "p2", "test-model")
        self.assertEqual(suggest_tag("A demo request", provider=provider).tag, "lead")
        args = client.responses.create.call_args.kwargs
        self.assertEqual(json.loads(args["input"]), {"contact_note":"A demo request"})
        self.assertFalse(args["store"])
        self.assertTrue(args["text"]["format"]["strict"])
        self.assertEqual(provider.records[0]["returned_model"], "test-snapshot")
        client.responses.create.return_value.output_text='{"tag":"invented"}'
        self.assertEqual(suggest_tag("note", provider=provider).error, "invalid_output")

    @patch.dict(os.environ, {}, clear=True)
    def test_live_requires_credentials_and_model(self):
        with self.assertRaises(ValueError):
            LabelProvider("openai", model="test-model")

    def test_eval_writes_report_before_failing_gate_and_rejects_changed_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"report.json"
            with self.assertRaises(CommandError):
                call_command("compare_labels", output=output, gate=True, min_accuracy=1)
            report=json.loads(output.read_text())
            self.assertEqual(len(report["cases"]), 8)
            self.assertEqual(report["accuracy"], .75)
            self.assertIn("OFFLINE FAKE", report["notice"])
            report["dataset_sha256"]="different"
            baseline=Path(directory)/"baseline.json"
            baseline.write_text(json.dumps(report))
            with self.assertRaisesMessage(CommandError, "identical dataset"):
                call_command("compare_labels", output=output, baseline=baseline)
