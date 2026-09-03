# Limitations

## The treatment is a client router

The benchmark does not measure Databricks Smart Routing. Its results apply only
to the frozen prompt-only client policy recorded in the repository.

## Small sample and one observation

The scored matrix has 21 tasks per arm after three symmetric corpus exclusions.
Each task ran once per arm. A single differing outcome separates fixed Haiku
from the other strategies, so the observed success rates do not establish
statistical equivalence or a general quality ranking.

## Corpus scope

The repositories are compact Python, SQL, YAML, and configuration fixtures with
deterministic acceptance tests. They do not represent every language, codebase
size, tool chain, or organizational constraint. Difficulty labels were assigned
when the corpus was authored and are descriptive, not calibrated measurements.

## Post-run fixture exclusions

Three fixture defects became clear during the run and audit. They were excluded
from every arm and bound to the exact base commit. Symmetric removal prevents an
invalid task from favoring one strategy, but post-run exclusion still creates a
risk of analyst discretion. The raw attempts and reasons remain public.

## Temporal confounding

The arms ran serially rather than interleaved. Service load, throttling, and
short-lived platform conditions can affect latency and retries. Median task time
is descriptive for this run, not a controlled model-speed estimate.

## Model and router nondeterminism

Coding-agent behavior and selector output can vary between runs. The selector
is Haiku 4.5, so routing has its own model error and cost. Repetition could
change both the selected model and the resulting patch.

## Cost boundary

The reported cost is reconstructed from gateway token records and a dated live
price snapshot. `system.billing.usage` had not ingested the benchmark window
when the article was completed. The estimate excludes usage-tracking charges,
SQL warehouse use, discounts, credits, taxes, and human time.

## Attribution boundary

Attribution uses requester-filtered gateway rows and exact serial time windows.
It does not use a benchmark request tag because the tested `ucode` flow did not
provide one. Concurrent activity by the same requester inside a run window
would be indistinguishable. The benchmark machine was reserved for the serial
run to reduce this risk.

## Version drift

Model availability, aliases, prices, `ucode`, Claude Code, and the Smart Routing
Beta can change. A later reproduction should capture a new environment and
price snapshot instead of treating the 2026-09-03 files as current defaults.
