CREATE TABLE IF NOT EXISTS feature_votes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id  TEXT NOT NULL,
  feature_key TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(session_id, feature_key)
);
CREATE INDEX IF NOT EXISTS idx_feature_votes_feature ON feature_votes(feature_key);
