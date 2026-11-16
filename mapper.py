#!/usr/bin/env python3
"""Hadoop Streaming mapper.
Input : CSV lines  date,station,temperature,co2,humidity,rainfall,sea_level
Output: station|YYYY-MM <TAB> temperature,co2,1
Missing values are skipped (handled gracefully)."""
import sys

for line in sys.stdin:
    p = line.strip().split(",")
    if len(p) < 4 or p[0] == "date":
        continue
    try:
        month = p[0][:7]
        temp = float(p[2])
        co2 = float(p[3]) if p[3] else None
    except ValueError:
        continue
    print(f"{p[1]}|{month}\t{temp},{co2 if co2 is not None else ''},1")
