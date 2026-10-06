"""Map canonical rows to daily event averages for complete stores only."""

import csv
import json
import sys
from collections import defaultdict
from datetime import date, timedelta

with open("holidays.json", encoding="utf-8") as handle:
    events = json.load(handle)
with open("included.json", encoding="utf-8") as handle:
    included = {key: set(value) for key, value in json.load(handle).items()}
with open("store.csv", newline="", encoding="utf-8-sig") as handle:
    stores = {int(row["Store"]): row for row in csv.DictReader(handle)}
by_day = defaultdict(list)
for event in events:
    anchor = date.fromisoformat(event["date"])
    eligible = included.get(event["id"], set())
    for offset in range(-33, 4):
        day = (anchor + timedelta(days=offset)).isoformat()
        by_day[day].append((event["id"], offset, eligible))
for line in sys.stdin:
    try:
        _, payload = line.rstrip("\n").split("\t", 1)
        row = json.loads(payload)
        for event_id, offset, eligible in by_day.get(row["date"], []):
            if row["store_id"] in eligible:
                store = stores[row["store_id"]]
                for group in ("all", f'store_type:{store["StoreType"]}', f'assortment:{store["Assortment"]}'):
                    print(f'{event_id}|{group}|{offset + 33:02d}\t{float(row["sales"])}')
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"bad daily row: {exc}", file=sys.stderr)
