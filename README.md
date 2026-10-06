# Holiday Season Sales Impact Analysis

This project compares **total sales amount per Rossmann store per day** around holidays with the preceding 30 days. Sales records pass through **Kafka → HDFS → Hadoop Streaming MapReduce → Next.js dashboard**. The dashboard uses [Drawably](https://www.drawably.dev/) for hand-drawn accents and controls.

The source has store-level daily totals. It has **no product-category sales or item quantities**. The dashboard therefore reports store-level sales, grouped by store type or assortment type. It does not claim to measure units sold or sales per product category. [IMPLEMENTATION.md](IMPLEMENTATION.md) explains the calculation and the dataset limits in more detail.

**New to this stack?** Read [LEARN_THE_PIPELINE.md](LEARN_THE_PIPELINE.md) for a plain-language explanation of every command below and how Docker, Kafka, HDFS, MapReduce, and the dashboard fit together.

## First setup after cloning

1. Open PowerShell in the **cloned project folder**, the folder containing `compose.yaml` and this README. The `Set-Location` examples below use the original author's path. If you cloned elsewhere, replace that path with your own project folder.
2. The `Rossmann Store Sales/` folder is ignored by Git, so a fresh clone will **not** contain the data. Get it from the official [Rossmann Store Sales Kaggle data page](https://www.kaggle.com/c/rossmann-store-sales/data). Sign in to Kaggle and accept the competition rules if Kaggle asks. Download the files and extract the ZIP.
3. In the project folder, make a directory named **`Rossmann Store Sales`**. Put **`train.csv`** and **`store.csv`** directly inside it. The project does not need `test.csv` or `sample_submission.csv` to calculate observed sales. The layout must look exactly like this:

   ```text
   bdaproject/
   ├── compose.yaml
   ├── Rossmann Store Sales/
   │   ├── train.csv
   │   └── store.csv
   └── README.md
   ```

4. In PowerShell, from the project folder, verify the files before starting Docker:

   ```powershell
   Test-Path '.\Rossmann Store Sales\train.csv'
   Test-Path '.\Rossmann Store Sales\store.csv'
   ```

   Both must say `True`. If either says `False`, check for an extra nested folder or a still zipped file. This current working folder already has the CSV files, but a new clone should perform the checks.
5. Start Docker Desktop, then follow **steps 1 through 5** below. Step 4 creates the Kafka topic before the consumer starts.

## Coming back after `docker compose down`

`docker compose down` stops and removes the containers, but **keeps** Kafka messages in its volume, HDFS files in its volumes, and dashboard results in `data/results/`. To start again from the project folder after code or design changes:

```powershell
Set-Location 'C:\Users\vinay\Desktop\bdaproject'
docker compose up -d --build
docker compose ps
Test-Path '.\data\results\latest.json'
```

If `Test-Path` says **True** and the previous run finished, open **http://localhost:3000**. Your saved result is already there; do **not** run the producer again just to view it. `--build` applies the latest UI/code changes. If nothing changed, `docker compose up -d` is enough.

If `Test-Path` says **False** and, like your first attempt, the consumer failed **before you ran the producer**, go to **step 4** below: create the topic, start the consumer, then run the producer in the second window. You do not need to clear the volumes.

If the producer had already sent **some** rows when you stopped, see [the interrupted-run instructions](LEARN_THE_PIPELINE.md#what-if-my-first-upload-was-interrupted). The fixed `--max-messages 1017209` counts messages **in the current consumer process**, so restarting it after a partial upload can otherwise leave it waiting indefinitely. Do not casually republish the CSV over a partial run.

## 1. Prerequisites

| Requirement | What to check |
| --- | --- |
| Windows computer | Use PowerShell. The commands below are written for PowerShell. |
| Docker Desktop | Install it from the [official Windows guide](https://docs.docker.com/desktop/setup/install/windows-install/), start it, and use **Linux containers** with WSL 2. |
| Network access | Needed the first time Docker downloads images and the Next.js image installs packages. |
| RAM and disk | Kafka, Hadoop, and Next.js run in separate containers. Start with roughly **8 GB of RAM available to Docker** and several GB of free disk. This is a planning estimate, not a tested minimum. |
| Kaggle files | The downloaded `train.csv` and `store.csv` must be directly in `Rossmann Store Sales/` beside `compose.yaml`. See **First setup after cloning** above. |

You do **not** need to install Python, Java, Node.js, Kafka, or Hadoop directly on Windows for this run. Docker images provide them. You do not need `test.csv` or `sample_submission.csv` for this analysis because `test.csv` has no actual `Sales` values.

Before doing anything else, open PowerShell and run:

```powershell
Set-Location 'C:\Users\vinay\Desktop\bdaproject'
docker info
docker compose version
Test-Path '.\Rossmann Store Sales\train.csv'
Test-Path '.\Rossmann Store Sales\store.csv'
```

`docker info` must show server information, and both `Test-Path` commands must print `True`. If `docker info` says it cannot connect to the engine, start Docker Desktop and try again.

## 2. Start the services

Run this from the project folder:

```powershell
docker compose up -d --build
docker compose ps
```

The first command downloads and builds the Kafka, Hadoop, Python, and Next.js images. It can take a while on the first run. `docker compose ps` should show `kafka`, `namenode`, `datanode`, `job`, `ingest`, and `web` running.

Check that Kafka responds and HDFS has a live DataNode:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list
docker compose exec job hdfs dfsadmin -report
```

The Kafka command should finish without an error; an empty topic list is normal at this point. The HDFS report should show **1 live DataNode**. Services may need a little time after `up`; repeat these checks if they are still starting. You can also open the HDFS NameNode page at `http://localhost:9870`.

## 3. Optional: check the calculation first

These small checks do **not** process your million-row dataset. They verify that 30 days at 8,000 per day versus seven days at 10,000 per day gives **+25%**, and check missing days, duplicate days, and a closed day.

```powershell
docker compose exec job python3 -m unittest discover -s /app/tests
```

Wait for `OK` before continuing. If this command fails, copy the error before trying the full run.

## 4. Load the Rossmann sales into Kafka and HDFS

Create the sales topic **before** starting the consumer. Run this once from the project folder; `--if-not-exists` also makes it safe to repeat after a restart:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic rossmann-sales-v1 --partitions 1 --replication-factor 1
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic rossmann-sales-v1
```

The description should show one partition and one replica. The consumer subscribes to `rossmann-sales-v1`; if that topic does not exist yet, it exits with `UNKNOWN_TOPIC_OR_PART` instead of waiting for the producer to create it. If you already got that error, run the two commands above, then restart the consumer command below. You do not need to rebuild the images or delete volumes.

Use **two PowerShell windows**. Both should start in the project folder:

```powershell
Set-Location 'C:\Users\vinay\Desktop\bdaproject'
```

**Window A — start the Kafka-to-HDFS consumer first:**

```powershell
docker compose exec ingest python /app/src/ingest/consumer.py --max-messages 1017209
```

Leave window A running. It will write HDFS batches and print a JSON manifest for each batch. Its row target matches the **1,017,209** rows in `train.csv`.

**Window B — publish the historical CSV into Kafka:**

```powershell
docker compose exec ingest python /app/src/ingest/producer.py
```

The producer replays old records in date order. It prints progress every 10,000 records. At the end, look for `"published": 1017209`, `"delivered": 1017209`, and no delivery failures. This is **historical replay**, not current 2026 sales.

Return to **window A**. Let the consumer finish and return to the PowerShell prompt before moving on. It may take longer than publishing because it writes many batches to HDFS. To inspect stored batches after it exits:

```powershell
docker compose exec job hdfs dfs -ls /holiday-impact/raw/ingest_date=*
```

You should see files ending in `.jsonl` and `.manifest.json`. If the producer reports fewer published rows because it rejected data, the consumer's fixed row target will not be reached. In that case, wait until it stops printing batches, press `Ctrl+C` in window A to flush the remaining batch, and inspect the reported rejected rows before analyzing.

## 5. Run MapReduce and open the dashboard

After the consumer exits, run:

```powershell
docker compose exec job python3 /app/src/jobs/run.py
```

This command generates `config/holidays.json` on the first run, then runs the deduplication, comparison, store-group summary, and daily-trend Hadoop Streaming jobs. It writes versioned outputs in HDFS and exports `data/results/latest.json` for Next.js.

Check that the export exists:

```powershell
Test-Path '.\data\results\latest.json'
```

It should print `True`. Open **http://localhost:3000** for the Results page. The site also has an **About** page that explains the project and a **Method** page that explains the comparison. Results has year, holiday type, event, and store-group filters; a sales comparison; a daily trend; and counts of included/excluded stores. The page shows the last completed run. It does not update for every Kafka message.

## 6. How to read the numbers

For a holiday dated 25 December, the default windows are:

```text
30-day baseline: 22 November to 21 December
7-day holiday:  22 December to 28 December
```

The dashboard compares **average sales amount per store per day** in those two windows. Example: baseline daily average 8,000 and holiday daily average 10,000 gives a change of `+2,000` or `+25%`.

- A recorded closed day (`Open=0`, zero sales) is included as a real zero-sales day.
- A missing store-day is **not** changed to zero. That store is excluded from the main result for that holiday; the dashboard reports exclusions.
- Only stores marked with that holiday code on the central date are eligible for the event.
- `a`, `b`, and `c` are holiday codes. The generated catalog uses code and date; you can edit display names in `config/holidays.json` after reviewing them.
- This is an **observed comparison**, not proof that the holiday caused the change. Promotions, store closures, weekday patterns, and other events may contribute.

## 7. If something fails

| Symptom | What to do |
| --- | --- |
| `docker info` cannot connect | Start Docker Desktop with Linux containers. |
| A service is not running | Run `docker compose ps` and `docker compose logs --tail=100 kafka namenode datanode job ingest web`. |
| HDFS shows 0 live DataNodes | Wait briefly; inspect `docker compose logs --tail=100 datanode namenode`. Do not publish until one DataNode is live. |
| The first build cannot download packages/images | Check network access and retry `docker compose up -d --build`. |
| Producer cannot find `train.csv` | Confirm the exact folder name and path shown in the prerequisites. |
| Consumer exits with `UNKNOWN_TOPIC_OR_PART` for `rossmann-sales-v1` | Create and describe the topic using the commands at the start of step 4, then restart the consumer. If the producer already completed, do not publish the CSV again: the consumer reads existing messages from the topic. |
| Consumer does not finish | Check the producer's `published` and `delivered` counts. The consumer stops only after its `--max-messages` count. |
| Dashboard says no analysis results | Run the MapReduce command, then check `data/results/latest.json` and `docker compose logs --tail=100 web`. |
| Port `3000` or `9870` already in use | Stop the conflicting application or change the host-side port in `compose.yaml`. |

To stop the services **while keeping Kafka and HDFS data**:

```powershell
docker compose down
```

The downloaded CSVs are not deleted by that command. Avoid `docker compose down -v` unless you intentionally want to remove the Kafka and HDFS volumes.

## Project files

| File or folder | Purpose |
| --- | --- |
| `IMPLEMENTATION.md` | Problem explanation, calculation rules, and Rossmann limitations |
| `LEARN_THE_PIPELINE.md` | Beginner guide to the commands, technologies, data flow, and restarts |
| `compose.yaml` | Local containers and volumes |
| `src/ingest/` | CSV validation, Kafka producer, and HDFS consumer |
| `src/jobs/` | Holiday catalog and MapReduce jobs |
| `web/` | Next.js dashboard, Drawably styling, and results API |
| `tests/` | Small hand-calculated checks |
| `data/results/latest.json` | Most recent completed dashboard result |

**Verification status:** The CSV headers and basic counts were inspected, and the Compose configuration was checked. The full Docker pipeline and Next.js build have **not** yet been run in this environment; use the steps above for the first manual test and keep any error output if a step fails.
