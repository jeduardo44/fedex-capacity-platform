"""DuckDB connection helpers.

One persistent warehouse file (data/warehouse.duckdb) shared by ingestion,
dbt, forecasting and dashboards. dbt manages its own connection through
profiles.yml; everything else goes through :func:`warehouse_connection`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pandas as pd

from src.utils.config import WAREHOUSE_PATH


@contextmanager
def warehouse_connection(
    db_path: Path = WAREHOUSE_PATH, read_only: bool = False
) -> Iterator[duckdb.DuckDBPyConnection]:
    """Context manager handling the DuckDB connection lifecycle."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path), read_only=read_only)
    try:
        yield con
    finally:
        con.close()


def load_parquet_to_table(
    con: duckdb.DuckDBPyConnection, parquet_glob: str, table: str
) -> int:
    """(Re)create ``table`` (schema-qualified, e.g. ``raw.weekly_demand``)
    from Parquet files and return the row count."""
    schema = table.split(".")[0] if "." in table else "main"
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    con.execute(
        f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_parquet('{parquet_glob}')"
    )
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def write_dataframe(
    con: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str
) -> int:
    """(Re)create ``table`` from a pandas DataFrame and return the row count."""
    schema = table.split(".")[0] if "." in table else "main"
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    con.register("_df_tmp", df)
    con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _df_tmp")
    con.unregister("_df_tmp")
    return len(df)


def read_table(con: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    """Run a query and return the result as a pandas DataFrame."""
    return con.execute(query).df()
