"""Calculate a store's two window totals and mark incomplete coverage."""

import json
import sys


def result(key, values):
    event_id, store_id = key.split("|", 1)
    days = {"baseline": set(), "holiday": set()}
    totals = {"baseline": 0.0, "holiday": 0.0}
    promo_days = {"baseline": 0, "holiday": 0}
    closed_days = {"baseline": 0, "holiday": 0}
    for value in values:
        window, day, sales, is_open, promo = json.loads(value)
        if day in days[window]:
            continue
        days[window].add(day)
        totals[window] += sales
        promo_days[window] += promo
        closed_days[window] += 1 - is_open
    baseline_count = len(days["baseline"])
    holiday_count = len(days["holiday"])
    complete = baseline_count == 30 and holiday_count == 7
    baseline_mean = totals["baseline"] / 30 if complete else None
    holiday_mean = totals["holiday"] / 7 if complete else None
    delta = holiday_mean - baseline_mean if complete else None
    change = 100 * delta / baseline_mean if complete and baseline_mean else None
    return {
        "event_id": event_id, "store_id": int(store_id), "complete": complete,
        "baseline_days": baseline_count, "holiday_days": holiday_count,
        "baseline_sales": totals["baseline"], "holiday_sales": totals["holiday"],
        "baseline_daily_mean": baseline_mean, "holiday_daily_mean": holiday_mean,
        "delta_daily": delta, "percent_change": change,
        "baseline_promo_days": promo_days["baseline"], "holiday_promo_days": promo_days["holiday"],
        "baseline_closed_days": closed_days["baseline"], "holiday_closed_days": closed_days["holiday"],
    }


previous = None
values = []
for line in sys.stdin:
    try:
        key, value = line.rstrip("\n").split("\t", 1)
        if key != previous and previous is not None:
            print(f'{previous}\t{json.dumps(result(previous, values), separators=(",", ":"))}')
            values = []
        values.append(value)
        previous = key
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"bad compare row: {exc}", file=sys.stderr)
if previous is not None:
    print(f'{previous}\t{json.dumps(result(previous, values), separators=(",", ":"))}')
