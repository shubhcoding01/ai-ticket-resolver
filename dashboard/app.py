# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime
# import sys
# import os

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from database.db_logger import (
#     get_resolution_stats,
#     get_all_ticket_logs,
#     get_daily_stats,
#     get_recent_automation_logs,
# )
# from database.db_setup import initialize_database

# st.set_page_config(
#     page_title = "AI Ticket Resolver — Dashboard",
#     page_icon  = "🎫",
#     layout     = "wide",
# )

# st.markdown("""
# <style>
#     .main { padding-top: 1rem; }
#     .metric-card {
#         background    : #f8f9fa;
#         border        : 1px solid #e0e0e0;
#         border-radius : 10px;
#         padding       : 16px 20px;
#         text-align    : center;
#     }
#     .metric-value {
#         font-size   : 36px;
#         font-weight : 700;
#         margin      : 0;
#     }
#     .metric-label {
#         font-size   : 13px;
#         color       : #666666;
#         margin      : 4px 0 0;
#     }
#     .status-resolved  { color: #1D9E75; }
#     .status-escalated { color: #E8A838; }
#     .status-auto      { color: #378ADD; }
#     .status-total     { color: #534AB7; }
#     div[data-testid="stMetricValue"] { font-size: 2rem; }
# </style>
# """, unsafe_allow_html=True)


# def main():
#     initialize_database()

#     st.title("AI Ticket Resolver — Live Dashboard")
#     st.caption(
#         f"ICICI Bank IT Support Automation  •  "
#         f"Last refreshed: {datetime.utcnow().strftime('%d %b %Y %I:%M %p UTC')}"
#     )

#     st.markdown("---")

#     _render_metric_cards()

#     st.markdown("---")

#     col_left, col_right = st.columns([1.4, 1])

#     with col_left:
#         _render_daily_trend_chart()

#     with col_right:
#         _render_category_pie_chart()

#     st.markdown("---")

#     _render_resolution_breakdown_chart()

#     st.markdown("---")

#     col_a, col_b = st.columns(2)

#     with col_a:
#         _render_recent_tickets_table()

#     with col_b:
#         _render_automation_log_table()

#     st.markdown("---")
#     _render_footer()


# def _render_metric_cards():
#     """Render the top-level KPI metric cards."""
#     stats = get_resolution_stats()

#     c1, c2, c3, c4, c5 = st.columns(5)

#     with c1:
#         st.metric(
#             label = "Total Tickets",
#             value = stats["total"],
#         )

#     with c2:
#         st.metric(
#             label = "Auto-Resolved",
#             value = stats["ai_resolved"],
#             delta = f"{stats['auto_rate_pct']}% rate",
#         )

#     with c3:
#         st.metric(
#             label = "Escalated",
#             value = stats["escalated"],
#         )

#     with c4:
#         st.metric(
#             label = "Resolved Total",
#             value = stats["resolved"],
#         )

#     with c5:
#         st.metric(
#             label = "Top Category",
#             value = stats["top_category"].replace("_", " ").title()
#             if stats["top_category"] != "N/A" else "N/A",
#         )


# def _render_daily_trend_chart():
#     """Render a line chart showing ticket volume over the last 7 days."""
#     st.subheader("Daily ticket trend (last 7 days)")

#     rows = get_daily_stats(days=7)

#     if not rows:
#         st.info("No ticket data available yet. Start processing tickets to see trends.")
#         return

#     df = pd.DataFrame(rows)
#     df["date"] = pd.to_datetime(df["date"])

#     fig = go.Figure()

#     fig.add_trace(go.Scatter(
#         x    = df["date"],
#         y    = df["total"],
#         name = "Total",
#         mode = "lines+markers",
#         line = dict(color="#534AB7", width=2.5),
#         marker = dict(size=7),
#     ))

#     fig.add_trace(go.Scatter(
#         x    = df["date"],
#         y    = df["resolved"],
#         name = "Resolved",
#         mode = "lines+markers",
#         line = dict(color="#1D9E75", width=2.5),
#         marker = dict(size=7),
#     ))

#     fig.add_trace(go.Scatter(
#         x    = df["date"],
#         y    = df["escalated"],
#         name = "Escalated",
#         mode = "lines+markers",
#         line = dict(color="#E8A838", width=2.5),
#         marker = dict(size=7),
#     ))

#     fig.update_layout(
#         height      = 320,
#         margin      = dict(l=0, r=0, t=10, b=0),
#         legend      = dict(orientation="h", yanchor="bottom", y=1.02),
#         xaxis_title = "",
#         yaxis_title = "Tickets",
#         plot_bgcolor  = "white",
#         paper_bgcolor = "white",
#         xaxis = dict(gridcolor="#f0f0f0"),
#         yaxis = dict(gridcolor="#f0f0f0"),
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def _render_category_pie_chart():
#     """Render a donut chart of ticket distribution by category."""
#     st.subheader("Tickets by category")

#     stats = get_resolution_stats()
#     category_counts = stats.get("category_counts", {})

#     if not category_counts:
#         st.info("No category data yet.")
#         return

#     labels = [k.replace("_", " ").title() for k in category_counts.keys()]
#     values = list(category_counts.values())

#     colors = [
#         "#534AB7", "#1D9E75", "#E8A838", "#D85A30",
#         "#378ADD", "#993556", "#3B6D11", "#854F0B",
#         "#185FA5", "#5F5E5A",
#     ]

#     fig = go.Figure(data=[go.Pie(
#         labels    = labels,
#         values    = values,
#         hole      = 0.5,
#         marker    = dict(colors=colors[:len(labels)]),
#         textinfo  = "label+percent",
#         textfont  = dict(size=12),
#     )])

#     fig.update_layout(
#         height        = 320,
#         margin        = dict(l=0, r=0, t=10, b=0),
#         showlegend    = False,
#         paper_bgcolor = "white",
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def _render_resolution_breakdown_chart():
#     """Render a horizontal bar chart of resolution method breakdown."""
#     st.subheader("Resolution breakdown by method")

#     logs = get_all_ticket_logs(limit=500)

#     if not logs:
#         st.info("No ticket logs available yet.")
#         return

#     df = pd.DataFrame(logs)
#     breakdown = df["resolved_by"].value_counts().reset_index()
#     breakdown.columns = ["method", "count"]

#     label_map = {
#         "AI_AUTO"        : "AI Auto-Resolved",
#         "KB+ESCALATION"  : "KB Guide + Escalated",
#         "ESCALATION"     : "Escalated to Engineer",
#         "ENGINEER_QUEUE" : "Engineer Queue",
#     }

#     color_map = {
#         "AI Auto-Resolved"     : "#1D9E75",
#         "KB Guide + Escalated" : "#378ADD",
#         "Escalated to Engineer": "#E8A838",
#         "Engineer Queue"       : "#D85A30",
#     }

#     breakdown["method"] = breakdown["method"].map(label_map).fillna(breakdown["method"])

#     fig = px.bar(
#         breakdown,
#         x              = "count",
#         y              = "method",
#         orientation    = "h",
#         color          = "method",
#         color_discrete_map = color_map,
#         text           = "count",
#     )

#     fig.update_traces(textposition="outside")
#     fig.update_layout(
#         height        = 280,
#         margin        = dict(l=0, r=40, t=10, b=0),
#         showlegend    = False,
#         xaxis_title   = "Number of Tickets",
#         yaxis_title   = "",
#         plot_bgcolor  = "white",
#         paper_bgcolor = "white",
#         xaxis         = dict(gridcolor="#f0f0f0"),
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def _render_recent_tickets_table():
#     """Render the recent ticket log table."""
#     st.subheader("Recent ticket log")

#     logs = get_all_ticket_logs(limit=20)

#     if not logs:
#         st.info("No tickets processed yet.")
#         return

#     df = pd.DataFrame(logs)

#     display_cols = {
#         "ticket_id"   : "Ticket #",
#         "category"    : "Category",
#         "priority"    : "Priority",
#         "status"      : "Status",
#         "resolved_by" : "Resolved By",
#         "created_at"  : "Time",
#     }

#     df = df[[c for c in display_cols.keys() if c in df.columns]]
#     df = df.rename(columns=display_cols)

#     if "Category" in df.columns:
#         df["Category"] = df["Category"].str.replace("_", " ").str.title()

#     def color_status(val):
#         if val == "RESOLVED":
#             return "color: #1D9E75; font-weight: bold"
#         elif val == "ESCALATED":
#             return "color: #E8A838; font-weight: bold"
#         return ""

#     def color_priority(val):
#         colors = {
#             "high"   : "color: #D85A30; font-weight: bold",
#             "urgent" : "color: #E24B4A; font-weight: bold",
#             "medium" : "color: #E8A838",
#             "low"    : "color: #1D9E75",
#         }
#         return colors.get(val.lower(), "") if isinstance(val, str) else ""

#     styled = df.style\
#         .applymap(color_status,   subset=["Status"]   if "Status"   in df.columns else [])\
#         .applymap(color_priority, subset=["Priority"] if "Priority" in df.columns else [])

#     st.dataframe(styled, use_container_width=True, height=400)


# def _render_automation_log_table():
#     """Render the recent automation script execution log."""
#     st.subheader("Automation script log")

#     logs = get_recent_automation_logs(limit=15)

#     if not logs:
#         st.info("No automation scripts have run yet.")
#         return

#     df = pd.DataFrame(logs)

#     display_cols = {
#         "ticket_id"    : "Ticket #",
#         "script_name"  : "Script",
#         "machine_name" : "Machine",
#         "success"      : "Status",
#         "duration_secs": "Duration (s)",
#         "ran_at"       : "Ran At",
#     }

#     df = df[[c for c in display_cols.keys() if c in df.columns]]
#     df = df.rename(columns=display_cols)

#     if "Status" in df.columns:
#         df["Status"] = df["Status"].apply(
#             lambda x: "SUCCESS" if x == 1 else "FAILED"
#         )

#     def color_auto_status(val):
#         if val == "SUCCESS":
#             return "color: #1D9E75; font-weight: bold"
#         elif val == "FAILED":
#             return "color: #E24B4A; font-weight: bold"
#         return ""

#     styled = df.style.applymap(
#         color_auto_status,
#         subset=["Status"] if "Status" in df.columns else []
#     )

#     st.dataframe(styled, use_container_width=True, height=400)


# def _render_footer():
#     """Render the dashboard footer."""
#     stats = get_resolution_stats()

#     st.markdown(
#         f"""
#         <div style='text-align:center;color:#aaaaaa;font-size:12px;padding:10px 0;'>
#             AI Ticket Resolver — ICICI Bank IT Support Automation &nbsp;|&nbsp;
#             {stats['total']} tickets processed &nbsp;|&nbsp;
#             {stats['auto_rate_pct']}% auto-resolution rate &nbsp;|&nbsp;
#             Built with Python, Claude AI, LangChain, Freshdesk API &nbsp;|&nbsp;
#             {datetime.utcnow().strftime('%Y')}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# if __name__ == "__main__":
#     main()

import os
import sys
import streamlit as st
import pandas      as pd
import plotly.express        as px
import plotly.graph_objects  as go
from datetime import datetime, timezone

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from dotenv import load_dotenv
load_dotenv("config/.env")

from database.db_logger import (
    get_resolution_stats,
    get_all_ticket_logs,
    get_daily_stats,
    get_recent_automation_logs,
)
from database.db_setup import initialize_database

DEMO_MODE    = os.getenv("DEMO_MODE",    "false").strip().lower() == "true"
COMPANY_NAME = os.getenv("COMPANY_NAME", "ICICI Bank")

st.set_page_config(
    page_title = f"AI Ticket Resolver — {COMPANY_NAME}",
    page_icon  = "🎫",
    layout     = "wide",
)

st.markdown("""
<style>
    .main { padding-top: 0.5rem; }

    div[data-testid="stMetricValue"] {
        font-size   : 2.2rem;
        font-weight : 700;
    }
    div[data-testid="stMetricDelta"] {
        font-size : 0.85rem;
    }

    .demo-banner {
        background    : linear-gradient(90deg, #534AB7, #378ADD);
        color         : white;
        padding       : 8px 20px;
        border-radius : 8px;
        font-size     : 13px;
        margin-bottom : 8px;
        text-align    : center;
    }

    .info-box {
        background    : #f0f7ff;
        border        : 1px solid #378ADD;
        border-radius : 8px;
        padding       : 12px 16px;
        font-size     : 13px;
        color         : #185FA5;
        margin-bottom : 12px;
    }

    .stat-card {
        background    : #fafafa;
        border        : 1px solid #eeeeee;
        border-radius : 10px;
        padding       : 14px 18px;
        text-align    : center;
        margin-bottom : 8px;
    }

    .footer-text {
        text-align  : center;
        color       : #aaaaaa;
        font-size   : 12px;
        padding     : 10px 0;
    }

    .section-header {
        font-size   : 15px;
        font-weight : 600;
        color       : #333333;
        margin      : 0 0 8px 0;
    }

    div[data-testid="stDataFrame"] {
        border-radius : 8px;
    }
</style>
""", unsafe_allow_html=True)


def _now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _format_now(fmt: str = "%d %b %Y %I:%M %p UTC") -> str:
    """Return formatted current UTC time string."""
    return _now().strftime(fmt)


def main():
    """
    Main dashboard entry point.
    Renders the complete Streamlit dashboard with all sections.
    """
    initialize_database()

    if DEMO_MODE:
        st.markdown(
            f"""
            <div class="demo-banner">
                🎮 DEMO MODE — Showing data from 10 sample ICICI Bank tickets
                &nbsp;|&nbsp;
                Set DEMO_MODE=false in config/.env to connect to live Freshdesk
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.title("🎫 AI Ticket Resolver — Live Dashboard")
    st.caption(
        f"{COMPANY_NAME} IT Support Automation  •  "
        f"Last refreshed: {_format_now()}"
    )

    stats = get_resolution_stats()

    if stats["total"] == 0:
        st.markdown(
            """
            <div class="info-box">
                📭 No tickets have been processed yet.<br>
                Run <code>python main.py</code> to process demo tickets,
                then refresh this page.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    _render_metric_cards(stats)

    st.markdown("---")
    _render_summary_row(stats)

    st.markdown("---")
    col_left, col_right = st.columns([1.4, 1])
    with col_left:
        _render_daily_trend_chart()
    with col_right:
        _render_category_pie_chart(stats)

    st.markdown("---")
    _render_resolution_breakdown_chart()

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        _render_recent_tickets_table()
    with col_b:
        _render_automation_log_table()

    st.markdown("---")
    _render_priority_chart()

    st.markdown("---")
    _render_footer(stats)


def _render_metric_cards(stats: dict) -> None:
    """
    Render the top-level KPI metric cards row.

    Args:
        stats : Resolution stats dict from db_logger
    """
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            label = "📋 Total Tickets",
            value = stats["total"],
            help  = "Total tickets processed since system started",
        )

    with c2:
        st.metric(
            label = "✅ Auto-Resolved",
            value = stats["ai_resolved"],
            delta = f"{stats['auto_rate_pct']}% rate",
            help  = "Tickets resolved automatically by AI + scripts",
        )

    with c3:
        st.metric(
            label = "🔺 Escalated",
            value = stats["escalated"],
            help  = "Tickets routed to human engineers",
        )

    with c4:
        st.metric(
            label = "📊 Total Resolved",
            value = stats["resolved"],
            help  = "Total tickets marked as resolved",
        )

    with c5:
        top_cat = stats.get("top_category", "N/A")
        st.metric(
            label = "🏆 Top Category",
            value = (
                top_cat.replace("_", " ").title()
                if top_cat and top_cat != "N/A"
                else "N/A"
            ),
            help  = "Most common ticket category",
        )


def _render_summary_row(stats: dict) -> None:
    """
    Render a summary stats row with auto-resolution rate,
    KB usage and escalation rate as simple stat boxes.

    Args:
        stats : Resolution stats dict from db_logger
    """
    total     = stats.get("total",          0)
    ai_auto   = stats.get("ai_resolved",    0)
    escalated = stats.get("escalated",      0)
    rate      = stats.get("auto_rate_pct",  0.0)

    kb_sent   = 0
    try:
        logs    = get_all_ticket_logs(limit=500)
        kb_sent = sum(
            1 for log in logs
            if log.get("resolved_by", "") in
            ["KB+ESCALATION"]
        )
    except Exception:
        pass

    esc_rate = round(escalated / total * 100, 1) if total > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        color = (
            "#1D9E75" if rate >= 60
            else "#E8A838" if rate >= 30
            else "#E24B4A"
        )
        st.markdown(
            f"""
            <div class="stat-card">
                <div style="font-size:28px;font-weight:700;
                            color:{color};">{rate}%</div>
                <div style="font-size:12px;color:#666;">
                    AI Auto-Resolution Rate
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div style="font-size:28px;font-weight:700;
                            color:#378ADD;">{ai_auto}</div>
                <div style="font-size:12px;color:#666;">
                    Tickets Saved by AI
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div style="font-size:28px;font-weight:700;
                            color:#534AB7;">{kb_sent}</div>
                <div style="font-size:12px;color:#666;">
                    KB Guides Sent to Users
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div style="font-size:28px;font-weight:700;
                            color:#E8A838;">{esc_rate}%</div>
                <div style="font-size:12px;color:#666;">
                    Escalation Rate
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_daily_trend_chart() -> None:
    """
    Render a line chart showing ticket volume over the last 7 days.
    Shows total, resolved, and escalated lines.
    """
    st.subheader("📈 Daily ticket trend (last 7 days)")

    rows = get_daily_stats(days=7)

    if not rows:
        st.info(
            "No daily data yet. "
            "Run the demo first: `python main.py`"
        )
        return

    df            = pd.DataFrame(rows)
    df["date"]    = pd.to_datetime(df["date"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x              = df["date"],
        y              = df["total"],
        name           = "Total",
        mode           = "lines+markers",
        line           = dict(color="#534AB7", width=2.5),
        marker         = dict(size=8, color="#534AB7"),
        hovertemplate  = "<b>%{x|%d %b}</b><br>Total: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x              = df["date"],
        y              = df["resolved"],
        name           = "Resolved",
        mode           = "lines+markers",
        line           = dict(color="#1D9E75", width=2.5),
        marker         = dict(size=8, color="#1D9E75"),
        hovertemplate  = "<b>%{x|%d %b}</b><br>Resolved: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x              = df["date"],
        y              = df["escalated"],
        name           = "Escalated",
        mode           = "lines+markers",
        line           = dict(color="#E8A838", width=2.5),
        marker         = dict(size=8, color="#E8A838"),
        hovertemplate  = "<b>%{x|%d %b}</b><br>Escalated: %{y}<extra></extra>",
    ))

    fig.update_layout(
        height        = 320,
        margin        = dict(l=0, r=0, t=10, b=0),
        legend        = dict(
            orientation = "h",
            yanchor     = "bottom",
            y           = 1.02,
            xanchor     = "left",
            x           = 0,
        ),
        xaxis_title   = "",
        yaxis_title   = "Tickets",
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        xaxis         = dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis         = dict(
            gridcolor = "#f0f0f0",
            showgrid  = True,
            rangemode = "tozero",
        ),
        hovermode     = "x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_category_pie_chart(stats: dict) -> None:
    """
    Render a donut chart of ticket distribution by category.

    Args:
        stats : Resolution stats dict from db_logger
    """
    st.subheader("🍩 Tickets by category")

    category_counts = stats.get("category_counts", {})

    if not category_counts:
        st.info("No category data yet.")
        return

    labels = [
        k.replace("_", " ").title()
        for k in category_counts.keys()
    ]
    values = list(category_counts.values())
    colors = [
        "#534AB7", "#1D9E75", "#E8A838", "#D85A30",
        "#378ADD", "#993556", "#3B6D11", "#854F0B",
        "#185FA5", "#5F5E5A",
    ]

    fig = go.Figure(data=[go.Pie(
        labels           = labels,
        values           = values,
        hole             = 0.55,
        marker           = dict(
            colors     = colors[:len(labels)],
            line       = dict(color="white", width=2),
        ),
        textinfo         = "label+percent",
        textfont         = dict(size=11),
        hovertemplate    = (
            "<b>%{label}</b><br>"
            "Count: %{value}<br>"
            "Share: %{percent}<extra></extra>"
        ),
    )])

    fig.update_layout(
        height        = 320,
        margin        = dict(l=0, r=0, t=10, b=0),
        showlegend    = False,
        paper_bgcolor = "white",
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_resolution_breakdown_chart() -> None:
    """
    Render a horizontal bar chart showing how tickets were resolved —
    AI auto, KB guide, escalation, or engineer queue.
    """
    st.subheader("📊 Resolution breakdown by method")

    logs = get_all_ticket_logs(limit=500)

    if not logs:
        st.info("No ticket logs available yet.")
        return

    df        = pd.DataFrame(logs)
    breakdown = (
        df["resolved_by"]
        .value_counts()
        .reset_index()
    )
    breakdown.columns = ["method", "count"]

    label_map = {
        "AI_AUTO"          : "AI Auto-Resolved",
        "KB+ESCALATION"    : "KB Guide + Escalated",
        "ESCALATION"       : "Escalated to Engineer",
        "ENGINEER_QUEUE"   : "Engineer Queue",
        "FORCE_ESCALATION" : "Force Escalated",
        "EMERGENCY"        : "Emergency Escalation",
    }

    color_map = {
        "AI Auto-Resolved"     : "#1D9E75",
        "KB Guide + Escalated" : "#378ADD",
        "Escalated to Engineer": "#E8A838",
        "Engineer Queue"       : "#D85A30",
        "Force Escalated"      : "#E24B4A",
        "Emergency Escalation" : "#993556",
    }

    breakdown["method"] = (
        breakdown["method"]
        .map(label_map)
        .fillna(breakdown["method"])
    )

    fig = px.bar(
        breakdown,
        x                  = "count",
        y                  = "method",
        orientation        = "h",
        color              = "method",
        color_discrete_map = color_map,
        text               = "count",
    )

    fig.update_traces(
        textposition = "outside",
        hovertemplate = "<b>%{y}</b><br>Count: %{x}<extra></extra>",
    )
    fig.update_layout(
        height        = 300,
        margin        = dict(l=0, r=60, t=10, b=0),
        showlegend    = False,
        xaxis_title   = "Number of Tickets",
        yaxis_title   = "",
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        xaxis         = dict(
            gridcolor = "#f0f0f0",
            rangemode = "tozero",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_recent_tickets_table() -> None:
    """
    Render the recent ticket log table with color-coded
    status and priority columns.
    """
    st.subheader("📋 Recent ticket log")

    logs = get_all_ticket_logs(limit=20)

    if not logs:
        st.info(
            "No tickets processed yet.\n"
            "Run `python main.py` first."
        )
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

    df = df[
        [c for c in display_cols.keys() if c in df.columns]
    ]
    df = df.rename(columns=display_cols)

    if "Category" in df.columns:
        df["Category"] = (
            df["Category"]
            .str.replace("_", " ")
            .str.title()
        )

    if "Resolved By" in df.columns:
        resolver_map = {
            "AI_AUTO"          : "🤖 AI Auto",
            "KB+ESCALATION"    : "📚 KB + Escalate",
            "ESCALATION"       : "🔺 Escalated",
            "ENGINEER_QUEUE"   : "👷 Engineer",
            "FORCE_ESCALATION" : "🚨 Force Escalate",
            "EMERGENCY"        : "⚠️ Emergency",
        }
        df["Resolved By"] = (
            df["Resolved By"]
            .map(resolver_map)
            .fillna(df["Resolved By"])
        )

    if "Time" in df.columns:
        df["Time"] = (
            df["Time"]
            .str[:16]
            .str.replace("T", " ")
        )

    def color_status(val):
        if val == "RESOLVED":
            return "color: #1D9E75; font-weight: bold"
        elif val == "ESCALATED":
            return "color: #E8A838; font-weight: bold"
        return ""

    def color_priority(val):
        priority_colors = {
            "high"   : "color: #D85A30; font-weight: bold",
            "urgent" : "color: #E24B4A; font-weight: bold",
            "medium" : "color: #E8A838",
            "low"    : "color: #1D9E75",
        }
        return (
            priority_colors.get(str(val).lower(), "")
            if isinstance(val, str)
            else ""
        )

    styled = df.style

    if "Status" in df.columns:
        styled = styled.applymap(
            color_status, subset=["Status"]
        )

    if "Priority" in df.columns:
        styled = styled.applymap(
            color_priority, subset=["Priority"]
        )

    st.dataframe(
        styled,
        use_container_width = True,
        height              = 400,
    )


def _render_automation_log_table() -> None:
    """
    Render the automation script execution log table
    with color-coded success/failure status.
    """
    st.subheader("⚙️ Automation script log")

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
        "duration_secs": "Secs",
        "ran_at"       : "Ran At",
    }

    df = df[
        [c for c in display_cols.keys() if c in df.columns]
    ]
    df = df.rename(columns=display_cols)

    if "Status" in df.columns:
        df["Status"] = df["Status"].apply(
            lambda x: "✅ SUCCESS" if x == 1 else "❌ FAILED"
        )

    if "Script" in df.columns:
        df["Script"] = (
            df["Script"]
            .str.replace(".ps1", "", regex=False)
            .str.replace("_", " ")
            .str.title()
        )

    if "Secs" in df.columns:
        df["Secs"] = df["Secs"].apply(
            lambda x: f"{x:.1f}s" if pd.notna(x) else "—"
        )

    if "Ran At" in df.columns:
        df["Ran At"] = (
            df["Ran At"]
            .str[:16]
            .str.replace("T", " ")
        )

    def color_auto_status(val):
        if "SUCCESS" in str(val):
            return "color: #1D9E75; font-weight: bold"
        elif "FAILED" in str(val):
            return "color: #E24B4A; font-weight: bold"
        return ""

    styled = df.style

    if "Status" in df.columns:
        styled = styled.applymap(
            color_auto_status,
            subset=["Status"]
        )

    st.dataframe(
        styled,
        use_container_width = True,
        height              = 400,
    )


def _render_priority_chart() -> None:
    """
    Render a grouped bar chart showing ticket counts
    by priority level across all categories.
    """
    st.subheader("🎯 Ticket priority distribution")

    logs = get_all_ticket_logs(limit=500)

    if not logs:
        st.info("No data yet.")
        return

    df = pd.DataFrame(logs)

    if "priority" not in df.columns or "category" not in df.columns:
        st.info("No priority/category data yet.")
        return

    df["category"] = (
        df["category"]
        .str.replace("_", " ")
        .str.title()
    )

    priority_counts = (
        df.groupby(["category", "priority"])
        .size()
        .reset_index(name="count")
    )

    priority_colors = {
        "low"    : "#1D9E75",
        "medium" : "#E8A838",
        "high"   : "#D85A30",
        "urgent" : "#E24B4A",
    }

    fig = go.Figure()

    for priority, color in priority_colors.items():
        subset = priority_counts[
            priority_counts["priority"] == priority
        ]
        if subset.empty:
            continue
        fig.add_trace(go.Bar(
            name          = priority.title(),
            x             = subset["category"],
            y             = subset["count"],
            marker_color  = color,
            text          = subset["count"],
            textposition  = "outside",
            hovertemplate = (
                "<b>%{x}</b><br>"
                f"Priority: {priority.title()}<br>"
                "Count: %{y}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode       = "group",
        height        = 320,
        margin        = dict(l=0, r=0, t=10, b=0),
        xaxis_title   = "",
        yaxis_title   = "Tickets",
        plot_bgcolor  = "white",
        paper_bgcolor = "white",
        legend        = dict(
            orientation = "h",
            yanchor     = "bottom",
            y           = 1.02,
        ),
        xaxis         = dict(
            gridcolor = "#f0f0f0",
            tickangle = -20,
        ),
        yaxis         = dict(
            gridcolor = "#f0f0f0",
            rangemode = "tozero",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def _render_footer(stats: dict) -> None:
    """
    Render the dashboard footer with summary stats.

    Args:
        stats : Resolution stats dict from db_logger
    """
    mode_label = "🎮 DEMO MODE" if DEMO_MODE else "🔴 LIVE MODE"

    st.markdown(
        f"""
        <div class="footer-text">
            🎫 AI Ticket Resolver &nbsp;|&nbsp;
            {COMPANY_NAME} IT Support Automation &nbsp;|&nbsp;
            {stats['total']} tickets processed &nbsp;|&nbsp;
            {stats['auto_rate_pct']}% auto-resolution rate &nbsp;|&nbsp;
            {mode_label} &nbsp;|&nbsp;
            Built with Python · Claude AI · ChromaDB · Streamlit &nbsp;|&nbsp;
            {_now().strftime('%Y')}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()