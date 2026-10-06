"""Assign each canonical store-day to eligible holiday and baseline windows."""

import json
import sys
from collections import defaultdict
from datetime import date, timedelta

with open("holidays.json", encoding="utf-8") as handle:
    events = json.load(handle)
by_day = defaultdict(list)
for event in events:
    anchor = date.fromisoformat(event["date"])
    eligible = set(event["store_ids"])
    for offset in range(-33, 4):
        day = (anchor + timedelta(days=offset)).isoformat()
        window = "holiday" if offset >= -3 else "baseline"
        by_day[day].append((event["id"], eligible, window))

for line in sys.stdin:
    try:
        _, payload = line.rstrip("\n").split("\t", 1)
        row = json.loads(payload)
        for event_id, eligible, window in by_day.get(row["date"], []):
            if int(row["store_id"]) in eligible:
                value = [window, row["date"], float(row["sales"]), int(row["open"]), int(row["promo"])]
                print(f'{event_id}|{int(row["store_id"]):06d}\t{json.dumps(value, separators=(",", ":"))}')
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"bad canonical row: {exc}", file=sys.stderr)
