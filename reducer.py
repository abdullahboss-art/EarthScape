#!/usr/bin/env python3
"""Hadoop Streaming reducer: monthly average temperature and CO2 per station."""
import sys

cur, t_sum, c_sum, t_n, c_n = None, 0.0, 0.0, 0, 0


def flush():
    if cur:
        t = round(t_sum / t_n, 3) if t_n else ""
        c = round(c_sum / c_n, 3) if c_n else ""
        print(f"{cur}\t{t}\t{c}\t{t_n}")


for line in sys.stdin:
    key, val = line.rstrip("\n").split("\t")
    t, c, _ = val.split(",")
    if key != cur:
        flush()
        cur, t_sum, c_sum, t_n, c_n = key, 0.0, 0.0, 0, 0
    t_sum += float(t); t_n += 1
    if c:
        c_sum += float(c); c_n += 1
flush()
