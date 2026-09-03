# Public benchmark evidence

This directory contains the sanitized evidence behind the article's tables and
charts.

- `results/normalized/`: one public-safe outcome row per attempted task and arm.
- `results/attributed/`: per-run gateway totals without invocation records or
  provider identifiers.
- `results/summary.json`: scored metrics after commit-scoped exclusions.
- `results/figures/`: charts generated from the same summary and routed rows.

Raw stdout, stderr, diffs, gateway rows, requester identity, request IDs,
invocation IDs, endpoint IDs, account IDs, workspace IDs, and hostnames are not
published here. Benchmark execution writes private audit data under the
Git-ignored `results/raw/` directory; keep that directory out of publication
packages. Provider-managed records remain unchanged.

Regenerate this directory after analysis with:

```bash
python scripts/export_public_evidence.py
```
