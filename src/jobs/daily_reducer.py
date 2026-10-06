"""Reduce daily sales to a mean across complete eligible stores."""

import json
import sys


def result(key, total, count):
    event_id, group, index = key.split("|", 2)
    offset = int(index) - 33
    return {"event_id": event_id, "group": group, "day_offset": offset, "window": "holiday" if offset >= -3 else "baseline", "sales_total": total, "stores": count, "sales_per_store": total / count if count else None}


previous = None
total = 0.0
count = 0
for line in sys.stdin:
    try:
        key, payload = line.rstrip("\n").split("\t", 1)
        if key != previous and previous is not None:
            print(f'{previous}\t{json.dumps(result(previous, total, count), separators=(",", ":"))}')
            total = 0.0
            count = 0
        total += float(payload)
        count += 1
        previous = key
    except ValueError as exc:
        print(f"bad daily mapped row: {exc}", file=sys.stderr)
if previous is not None:
    print(f'{previous}\t{json.dumps(result(previous, total, count), separators=(",", ":"))}')
