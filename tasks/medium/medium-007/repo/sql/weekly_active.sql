-- BUG: two joins to accounts produce a fan-out.
SELECT
  strftime('%Y-%W', e.event_ts) AS week,
  COUNT(*) AS wau
FROM events e
JOIN accounts a ON a.account_id = e.account_id
JOIN accounts a2 ON a2.plan = a.plan
WHERE e.kind IN ('login', 'click')
GROUP BY strftime('%Y-%W', e.event_ts)
ORDER BY week ASC;
