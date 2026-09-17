"""Macro Tracker — Streamlit app.

A small nutrition data app: import foods (Open Food Facts / offline table / CSV),
log what you eat, then filter and visualise your daily calories and macros.
All analysis logic lives in the tested ``macro_tracker`` package.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from macro_tracker import (
    add_entry,
    calories,
    daily_calorie_series,
    daily_macro_series,
    empty_log,
    estimate_targets,
    filter_by_date_range,
    load_log_csv,
    offline_lookup,
    scale_per_100g,
    search_openfoodfacts,
)

st.set_page_config(page_title="Macro Tracker", page_icon="🥗", layout="wide")

if "log" not in st.session_state:
    st.session_state.log = empty_log()


def _log() -> pd.DataFrame:
    return st.session_state.log


st.title("🥗 Macro Tracker")
st.caption("Import foods, log meals, and analyse your calories & macros.")

with st.sidebar:
    st.header("Import a log")
    uploaded = st.file_uploader("Upload a food-log CSV", type="csv")
    if uploaded is not None:
        try:
            st.session_state.log = load_log_csv(uploaded)
            st.success(f"Imported {len(st.session_state.log)} rows.")
        except ValueError as exc:
            st.error(str(exc))
    st.download_button(
        "Download current log (CSV)",
        _log().to_csv(index=False),
        file_name="macro_log.csv",
        mime="text/csv",
    )

add_tab, log_tab, metrics_tab, targets_tab = st.tabs(
    ["➕ Add", "📋 Log", "📈 Metrics", "🎯 Targets"]
)

with add_tab:
    st.subheader("Add a food")
    name = st.text_input("Food name", key="food_name")
    grams = st.number_input("Amount eaten (g)", min_value=0.0, value=100.0, step=10.0)
    col1, col2 = st.columns(2)
    with col1:
        use_online = st.checkbox("Look up macros online (Open Food Facts)", value=True)
    if st.button("Estimate macros for this amount", disabled=not name):
        per100 = search_openfoodfacts(name) if use_online else offline_lookup(name)
        if per100 is None:
            st.warning("No macro data found — enter the values manually below.")
        else:
            p, c, f = scale_per_100g(per100, grams)
            st.session_state.update(est_p=p, est_c=c, est_f=f)
            st.info(f"Estimated: {p} g protein · {c} g carbs · {f} g fat")

    with st.form("add_entry_form"):
        date = st.date_input("Date")
        p = st.number_input("Protein (g)", min_value=0.0, value=float(st.session_state.get("est_p", 0.0)))  # noqa: E501
        c = st.number_input("Carbs (g)", min_value=0.0, value=float(st.session_state.get("est_c", 0.0)))  # noqa: E501
        f = st.number_input("Fat (g)", min_value=0.0, value=float(st.session_state.get("est_f", 0.0)))  # noqa: E501
        eaten = st.checkbox("Eaten (uncheck for a what-if)", value=True)
        if st.form_submit_button("Add to log") and name:
            st.session_state.log = add_entry(
                _log(), date.isoformat(), name, p, c, f, eaten
            )
            st.success(f"Added {name} ({calories(p, c, f):.0f} kcal).")

with log_tab:
    st.subheader("Food log")
    log = _log()
    if log.empty:
        st.info("No entries yet — add a food or import a CSV.")
    else:
        st.dataframe(log, use_container_width=True)
        st.metric("Entries", len(log))

with metrics_tab:
    st.subheader("Metrics")
    log = _log()
    if log.empty or daily_calorie_series(log).empty:
        st.info("Log some eaten foods to see charts.")
    else:
        dates = sorted(log["date"].unique())
        start, end = st.select_slider(
            "Date range",
            options=dates,
            value=(dates[0], dates[-1]),
        )
        window = filter_by_date_range(log, start, end)

        cal = daily_calorie_series(window)
        st.plotly_chart(
            px.line(cal, x="date", y="calories", markers=True, title="Calories eaten per day"),
            use_container_width=True,
        )

        macros = daily_macro_series(window)
        macros_long = macros.melt(
            id_vars="date", value_vars=["protein", "carbs", "fat"],
            var_name="macro", value_name="grams",
        )
        st.plotly_chart(
            px.line(macros_long, x="date", y="grams", color="macro", markers=True,
                    title="Macros eaten per day (g)"),
            use_container_width=True,
        )

with targets_tab:
    st.subheader("Estimate starting targets")
    st.caption("Mifflin-St Jeor BMR → activity → TDEE. A science-based estimate to fine-tune.")
    c1, c2, c3 = st.columns(3)
    sex = c1.selectbox("Sex", ["male", "female"])
    age = c2.number_input("Age", min_value=1, value=30)
    activity = c3.selectbox(
        "Activity", ["sedentary", "light", "moderate", "active", "very"], index=2
    )
    cm = c1.number_input("Height (cm)", min_value=1.0, value=180.0)
    kg = c2.number_input("Weight (kg)", min_value=1.0, value=80.0)
    est = estimate_targets(sex, age, cm, kg, activity)
    if est:
        st.metric("Maintenance (TDEE)", f"{est['tdee']} kcal")
        st.write("**Lean (cut):**", est["lean"])
        st.write("**Bulk (gain):**", est["bulk"])
