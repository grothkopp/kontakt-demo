# AI labels and evals

Stage: `sg/demo-02-ai-labels`. The app checks authentication, CSRF and ownership before calling a provider. Only the selected contact's stored note is sent; the suggested label is validated and never saved. The implementation is prepared, so this lesson can focus on quality rather than feature coding.

## Start offline

```sh
uv sync --locked
uv run manage.py migrate
uv run manage.py loaddata demo
uv run manage.py runserver
```

Sign in as `anna` / `Workshop-2026!`. Click **Suggest tag**. The default fake only recognizes three English example notes (plus legacy German equivalents); other notes return no suggestion. It is deliberately not an AI classifier.

To give the first fictional contact a known example, use the Django shell:

```sh
uv run manage.py shell -c 'from contacts.models import Contact; Contact.objects.filter(pk=1, owner__username="anna").update(note="Purchased our product and has used it since June.")'
```

## Enable real responses

Copy `.env.example` to `.env` and edit it locally. Set `OPENAI_API_KEY` to a key for your API project, `AI_PROVIDER=openai` and `AI_MODEL` to an exact model ID accessible to that project and supporting structured outputs. Prefer a dated snapshot when available. Keep `AI_REASONING_EFFORT` empty unless the model supports the requested setting. API billing is separate from a chat subscription.

Restart the development server after configuration changes. Never put keys into slides, terminal history or Git. Use only fictional contact notes in this demo. The note goes to the model provider in live mode.

## Compare prompts on fixed inputs

First inspect `evals/workshop_labels.json`: six development examples and two held-out examples. Expected labels and abstentions are human decisions. Eight cases teach the mechanism; they do not establish production reliability.

Offline rehearsal (no key needed):

```sh
uv run manage.py compare_labels --output output/fake.json
```

Expect **6/8**, explicitly labelled an offline fake. The two unfamiliar held-out cases fail. This score is not a model benchmark and fake prompt comparisons are meaningless.

For real comparisons, configure `AI_MODEL` and the key in `.env`, then:

```sh
uv run manage.py compare_labels --provider openai --prompt p1 --output output/p1.json
uv run manage.py compare_labels --provider openai --prompt p2 --baseline output/p1.json --output output/p2.json
```

Open the two JSON reports side by side. Inspect individual improvements and regressions, not only the average. The run records dataset hash, prompt hash, requested and returned model IDs, reasoning setting, response ID, usage and latency. An empty note does not call a model. Model changes use `--model`; supported thinking settings use `--effort`. Change one variable at a time. Repeat runs and keep truly held-out data out of prompt tuning.

Optional gate (fails on any case regression or an accuracy below the chosen threshold):

```sh
uv run manage.py compare_labels --provider openai --prompt p2 --baseline output/p1.json --output output/gated.json --gate --min-accuracy 0.875
```

A semantic miss is reported without failing the command unless `--gate` is set. Provider failures always fail, after saving the report. Compare only reports with the same dataset and scorer. Keep genuine rehearsal results as backups. No live quality results are supplied with this repository.

## What to explain

Code tests cover access, validation, error handling and no unintended writes. Evals assess the model's choice of label. For richer answers, use a versioned rubric and an LLM judge calibrated against human judgments. Run costly live evals on demand, before prompt/model releases or on a schedule; ordinary CI uses offline checks without secrets.
