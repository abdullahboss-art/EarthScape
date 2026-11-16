"""MongoDB <-> Hadoop bridge.  Run from the project root (EarthScape_py):
    python hadoop/bridge.py export     MongoDB -> data/climate_for_hdfs.csv + data/hdfs_partitioned/year=../station=..
    python hadoop/bridge.py import     data/hadoop_output/part-00000.tsv -> MongoDB (Pipeline Monitor)
    python hadoop/bridge.py demo       NO Docker: export -> mapper|sort|reducer locally -> import
"""
import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
CSV_IN = DATA / "climate_for_hdfs.csv"
PART_DIR = DATA / "hdfs_partitioned"
OUT_DIR = DATA / "hadoop_output"
OUT = OUT_DIR / "part-00000.tsv"
COLS = ["date", "station", "temperature", "co2", "humidity", "rainfall", "sea_level", "aqi"]
JOB = "Hadoop: monthly avg temperature & CO2 per station"


def get_db(allow_mock=False):
    import analytics
    db = analytics.get_db()
    if type(db).__module__.startswith("mongomock") and not allow_mock:
        sys.exit("MongoDB is not running (analytics fell back to a temporary in-memory DB). Start MongoDB and retry.")
    return db


def export_csv(db):
    """Writes one flat CSV (for the local demo) AND a partitioned tree for HDFS:
    data/hdfs_partitioned/year=YYYY/station=NAME/climate.csv"""
    DATA.mkdir(exist_ok=True)
    shutil.rmtree(PART_DIR, ignore_errors=True)
    handles, writers, n = [], {}, 0
    flat = open(CSV_IN, "w", newline="", encoding="utf-8")
    fw = csv.writer(flat, lineterminator="\n")
    fw.writerow(COLS)
    try:
        for r in db.records.find({"source": {"$ne": "simulator"}}, {"_id": 0}).sort("date", 1):
            d = r.get("date")
            day = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
            row = [day, r.get("station", "")] + ["" if v is None or v != v else v for v in (r.get(c) for c in COLS[2:])]
            fw.writerow(row)
            key = (day[:4], re.sub(r"[^A-Za-z0-9]+", "_", str(r.get("station", ""))).strip("_") or "unknown")
            if key not in writers:
                folder = PART_DIR / f"year={key[0]}" / f"station={key[1]}"
                folder.mkdir(parents=True, exist_ok=True)
                h = open(folder / "climate.csv", "w", newline="", encoding="utf-8")
                handles.append(h)
                writers[key] = csv.writer(h, lineterminator="\n")
                writers[key].writerow(COLS)
            writers[key].writerow(row)
            n += 1
    finally:
        flat.close()
        for h in handles:
            h.close()
    print(f"Exported {n} records -> {CSV_IN} and {len(writers)} partitions in {PART_DIR}")
    return n


def run_local():
    """Same as `cat csv | mapper.py | sort | reducer.py` (what Hadoop Streaming does)."""
    t0 = time.time()
    with open(CSV_IN, "rb") as f:
        m = subprocess.run([sys.executable, str(ROOT / "mapper.py")], stdin=f, capture_output=True, check=True)
    lines = sorted(m.stdout.decode().splitlines(), key=lambda s: s.split("\t")[0])
    data = ("\n".join(lines) + "\n").encode() if lines else b""
    r = subprocess.run([sys.executable, str(ROOT / "reducer.py")], input=data, capture_output=True, check=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(r.stdout)
    return round(time.time() - t0, 2)


def import_output(db, engine, seconds):
    if not OUT.exists():
        sys.exit(f"{OUT} not found. Run the Hadoop job first.")
    docs = []
    for line in OUT.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 4:
            continue
        num = lambda s: float(s) if s != "" else None
        docs.append({"job": JOB, "key": p[0], "value": num(p[1]), "co2": num(p[2]), "count": int(p[3])})
    db.pipeline_results.delete_many({"job": JOB})
    if docs:
        db.pipeline_results.insert_many(docs)
    records = max(sum(1 for _ in open(CSV_IN, encoding="utf-8")) - 1, 0) if CSV_IN.exists() else 0
    db.pipeline_jobs.insert_one({"name": JOB, "status": "Completed", "seconds": seconds, "records": records,
                                 "error": "", "user": "cli", "engine": engine, "time": datetime.datetime.utcnow()})
    print(f"Imported {len(docs)} result rows into MongoDB (engine: {engine}).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["export", "import", "demo"])
    ap.add_argument("--engine", default="hadoop")
    ap.add_argument("--seconds", type=float, default=0)
    ap.add_argument("--allow-mock", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    db = get_db(a.allow_mock)
    if a.cmd == "export":
        export_csv(db)
    elif a.cmd == "import":
        import_output(db, a.engine, a.seconds)
    else:
        export_csv(db)
        import_output(db, "streaming-local", run_local())
