"""Keep one deterministic version of each store-day after Kafka replay."""

import sys

previous = None
chosen = None
for line in sys.stdin:
    try:
        key, value = line.rstrip("\n").split("\t", 1)
    except ValueError:
        continue
    if key != previous and previous is not None:
        print(f"{previous}\t{chosen}")
        chosen = None
    if chosen is not None and chosen != value:
        print(f"conflicting duplicate for {key}; choosing lexical maximum", file=sys.stderr)
    chosen = value if chosen is None or value > chosen else chosen
    previous = key
if previous is not None:
    print(f"{previous}\t{chosen}")
