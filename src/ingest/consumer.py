"""Land Kafka batches in HDFS through WebHDFS before committing offsets."""

import argparse
import json
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from confluent_kafka import Consumer, KafkaException


class WebHDFS:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, op, **kwargs):
        url = f"{self.base}/webhdfs/v1/{quote(path.lstrip('/'), safe='/')}"
        response = self.session.request(
            method, url, params={"op": op, **kwargs.pop("params", {})},
            timeout=90, **kwargs,
        )
        response.raise_for_status()
        return response

    def mkdir(self, path):
        self.request("PUT", path, "MKDIRS")

    def create(self, path, content):
        self.request("PUT", path, "CREATE", params={"overwrite": "false"}, data=content)

    def rename(self, source, destination):
        result = self.request("PUT", source, "RENAME", params={"destination": destination}).json()
        if not result.get("boolean"):
            raise RuntimeError(f"HDFS rename failed: {source} -> {destination}")


def land_batch(hdfs, rows, root):
    batch_id = f'{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:10]}'
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parent = f"{root}/ingest_date={day}"
    hdfs.mkdir(parent)
    offsets = defaultdict(lambda: [None, None])
    payload = []
    for message in rows:
        payload.append(message.value().decode("utf-8"))
        key = f"{message.topic()}:{message.partition()}"
        pair = offsets[key]
        pair[0] = message.offset() if pair[0] is None else min(pair[0], message.offset())
        pair[1] = message.offset() if pair[1] is None else max(pair[1], message.offset())
    temporary = f"{parent}/.{batch_id}.tmp"
    final = f"{parent}/{batch_id}.jsonl"
    hdfs.create(temporary, ("\n".join(payload) + "\n").encode())
    hdfs.rename(temporary, final)
    manifest = {"batch": batch_id, "rows": len(rows), "offsets": dict(offsets), "hdfs_path": final}
    hdfs.create(f"{parent}/{batch_id}.manifest.json", json.dumps(manifest).encode())
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-messages", type=int, default=0, help="stop after N messages; 0 runs continuously")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()
    hdfs = WebHDFS(os.getenv("WEBHDFS_URL", "http://namenode:9870"))
    root = os.getenv("HDFS_RAW_ROOT", "/holiday-impact/raw")
    consumer = Consumer({
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"),
        "group.id": os.getenv("KAFKA_GROUP", "holiday-impact-hdfs-v1"),
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([os.getenv("KAFKA_TOPIC", "rossmann-sales-v1")])
    pending = []
    received = 0
    last_flush = time.monotonic()
    try:
        while not args.max_messages or received < args.max_messages:
            message = consumer.poll(1)
            if message is not None:
                if message.error():
                    raise KafkaException(message.error())
                pending.append(message)
                received += 1
            if pending and (len(pending) >= args.batch_size or time.monotonic() - last_flush >= 5 or (args.max_messages and received >= args.max_messages)):
                manifest = land_batch(hdfs, pending, root)
                consumer.commit(asynchronous=False)
                print(json.dumps(manifest), flush=True)
                pending.clear()
                last_flush = time.monotonic()
    except KeyboardInterrupt:
        pass
    finally:
        if pending:
            manifest = land_batch(hdfs, pending, root)
            consumer.commit(asynchronous=False)
            print(json.dumps(manifest), flush=True)
        consumer.close()


if __name__ == "__main__":
    main()
