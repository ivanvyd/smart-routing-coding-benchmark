CREATE TABLE accounts (account_id INTEGER PRIMARY KEY, plan TEXT);
CREATE TABLE events (
  event_id INTEGER PRIMARY KEY,
  account_id INTEGER,
  event_ts TEXT,
  kind TEXT
);
