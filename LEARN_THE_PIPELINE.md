# Learn the Rossmann pipeline

This is a local learning project. You do not need to know Kafka or Hadoop to run it. The short version: a Python program reads old sales rows, Kafka passes them along, HDFS stores them, MapReduce calculates holiday comparisons, and a Next.js page shows the finished numbers.

## The whole journey

```text
Rossmann train.csv (historical sales, 2013–2015)
    ↓ Python producer: reads and checks each row
Kafka topic rossmann-sales-v1: a numbered stream of messages
    ↓ Python consumer: reads messages and writes batches
HDFS /holiday-impact/raw/: stored JSON lines plus batch manifests
    ↓ Hadoop Streaming MapReduce: dedupe → compare → roll up → daily trend
data/results/latest.json: finished answer on your computer
    ↓ Next.js reads it and serves the page
http://localhost:3000: dashboard in your browser
```

`store.csv` also enters the MapReduce step. It describes each store's type and assortment so the dashboard can show groups. It does **not** provide sales by product category.

## What each piece means

| Name | Think of it as | What it does here |
| --- | --- | --- |
| Docker | A way to run packaged programs in separate boxes called containers | Runs the six project services without installing each program on Windows. |
| Docker Compose | A starter and manager for several containers | Reads `compose.yaml` and starts `kafka`, `namenode`, `datanode`, `ingest`, `job`, and `web`. |
| Python | The language used for data scripts | Reads the CSV, checks rows, publishes and consumes messages, and implements the MapReduce steps. |
| Kafka | An ordered, durable message log | Holds sales records in a **topic** named `rossmann-sales-v1`. The producer writes messages; the consumer reads them. A topic is like a named channel. |
| Kafka offset | A position number in a topic partition | Lets the consumer record how far it has read. It commits its position after writing a batch to HDFS. |
| HDFS | Hadoop's file storage | Stores raw sales batches and job outputs. This local setup has one NameNode (directory/index) and one DataNode (file blocks). |
| Hadoop MapReduce | A way to process many records in stages | A **mapper** turns input rows into key/value pairs. Hadoop groups and sorts by key. A **reducer** combines each group into an answer. |
| Hadoop Streaming | MapReduce's interface for ordinary programs | Allows our mappers and reducers to be Python programs. This project uses Hadoop's **local execution mode** with one reducer. |
| Next.js + React + TypeScript | The web application | Reads `latest.json`, serves the results API and renders the dashboard. TypeScript helps catch UI code mistakes. |
| ECharts | Charting library | Draws the daily sales line. |
| Drawably | UI decoration library | Adds a restrained hand-drawn underline and reset control. The rest of the dashboard uses standard HTML and CSS. |

Kafka is used here to **replay old data**. It does not mean we have a live sales feed. The webpage displays the last completed MapReduce run, so sending another Kafka message by itself does not update the displayed results.

## Why there are two PowerShell windows

The consumer is meant to keep listening while the producer sends messages. Window A runs the consumer; Window B runs the producer. Leave A open until it returns to the PowerShell prompt. A printed JSON manifest means one batch was written to HDFS. When the producer prints its final counts, check that `published` and `delivered` are both **1017209** and `failed` is zero or absent.

## The commands, one by one

Run these in **PowerShell**, from the project folder. You can copy the commands from [README.md](README.md); this section explains them.

