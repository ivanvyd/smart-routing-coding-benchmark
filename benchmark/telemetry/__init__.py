"""Telemetry extraction and normalization.

The benchmark uses Unity AI Gateway's `system.ai_gateway.usage` table as the
source of truth for tokens, latency, and destination model. The source query
filters to the benchmark requester, then exact serial run windows attribute
calls to tasks. Estimated model cost uses a dated price snapshot.
"""
