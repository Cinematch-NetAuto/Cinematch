"""Create the database tables from db/schema.sql.

Run from backend/:  python -m scripts.init_db

Safe to run again: schema.sql only uses CREATE ... IF NOT EXISTS, so tables
that already exist, and the rows in them, are left alone.
"""

from pathlib import Path

from sqlalchemy import inspect

from app.db import engine

SCHEMA_FILE = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def init_db() -> list[str]:
    """Run schema.sql in one transaction and return the table names."""
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    with engine.begin() as conn:  # commits at the end, rolls back on any error
        conn.exec_driver_sql(sql)
    return sorted(inspect(engine).get_table_names())


if __name__ == "__main__":
    tables = init_db()
    print(f"Database ready: {len(tables)} tables ({', '.join(tables)})")