| Command | Plain meaning |
| --- | --- |
| `Set-Location 'C:\Users\vinay\Desktop\bdaproject'` | Move the PowerShell window into this project folder. Relative paths and Compose commands then refer to this project. |
| `docker info` | Ask Docker Desktop whether its engine is running. If it cannot connect, start Docker Desktop. |
| `docker compose version` | Show the installed Compose version. It does not start anything. |
| `Test-Path '.\Rossmann Store Sales\train.csv'` | Check whether the main sales file exists. `True` means yes. |
| `Test-Path '.\Rossmann Store Sales\store.csv'` | Check whether the store information file exists. |
| `docker compose up -d --build` | Build the project images if needed and start all six services in the background. Use this after changing the UI or code. `-d` means detached. |
| `docker compose up -d` | Start services using existing images. Use when you only want to resume without applying code changes. |
| `docker compose ps` | Show which project containers are running. |
| `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list` | Ask the Kafka service to list topic names. Empty output is normal before the topic is created. `exec kafka` means run the following program **inside** the running Kafka container. |
| `docker compose exec job hdfs dfsadmin -report` | Ask HDFS about its nodes. Look for **1 live DataNode** before loading data. |
| `docker compose exec job python3 -m unittest discover -s /app/tests` | Run small calculation tests in the `job` container. These use examples, not the million-row file. |
| `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic rossmann-sales-v1 --partitions 1 --replication-factor 1` | Create the sales topic if missing. This local broker uses one partition and one replica. Safe to repeat because of `--if-not-exists`. Do this before starting the consumer. |
| `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic rossmann-sales-v1` | Confirm that the topic exists and show its partition and replica information. |
| `docker compose exec ingest python /app/src/ingest/consumer.py --max-messages 1017209` | In Window A, start the Kafka-to-HDFS reader. It stops after reading 1,017,209 messages **in that launch**. `exec ingest` runs the Python script inside the ingest container. |
| `docker compose exec ingest python /app/src/ingest/producer.py` | In Window B, read `train.csv` and publish valid rows to the Kafka topic. This is the full historical replay. Run it once for a clean upload. |
| `docker compose exec job hdfs dfs -ls /holiday-impact/raw/ingest_date=*` | List raw batch files in HDFS. The `*` matches all ingestion dates. Look for `.jsonl` data files and `.manifest.json` batch descriptions. |
| `docker compose exec job python3 /app/src/jobs/run.py` | Run the holiday catalog setup and MapReduce stages. Export the finished result to `data/results/latest.json`. Wait for it to finish before viewing the result. |
| `Test-Path '.\data\results\latest.json'` | Check whether a finished dashboard result exists on your computer. `True` means the web service has a result to read. |
| `docker compose logs --tail=100 kafka namenode datanode job ingest web` | Print the last 100 log lines for each named service to help diagnose a startup problem. |
| `docker compose logs --tail=100 datanode namenode` | Narrow the logs to the two HDFS services when there is no live DataNode. |
| `docker compose logs --tail=100 web` | Show recent web container messages if the dashboard is not loading. |
| `docker compose down` | Stop and remove the containers. **Keeps** Kafka and HDFS volumes and files on your computer. |

`http://localhost:9870` is the HDFS NameNode information page. `http://localhost:3000` is the dashboard. `localhost` means your own computer. Opening a URL is separate from running a PowerShell command.

The README also mentions pressing **Ctrl+C** in Window A if the producer rejected rows and the consumer cannot reach its target. This interrupts the consumer and makes it flush its remaining in-memory batch before exiting. Do that only after the producer has finished and the consumer has stopped printing batches.

## What happens inside MapReduce

1. **Dedupe:** repeated uploads may create two copies of a store/day. The first job chooses one canonical record for each store and date so the sale is not counted twice.
2. **Compare:** for each eligible store and holiday, calculate the average of the preceding 30 days and the seven-day holiday window. A store missing any required day is excluded from that event's main comparison.
3. **Roll up:** combine stores into overall and store-type/assortment summaries using `store.csv`.
4. **Daily trend:** calculate the points for the line chart.
5. **Export:** save the finished answer to `data/results/latest.json`. The page reads this file; it does not query Kafka or HDFS directly.

For a simple example, a 30-day average of 8,000 and a seven-day average of 10,000 is an observed **+25%** change: `(10,000 - 8,000) / 8,000 × 100`. This is an association, not proof that the holiday caused it. See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the exact data rules.

## Coming back tomorrow after a completed run

If you ran `docker compose down` after the pipeline **finished**, use:

```powershell
Set-Location 'C:\Users\vinay\Desktop\bdaproject'
docker compose up -d --build
docker compose ps
Test-Path '.\data\results\latest.json'
```

Then open `http://localhost:3000`. There is no need to run the producer, consumer, or MapReduce again just to see the saved report. If you changed only the dashboard, `--build` is what puts your new UI into the web image.

## What if my first upload was interrupted?

First check whether the producer ever ran. If the consumer failed with `UNKNOWN_TOPIC_OR_PART` **before you started the producer**, no sales messages were uploaded. Start the services, create the topic, then follow step 4 of the README normally.

If the producer sent only **part** of the file, the simplest repeatable learning path is a clean replay. This intentionally removes the project's **Kafka and HDFS volume data**; it also removes any completed HDFS job outputs, so use it only when you want to restart the data pipeline from scratch:

```powershell
docker compose down -v
docker compose up -d --build
```

Then follow README steps 2 through 5: check HDFS, create the topic, start the consumer in Window A, publish once in Window B, wait for the consumer, and run MapReduce. `down -v` does **not** remove the original CSV files. It also does **not** remove `data/results/latest.json`, which is a normal file on your computer; the next successful MapReduce run replaces it. Until then, an old report may still appear in the dashboard.

If the producer **fully completed** and only the consumer was interrupted, the messages remain in Kafka after `docker compose down`. Avoid running the producer again. The existing consumer group resumes from its committed offset, but the fixed `--max-messages 1017209` target no longer matches its remaining message count. You can run the consumer **without** `--max-messages`, wait until it stops writing new batch manifests, then press **Ctrl+C** to flush and exit before running MapReduce:

```powershell
docker compose exec ingest python /app/src/ingest/consumer.py
```

That path requires checking the HDFS batches and producer delivery count carefully. For a first learning run where you are unsure what completed, the clean replay above is easier to reason about. Do not run `down -v` when you want to preserve the existing Kafka/HDFS data.
