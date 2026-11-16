"""Data cleaning, KPIs, forecast, anomaly detection and alert rules (all the data science in one file)."""
import datetime
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

NUM = ["temperature", "co2", "humidity", "rainfall", "sea_level", "aqi"]
DEFAULT_TH = {"temperature": {"max": 45, "min": -30}, "co2": {"max": 450}, "aqi": {"max": 150}, "rainfall": {"max": 200}}
TITLES = {"temperature": "Extreme Heat Alert", "co2": "Rising CO₂ Levels", "aqi": "Poor Air Quality", "rainfall": "Heavy Rain Forecast"}
_cache = {"n": None, "df": None}
_db = None


def get_db():
    """MongoDB if it is running, otherwise a temporary in-memory database (data lost when the app stops)."""
    global _db
    if _db is None:
        if os.getenv("USE_MOCK_DB") != "1":
            try:
                from pymongo import MongoClient
                c = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=1500)
                c.admin.command("ping")
                _db = c["earthscape"]
            except Exception:
                print("!! MongoDB not found - using a TEMPORARY in-memory database.")
        if _db is None:
            import mongomock
            _db = mongomock.MongoClient()["earthscape"]
    return _db


# ---------------------------------------------------------------- loading / cleaning
def clean(df):
    df.columns = [c.strip().lower() for c in df.columns]
    for need in ("date", "station", "temperature"):
        if need not in df.columns:
            raise ValueError(f"Column '{need}' is missing. Needed: date, station, temperature")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "station"]).sort_values(["station", "date"])
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    # missing values: interpolate inside each station
    df[NUM] = df.groupby("station")[NUM].transform(lambda s: s.interpolate(limit_direction="both"))
    return df[["date", "station"] + NUM]


def save(db, df):
    recs = df.astype(object).where(df.notna(), None).to_dict("records")
    for r in recs:
        r["date"] = pd.Timestamp(r["date"]).to_pydatetime()
    db.records.insert_many(recs)
    return len(recs)


def load(db):
    n = db.records.count_documents({})
    if _cache["n"] != n:
        df = pd.DataFrame(list(db.records.find({}, {"_id": 0})))
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            for c in NUM:
                df[c] = pd.to_numeric(df.get(c), errors="coerce")
            df = df.sort_values("date").reset_index(drop=True)
        _cache.update(n=n, df=df)
    return _cache["df"].copy()


# ---------------------------------------------------------------- dashboard numbers
def _mean(d, f):
    return None if d is None or d.empty or d[f].notna().sum() == 0 else float(d[f].mean())


def monthly(df, field):
    s = df.set_index("date")[field].resample("MS").mean().dropna()
    return [(t.strftime("%Y-%m"), round(float(v), 3)) for t, v in s.items()]


def kpis(df, days):
    end = df["date"].max()
    cur = df if not days else df[df["date"] > end - pd.Timedelta(days=days)]
    prev = None if not days else df[(df["date"] <= end - pd.Timedelta(days=days)) & (df["date"] > end - pd.Timedelta(days=2 * days))]
    out = {}
    for f in ("temperature", "co2", "aqi"):
        v, p = _mean(cur, f), _mean(prev, f)
        out[f] = {"value": None if v is None else round(v, 1),
                  "change": None if (v is None or p is None) else round(v - p, 2),
                  "pct": None if (v is None or not p) else round((v - p) / p * 100, 1)}
    m = monthly(df, "sea_level") if df["sea_level"].notna().any() else []
    rate = None
    if len(m) >= 6:
        y = np.array([v for _, v in m])
        rate = round(float(LinearRegression().fit(np.arange(len(y)).reshape(-1, 1), y).coef_[0]) * 12, 2)
    out["sea_level"] = {"value": rate}
    out["aqi"]["label"] = aqi_label(out["aqi"]["value"])
    return out


def aqi_label(v):
    if v is None:
        return ""
    for lim, name in ((50, "Good"), (100, "Moderate"), (150, "Unhealthy for some"), (200, "Unhealthy")):
        if v <= lim:
            return name
    return "Very unhealthy"


