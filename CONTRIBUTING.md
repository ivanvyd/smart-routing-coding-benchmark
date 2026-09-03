# Contributing

Open an issue before proposing a change that alters the benchmark question,
corpus, routing policy, scoring rules, or exclusions. Bug fixes, documentation
corrections, and portability improvements can go straight to a pull request.

## Development setup

Use Python 3.12 or later and [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync --frozen --extra dev
uv run ruff check benchmark scripts notebooks
uv run mypy benchmark --exclude 'test_.*\.py'
uv run pytest -q
```

Keep pull requests focused and explain any change that can affect reported
metrics. Add or update tests for code changes.

## Data safety

Never commit raw model output, gateway rows, credentials, user identity,
workspace details, request identifiers, or local paths. Benchmark execution
writes private artifacts under Git-ignored `results/` directories. Run
`scripts/export_public_evidence.py` to produce the allowlisted evidence under
`evidence/results/`, then inspect the staged diff before pushing.
