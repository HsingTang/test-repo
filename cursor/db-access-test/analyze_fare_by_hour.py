"""Query average fare by pickup hour via Databricks SQL and save a bar chart."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import Disposition, Format

WAREHOUSE_NAME = "Serverless Starter Warehouse"
OUTPUT_DIR = Path(__file__).resolve().parent
CHART_PATH = OUTPUT_DIR / "fare_by_hour.png"

SQL = """
SELECT
  HOUR(tpep_pickup_datetime) AS pickup_hour,
  AVG(fare_amount) AS avg_fare_amount
FROM samples.nyctaxi.trips
GROUP BY pickup_hour
ORDER BY pickup_hour
"""


def warehouse_id_for_name(client: WorkspaceClient, name: str) -> str:
    for wh in client.warehouses.list():
        if wh.name == name:
            if wh.id is None:
                raise RuntimeError(f"Warehouse {name!r} has no id")
            return wh.id
    raise RuntimeError(f"No SQL warehouse named {name!r}")


def run_query(client: WorkspaceClient, warehouse_id: str) -> pd.DataFrame:
    resp = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=SQL,
        disposition=Disposition.INLINE,
        format=Format.JSON_ARRAY,
        wait_timeout="50s",
    )
    if resp.status is None or resp.status.state is None:
        raise RuntimeError("Statement finished without status")
    from databricks.sdk.service.sql import StatementState

    if resp.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"Query failed: {resp.status}")

    if resp.manifest is None or resp.manifest.schema is None:
        raise RuntimeError("Missing result schema")

    columns = [c.name for c in resp.manifest.schema.columns]
    data = resp.result.data_array if resp.result else []
    rows = [[col for col in row] for row in data]
    df = pd.DataFrame(rows, columns=columns)
    df["pickup_hour"] = df["pickup_hour"].astype(int)
    df["avg_fare_amount"] = df["avg_fare_amount"].astype(float)
    return df


def plot_and_save(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["pickup_hour"], df["avg_fare_amount"], color="#1f77b4", edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Pickup hour of day (0–23)")
    ax.set_ylabel("Average fare amount (USD)")
    ax.set_title("Average NYC taxi fare by pickup hour")
    ax.set_xticks(range(24))
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHART_PATH, dpi=150)
    plt.close(fig)


def main() -> None:
    client = WorkspaceClient()
    wh_id = warehouse_id_for_name(client, WAREHOUSE_NAME)
    df = run_query(client, wh_id)
    plot_and_save(df)
    peak = df.loc[df["avg_fare_amount"].idxmax()]
    print(f"Highest average fare: hour {int(peak['pickup_hour'])} "
          f"(${peak['avg_fare_amount']:.4f})")


if __name__ == "__main__":
    main()
