"""Run the same labelled dataset through one explicitly chosen configuration."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from contacts.evaluation import validate_dataset
from contacts.providers import LabelProvider, PROMPTS
from contacts.suggestions import suggest_tag


class Command(BaseCommand):
    help = "Compare label outputs against fixed expected answers; optionally enforce a quality gate."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
        parser.add_argument("--prompt", choices=list(PROMPTS), default="p2")
        parser.add_argument("--model", default=settings.AI_MODEL)
        parser.add_argument("--effort", default="")
        parser.add_argument("--dataset", type=Path, default=settings.BASE_DIR / "evals/workshop_labels.json")
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--baseline", type=Path)
        parser.add_argument("--min-accuracy", type=float, default=0.0)
        parser.add_argument("--gate", action="store_true")

    def handle(self, *args, **o):
        if not 0 <= o["min_accuracy"] <= 1:
            raise CommandError("min-accuracy must be between 0 and 1")
        try:
            raw = o["dataset"].read_bytes()
            dataset = json.loads(raw)
            cases = validate_dataset(dataset)
            baseline = json.loads(o["baseline"].read_text()) if o["baseline"] else None
            digest = hashlib.sha256(raw).hexdigest()
            if baseline and (baseline.get("dataset_sha256") != digest or baseline.get("scorer") != "exact-label-v1"):
                raise ValueError("Baseline must use the identical dataset and scorer")
            provider = LabelProvider(o["provider"], o["prompt"], o["model"], o["effort"])
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        rows = []
        for case in cases:
            before = len(provider.records)
            start = perf_counter()
            result = suggest_tag(case["note"], provider=provider)
            rows.append({"id": case["id"], "split": case["split"], "expected": case["expected"],
                         "actual": result.tag, "error": result.error,
                         "correct": result.error is None and result.tag == case["expected"],
                         "latency_ms": round((perf_counter()-start)*1000, 1),
                         "model_call": provider.records[-1] if len(provider.records)>before else None})
        score = sum(row["correct"] for row in rows) / len(rows)
        report = {"run_at": datetime.now(timezone.utc).isoformat(), "provider": o["provider"],
                  "notice": "OFFLINE FAKE: not a model benchmark" if o["provider"] == "fake" else "Live API responses",
                  "requested_model": o["model"] if o["provider"] == "openai" else None,
                  "prompt": o["prompt"], "prompt_sha256": hashlib.sha256(PROMPTS[o["prompt"]].encode()).hexdigest(),
                  "effort": o["effort"] or "provider default", "dataset_version": dataset["version"],
                  "dataset_sha256": digest, "scorer": "exact-label-v1", "accuracy": score,
                  "cases": rows}
        if baseline:
            prior = {r["id"]: r for r in baseline["cases"]}
            report["comparison"] = {"baseline": str(o["baseline"]), "accuracy_delta": score-baseline["accuracy"],
                "regressions": [r["id"] for r in rows if prior[r["id"]]["correct"] and not r["correct"]],
                "improvements": [r["id"] for r in rows if not prior[r["id"]]["correct"] and r["correct"]]}
        o["output"].parent.mkdir(parents=True, exist_ok=True)
        o["output"].write_text(json.dumps(report, indent=2)+"\n")
        self.stdout.write(f"{report['notice']}: {sum(r['correct'] for r in rows)}/{len(rows)} correct. Report: {o['output']}")
        if any(r["error"] for r in rows) or (o["gate"] and (score < o["min_accuracy"] or report.get("comparison", {}).get("regressions"))):
            raise CommandError("Evaluation gate failed; inspect the saved report.")
