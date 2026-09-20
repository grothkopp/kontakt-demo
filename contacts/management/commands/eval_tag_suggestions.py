import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from contacts.evaluation import evaluate


class Command(BaseCommand):
    help = "Evaluate the offline fake against synthetic notes (no contact database access)."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--dataset", type=Path,
                            default=settings.BASE_DIR / "evals" / "tag_suggestions.json")

    def handle(self, *args, **options):
        try:
            dataset = json.loads(options["dataset"].read_text(encoding="utf-8"))
            report = evaluate(dataset)
        except (OSError, UnicodeError, ValueError) as exc:
            raise CommandError(f"Invalid evaluation dataset: {exc}") from exc
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        if any(row["status"] == "error" for row in report["cases"]):
            raise CommandError("Evaluation had invalid outputs or provider errors; see case results.")
