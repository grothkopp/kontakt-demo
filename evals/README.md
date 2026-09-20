# Tag suggestion evals

Run `uv run python manage.py eval_tag_suggestions`. The command emits a JSON report
with each expected/actual result, dataset version, provider identity, and metrics by
split. It reads synthetic cases, not contact records, and makes no network requests.
Use `--dataset path/to/cases.json` to inspect another dataset with the same schema.

## Label policy

- `customer`: explicit current purchase or use of our offering.
- `partner`: explicit collaboration or partnership.
- `lead`: explicit commercial interest without purchase.
- `null`: insufficient evidence, mere acquaintance, negated evidence without a
  positive relationship, or conflicting relationships with no single clear tag.

Instructions embedded in notes are not relationship evidence. Do not infer a
relationship from job title or company. Labels were reviewed against this policy:
the conflict case explicitly describes two relationships, the negation case supplies
no positive evidence, and the instruction cases supply no commercial relationship.
English and German cases exercise multilingual inputs; user-facing copy is English.

## Dataset and fake baseline

`tag_suggestions.json` version 1 has 12 development and four held-out cases.
The six exact development notes mapped by `contacts/suggestions.py:DEMO_RESULTS`
produce tags; every other note abstains. The fake does not read expected answers or
load this dataset. Held-out notes must not be added to the mapping or used to tune
a future prompt. Keep the dataset version aligned with any changes to cases or labels.

| Split | Classification | Abstention | Instruction failures | Invalid / provider errors |
| --- | --- | --- | --- | --- |
| Development | 6/6 | 6/6 | 0/1 | 0 / 0 |
| Held-out | 0/3 | 1/1 | 0/1 | 0 / 0 |

This is the observed `offline-fake-v1` baseline, not evidence of live-model quality.
All three held-out classification cases fail because the fake abstains on unknown
notes. A perfect development score demonstrates fixed mappings, not generalization.
The existing app fixture notes are also unmatched and show “No clear suggestion”.
For a successful local UI example, use one of the six documented development notes
in a disposable demo contact; the suggestion feature itself never edits notes.

Classification accuracy counts correct results on cases with a non-null expected
tag. Abstention accuracy counts correct null results on null-labeled cases. An
invalid output or provider exception is a failure in the relevant denominator,
never a successful abstention. Empty denominators display `N/A`. Instruction
failures count every mismatch or error on an instruction case. The report also
counts invalid outputs separately from provider errors.

Semantic mismatches remain visible but the command exits zero after a completed
run. Invalid datasets, invalid provider output, and provider errors exit nonzero.
Use case counts and individual failures when interpreting percentages.

## What each workshop check establishes

| Contract | Evidence |
| --- | --- |
| Explicit request, CSRF, owner-only access before inference | `contacts/test_suggestion_views.py` |
| Unchanged saved data and transient results | Database snapshots and request tests in `contacts/test_suggestion_views.py` |
| Output vocabulary, abstention, safe failures | `contacts/test_suggestions.py` |
| Scoring, errors, repeatability, no database access | `contacts/test_evaluation.py` |
| Appropriate classification of synthetic notes | Per-case eval output; separate from application tests |

Acceptance scenarios are in
[`contact-tag-suggestions`](../openspec/changes/suggest-contact-tags/specs/contact-tag-suggestions/spec.md)
and [`tag-suggestion-evals`](../openspec/changes/suggest-contact-tags/specs/tag-suggestion-evals/spec.md).

A live adapter requires a separate reviewed change. Before enabling one, run
example-based evals, agree on quality thresholds and repeated-run policy, record
model/prompt versions alongside dataset/provider identity, and enforce a total
five-second call budget including retries at the transport boundary. The current
fake performs no network I/O; timeout behavior is tested with a raising double.
Model scores never replace the deterministic ownership and non-mutation tests.
