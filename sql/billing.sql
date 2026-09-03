-- =====================================================================
-- Billing usage — system.billing.usage
-- =====================================================================
-- This query joins billable usage to the list price that was effective when
-- the usage occurred. The result is an estimate, not an invoice amount; private
-- prices, discounts, credits, and taxes are outside this public benchmark.
-- =====================================================================

-- :start_iso
-- :end_iso
-- :workspace_id  -- numeric workspace ID; not the full hostname

SELECT
  u.workspace_id,
  u.cloud,
  u.sku_name,
  u.usage_unit,
  u.usage_quantity,
  u.usage_start_time,
  u.usage_end_time,
  u.usage_metadata.endpoint_id,
  u.usage_metadata.endpoint_name,
  p.pricing.effective_list.default AS effective_list_price,
  u.usage_quantity * p.pricing.effective_list.default AS estimated_list_cost
FROM system.billing.usage AS u
LEFT JOIN system.billing.list_prices AS p
  ON u.cloud = p.cloud
  AND u.sku_name = p.sku_name
  AND u.usage_unit = p.usage_unit
  AND u.usage_end_time >= p.price_start_time
  AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
WHERE u.usage_start_time >= TIMESTAMP ':start_iso'
  AND u.usage_start_time <  TIMESTAMP ':end_iso'
  AND u.workspace_id = :workspace_id
  AND u.billing_origin_product IN ('MODEL_SERVING', 'AI_GATEWAY')
ORDER BY u.usage_start_time ASC;
