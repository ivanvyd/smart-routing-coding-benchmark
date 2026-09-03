# Run log

## Environment

- Date: 2026-09-03
- Workspace: isolated non-client Databricks workspace
- OS: Linux 6.18 under WSL2
- Python: 3.12.3
- Databricks CLI: v1.10.0
- Claude Code: 2.1.258
- `ucode`: source installation, package metadata 0.0.0
- Authentication: OAuth through a local Databricks CLI profile
- Benchmark base commit: `386387056c8fb9502a975776b4df695e0029fd0b`

No hostname, account ID, workspace ID, user email, token, or credential is
stored in the tracked evidence.

## Execution

- Arms: `FIXED_STRONG`, `FIXED_CHEAP`, `CLIENT_ROUTING`
- Tasks attempted: 24 per arm, 72 total
- Execution: serial
- Task order: randomized with seed 42 within each arm
- Agent timeout: 900 seconds
- Raw pass counts: 22/24, 22/24, and 23/24 respectively

## Corpus audit

Three invalid fixtures were excluded from every arm:

- `easy-004`: incompatible expected-row types.
- `medium-007`: inconsistent seed and expected data; stated fanout absent.
- `hard-005`: starting code already met the assertion; server teardown caused
  the apparent hang.

Scored rows: 21 per arm, with seven easy, seven medium, and seven hard tasks.
The exclusions apply only to the recorded base commit. Corrected fixtures are
included for future runs.

## Scored results

| Arm | Passes | Estimated model cost | Cost per success | Median duration | Gateway tokens | Invocations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `FIXED_STRONG` | 21/21 | $3.6696 | $0.1747 | 55.911 s | 7,233,486 | 235 |
| `FIXED_CHEAP` | 20/21 | $2.3369 | $0.1168 | 76.759 s | 10,658,179 | 394 |
| `CLIENT_ROUTING` | 21/21 | $2.6447 | $0.1259 | 64.967 s | 6,880,148 | 285 |

The client router chose Haiku for 9 scored tasks and Sonnet for 12. By label,
the Haiku/Sonnet split was 6/1 easy, 2/5 medium, and 1/6 hard.

## Telemetry validation

- Source: `system.ai_gateway.usage`
- Pulled rows in the full research window: 1,118
- Invocation rows attributed across all attempted runs: 1,105
- Duplicate invocation IDs across attributed runs: 0
- Fixed-arm destination mismatches: 0
- Routed rows missing their recorded worker model: 0 among matched rows
- Unmatched routed rows: one, the excluded `hard-005` timeout fixture

`system.billing.usage` returned zero records for the benchmark window at
completion. This is consistent with the documented ingestion delay. Reported
costs use the dated, cache-aware model-price snapshot and are not invoice
amounts.

## Cleanup and publication boundary

The public repository excludes raw gateway rows because they contain provider
identifiers needed for private audit. The evidence export includes benchmark
fields and aggregate telemetry. Provider-managed audit and billing records were
not modified.
