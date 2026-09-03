# Reproduction

Run the benchmark against a Databricks workspace you are authorized to use.
The published run used an isolated non-client workspace.

## Requirements

- Python 3.12 or later and `uv`
- Databricks CLI
- [`ucode`](https://github.com/databricks/ucode)
- Claude Code
- Git
- Linux, macOS, or WSL2
- Access to `system.ai.claude-haiku-4-5` and
  `system.ai.claude-sonnet-5`
- Read access to `system.ai_gateway.usage` for telemetry

Install the package and launcher:

```bash
uv sync --extra dev
uv tool install git+https://github.com/databricks/ucode
ucode configure --agents claude --profiles <your-profile>
```

Capture tool versions without recording a hostname or credential:

```bash
src-bench capture-env \
  --manifest benchmark/manifest.yaml \
  --profile <your-profile>
```

## Validate the harness

Run focused tests, lint, and type checking before spending model tokens:

```bash
uv run pytest benchmark
uv run ruff check benchmark scripts/export_public_evidence.py
uv run mypy benchmark --exclude 'test_.*\.py'
```

A dry run exercises worktree creation, evaluation, and result capture without
calling a model:

```bash
src-bench run --manifest benchmark/manifest.yaml --dry-run
```

## Run the matrix

Run one smoke task per arm, then the complete arms:

```bash
for arm in FIXED_STRONG FIXED_CHEAP CLIENT_ROUTING; do
  src-bench run --manifest benchmark/manifest.yaml \
    --profile <your-profile> --arm "$arm" --task easy-001
done

for arm in FIXED_STRONG FIXED_CHEAP CLIENT_ROUTING; do
  src-bench run --manifest benchmark/manifest.yaml \
    --profile <your-profile> --arm "$arm"
done
```

Each run must start from the same `git_base_commit`. Keep execution serial if
you plan to attribute calls by time window. The original run used random seed
42 for task order.

## Pull and attribute telemetry

Query `system.ai_gateway.usage` with `sql/usage.sql` for the complete benchmark
window and current requester. Do not filter by user agent: selector requests
and Claude Code worker requests use different clients.

Then attribute each arm:

```bash
for arm in FIXED_STRONG FIXED_CHEAP CLIENT_ROUTING; do
  src-telemetry attribute \
    --runs "results/normalized/$arm.jsonl" \
    --invocations results/raw/invocations/all.jsonl \
    --prices benchmark/prices-2026-09-03.json \
    --out "results/attributed/$arm.jsonl"
done
```

The checked-in price file is a dated snapshot used to reproduce this run. Use a
new dated snapshot for a later run. Estimated model inference cost excludes the
SQL warehouse, billed usage tracking, discounts, credits, taxes, and human
time.

## Analyze and export

```bash
src-analyze \
  --results-dir results \
  --manifest benchmark/manifest.yaml \
  --exclusions benchmark/exclusions.yaml
python scripts/export_public_evidence.py
```

The exclusions file applies only to its recorded base commit. Do not carry its
entries to a rerun after the corrected fixtures have been committed.

Before publishing, confirm 24 attempted rows per arm, inspect the summary and
figures, and scan `evidence/` for hostnames, account IDs, workspace IDs, request
IDs, and email addresses.
