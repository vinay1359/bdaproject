"""Map store comparisons to all-store and store-segment groups."""

import csv
import json
import sys

with open("store.csv", newline="", encoding="utf-8-sig") as handle:
    stores = {int(row["Store"]): row for row in csv.DictReader(handle)}

for line in sys.stdin:
    try:
        _, payload = line.rstrip("\n").split("\t", 1)
        record = json.loads(payload)
        store = stores[record["store_id"]]
        groups = ["all", f'store_type:{store["StoreType"]}', f'assortment:{store["Assortment"]}']
        for group in groups:
            print(f'{record["event_id"]}|{group}\t{payload}')
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"bad store comparison: {exc}", file=sys.stderr)
