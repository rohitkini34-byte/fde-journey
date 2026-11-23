-- ===== section: Today at a glance =====
# One-time setup for Day 25, inside day25/ (macOS / Linux shell).
python3 -m venv .venv               # a fresh venv (Day 6)
source .venv/bin/activate           # Windows: .venv\Scripts\activate
python3 -m pip install "fastapi[standard]" "psycopg[binary,pool]" \
    pydantic-settings pytest
createdb fde_test                   # skip if Day 24 already made it
cp .env.example .env                # .env stays out of git (Day 24)
psql -d fde -v ON_ERROR_STOP=1 -f schema.sql   # api_assets, for curl
python3 -m pytest -q
# -> 37 errors in 0.12s    every one ends in NotImplementedError: expected.
# Tomorrow's you: the same command must end in "37 passed".
