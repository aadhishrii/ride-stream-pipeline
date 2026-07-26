# RideStream

A streaming data pipeline for ride-share event data, ingesting events through Azure Event Hub, processing them through a Databricks medallion architecture, and modeling them into a STAR schema, with a natural language query layer on top.

## Problem statement

Ride-share platforms generate high-volume, continuous event data: bookings, driver assignments, fare calculations, that needs to be both immediately usable (for operational dashboards) and reliably queryable (for historical analytics), without one use case degrading the other.

This project simulates that environment: ingesting ride events in near real time, landing them through a medallion architecture so raw and processed data stay separable and debuggable, and modeling the result into a STAR schema so it's actually queryable for the kinds of questions an analytics or ops team would ask: "which city has the most cancellations," "how is surge pricing distributed," and so on, without needing to hand-write a join across raw event data every time.

The natural language layer on top is a response to a narrower problem: STAR schemas are efficient to query but require knowing the schema to use well. A text-to-SQL layer lowers that barrier for someone who understands the business question but not the underlying table structure, while still enforcing the same safety and correctness guarantees a hand-written query would need.

## Architecture

<!-- Insert the overall architecture diagram here -->
<img width="636" height="329" alt="Screenshot 2026-07-27 at 12 54 24 AM" src="https://github.com/user-attachments/assets/18688dfc-0c3e-4792-84cb-da379c04109f" />


```
Event Hub → Azure Data Factory → Azure Data Lake Storage (bronze)
    → Databricks (silver, Jinja-templated SQL)
    → Spark Declarative Pipeline (SCD Type 1/2 dimension + fact tables)
    → Natural language query layer (Claude API)
```

## What it does

- **Ingestion**: Ride event data lands via Azure Event Hub, with historical/batch loads handled through Azure Data Factory into Azure Data Lake Storage.
- **Processing**: Databricks notebooks transform raw data into a cleaned, deduplicated "one big table" (OBT) silver layer, with SQL generation templated via Jinja.
- **Dimensional modeling**: A Spark Declarative Pipeline builds six dimension tables and a fact table using Auto CDC flows. Five dimensions use SCD Type 1 (current-value only); `dim_location` uses SCD Type 2, tracking city/region history over time.
- **Natural language query layer**: A Claude-API-backed layer translates plain-English questions into validated SQL, executed against the Databricks SQL Warehouse, with every query logged for accuracy and performance tracking.

## Data model

The gold-layer schema follows a standard STAR pattern: one fact table (`fact`, ride-level grain) surrounded by six dimension tables.

| Table | Grain | SCD Type |
|---|---|---|
| `fact` | one row per ride | — |
| `dim_passenger` | one row per passenger | Type 1 |
| `dim_driver` | one row per driver | Type 1 |
| `dim_vehicle` | one row per vehicle | Type 1 |
| `dim_payment` | one row per payment method | Type 1 |
| `dim_booking` | one row per ride (booking/location detail) | Type 1 |
| `dim_location` | one row per city, versioned | **Type 2** |

There's no dedicated `dim_time` — date/time filtering is derived inline from `dim_booking.booking_timestamp`. This was a conscious gap, not an oversight; see "What's next."

## Example queries

A few of the natural language questions this system answers correctly end-to-end, to give a sense of what "it works" actually means here:

- *"which pickup city had the most rides"* → joins `fact` → `dim_location`, groups, orders, limits to 1
- *"what is the average tip amount by payment method"* → joins `fact` → `dim_payment`, aggregates
- *"how many rides were paid by card"* → filters on `dim_payment.is_card`
- *"what is the weather in each pickup city"* → correctly rejected — no weather data exists in this schema

That last one matters as much as the successful ones: a system that always produces *some* SQL, even for unanswerable questions, is more dangerous than one that knows what it doesn't know.

## Design decisions

**Why SCD Type 2 only for `dim_location`**: most dimensions here (passenger, driver, vehicle, payment) only need current values, there's little value in tracking history for a passenger's phone number. Location is different: city/region classifications can change, and preserving that history matters for time-based analytics. This is a deliberate split, not a default.

**Why a validation layer in front of the query executor**: the LLM is instructed to only generate `SELECT` statements, but instructions alone aren't a safety boundary. A second layer rejects anything that isn't a clean `SELECT`, including destructive statements, before it ever reaches the warehouse, so the system doesn't rely solely on the model behaving correctly.

<!-- Add your specific hard-problem writeup here once decided, e.g. late-event handling -->

## Results

Tested against a 20-question set spanning simple lookups, single/multi-table joins, aggregations, and deliberately out-of-scope or unsafe requests:

- **17/17 (100%)** of answerable questions executed successfully with correct SQL
- **3/3** out-of-scope/unsafe requests correctly rejected (unsupported data, non-SQL forecasting requests, and a destructive query)
- Average query latency: ~4–6 seconds after warehouse warm-up (includes LLM generation + execution)

## What I'd do differently

A few things that only became clear during the build, worth naming honestly rather than glossing over:

- **Catalog/schema naming was an early mistake.** Everything: raw, silver, and gold-layer tables ended up in a single schema literally named `bronze`, which doesn't match standard medallion convention (bronze should mean raw/unprocessed only). This didn't break anything functionally, but it's a naming discipline lesson: decide the schema layout before building, not after.
- **Query latency includes a cold-start cost I didn't account for initially.** First-query latency on a serverless SQL Warehouse is meaningfully higher than steady-state, worth measuring warm vs. cold separately rather than reporting one blended average.
- **Table IDs matter more than they seem to at first.** An early version of the NL query logging kept results keyed by loop index rather than a stable identifier, harmless until you skip a record, at which point the indexing silently shifts. Worth designing IDs around something stable from the start.

## Tech stack

Azure Event Hub, Azure Data Factory, Azure Data Lake Storage, Azure Databricks, PySpark, Spark Declarative Pipelines, Delta Lake, Jinja, Claude API, Databricks SQL Warehouse

## Setup

1. Configure Azure Event Hub and Data Factory pipelines (see `ingestion/`)
2. Run the Databricks bronze/silver notebooks
3. Deploy the Spark Declarative Pipeline (`databricks/sdp_pipeline/`)
4. Set up local environment for the NL query layer:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a `.env` file with:
   ```
   DATABRICKS_SERVER_HOSTNAME=
   DATABRICKS_HTTP_PATH=
   DATABRICKS_ACCESS_TOKEN=
   ANTHROPIC_API_KEY=
   ```
6. Run a query:
   ```bash
   python run_query.py
   ```

## What's next

- Split the medallion layers into separate schemas (bronze/silver/gold) rather than a single shared schema, current setup is a Databricks Free Edition constraint
- Expand the test question set and track accuracy over time as the schema evolves
- Add a `dim_time` dimension for cleaner date/time filtering, rather than deriving from `dim_booking.booking_timestamp` inline
