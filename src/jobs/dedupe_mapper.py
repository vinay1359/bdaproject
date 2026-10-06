"""Map raw HDFS JSONL to one key per store and date."""

import json
import sys

for line in sys.stdin:
    try:
        row = json.loads(line)
        key = f'{int(row["store_id"]):06d}|{row["date"]}'
        if float(row["sales"]) < 0:
            raise ValueError("negative sales")
        print(f'{key}\t{json.dumps(row, sort_keys=True, separators=(",", ":"))}')
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"rejected raw row: {exc}", file=sys.stderr)
