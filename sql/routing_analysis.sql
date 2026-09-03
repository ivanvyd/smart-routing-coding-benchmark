-- =====================================================================
-- Routing analysis — per-arm aggregates from system.ai_gateway.usage
-- =====================================================================
-- This query rolls the per-invocation detail up to per (arm, task) totals
-- given a labelled "benchmark_run_id" request tag. The benchmark runner
-- would attach this tag via the official Databricks-Ai-Gateway-Request-Tags
-- header IF the current ucode path supports it. If it does not, the
-- benchmark labels by time window + requester; the query still works but
-- the WHERE clause uses the requester + window instead of the tag.
-- =====================================================================

-- :start_iso
-- :end_iso
-- :requester

WITH attributed AS (
  SELECT *
  FROM system.ai_gateway.usage
  WHERE event_time >= TIMESTAMP ':start_iso'
    AND event_time <  TIMESTAMP ':end_iso'
    AND requester = ':requester'
)
SELECT
  endpoint_name,
  destination_name,
  destination_model,
  COUNT(*)                                        AS invocations,
  SUM(input_tokens)                               AS total_input_tokens,
  SUM(output_tokens)                              AS total_output_tokens,
  SUM(total_tokens)                               AS total_tokens,
  SUM(token_details.cache_read_input_tokens)      AS total_cache_read_tokens,
  SUM(token_details.cache_creation_input_tokens)  AS total_cache_creation_tokens,
  SUM(token_details.output_reasoning_tokens)      AS total_reasoning_tokens,
  ROUND(AVG(latency_ms), 2)                       AS mean_latency_ms,
  ROUND(APPROX_PERCENTILE(latency_ms, 0.95), 2)   AS p95_latency_ms,
  SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS error_count
FROM attributed
GROUP BY endpoint_name, destination_name, destination_model
ORDER BY invocations DESC;
