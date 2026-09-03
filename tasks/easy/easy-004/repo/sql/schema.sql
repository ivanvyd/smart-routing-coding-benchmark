CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  signup_date TEXT
);
CREATE TABLE events (
  event_id INTEGER PRIMARY KEY,
  user_id  INTEGER,
  event_ts TEXT,
  kind     TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);
