import os
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from .observability import suggest_observed, trace_client
from .providers import LabelProvider

class ObservabilityTests(SimpleTestCase):
    @patch.dict(os.environ, {"DEMO_TRACING": "0"})
    def test_disabled_does_not_create_sdk_client(self):
        trace_client.cache_clear()
        with patch("langfuse.Langfuse") as factory:
            result=suggest_observed("Purchased our product and has used it since June.", provider=LabelProvider())
        self.assertEqual(result.tag,"customer")
        factory.assert_not_called()

    @patch.dict(os.environ, {"DEMO_CAPTURE_CONTENT": "0"})
    @patch("contacts.observability.trace_client")
    def test_nested_trace_masks_note_and_records_validation_failure(self, factory):
        client=factory.return_value
        root, generation=MagicMock(),MagicMock()
        contexts=[]
        for value in (root,generation):
            context=MagicMock()
            context.__enter__.return_value=value
            contexts.append(context)
        client.start_as_current_observation.side_effect=contexts
        result=suggest_observed("private note",provider=lambda note:{"tag":"invented"})
        self.assertEqual(result.error,"invalid_output")
        calls=client.start_as_current_observation.call_args_list
        self.assertEqual(calls[0].kwargs["input"], {"note_length":12})
        self.assertIsNone(calls[1].kwargs["input"])
        self.assertEqual(root.update.call_args.kwargs["level"],"ERROR")
        self.assertNotIn("private note",str(client.mock_calls))
