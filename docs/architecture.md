# Architecture

The benchmark holds the coding harness and task corpus constant while changing
only model selection.

```text
task title + request
        |
        +--> FIXED_STRONG --> Sonnet 5 --> Claude Code --> verifier
        +--> FIXED_CHEAP  --> Haiku 4.5 --> Claude Code --> verifier
        +--> CLIENT_ROUTING --> Haiku selector --> pinned worker --> verifier
```

The client router is deliberately small. It sees only the task title and
request, returns `cheap` or `strong`, and records its reason, token count,
duration, policy version, and policy hash. It cannot read the corpus difficulty
label, verifier, expected output, or another arm's result.

This treatment is not Databricks Smart Routing. All selector and worker calls
still travel through Databricks Unity AI Gateway, but model selection happens in
the benchmark client. The distinction is preserved in the manifest, results,
charts, and article.

## Run lifecycle

1. The runner checks that tracked files are clean and records the Git commit.
2. It creates a detached worktree for one arm-task pair.
3. It writes the task prompt inside the nested fixture repository.
4. For `CLIENT_ROUTING`, it asks the frozen selector for a routing decision.
5. It launches Claude Code through `ucode` with the selected model pinned.
6. It captures stdout, stderr, duration, exit code, and the Git diff.
7. A deterministic verifier checks behavior, required files, and forbidden
   modifications.
8. The worktree is removed and one normalized result is written.

The raw model calls are joined to each run by its exact time window. The
telemetry layer totals tokens, cache activity, latency, errors, and estimated
model inference cost. The analyzer applies commit-scoped exclusions, computes
per-arm metrics, and renders the publication figures.

## Module ownership

- `benchmark/runner/`: isolation, routing decision, agent launch, capture.
- `benchmark/evaluators/`: deterministic acceptance and file-boundary checks.
- `benchmark/telemetry/`: AI Gateway attribution and cache-aware cost estimates.
- `benchmark/analysis/`: exclusions, metrics, routing diagnostics, and charts.
- `tasks/`: 24 self-contained coding fixtures.
- `evidence/results/`: sanitized result rows, summary, and figures safe to
  publish.

## Data boundaries

Benchmark execution writes raw gateway rows under the Git-ignored
`results/raw/` directory because they can contain requester and workspace
identifiers. The evidence exporter copies the fields required to reproduce the
published calculations. It does not modify or delete provider-managed audit or
billing records.
