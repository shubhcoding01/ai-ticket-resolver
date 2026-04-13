import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_logger import (
    get_resolution_stats,
    get_all_ticket_logs,
    get_daily_stats,
    get_recent_automation_logs,
)
from database.db_setup import initialize_database

st.set_page_config(
    page_title = "AI Ticket Resolver — Dashboard",
    page_icon  = "🎫",
    layout     = "wide",
)

st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .metric-card {
        background    : #f8f9fa;
        border        : 1px solid #e0e0e0;
        border-radius : 10px;
        padding       : 16px 20px;
        text-align    : center;
    }
    .metric-value {
        font-size   : 36px;
        font-weight : 700;
        margin      : 0;
    }
    .metric-label {
        font-size   : 13px;
        color       : #666666;
        margin      : 4px 0 0;
    }
    .status-resolved  { color: #1D9E75; }
    .status-escalated { color: #E8A838; }
    .status-auto      { color: #378ADD; }
    .status-total     { color: #534AB7; }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)


def main():
    initialize_database()

    st.title("AI Ticket Resolver — Live Dashboard")
    st.caption(
        f"ICICI Bank IT Support Automation  •  "
        f"Last refreshed: {datetime.utcnow().strftime('%d %b %Y %I:%M %p UTC')}"
    )

    st.markdown("---")

    _render_metric_cards()

    st.markdown("---")

    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        _render_daily_trend_chart()

    with col_right:
        _render_category_pie_chart()

    st.markdown("---")

    _render_resolution_breakdown_chart()

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        _render_recent_tickets_table()

    with col_b:
        _render_automation_log_table()

    st.markdown("---")
    _render_footer()


def _render_metric_cards():
    """Render the top-level KPI metric cards."""
    stats = get_resolution_stats()

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            label = "Total Tickets",
            value = stats["total"],
        )

    with c2:
        st.metric(
            label = "Auto-Resolved",
            value = stats["ai_resolved"],
            delta = f"{stats['auto_rate_pct']}% rate",
        )

    with c3:
        st.metric(
            label = "Escalated",
            value = stats["escalated"],
        )

    with c4:
        st.metric(
            label = "Resolved Total",
            value = stats["resolved"],
        )

    with c5:
        st.metric(
            label = "Top Category",
            value = stats["top_category"].replace("_", " ").title()
            if stats["top_category"] != "N/A" else "N/A",
        )


def _render_daily_trend_chart():
    """Render a line chart showing ticket volume over the last 7 days."""
    st.subheader("Daily ticket trend (last 7 days)")

    rows = get_daily_stats(days=7)

    if not rows:
        st.info("No ticket data available yet. Start processing tickets to see trends.")
        return

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["total"],
        name = "Total",
        mode = "lines+markers",
        line = dict(color="#534AB7", width=2.5),
        marker = dict(size=7),
    ))

    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["resolved"],
        name = "Resolved",
        mode = "lines+markers",
        line = dict(color="#1D9E75", width=2.5),
        marker = dict(size=7),
    ))

    fig.add_trace(go.Scatter(
        x    = df["date"],
        y    = df["escalated"],
        name = "Escalated",
        mode = "lines+markers",
        line = dict(color="#E8A838", width=2.5),
        marker = dict(size=7),
    ))

    fig.update_layout(
        height      = 320,
        margin      = dict(l=0, r=0, t=10, b=0),
        legend      = dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_title = "",
        yaxis_title = "Tickets",
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        xaxis = dict(gridcolor="#f0f0f0"),
        yaxis = dict(gridcolor="#f0f0f0"),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_category_pie_chart():
    """Render a donut chart of ticket distribution by category."""
    st.subheader("Tickets by category")

    stats = get_resolution_stats()
    category_counts = stats.get("category_counts", {})

    if not category_counts:
        st.info("No category data yet.")
        return

    labels = [k.replace("_", " ").title() for k in category_counts.keys()]
    values = list(category_counts.values())

    colors = [
        "#534AB7", "#1D9E75", "#E8A838", "#D85A30",
        "#378ADD", "#993556", "#3B6D11", "#854F0B",
        "#185FA5", "#5F5E5A",
    ]

    fig = go.Figure(data=[go.Pie(
        labels    = labels,
        values    = values,
        hole      = 0.5,
        marker    = dict(colors=colors[:len(labels)]),
        textinfo  = "label+percent",
        textfont  = dict(size=12),
    )])

    fig.update_layout(
        height        = 320,
        margin        = dict(l=0, r=0, t=10, b=0),
        showlegend    = False,
        paper_bgcolor = "white",
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_resolution_breakdown_chart():
    """Render a horizontal bar chart of resolution method breakdown."""
    st.subheader("Resolution breakdown by method")

    logs = get_all_ticket_logs(limit=500)

    if not logs:
        st.info("No ticket logs available yet.")
        return

    df = pd.DataFrame(logs)
    breakdown = df["resolved_by"].value_counts().reset_index()
    breakdown.columns = ["method", "count"]

    label_map = {
        "AI_AUTO"        : "AI Auto-Resolved",
        "KB+ESCALATION"  : "KB Guide + Escalated",
        "ESCALATION"     : "Escalated to Engineer",
        "ENGINEER_QUEUE" : "Engineer Queue",
    }

    color_map = {
        "AI Auto-Resolved"     : "#1D9E75",
        "KB Guide + Escalated" : "#378ADD",
        "Escalated to Engineer": "#E8A838",
        "Engineer Queue"       : "#D85A30",
    }

    breakdown["method"] = breakdown["method"].map(label_map).fillna(breakdown["method"])

    fig = px.bar(
        breakdown,
        x              = "count",
        y              = "method",
        orientation    = "h",
        color          = "method",
        color_discrete_map = color_map,
        text           = "count",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        height        = 280,
        margin        = dict(l=0, r=40, t=10, b=0),
        showlegend    = False,
        xaxis_title   = "Number of Tickets",
        yaxis_title   = "",
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        xaxis         = dict(gridcolor="#f0f0f0"),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_recent_tickets_table():
    """Render the recent ticket log table."""
    st.subheader("Recent ticket log")

    logs = get_all_ticket_logs(limit=20)

    if not logs:
        st.info("No tickets processed yet.")
        return

    df = pd.DataFrame(logs)

    display_cols = {
        "ticket_id"   : "Ticket #",
        "category"    : "Category",
        "priority"    : "Priority",
        "status"      : "Status",
        "resolved_by" : "Resolved By",
        "created_at"  : "Time",
    }

    df = df[[c for c in display_cols.keys() if c in df.columns]]
    df = df.rename(columns=display_cols)

    if "Category" in df.columns:
        df["Category"] = df["Category"].str.replace("_", " ").str.title()

    def color_status(val):
        if val == "RESOLVED":
            return "color: #1D9E75; font-weight: bold"
        elif val == "ESCALATED":
            return "color: #E8A838; font-weight: bold"
        return ""

    def color_priority(val):
        colors = {
            "high"   : "color: #D85A30; font-weight: bold",
            "urgent" : "color: #E24B4A; font-weight: bold",
            "medium" : "color: #E8A838",
            "low"    : "color: #1D9E75",
        }
        return colors.get(val.lower(), "") if isinstance(val, str) else ""

    styled = df.style\
        .applymap(color_status,   subset=["Status"]   if "Status"   in df.columns else [])\
        .applymap(color_priority, subset=["Priority"] if "Priority" in df.columns else [])

    st.dataframe(styled, use_container_width=True, height=400)


def _render_automation_log_table():
    """Render the recent automation script execution log."""
    st.subheader("Automation script log")

    logs = get_recent_automation_logs(limit=15)

    if not logs:
        st.info("No automation scripts have run yet.")
        return

    df = pd.DataFrame(logs)

    display_cols = {
        "ticket_id"    : "Ticket #",
        "script_name"  : "Script",
        "machine_name" : "Machine",
        "success"      : "Status",
        "duration_secs": "Duration (s)",
        "ran_at"       : "Ran At",
    }

    df = df[[c for c in display_cols.keys() if c in df.columns]]
    df = df.rename(columns=display_cols)

    if "Status" in df.columns:
        df["Status"] = df["Status"].apply(
            lambda x: "SUCCESS" if x == 1 else "FAILED"
        )

    def color_auto_status(val):
        if val == "SUCCESS":
            return "color: #1D9E75; font-weight: bold"
        elif val == "FAILED":
            return "color: #E24B4A; font-weight: bold"
        return ""

    styled = df.style.applymap(
        color_auto_status,
        subset=["Status"] if "Status" in df.columns else []
    )

    st.dataframe(styled, use_container_width=True, height=400)


def _render_footer():
    """Render the dashboard footer."""
    stats = get_resolution_stats()

    st.markdown(
        f"""
        <div style='text-align:center;color:#aaaaaa;font-size:12px;padding:10px 0;'>
            AI Ticket Resolver — ICICI Bank IT Support Automation &nbsp;|&nbsp;
            {stats['total']} tickets processed &nbsp;|&nbsp;
            {stats['auto_rate_pct']}% auto-resolution rate &nbsp;|&nbsp;
            Built with Python, Claude AI, LangChain, Freshdesk API &nbsp;|&nbsp;
            {datetime.utcnow().strftime('%Y')}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()