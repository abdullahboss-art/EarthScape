"""Creates climate_sample.csv  (6 stations, 3 years daily, with missing values and a few extreme readings)."""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
STATIONS = {"Karachi": (27, 5, 1, 95), "London": (11, 7, 1, 40), "New York": (13, 12, 1, 45),
            "Tokyo": (16, 10, 1, 50), "Sydney": (18, 5, -1, 30), "Delhi": (25, 10, 1, 105)}   # mean, amplitude, hemisphere, AQI
dates = pd.date_range("2023-01-01", "2025-12-31", freq="D")
t = np.arange(len(dates))
frames = []
for st, (base, amp, hemi, aqi0) in STATIONS.items():
    hum = np.clip(60 + 15 * np.cos(2 * np.pi * t / 365) + rng.normal(0, 6, len(t)), 5, 100)
    frames.append(pd.DataFrame({
        "date": dates, "station": st,
        "temperature": (base + hemi * amp * np.sin(2 * np.pi * (t - 100) / 365) + t * 0.0006 + rng.normal(0, 1.4, len(t))).round(2),
        "co2": (415 + t * 0.0075 + 2 * np.sin(2 * np.pi * t / 365) + rng.normal(0, 1, len(t))).round(2),
        "humidity": hum.round(1),
        "rainfall": (np.clip(rng.gamma(0.5, 7, len(t)) * (hum > 62), 0, None)).round(1),
        "sea_level": (50 + t * 0.0099 + rng.normal(0, 0.6, len(t))).round(2),        # ~3.6 mm per year
        "aqi": np.clip(aqi0 + 15 * np.cos(2 * np.pi * (t - 20) / 365) + rng.normal(0, 12, len(t)), 5, 400).round(0)}))
out = pd.concat(frames, ignore_index=True)
out.loc[rng.choice(len(out), 100, replace=False), "temperature"] = np.nan          # missing values
out.loc[rng.choice(len(out), 60, replace=False), "co2"] = np.nan
late = out.index[out["date"] >= "2025-12-01"].to_numpy()
out.loc[rng.choice(late, 3, replace=False), "temperature"] = 47.5                    # shows up as alerts
out.loc[rng.choice(len(out), 5, replace=False), "temperature"] = 52.0
out.loc[rng.choice(late, 2, replace=False), "aqi"] = 260
path = os.path.join(os.path.dirname(__file__), "climate_sample.csv")
out.to_csv(path, index=False)
print("written", path, len(out), "rows")
