"""Run Hadoop Streaming stages against HDFS and export dashboard JSON."""

import glob
import json
import os
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/app")
JOBS = ROOT / "src/jobs"
DATA = ROOT / "data/results"
CATALOG = ROOT / "config/holidays.json"
HDFS_BASE = "/holiday-impact"


def command(args, capture=False):
    print("$", " ".join(map(str, args)), flush=True)
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def streaming_jar():
    matches = glob.glob("/opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar")
    if not matches:
        raise FileNotFoundError("Hadoop Streaming jar missing from the Hadoop image")
    return matches[0]


def stage(name, input_path, output_path, extra_files=()):
    files = [
        f"{JOBS / (name + '_mapper.py')}#{name}_mapper.py",
        f"{JOBS / (name + '_reducer.py')}#{name}_reducer.py",
        *extra_files,
    ]
    command([
        "hadoop", "jar", streaming_jar(),
        "-D", "mapreduce.framework.name=local",
        "-D", "mapreduce.job.reduces=1",
        "-files", ",".join(map(str, files)),
        "-input", input_path,
        "-output", output_path,
        "-mapper", f"python3 {name}_mapper.py",
        "-reducer", f"python3 {name}_reducer.py",
    ])


def output_rows(path):
    content = command(["hdfs", "dfs", "-cat", f"{path}/part-*"], capture=True).stdout
    return [json.loads(line.split("\t", 1)[1]) for line in content.splitlines() if "\t" in line]


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    if not CATALOG.exists():
        command([sys.executable, str(JOBS / "make_catalog.py"), "--output", str(CATALOG)])
    events = json.loads(CATALOG.read_text(encoding="utf-8"))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    base = f"{HDFS_BASE}/jobs/{run_id}"
    input_path = os.getenv("HDFS_INPUT", f"{HDFS_BASE}/raw/ingest_date=*/*.jsonl")
    command(["hdfs", "dfs", "-ls", input_path])
    stage("dedupe", input_path, f"{base}/canonical")
    stage("compare", f"{base}/canonical/part-*", f"{base}/comparison", [f"{CATALOG}#holidays.json"])
    comparisons = output_rows(f"{base}/comparison")
    included = defaultdict(list)
    for row in comparisons:
        if row["complete"]:
            included[row["event_id"]].append(row["store_id"])
    included_path = DATA / f"included-{run_id}.json"
    included_path.write_text(json.dumps(included), encoding="utf-8")
    stage("rollup", f"{base}/comparison/part-*", f"{base}/rollup", ["/data/rossmann/store.csv#store.csv"])
    stage("daily", f"{base}/canonical/part-*", f"{base}/daily", [f"{CATALOG}#holidays.json", f"{included_path}#included.json", "/data/rossmann/store.csv#store.csv"])
    result = {
        "run_id": run_id,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source": "Rossmann Store Sales train.csv",
        "measure": "store daily sales amount",
        "hdfs_run_path": base,
        "events": [{key: value for key, value in event.items() if key != "store_ids"} for event in events],
        "summary": output_rows(f"{base}/rollup"),
        "daily": output_rows(f"{base}/daily"),
    }
    run_file = DATA / f"run-{run_id}.json"
    run_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    temporary = DATA / "latest.tmp"
    temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, DATA / "latest.json")
    print(f"Exported {run_file} and latest.json")


if __name__ == "__main__":
    main()
