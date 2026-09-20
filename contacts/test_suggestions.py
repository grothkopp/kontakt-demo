from unittest.mock import Mock

from django.test import SimpleTestCase

from .suggestions import DEMO_RESULTS, ProviderError, fake_provider, suggest_tag


class SuggestionServiceTests(SimpleTestCase):
    def test_empty_notes_skip_provider(self):
        provider = Mock()
        for note in ("", " \n\t"):
            with self.subTest(note=note):
                result = suggest_tag(note, provider=provider)
                self.assertIsNone(result.tag)
                self.assertIsNone(result.error)
        provider.assert_not_called()

    def test_allowed_tags_and_abstention(self):
        for tag, label in (("customer", "Customer"), ("partner", "Partner"),
                           ("lead", "Lead"), (None, None)):
            with self.subTest(tag=tag):
                provider = Mock(return_value={"tag": tag})
                result = suggest_tag(" stored note ", provider=provider)
                self.assertEqual(result.tag, tag)
                self.assertEqual(result.label, label)
                self.assertIsNone(result.error)
                provider.assert_called_once_with(" stored note ")

    def test_invalid_output_is_not_abstention(self):
        for output in (None, "customer", '{"tag":"customer"}', [], {},
                       {"tag": "unknown"}, {"tag": True}, {"tag": []},
                       {"tag": {}}, {"tag": 1}, {"tag": "customer", "reason": "x"}):
            with self.subTest(output=output):
                result = suggest_tag("note", provider=Mock(return_value=output))
                self.assertEqual(result.error, "invalid_output")
                self.assertIsNone(result.tag)

    def test_expected_errors_have_safe_codes(self):
        for error, code in ((TimeoutError("private detail"), "timeout"),
                            (ProviderError("private detail"), "provider_error")):
            with self.subTest(code=code):
                result = suggest_tag("note", provider=Mock(side_effect=error))
                self.assertEqual(result.error, code)
                self.assertIsNone(result.tag)

    def test_programming_errors_are_not_hidden(self):
        with self.assertRaises(RuntimeError):
            suggest_tag("note", provider=Mock(side_effect=RuntimeError))

    def test_fake_is_repeatable_and_unknown_notes_abstain(self):
        for note, tag in [*DEMO_RESULTS.items(), ("Unrecognized note", None)]:
            with self.subTest(note=note):
                self.assertEqual(fake_provider(note), {"tag": tag})
                self.assertEqual(suggest_tag(note), suggest_tag(note))
