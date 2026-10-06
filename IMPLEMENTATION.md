# Holiday Season Sales Impact Analysis

## 1. The idea in simple words

Imagine asking: **"Did stores sell more around Christmas than they usually did in the month before it?"**

We will calculate that answer from daily sales records. We will repeat the same calculation for each holiday, store, and available store group. The dashboard will show the numbers and charts. This is an **observed comparison**: a sales increase around a holiday does not, by itself, prove the holiday caused the increase.

The required technical pipeline is:

```text
Rossmann CSV -> Kafka -> HDFS -> Hadoop MapReduce -> result files -> API -> web dashboard
```

Each tool has one job. Kafka carries records, HDFS keeps them, MapReduce calculates results, and the dashboard displays those results.

## 2. What data we actually have

The downloaded files are in `Rossmann Store Sales/`:

| File | Meaning | Use here |
| --- | --- | --- |
| `train.csv` | One row per store and day, with `Sales`, `Date`, `Open`, `Promo`, and holiday flags | **Main input** |
| `store.csv` | One row per store, with `StoreType` and `Assortment` | Optional store-group filters |
| `test.csv` | Future dates from the original forecasting competition, without actual `Sales` | Cannot measure actual impact |
| `sample_submission.csv` | Example prediction-submission format | Not needed |

