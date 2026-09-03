# Methodology

## Question

Can a transparent prompt-only router reduce model inference cost per successful
coding task relative to a fixed stronger model without lowering observed task
success?

## Arms

| Arm | Selection path |
| --- | --- |
| `FIXED_STRONG` | Claude Sonnet 5 pinned for the entire task |
| `FIXED_CHEAP` | Claude Haiku 4.5 pinned for the entire task |
| `CLIENT_ROUTING` | Haiku 4.5 selects `cheap` or `strong`, then the chosen worker model is pinned |

Every model call used Databricks Unity AI Gateway. Claude Code 2.1.258, the
prompt, the repository state, and the deterministic verifier were held
constant.

The treatment is the repository's frozen client-side policy, not Databricks
Smart Routing. The benchmark makes no claim about the proprietary routing
algorithm.

## Corpus

The corpus contains 24 self-contained repositories: eight labeled easy, eight
medium, and eight hard. Tasks cover localized fixes, tests, SQL, configuration,
async cancellation, concurrency, state transitions, schema changes, and
cross-module refactoring.

All 24 tasks ran once under each arm, for 72 attempted runs. Three fixture
defects were discovered during the audit and excluded symmetrically:

- `easy-004`: incompatible tuple and list types in the expected-row comparison.
- `medium-007`: inconsistent seed and expected data, plus a starting query that
  did not reproduce the stated bug.
- `hard-005`: the starting implementation already satisfied the asserted
  timeout; server teardown caused the apparent hang.

The scored matrix therefore contains 21 tasks per arm, balanced at seven per
difficulty label. `benchmark/exclusions.yaml` binds the exclusions to base
commit `386387056c8fb9502a975776b4df695e0029fd0b`.

## Router policy

The selector saw only the task title and request. It could not read difficulty,
fixture tests, expected output, verifier commands, or results from other arms.

The frozen policy selected Haiku for localized changes with explicit
requirements and low risk. It selected Sonnet for ambiguous debugging,
concurrency, state transitions, SQL, security-sensitive behavior, or changes
spanning several components.

Each routed row records the selected model, reason, selector duration, selector
tokens, policy ID, and policy SHA-256. Selector requests are included in routed
cost and token totals.

## Run protocol

1. Require a clean tracked workspace and record `HEAD`.
2. Create a detached Git worktree for one arm-task pair.
3. Set the agent and evaluator directory to the task's nested repository.
4. Write the task prompt and declared verification command.
5. For `CLIENT_ROUTING`, request and validate one JSON routing decision.
6. Launch Claude Code through `ucode` with the worker model pinned and a
   15-minute agent timeout.
7. Capture stdout, stderr, exit code, duration, and binary-safe Git diff.
8. Run the deterministic verifier and required-file checks.
9. Check forbidden modifications relative to the nested task repository.
10. Remove the worktree and write one normalized JSONL row.

Task order was randomized with seed 42 within each arm. Execution was serial.
The three arms were not interleaved.

## Success rule

A task passes when its deterministic verifier exits zero, every required file
exists, and no forbidden file was modified. No LLM judge participates. Agent
exit code alone does not decide success because an agent can finish the code and
then fail while summarizing; raw exit codes remain available for audit.

## Telemetry attribution

The source query filtered `system.ai_gateway.usage` to the benchmark requester
and full benchmark window. Attribution then matched each record to an exact run
window. Serial execution made the windows non-overlapping.

The final attributed set contained 1,105 unique invocation IDs with no ID
assigned to more than one run. Fixed Sonnet rows contained only Sonnet calls;
fixed Haiku rows contained only Haiku calls. Every matched routed row contained
its recorded worker model. The only routed row without a match belonged to the
excluded `hard-005` fixture.

## Cost calculation

The dated price snapshot stores USD rates per million tokens for uncached input,
cache reads, cache writes, and output. Per invocation:

```text
uncached input = input tokens - cache-read tokens - cache-write tokens

estimated cost =
  uncached input * input rate
  + cache-read tokens * cache-read rate
  + cache-write tokens * cache-write rate
  + output tokens * output rate
```

The analysis sums invocation estimates into each task and arm. This is estimated
model inference cost. It is not a Databricks invoice and excludes SQL compute,
AI Gateway usage-tracking charges, discounts, credits, taxes, and human time.

## Metrics

The primary metric is estimated model cost per successful task. Supporting
metrics are success rate, total estimated model cost, median task duration,
input and output tokens, invocations per run, gateway request error rate, and
routing distribution by hidden difficulty label.
