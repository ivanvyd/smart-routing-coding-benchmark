# Sources

Checked on 2026-09-03.

## Platform documentation

- [Smart Routing for coding agents](https://docs.databricks.com/aws/en/ai-gateway/smart-routing): Beta status, account-level enablement, `ucode` invocation, `system.ai` candidates, and the requirement that the user can access every candidate.
- [Databricks-hosted foundation models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models): availability and request constraints for Claude Haiku 4.5 and Claude Sonnet 5.
- [Track model usage](https://docs.databricks.com/aws/en/ai-gateway/usage-tracking): `system.ai_gateway.usage`, tokens, latency, requester data, required admin access, and the separate charge for usage tracking.
- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing): `system.billing.usage` schema and the typical 12-hour delivery delay, which can be longer for a new workspace.
- [Monitor costs using system tables](https://docs.databricks.com/aws/en/admin/usage/system-tables): time-effective joins between usage and list prices.
- [Pricing table reference](https://docs.databricks.com/aws/en/admin/system-tables/pricing): `system.billing.list_prices` and `pricing.effective_list.default`.
- [`ucode`](https://github.com/databricks/ucode): the public launcher used to run Claude Code through Unity AI Gateway and inspect usage.

## Routing research

- [RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665): the strong-model versus weak-model cost-quality framing for dynamic routing.

## Run evidence

- `benchmark/manifest.yaml`: frozen arms, models, selector policy, environment, and base commit.
- `benchmark/prices-2026-09-03.json`: dated model-price snapshot returned by the live `ucode` catalog.
- `benchmark/exclusions.yaml`: base-commit-scoped corpus defects discovered during the run.
- `evidence/results/normalized/*.jsonl`: sanitized outcomes for all attempted runs.
- `evidence/results/attributed/*.jsonl`: sanitized per-run telemetry totals.
- `evidence/results/summary.json`: scored metrics after symmetric exclusions.

The public evidence omits request IDs, invocation IDs, requester identity,
account ID, workspace ID, and workspace hostname. Raw system-table rows are not
part of the public repository.
