"""Performance Monitor page: live CPU, memory, job time and query time (refreshes every 2 seconds)."""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import psutil
import streamlit as st

from common import get_db, get_store, inject_css, timed_query
from theme import page_header

MAX_POINTS = 30


def _avg(xs):
    return round(sum(xs) / len(xs), 2) if xs else 0


@st.fragment(run_every=2)
def _live():
    store = get_store()
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    db = get_db()
    timed_query(lambda: db.command("ping") if db is not None else sum(range(10000)))

    history = st.session_state.setdefault("perf_history", [])
    history.append({"time": datetime.now().strftime("%H:%M:%S"), "CPU": cpu, "Memory": mem.percent})
    del history[:-MAX_POINTS]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CPU Usage", f"{cpu:.1f}%")
    c2.metric("Memory Usage", f"{mem.percent:.1f}%", help=f"{mem.used / 1024 ** 3:.2f} GB used")
    c3.metric("Job Time", f"{_avg(store['job_times'])}s")
    c4.metric("Query Time", f"{_avg(store['query_times'])}ms")

    df = pd.DataFrame(history)
    fig = go.Figure()
    fig.add_scatter(x=df["time"], y=df["CPU"], name="CPU", mode="lines",
                    line=dict(color="#3b82f6", width=2.5, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(59,130,246,.14)")
    fig.add_scatter(x=df["time"], y=df["Memory"], name="Memory", mode="lines",
                    line=dict(color="#22c55e", width=2.5, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(34,197,94,.10)")
    fig.update_layout(
        height=340, margin=dict(l=6, r=6, t=6, b=6), template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8aa0b8", size=12),
        yaxis=dict(range=[0, 100], ticksuffix="%", gridcolor="rgba(255,255,255,.07)", zeroline=False),
        xaxis=dict(showgrid=False, nticks=6),
        legend=dict(orientation="h", x=1, xanchor="right", y=1.12, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    with st.container(key="card_perf"):
        st.markdown("<div class='es-card-title'>System Performance</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render():
    inject_css()
    page_header("Performance Monitor")
    psutil.cpu_percent(interval=None)  # prime the counter
    _live()
