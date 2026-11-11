"""Generate a clearly labelled synthetic trace, with or without model access."""
from time import sleep
from django.core.management.base import BaseCommand, CommandError
from contacts.observability import suggest_observed, trace_client
from contacts.providers import configured_provider


class Command(BaseCommand):
    help = "Trace a synthetic note; fault scenarios simulate provider behavior."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--scenario", choices=["normal", "slow", "timeout", "invalid"], default="normal")

    def handle(self, *args, **options):
        scenario = options["scenario"]
        try:
            client = trace_client()
            provider = configured_provider() if scenario == "normal" else self.simulated(scenario)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        result = suggest_observed("Purchased our product and has used it since June.", provider=provider, scenario=scenario)
        self.stdout.write(f"scenario={scenario}; tag={result.tag}; error={result.error}; tracing={'enabled' if client else 'disabled'}")
        if client:
            client.flush()
            self.stdout.write("Export requested. Confirm delivery in Langfuse: suggest-contact-tag, environment workshop.")
        if scenario != "normal":
            self.stdout.write("SIMULATED provider behavior; not an actual model failure.")

    @staticmethod
    def simulated(scenario):
        def provider(note):
            if scenario == "slow":
                sleep(1)
            if scenario == "timeout":
                raise TimeoutError("Simulated timeout")
            return {"tag": "invented" if scenario == "invalid" else "customer"}
        return provider
