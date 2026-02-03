CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS saved_businesses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE
);

-- keep only one row per user/business pair before adding unique index
DELETE FROM saved_businesses a
USING saved_businesses b
WHERE a.id < b.id
  AND a.user_id = b.user_id
  AND a.business_id = b.business_id;

CREATE UNIQUE INDEX IF NOT EXISTS saved_businesses_user_business_idx
ON saved_businesses (user_id, business_id);
