# First Langfuse rehearsal

Use `sg/demo-03-langfuse`. Langfuse observes the existing Python service; LangChain is not required. Start with Langfuse Cloud to avoid teaching infrastructure setup. The SDK is already locked in `uv.lock` (Langfuse 5.2.0). Self-hosting is optional and outside this workshop.

## 1. Create the account before the workshop

1. Open [Langfuse Cloud](https://cloud.langfuse.com), sign up/sign in and create a project named `kontakt-workshop`.
2. Choose the region appropriate for your project. The example uses the EU endpoint `https://cloud.langfuse.com`. If you choose another region, use that project's base URL instead.
3. In project settings, create an API key pair. Copy the public and secret key into your local `.env`; never share them with participants.
4. Start with `AI_PROVIDER=fake`, `DEMO_TRACING=1`, the two Langfuse keys, and `LANGFUSE_BASE_URL`. This tests tracing independently of a paid model call.
5. Set `DEMO_CAPTURE_CONTENT=1` only for this fictional dataset. Without it, traces record note length rather than note contents. Traces still include the suggested label/error. Do not use real customer notes for this demo.

The `.env` file is ignored by Git. Each participant who wants cloud tracing creates their own project and keys. Watching your screen or using the offline mode needs no account.

## 2. Verify ingestion

```sh
uv sync --locked
uv run manage.py trace_demo
```

Open the project's traces view. Find `suggest-contact-tag`, environment `workshop`, with a child generation named `label-provider`. The command flushes buffered telemetry. Its message means export was requested, not that cloud delivery was verified. Allow a few seconds and refresh.

Check the keys and endpoint belong to the same project/region if no trace appears. Check connectivity, SDK logs and the time filter. Never print a secret while troubleshooting. This repository's tests mock the SDK; you must verify actual cloud delivery during rehearsal.

## 3. Connect the running app

```sh
uv run manage.py migrate
uv run manage.py loaddata demo
uv run manage.py runserver
```

Sign in, click **Suggest tag**, then switch once to Langfuse. The app uses the same instrumented service as the command and eval runner. Restart the server after editing `.env`.

Trace tree:

```text
suggest-contact-tag       overall result, error, scenario
  label-provider          model call, duration, model, token usage
```

Point out where time was spent, which prompt version/provider ran, and the final validated result. Blank notes skip the model call. Offline fake generations have no genuine model usage or model cost; do not interpret them as a model benchmark. Langfuse can calculate costs for recognized models; absent cost data is not evidence of zero cost.

For real calls, follow [AI-DEMO.md](AI-DEMO.md). The generation records the returned model ID and available token usage. There is no separate logging framework or background worker to install.

## 4. A reliable live investigation (8–10 minutes)

Keep only the app and Langfuse tabs visible. State the question first: **Was the response wrong, slow, or unavailable?**

1. Normal run: show the validated result and its child call.
2. Run `uv run manage.py trace_demo --scenario slow`. Inspect the roughly one-second child duration. This is a labelled simulation, not a slow live model.
3. Run `uv run manage.py trace_demo --scenario timeout`. The root records `timeout`; the child is an error.
4. Run `uv run manage.py trace_demo --scenario invalid`. The provider returns successfully, but application validation rejects the label. The root records `invalid_output`.
5. Explain the follow-up: a code defect becomes a regression test; a plausible but wrong label becomes a reviewed eval case. A timeout suggests reliability/latency work, not necessarily a better prompt.

Keep a genuine trace screenshot or screen recording from your rehearsal as a fallback. Do not expose keys or personal data. No fabricated cloud screenshots are supplied.

## 5. Connect evals and observability

```sh
uv run manage.py compare_labels --output output/traced-fake.json
```

The report scores expected labels. Traces explain the individual executions. Live mode uses `--provider openai`. The same run may provide evidence for both purposes, but collecting traces does not prove response quality.

## Minimum team setup

Assign an owner for prompt/model changes, eval baselines and operational follow-up. Agree on data redaction, retention and who can inspect traces. Track error rate, latency and usage/cost alongside quality scores; define a concrete response to each signal. Start with one user journey, then expand after the team has used the evidence.

## Official references

- [Langfuse quickstart](https://langfuse.com/docs/observability/get-started)
- [Python SDK](https://langfuse.com/docs/observability/sdk/overview)
- [Instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)
