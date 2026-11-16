"""Reports page: report cards, export format and region filters, download CSV or PDF."""
from datetime import datetime

import pandas as pd
import streamlit as st

from common import REGIONS, REPORT_TYPES, get_store, inject_css, make_report
from theme import page_header, report_card_html


def render():
    inject_css()
    page_header("Reports")
    store = get_store()

    cards = st.container()          # drawn first on screen, filled after the controls are read
    bar = st.container(key="card_export")

    # ---- bottom bar: Export Format / Region / Generate Report ----
    with bar:
        c1, c2, c3 = st.columns([1.5, 1.4, 1], vertical_alignment="center")
        fmt = c1.radio("Export Format", ["pdf", "csv"], horizontal=True, format_func=str.upper)
        region = c2.selectbox("Region", ["all"] + REGIONS,
                              format_func=lambda x: "All regions" if x == "all" else x)
        generate = c3.button("Generate Report", type="primary", width="stretch")

    # ---- 4 report cards ----
    with cards:
        cols = st.columns(len(REPORT_TYPES))
        for col, rep in zip(cols, REPORT_TYPES):
            with col:
                with st.container(key=f"rep_{rep['key']}"):
                    st.markdown(report_card_html(rep["key"], rep["title"], rep["sub"]), unsafe_allow_html=True)
                    result = make_report(rep["key"], fmt, region)
                    if result is None:
                        st.caption("No data for selected filters")
                        continue
                    payload, mime, filename = result
                    if st.download_button("Download →", data=payload, file_name=filename, mime=mime,
                                          key=f"dl_{rep['key']}_{fmt}_{region}"):
                        store["report_log"].append(
                            {"File": filename, "When": datetime.now().strftime("%d %b %Y %H:%M")})

    # ---- Generate Report: one combined report with all data for the chosen filters ----
    if generate:
        result = make_report("full", fmt, region)
        if result is None:
            st.warning("No data for selected filters")
        else:
            payload, mime, filename = result
            st.success(f"Report ready: {filename}")
            if st.download_button("⬇  Download generated report", data=payload, file_name=filename,
                                  mime=mime, key="dl_generated"):
                store["report_log"].append({"File": filename, "When": datetime.now().strftime("%d %b %Y %H:%M")})

    # ---- history ----
    with st.container(key="card_history"):
        st.markdown("<div class='es-card-title'>Recent Downloads</div>", unsafe_allow_html=True)
        history = store["report_log"][-5:][::-1]
        if history:
            st.dataframe(pd.DataFrame(history), hide_index=True, width="stretch")
        else:
            st.markdown("<div class='es-muted'>No reports downloaded yet.</div>", unsafe_allow_html=True)
