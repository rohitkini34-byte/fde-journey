"""Day 20 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 5: pandas read_sql, from a query to a report =====
# Concept 5: run SQL from pandas and get a DataFrame back.
import os

import pandas as pd                        # "pd" is the usual short name
from sqlalchemy import create_engine

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")
# SQLAlchemy picks the driver from the URL: "+psycopg" means psycopg 3.
engine = create_engine(DB_URL.replace("postgresql://",
                                      "postgresql+psycopg://", 1))
# An engine is a connection factory: it connects when a query runs.

df = pd.read_sql("SELECT uid, day, views FROM lesson_views", engine)
print(df.shape)              # (rows, columns), like a tuple from Day 3
# -> (18, 3)
print(df.dtypes)             # one data type per column
# -> uid         str
# -> day      object
# -> views     int64
print(df.head(3))            # first 3 rows; the left column is the index
# ->       uid         day  views
# -> 0  blt101  2026-11-01    120
# -> 1  blt101  2026-11-02    340
# -> 2  blt101  2026-11-03    310
# GOTCHA: day is "object" (Python date objects), not a real date column,
# so .dt date methods will not work on it yet. The next example fixes it.

# ===== section: Concept 5: pandas read_sql, from a query to a report =====
# Concept 5: parameters, real dates, groupby and a pivot table.
import os

import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")
engine = create_engine(DB_URL.replace("postgresql://",
                                      "postgresql+psycopg://", 1))

# text() + :since: the value travels separately from the SQL (Day 18).
SQL = text("""
    SELECT v.uid, e.content_type, v.day, v.views
    FROM lesson_views v
    JOIN lesson_entries e USING (uid)
    WHERE v.day >= :since
""")
df = pd.read_sql(SQL, engine, params={"since": "2026-11-02"},
                 parse_dates=["day"])          # day becomes datetime64
print(df.dtypes["day"])
# -> datetime64[s]

# groupby + agg: GROUP BY in memory. Each name=("col", "func") pair
# becomes one output column, like SUM(...) AS total in SQL.
by_type = (df.groupby("content_type")["views"]
             .agg(total="sum", best_day="max")
             .sort_values("total", ascending=False))
print(by_type)
# ->               total  best_day
# -> content_type
# -> campaign        910       340
# -> page            257        52

# pivot_table: one row per entry, one column per day, like a spreadsheet.
grid = df.pivot_table(index="uid", columns=df["day"].dt.strftime("%d %b"),
                      values="views", aggfunc="sum", fill_value=0)
print(grid)
# -> day     02 Nov  03 Nov  04 Nov  05 Nov
# -> uid
# -> blt101     340     310      90      75
# -> blt102      45      38      52      47
# -> blt103       0      10      25      60
# -> blt104      15      20      18      22
grid.to_csv("views_grid.csv")      # a file the editors open in Excel
# GOTCHA: blt103's 0 on 02 Nov is fill_value. The database has no row
# that day. Say so in the report if "no data" and "0 views" differ.
