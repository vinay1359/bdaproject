"""Create dated holiday events from the observed Rossmann holiday flags."""

import argparse
import csv
import json
from collections import defaultdict


LABELS = {"a": "Public holiday", "b": "Easter holiday", "c": "Christmas holiday"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/data/rossmann/train.csv")
    parser.add_argument("--output", default="/app/config/holidays.json")
    args = parser.parse_args()
    observed = defaultdict(set)
    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            code = row["StateHoliday"]
            if code in LABELS:
                observed[(row["Date"], code)].add(int(row["Store"]))
    events = []
    for (day, code), stores in sorted(observed.items()):
        events.append({
            "id": f"{day}-{code}",
            "date": day,
            "code": code,
            "name": f"{LABELS[code]} — {day}",
            "store_ids": sorted(stores),
        })
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(events, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"catalog: {len(events)} dated holiday events")


if __name__ == "__main__":
    main()
