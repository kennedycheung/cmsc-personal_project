-- SQLite schema for initial Adventure Arbitrage Engine data.
-- Mirrors the SQLAlchemy models under backend/app/models/. The FastAPI app itself
-- creates tables via SQLAlchemy's Base.metadata.create_all (portable across SQLite
-- and Postgres); this file is kept in sync for the standalone database/init_db.py
-- tool and as human-readable schema documentation.
CREATE TABLE IF NOT EXISTS health_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checked_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS destinations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name VARCHAR(200) NOT NULL,
  country VARCHAR(100) NOT NULL,
  region VARCHAR(100) NOT NULL,
  description TEXT,
  budget_per_day FLOAT NOT NULL DEFAULT 0,
  interests TEXT,
  uniqueness_score FLOAT NOT NULL DEFAULT 5,
  travel_difficulty FLOAT NOT NULL DEFAULT 5,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'USD',
  seasonal_multipliers TEXT
);

CREATE INDEX IF NOT EXISTS idx_destinations_region ON destinations(region);

CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  category VARCHAR(100),
  price FLOAT NOT NULL DEFAULT 0,
  duration_hours FLOAT,
  location VARCHAR(150),
  opening_time VARCHAR(5),
  closing_time VARCHAR(5),
  travel_minutes FLOAT NOT NULL DEFAULT 15,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  is_outdoor BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_activities_destination_id ON activities(destination_id);

CREATE TABLE IF NOT EXISTS deals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  destination_id INTEGER REFERENCES destinations(id),
  deal_type VARCHAR(20) NOT NULL,
  source VARCHAR(50) NOT NULL,
  external_id VARCHAR(100) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  location VARCHAR(150) NOT NULL,
  price FLOAT NOT NULL,
  original_price FLOAT,
  discount_percent FLOAT,
  currency VARCHAR(3) NOT NULL DEFAULT 'USD',
  url VARCHAR(500),
  valid_from VARCHAR(10),
  valid_until VARCHAR(10),
  categories TEXT,
  created_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL,
  UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_deals_destination_id ON deals(destination_id);
CREATE INDEX IF NOT EXISTS idx_deals_deal_type ON deals(deal_type);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email VARCHAR(255) NOT NULL UNIQUE,
  hashed_password VARCHAR(255) NOT NULL,
  created_at VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_preferences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  max_budget_per_day FLOAT,
  interests TEXT,
  travel_style VARCHAR(50),
  updated_at VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_adventures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  name VARCHAR(200) NOT NULL,
  days INTEGER NOT NULL,
  budget FLOAT,
  interests TEXT,
  itinerary_snapshot TEXT NOT NULL,
  created_at VARCHAR(40) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_adventures_user_id ON saved_adventures(user_id);

CREATE TABLE IF NOT EXISTS favorite_destinations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  created_at VARCHAR(40) NOT NULL,
  UNIQUE (user_id, destination_id)
);

CREATE INDEX IF NOT EXISTS idx_favorite_destinations_user_id ON favorite_destinations(user_id);

CREATE TABLE IF NOT EXISTS airports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  destination_id INTEGER NOT NULL REFERENCES destinations(id),
  iata_code VARCHAR(3) NOT NULL,
  name VARCHAR(150) NOT NULL,
  distance_km FLOAT NOT NULL,
  ground_transport_cost_usd FLOAT NOT NULL,
  ground_transport_minutes FLOAT NOT NULL,
  baseline_fare_usd FLOAT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_airports_destination_id ON airports(destination_id);
