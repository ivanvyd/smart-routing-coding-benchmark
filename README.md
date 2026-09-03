# Prompt-based model routing for coding agents on Databricks

[![CI](https://github.com/ivanvyd/smart-routing-coding-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/ivanvyd/smart-routing-coding-benchmark/actions/workflows/ci.yml)

This repository contains a 72-run engineering benchmark of three model-selection
strategies for Claude Code through Databricks Unity AI Gateway:

| Arm | Strategy |
| --- | --- |
| `FIXED_STRONG` | Pin Claude Sonnet 5 |
| `FIXED_CHEAP` | Pin Claude Haiku 4.5 |
| `CLIENT_ROUTING` | Ask Haiku 4.5 to choose Haiku or Sonnet from the task prompt, then pin the worker |

The prompt-only router matched fixed Sonnet's 21/21 scored task success while
reducing estimated model inference cost by 27.9%. Fixed Haiku cost less but
passed 20/21. Three invalid task fixtures were excluded symmetrically from all
arms, leaving 63 scored runs from 72 attempts.

| Strategy | Success | Estimated cost | Cost per success | Median time |
| --- | ---: | ---: | ---: | ---: |
| Fixed Sonnet 5 | 21/21 | $3.670 | $0.175 | 55.9 s |
| Fixed Haiku 4.5 | 20/21 | $2.337 | $0.117 | 76.8 s |
| Client routed | 21/21 | $2.645 | $0.126 | 65.0 s |

Read the [complete article](article/article.md), [methodology](article/methodology.md),
and [limitations](article/limitations.md). Sanitized rows, summary data, and
figures are under [`evidence/results/`](evidence/results/).

## Scope

This benchmark measures the repository's transparent prompt-only client router,
not Databricks Smart Routing. Every selector and worker call used Unity AI
Gateway while the coding harness remained constant.

## Repository map

```text
benchmark/
  runner/       isolated worktrees, client router, Claude Code launch
  evaluators/   deterministic acceptance and forbidden-file checks
  telemetry/    gateway attribution and cache-aware cost estimates
  analysis/     exclusions, metrics, routing diagnostics, charts
tasks/          24 self-contained coding fixtures
sql/            usage and billing query templates
article/        article, methodology, limitations
docs/           architecture, reproduction, sources
evidence/       sanitized publishable results
results/        ignored raw and working results
```

## Reproduce

The short path is:

```bash
uv sync --extra dev
uv tool install git+https://github.com/databricks/ucode
ucode configure --agents claude --profiles <your-profile>

src-bench capture-env --manifest benchmark/manifest.yaml --profile <your-profile>

for arm in FIXED_STRONG FIXED_CHEAP CLIENT_ROUTING; do
  src-bench run --manifest benchmark/manifest.yaml \
    --profile <your-profile> --arm "$arm"
done
```

See [reproduction.md](docs/reproduction.md) for telemetry, analysis, evidence
export, and pre-publication checks.

Contributions are welcome through pull requests. Read
[`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes and report
security concerns through the process in [`SECURITY.md`](SECURITY.md).

## Evidence and cost boundary

Task acceptance uses deterministic tests and file checks, never an LLM judge.
Gateway telemetry is requester-filtered and assigned through exact serial time
windows. The published attribution contains no duplicate invocation IDs.

Cost is an estimate from gateway token records and the dated model-price
snapshot in [`benchmark/prices-2026-09-03.json`](benchmark/prices-2026-09-03.json).
It excludes SQL compute, billed usage tracking, discounts, credits, taxes, and
human time. The billing table had not ingested the run window when the article
was completed.

## License

MIT. See [`LICENSE`](LICENSE).
