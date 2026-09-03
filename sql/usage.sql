-- =====================================================================
-- Unity AI Gateway usage — system.ai_gateway.usage
-- =====================================================================
-- Schema reference: docs/sources.md (Databricks docs, accessed 2026-08-30)
--
-- IMPORTANT: this query is a TEMPLATE. Substitute the start/end/requester
-- values per benchmark run. Do NOT commit real user emails or request IDs.
--
-- The Databricks SQL connector does not support :named parameters in a
-- portable way across warehouse/serverless backends, so we use jinja-style
-- placeholders. The runner substitutes them before submission.
-- =====================================================================

-- :start_iso   -- e.g. 2026-08-30T12:00:00Z
-- :end_iso     -- e.g. 2026-08-30T13:00:00Z
-- :requester   -- the user ID that the benchmark ran as (run-scoped)

SELECT
  request_id,
  invocation_id,
  schema_version,
  endpoint_id,
  endpoint_name,
  endpoint_tags,
  event_time,
  latency_ms,
  time_to_first_byte_ms,
  destination_type,
  destination_name,
  destination_id,
  destination_model,
  requester,
  requester_type,
  user_agent,
  api_type,
  input_tokens,
  output_tokens,
  total_tokens,
  token_details.cache_read_input_tokens        AS cache_read_input_tokens,
  token_details.cache_creation_input_tokens    AS cache_creation_input_tokens,
  token_details.output_reasoning_tokens        AS output_reasoning_tokens,
  status_code,
  routing_information,
  request_tags,
  invocation_metadata
FROM system.ai_gateway.usage
WHERE event_time >= TIMESTAMP ':start_iso'
  AND event_time <  TIMESTAMP ':end_iso'
  AND requester = ':requester'
ORDER BY event_time ASC;
