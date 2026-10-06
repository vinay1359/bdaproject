"""Calculate group comparison from eligible store-day totals."""

import json
import sys


def result(key, values):
    event_id, group = key.split("|", 1)
    complete = [row for row in values if row["complete"]]
    baseline_sum = sum(row["baseline_sales"] for row in complete)
    holiday_sum = sum(row["holiday_sales"] for row in complete)
    stores = len(complete)
    baseline_mean = baseline_sum / (stores * 30) if stores else None
    holiday_mean = holiday_sum / (stores * 7) if stores else None
    delta = holiday_mean - baseline_mean if stores else None
    change = 100 * delta / baseline_mean if stores and baseline_mean else None
    return {
        "event_id": event_id, "group": group,
        "eligible_stores": len(values), "included_stores": stores,
        "excluded_stores": len(values) - stores,
        "baseline_sales": baseline_sum, "holiday_sales": holiday_sum,
        "baseline_daily_mean": baseline_mean, "holiday_daily_mean": holiday_mean,
        "delta_daily": delta, "percent_change": change,
        "baseline_promo_days": sum(row["baseline_promo_days"] for row in complete),
        "holiday_promo_days": sum(row["holiday_promo_days"] for row in complete),
        "baseline_closed_days": sum(row["baseline_closed_days"] for row in complete),
        "holiday_closed_days": sum(row["holiday_closed_days"] for row in complete),
    }


previous = None
values = []
for line in sys.stdin:
    try:
        key, payload = line.rstrip("\n").split("\t", 1)
        if key != previous and previous is not None:
            print(f'{previous}\t{json.dumps(result(previous, values), separators=(",", ":"))}')
            values = []
        values.append(json.loads(payload))
        previous = key
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"bad rollup row: {exc}", file=sys.stderr)
if previous is not None:
    print(f'{previous}\t{json.dumps(result(previous, values), separators=(",", ":"))}')
