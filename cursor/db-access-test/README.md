# NYC taxi fare by pickup hour (Databricks SQL)

This folder documents a quick check that the Databricks SDK can run SQL against the workspace **Serverless Starter Warehouse** and produce a local visualization.

## Data and query

- **Table:** `samples.nyctaxi.trips` (NYC yellow taxi trip sample in the Databricks samples catalog).
- **Metric:** `AVG(fare_amount)` grouped by `HOUR(tpep_pickup_datetime)`.

```sql
SELECT
  HOUR(tpep_pickup_datetime) AS pickup_hour,
  AVG(fare_amount) AS avg_fare_amount
FROM samples.nyctaxi.trips
GROUP BY pickup_hour
ORDER BY pickup_hour
```

## How the result was produced

1. **`WorkspaceClient()`** — Uses the sandbox’s existing Databricks authentication (no extra tokens or config in this environment).
2. **Resolve warehouse** — Listed SQL warehouses with `client.warehouses.list()` and selected the warehouse named `Serverless Starter Warehouse` (id resolved at runtime).
3. **Run SQL** — Called `client.statement_execution.execute_statement()` with:
   - `warehouse_id` set to that warehouse
   - `disposition=Disposition.INLINE` and `format=Format.JSON_ARRAY` so rows return in the response
   - `wait_timeout="50s"` so the statement can finish on serverless compute
4. **Load into pandas** — Built a `DataFrame` from `resp.manifest.schema.columns` (column names) and `resp.result.data_array` (JSON rows), casting `pickup_hour` to `int` and `avg_fare_amount` to `float`.
5. **Plot** — Matplotlib bar chart: x = hour 0–23, y = average fare; saved as `fare_by_hour.png`.

You can reproduce the chart by running:

```bash
python3 cursor/db-access-test/analyze_fare_by_hour.py
```

The script prints which pickup hour has the highest average fare.

## Artifacts

| File | Description |
|------|-------------|
| `fare_by_hour.png` | Bar chart of average fare by pickup hour |
| `analyze_fare_by_hour.py` | Script that runs the query and generates the chart |
