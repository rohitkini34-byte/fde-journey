-- ===== section: Today at a glance =====
# One-time setup for Day 24, inside day24/ (macOS / Linux shell).
python3 -m venv .venv               # a fresh venv (Day 6)
source .venv/bin/activate           # Windows: .venv\Scripts\activate
# psycopg[binary,pool]: the driver (Day 18) plus its pool package.
# pydantic-settings: typed settings from environment variables.
python3 -m pip install "fastapi[standard]" "psycopg[binary,pool]" \
    pydantic-settings pytest
python3 -c "import psycopg_pool, pydantic_settings; print('ok')"
# -> ok
# Build today's table in your Week 3 database, and a test database.
psql -d fde -v ON_ERROR_STOP=1 -f schema.sql
# -> NOTICE:  table "api_entries" does not exist, skipping   (first run only)
createdb fde_test                   # tests use their OWN database
cp .env.example .env                # then edit .env if your DB needs a user
