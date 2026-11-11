"""Optional tracing around the same service used by the UI and evals."""
import os
from contextlib import nullcontext
from functools import lru_cache

from .suggestions import suggest_tag


@lru_cache(maxsize=1)
def trace_client():
    if os.getenv("DEMO_TRACING", "0") != "1":
        return None
    if not all(os.getenv(key) for key in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")):
        raise ValueError("DEMO_TRACING=1 requires both Langfuse keys")
    from langfuse import Langfuse
    return Langfuse(environment="workshop")


def observation(client, **kwargs):
    return client.start_as_current_observation(**kwargs) if client else nullcontext(None)


def suggest_observed(note, *, provider, scenario="normal"):
    client = trace_client()
    capture = os.getenv("DEMO_CAPTURE_CONTENT", "0") == "1"
    metadata = {"provider": getattr(provider, "mode", "simulation"),
                "prompt_version": getattr(provider, "prompt", "none"), "scenario": scenario}
    with observation(client, name="suggest-contact-tag", as_type="span", metadata=metadata,
                     input={"note": note} if capture else {"note_length": len(note)}) as root:
        def traced_provider(value):
            with observation(client, name="label-provider", as_type="generation",
                             model=getattr(provider, "model", "") or "offline-fake",
                             metadata=metadata, input={"note": value} if capture else None) as generation:
                try:
                    output = provider(value)
                except Exception:
                    if generation:
                        generation.update(level="ERROR", status_message="Provider call failed")
                    raise
                if generation:
                    record = provider.records[-1] if getattr(provider, "records", []) else {}
                    usage = record.get("usage") or {}
                    generation.update(output=output if capture else {"captured": False},
                        model=record.get("returned_model") or getattr(provider, "model", "") or "offline-fake",
                        usage_details={key: usage[source] for key, source in
                            (("input", "input_tokens"), ("output", "output_tokens"), ("total", "total_tokens"))
                            if source in usage})
                return output
        result = suggest_tag(note, provider=traced_provider)
        if root:
            root.update(output={"tag": result.tag, "error": result.error},
                        level="ERROR" if result.error else "DEFAULT",
                        status_message=result.error or "Validated; no contact data saved")
        return result