I checked `train.csv`: it has **1,017,209 rows** from **2013-01-01 to 2015-07-31**. The header and all checked rows have nine fields. Its holiday codes are `0` (none), `a` (public holiday), `b` (Easter holiday), and `c` (Christmas). The original Kaggle [dataset page](https://www.kaggle.com/c/rossmann-store-sales/data) describes the files and access rules.

### The important mismatch with the problem statement

The statement says **"sales volume per product category."** Rossmann does not contain product categories, item quantities, or category-level sales. `Sales` is a store's daily sales amount. `Assortment` says what kind of range a **store** carries; it is not the sales of a product category.

The project will use **Rossmann only**, as decided. The truthful output is **holiday impact on store-level daily sales amount**, optionally grouped by store type or assortment. We will never label these groups "product categories" or call the amount "units sold."

Here is exactly what the college wording asks for, and what this dataset lets us do:

| College wording | Missing from Rossmann | What this project will actually report |
| --- | --- | --- |
| "Per product category" | No category or product identifier on a sales row. A store's total cannot be split into real category totals. | Per store, store type, and assortment type. `Assortment` is a store attribute, **not** category sales. |
| "Sales volume" if that means items sold | No item quantity or transaction-level product counts. | The numeric `Sales` amount per store per day. We will label it sales amount, not units. |
| "Individual holidays" by name | Only `StateHoliday` codes `a`, `b`, and `c`; `a` does not name the particular public holiday. | Holiday code plus date. We can add reviewed display names, but never guess them from the code alone. |
| "Current sales" | The provided measured sales end on 2015-07-31. | Replay historical records through Kafka to demonstrate the streaming pipeline. A truly current result would require a new current-data feed. |

For example, if a store sold 5,263 on one day, this data cannot tell whether cosmetics contributed 1,000 or 4,000. Both possibilities fit the same store total. No MapReduce job or dashboard can recover the missing category figures.

## 3. The calculation, with an example

The phrase **"seven days surrounding each holiday"** needs an exact rule. My proposed rule is three days before, the holiday itself, and three days after.

For an example holiday on **25 December**:

```text
Baseline:       22 November through 21 December = 30 days
Holiday window: 22 December through 28 December = 7 days
                                      ^ 25 December is in the middle
```

We compare **average sales per day**, because comparing the raw total of seven days with the raw total of 30 days would be misleading.

Example for one store:

```text
30-day baseline sales total = 240,000
Baseline daily average      = 240,000 / 30 = 8,000

7-day holiday sales total   = 70,000
Holiday daily average       = 70,000 / 7 = 10,000

Difference                  = 10,000 - 8,000 = +2,000 per day
Percentage change           = (2,000 / 8,000) * 100 = +25%
```

We calculate this for each eligible store, then combine stores for the overall or store-group view. A store is eligible for a holiday when its `StateHoliday` flag marks that holiday on the central date. This matters because some public holidays apply to only some stores.

### Rules that prevent misleading results

- A recorded closed day (`Open=0`, generally `Sales=0`) is a real observed day and stays in the comparison. Closures are part of the business impact.
- A **missing** store-day is different from a closed day. We will not invent a zero. If any of the 37 required days is missing, we will exclude that store from the main comparison for that event and show how many stores were excluded.
- If baseline average is zero, the percentage is undefined. We will show the absolute difference and a blank percentage.
- Promotions, weekday patterns, other nearby holidays, and closures can also change sales. The dashboard will show `Promo` and coverage information so users can interpret the result carefully.
- Holiday windows can overlap. A day's sale may be used in two separate holiday comparisons, and we will flag that overlap.

The source gives holiday **codes**, not a complete list of individual holiday names. We will first create a holiday catalog from dates with nonzero `StateHoliday`, then allow reviewed names to be added. Until then, an event can be labelled, for example, `Public holiday — 2014-05-01` without guessing its name.

## 4. What each technology does

| Technology | Plain meaning | Job in this project |
| --- | --- | --- |
| **Python** | Programming language | Read and validate CSV, send/receive Kafka messages, and write MapReduce scripts |
| **Apache Kafka** | A durable stream of messages | Receive one sales-day record at a time; let us replay historical data as if it were arriving now |
| **Apache Hadoop HDFS** | Storage spread across Hadoop nodes | Keep the raw batches and MapReduce input/output files |
| **Hadoop MapReduce** | Batch processing that maps records into groups and reduces each group to an answer | Deduplicate store-days, assign days to holiday/baseline windows, sum sales, calculate comparison results |
| **Hadoop Streaming** | A Hadoop feature for running mapper/reducer executables | Let us write real MapReduce jobs in Python rather than Java |
| **Next.js + React + TypeScript** | Web application framework and UI library | Build a polished, responsive dashboard and serve finished result files through read-only API routes |
| **Drawably** | React UI control and annotation library | Add the hand-drawn heading and controls inside the Next.js dashboard; the sales chart and labels stay easy to read |
| **Apache ECharts** | Interactive chart library | Show holiday trends and comparisons, including tooltips and zoom |
| **Docker Compose** | Starts several containers together | Run Kafka, Hadoop, the ingestion code, and dashboard on one computer |
| **Git** | Version control | Track our code and documents, while keeping downloaded dataset files out of commits |

[Hadoop Streaming](https://hadoop.apache.org/docs/stable/hadoop-streaming/HadoopStreaming.html) is still genuine Hadoop MapReduce: Hadoop schedules the map and reduce tasks; Python programs read and write the records. This is a practical choice because Python also handles the other parts of the project.

### What Kafka and MapReduce mean here

Kafka is the **entry line**. A producer publishes a message such as `store 1, 2015-07-31, sales 5263`. A consumer reads it and writes batches into HDFS. The dataset is historical, so this is a **replay that demonstrates streaming**. It is not live 2026 sales.

MapReduce is the **calculation step**. A mapper reads each sales record and emits a key such as `holiday_event | store | holiday_or_baseline` with the sales value. Hadoop groups identical keys. A reducer sums the values and counts valid days. A following MapReduce step combines store results into dashboard summaries. We will test the final output against a tiny example that can be calculated by hand.

HDFS is the **stored record of what arrived**. The completed job exports result files; Next.js reads those files and shows them in the dashboard. The dashboard does not continuously update after each Kafka message. It will show the time of the last successful run. Next.js replaces the previously proposed Streamlit/FastAPI combination, avoiding a separate API service for this local project.

## 5. How the system will work, step by step

1. **Validate input.** Read `train.csv` and `store.csv`; reject rows with unusable dates, IDs, or sales values. Keep the original files untouched.
2. **Publish to Kafka.** Send validated `train.csv` rows in date order to a sales topic. Use `store_id|date` as a stable message key. Offer a slow replay for a demo and a fast replay for full processing.
3. **Store in HDFS.** The Kafka consumer writes immutable batches as newline-delimited JSON, with a small manifest containing row count and Kafka offset range. It commits offsets only after the batch is stored.
4. **Prepare daily records.** The first MapReduce job removes identical replay duplicates, records conflicts or invalid rows, and joins `store.csv` so results can be filtered by `StoreType` or `Assortment`.
5. **Build the holiday catalog.** Find dates with `StateHoliday` codes `a`, `b`, or `c`; generate candidate events; allow reviewed names.
6. **Compare windows.** MapReduce assigns eligible store-days to the 30-day baseline or seven-day holiday window, checks that all days are present, and calculates sums, daily averages, differences, and percentages.
7. **Show results.** Save versioned CSV/JSON output. Next.js reads those results and displays event/year/store-group filters, a daily trend chart, and missing-data and promotion context.

Kafka replay can produce duplicate messages, so the MapReduce preparation step must avoid counting a store-day twice. We will use an explicit deterministic rule and test repeated runs. We will not claim a complete "exactly once" system just because Kafka is in the diagram.

## 6. What you need to set up manually

The Rossmann download is **already present** in `Rossmann Store Sales/`. There is no need to download it again or move it right now; the code will accept that path.

On this Windows machine, Docker CLI and WSL are installed. **Docker Engine is not currently running.** No host Python command was found, but Python will run inside containers, so host Python is optional. Java is installed, but the containerized Hadoop runtime should not depend on that host installation.

Before we can run the full pipeline, start **Docker Desktop** using its Linux/WSL 2 backend. Then verify in PowerShell:

```powershell
docker info
docker compose version
```

If Docker Desktop is not installed or has a setup problem, use the [official Windows guide](https://docs.docker.com/desktop/setup/install/windows-install/). Kafka and Hadoop need several containers, so some free RAM and disk space are required; we will measure the practical amount during the first full run.

After implementation, the README will have copyable commands for starting services, running a small test, replaying Rossmann, launching MapReduce, and opening the dashboard.

## 7. Code we will build

```text
compose.yaml                 Container definitions
docker/                      Container setup
src/ingest/producer.py       CSV validation and Kafka publishing
src/ingest/consumer.py       Kafka-to-HDFS batch writer
src/jobs/                    Hadoop Streaming mappers and reducers
src/jobs/run.py              Job launcher and result paths
web/                         Next.js, React, TypeScript, Drawably, and ECharts dashboard
config/holidays.csv          Holiday dates, codes, and reviewed names
data/sample/                 Small synthetic data for repeatable tests
tests/                      Calculation and pipeline checks
scripts/                    Simple setup and run commands
README.md                   Instructions from a fresh copy of the project
```

The downloaded Rossmann files are ignored by Git. Container image tags and direct dashboard dependencies are specified in the project files. A package lockfile and full version verification require package installation when network access is available.

## 8. Build order and proof that it works

| Stage | What gets built | How we check it |
| --- | --- | --- |
| 1 | Docker Compose stack and tiny sample data | Kafka and HDFS start; a small job runs |
| 2 | Kafka producer and HDFS consumer | Published sample rows appear in HDFS; bad rows are reported |
| 3 | Holiday catalog and MapReduce jobs | Results match a hand-calculated 37-day example; duplicates and missing days behave correctly |
| 4 | Next.js dashboard | Its cards and charts exactly match the MapReduce result files |
| 5 | Full Rossmann run and README | All 1,017,209 training rows are accounted for or reported as rejected; a clean setup can reproduce the output |

## 9. Decisions for the build

- Use Rossmann only and state its limits plainly.
- Measure total daily sales amount per store, never category sales or item units.
- Use all three observed holiday codes (`a`, `b`, `c`) and identify events by code plus date. A reviewed catalog may add names.
- Use the proposed seven-day window (three before, the day itself, three after) and the preceding 30 calendar days.
- Keep recorded zero-sale closed days and exclude missing days from the primary comparison.
- Use Next.js for the dashboard. Streamlit was considered as a quick prototype tool; the chosen UI gives full control over the final design.
- Use Drawably for paper-and-ink visual accents and native React controls in the dashboard. The data labels and charts remain clear and accessible.
