-- BUG: counting events inflates the result when one user has several events.
-- The expected output is one row per day with the distinct active-user count.
SELECT
  substr(e.event_ts, 1, 10) AS day,
  COUNT(*) AS dau
FROM events e
JOIN users u ON u.user_id = e.user_id
WHERE e.kind IN ('page_view', 'click')
GROUP BY substr(e.event_ts, 1, 10)
ORDER BY day ASC;
