"""Publish historical Rossmann sales to Kafka, oldest dates first."""

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter
from itertools import chain

from confluent_kafka import Producer

from common import parse_row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/data/rossmann/train.csv")
    parser.add_argument("--limit", type=int, default=0, help="0 means the full file")
    parser.add_argument("--pause-ms", type=float, default=0)
    args = parser.parse_args()
    producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")})
    topic = os.getenv("KAFKA_TOPIC", "rossmann-sales-v1")
    counts = Counter()

    def delivery(error, _message):
        counts["failed"] += bool(error)
        counts["delivered"] += not bool(error)
        if error and counts["failed"] <= 10:
            print(f"Kafka delivery failed: {error}", file=sys.stderr)

    # Kaggle train.csv is newest-first. Keep only source lines in memory, not 1M dictionaries.
    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        header = handle.readline()
        source_lines = handle.readlines()
    reader = csv.DictReader(chain([header], reversed(source_lines)))
    previous_date = None
    for line_number, row in enumerate(reader, 2):
        try:
            record = parse_row(row)
            if previous_date and record["date"] < previous_date:
                raise ValueError("source file is not newest-first as expected")
            previous_date = record["date"]
        except (ValueError, TypeError) as exc:
            counts["rejected"] += 1
            if counts["rejected"] <= 10:
                print(f"replay row {line_number}: {exc}", file=sys.stderr)
            continue
        producer.produce(
            topic,
            key=f'{record["store_id"]}|{record["date"]}'.encode(),
            value=json.dumps(record, separators=(",", ":")).encode(),
            on_delivery=delivery,
        )
        counts["published"] += 1
        if counts["published"] % 10000 == 0:
            producer.flush()
            print(f'published {counts["published"]}', flush=True)
        else:
            producer.poll(0)
        if args.pause_ms:
            time.sleep(args.pause_ms / 1000)
        if args.limit and counts["published"] >= args.limit:
            break
    producer.flush()
    print(json.dumps(dict(counts), sort_keys=True))
    if counts["failed"]:
        raise SystemExit(f'{counts["failed"]} messages failed delivery; do not run the analysis yet')


if __name__ == "__main__":
    main()