def _features(periods, t0):
    """Time index + month-of-year dummies, so the forecast keeps the seasonal pattern."""
    t = np.array([(p - t0).n for p in periods])
    dummies = np.eye(12)[np.array([p.month for p in periods]) - 1][:, 1:]
    return np.column_stack([t, dummies])


def trend(df, field, ahead=12):
    """Monthly average + forecast (linear trend + seasonality when there are 2+ years of data)."""
    m = monthly(df, field) if df[field].notna().any() else []
    if len(m) < 6:
        return {"labels": [k for k, _ in m], "history": [v for _, v in m], "forecast": [], "slope": None}
    periods = pd.PeriodIndex([k for k, _ in m], freq="M")
    y = np.array([v for _, v in m])
    seasonal = len(m) >= 24
    X = _features(periods, periods[0]) if seasonal else np.arange(len(y)).reshape(-1, 1)
    lr = LinearRegression().fit(X, y)
    future = pd.PeriodIndex([periods[-1] + i + 1 for i in range(ahead)])
    Xf = _features(future, periods[0]) if seasonal else np.arange(len(y), len(y) + ahead).reshape(-1, 1)
    fc = [round(float(v), 3) for v in lr.predict(Xf)]
    return {"labels": [k for k, _ in m] + [str(p) for p in future], "history": list(y), "forecast": fc,
            "slope": round(float(lr.coef_[0]) * 12, 3)}


def predict_delta(df, year=2031):
    t = trend(df, "temperature")
    if t["slope"] is None:
        return None
    last_year = int(pd.Timestamp(df["date"].max()).year)
    return {"year": year, "delta": round(t["slope"] * max(1, year - last_year), 2), "slope": t["slope"]}


def by_station(df, days):
    d = df if not days else df[df["date"] > df["date"].max() - pd.Timedelta(days=days)]
    g = d.groupby("station")["temperature"].mean().round(2)
    return {"labels": list(g.index), "values": [float(v) for v in g.values]}


def anomalies(df, limit=12):
    d = df.dropna(subset=["temperature", "co2"]).copy()
    if len(d) < 50:
        return []
    d["flag"] = IsolationForest(contamination=0.005, random_state=42).fit_predict(d[["temperature", "co2"]])
    out = d[d["flag"] == -1].sort_values("date").tail(limit)
    return [{"date": r.date.strftime("%Y-%m-%d"), "station": r.station, "temperature": r.temperature, "co2": r.co2}
            for r in out.itertuples()]


# ---------------------------------------------------------------- alerts
def alert_docs(rec, th):
    docs = []
    for field, lim in th.items():
        v = rec.get(field)
        if v is None or pd.isna(v):
            continue
        for kind in ("max", "min"):
            if kind in lim and ((kind == "max" and v > lim[kind]) or (kind == "min" and v < lim[kind])):
                title = TITLES.get(field, field) if kind == "max" else "Extreme Cold Alert"
                docs.append({"station": rec["station"], "title": title, "field": field, "value": round(float(v), 1),
                             "message": f"{field} {round(float(v), 1)} is {'above' if kind == 'max' else 'below'} limit {lim[kind]}",
                             "severity": "danger" if field == "temperature" else "warning",
                             "time": rec.get("date") or datetime.datetime.utcnow(), "read": False})
    return docs


def scan(db, df, th, limit=30):
    docs = []
    for rec in df.to_dict("records"):
        docs += alert_docs(rec, th)
    docs.sort(key=lambda d: d["time"], reverse=True)
    docs = [{**d, "time": pd.Timestamp(d["time"]).to_pydatetime()} for d in docs[:limit]]
    seen = {(a["station"], a["field"], a["time"]) for a in db.alerts.find({}, {"station": 1, "field": 1, "time": 1})}
    docs = [d for d in docs if (d["station"], d["field"], d["time"]) not in seen]
    if docs:
        db.alerts.insert_many(docs)
    return len(docs)
