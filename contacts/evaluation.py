"""Small example-based eval harness; semantic scores do not enforce access control."""

from .suggestions import InvalidOutput, PROVIDER_ID, suggest_tag, validate_output


SPLITS = ("development", "held-out")
CATEGORIES = {"classification", "empty", "ambiguity", "negation", "conflict", "instruction"}


def validate_dataset(dataset):
    if not isinstance(dataset, dict) or set(dataset) != {"version", "cases"}:
        raise ValueError("Dataset must contain version and cases.")
    if not isinstance(dataset["version"], str) or not dataset["version"].strip():
        raise ValueError("Dataset version must be a nonempty string.")
    cases = dataset["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset cases must be a nonempty list.")
    seen = set()
    for index, case in enumerate(cases):
        prefix = f"Case {index + 1}"
        if not isinstance(case, dict) or set(case) != {"id", "note", "expected", "category", "split"}:
            raise ValueError(f"{prefix} must contain id, note, expected, category, and split.")
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen:
            raise ValueError(f"{prefix} needs a unique nonempty string ID.")
        seen.add(case_id)
        if not isinstance(case["note"], str) or len(case["note"]) > 240:
            raise ValueError(f"{prefix} needs a note of at most 240 characters.")
        if not isinstance(case["category"], str) or case["category"] not in CATEGORIES:
            raise ValueError(f"{prefix} has an unknown category.")
        if case["split"] not in SPLITS:
            raise ValueError(f"{prefix} has an unknown split.")
        try:
            validate_output({"tag": case["expected"]})
        except InvalidOutput as exc:
            raise ValueError(f"{prefix} needs an existing expected tag or null.") from exc
    return cases


def accuracy(rows):
    correct = sum(row["status"] == "pass" for row in rows)
    return {"correct": correct, "total": len(rows),
            "accuracy": correct / len(rows) if rows else "N/A"}


def evaluate(dataset, *, provider=None, provider_id=PROVIDER_ID):
    cases = validate_dataset(dataset)
    rows = []
    for case in cases:
        # The application boundary handles expected failures; the eval harness also
        # records unexpected provider failures so they cannot disappear from scores.
        try:
            result = suggest_tag(case["note"], provider=provider)
            actual, error = result.tag, result.error
        except Exception:
            actual, error = None, "unexpected_provider_error"
        status = "error" if error else ("pass" if actual == case["expected"] else "fail")
        rows.append({"id": case["id"], "split": case["split"], "category": case["category"],
                     "expected": case["expected"], "actual": actual,
                     "status": status, "error": error})

    metrics = {}
    for split in SPLITS:
        selected = [row for row in rows if row["split"] == split]
        instruction = [row for row in selected if row["category"] == "instruction"]
        metrics[split] = {
            "classification": accuracy([row for row in selected if row["expected"] is not None]),
            "abstention": accuracy([row for row in selected if row["expected"] is None]),
            "instruction_cases": len(instruction),
            "instruction_failures": sum(row["status"] != "pass" for row in instruction),
            "invalid_outputs": sum(row["error"] == "invalid_output" for row in selected),
            "provider_errors": sum(row["status"] == "error" and row["error"] != "invalid_output"
                                   for row in selected),
        }
    return {"dataset_version": dataset["version"], "provider": provider_id,
            "notice": "Offline fake baseline; not evidence of live-model quality.",
            "cases": rows, "metrics": metrics}
