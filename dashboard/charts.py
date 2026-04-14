import plotly.express        as px
import plotly.graph_objects  as go
from plotly.subplots         import make_subplots
import pandas                as pd
from datetime                import datetime, timedelta

COLORS = {
    "purple"  : "#534AB7",
    "teal"    : "#1D9E75",
    "amber"   : "#E8A838",
    "coral"   : "#D85A30",
    "blue"    : "#378ADD",
    "pink"    : "#993556",
    "green"   : "#3B6D11",
    "red"     : "#E24B4A",
    "gray"    : "#5F5E5A",
    "dark"    : "#2C2C2A",
}

CATEGORY_COLORS = {
    "app_install"       : "#534AB7",
    "antivirus"         : "#1D9E75",
    "password_reset"    : "#E8A838",
    "network"           : "#378ADD",
    "printer"           : "#D85A30",
    "email_issue"       : "#993556",
    "hardware"          : "#854F0B",
    "os_issue"          : "#3B6D11",
    "access_permission" : "#185FA5",
    "other"             : "#5F5E5A",
}

STATUS_COLORS = {
    "RESOLVED"  : "#1D9E75",
    "ESCALATED" : "#E8A838",
    "OPEN"      : "#378ADD",
    "PENDING"   : "#D85A30",
}

PRIORITY_COLORS = {
    "low"    : "#1D9E75",
    "medium" : "#E8A838",
    "high"   : "#D85A30",
    "urgent" : "#E24B4A",
}

RESOLVER_COLORS = {
    "AI_AUTO"        : "#1D9E75",
    "KB+ESCALATION"  : "#378ADD",
    "ESCALATION"     : "#E8A838",
    "ENGINEER_QUEUE" : "#D85A30",
}

CHART_DEFAULTS = {
    "plot_bgcolor"  : "white",
    "paper_bgcolor" : "white",
    "font_family"   : "Arial, sans-serif",
    "font_color"    : "#333333",
    "margin"        : dict(l=10, r=10, t=30, b=10),
}


def _apply_defaults(fig: go.Figure, height: int = 320) -> go.Figure:
    """
    Apply consistent styling defaults to any Plotly figure.
    Call this at the end of every chart builder function.

    Args:
        fig    : Plotly Figure object
        height : Chart height in pixels

    Returns:
        Styled Figure object
    """
    fig.update_layout(
        height        = height,
        plot_bgcolor  = CHART_DEFAULTS["plot_bgcolor"],
        paper_bgcolor = CHART_DEFAULTS["paper_bgcolor"],
        font          = dict(
            family = CHART_DEFAULTS["font_family"],
            color  = CHART_DEFAULTS["font_color"],
            size   = 12,
        ),
        margin     = CHART_DEFAULTS["margin"],
        xaxis      = dict(gridcolor="#f0f0f0", showgrid=True),
        yaxis      = dict(gridcolor="#f0f0f0", showgrid=True),
        legend     = dict(
            orientation = "h",
            yanchor     = "bottom",
            y           = 1.02,
            xanchor     = "left",
            x           = 0,
            font        = dict(size=11),
        ),
    )
    return fig


def daily_trend_chart(daily_rows: list, days: int = 7) -> go.Figure:
    """
    Line chart showing total, resolved, and escalated ticket
    counts for each day over the last N days.

    Args:
        daily_rows : List of dicts from db_logger.get_daily_stats()
                     Each dict has: date, total, resolved, escalated
        days       : Number of days shown (used for title)

    Returns:
        Plotly Figure object
    """
    if not daily_rows:
        return _empty_chart(f"No data for last {days} days")

    df = pd.DataFrame(daily_rows)
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x          = df["date"],
        y          = df["total"],
        name       = "Total",
        mode       = "lines+markers",
        line       = dict(color=COLORS["purple"], width=2.5),
        marker     = dict(size=7, color=COLORS["purple"]),
        hovertemplate = "<b>%{x|%d %b}</b><br>Total: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x          = df["date"],
        y          = df["resolved"],
        name       = "Resolved",
        mode       = "lines+markers",
        line       = dict(color=COLORS["teal"], width=2.5),
        marker     = dict(size=7, color=COLORS["teal"]),
        hovertemplate = "<b>%{x|%d %b}</b><br>Resolved: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x          = df["date"],
        y          = df["escalated"],
        name       = "Escalated",
        mode       = "lines+markers",
        line       = dict(color=COLORS["amber"], width=2.5),
        marker     = dict(size=7, color=COLORS["amber"]),
        hovertemplate = "<b>%{x|%d %b}</b><br>Escalated: %{y}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title = "",
        yaxis_title = "Tickets",
    )

    return _apply_defaults(fig, height=320)


def category_donut_chart(category_counts: dict) -> go.Figure:
    """
    Donut chart showing ticket distribution across categories.

    Args:
        category_counts : Dict of category -> count
                          from db_logger.get_resolution_stats()

    Returns:
        Plotly Figure object
    """
    if not category_counts:
        return _empty_chart("No category data available")

    labels = [
        k.replace("_", " ").title()
        for k in category_counts.keys()
    ]
    values = list(category_counts.values())
    colors = [
        CATEGORY_COLORS.get(k, COLORS["gray"])
        for k in category_counts.keys()
    ]

    fig = go.Figure(data=[go.Pie(
        labels           = labels,
        values           = values,
        hole             = 0.55,
        marker           = dict(colors=colors, line=dict(color="white", width=2)),
        textinfo         = "label+percent",
        textfont         = dict(size=11),
        hovertemplate    = "<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        insidetextorientation = "radial",
    )])

    fig.update_layout(
        showlegend    = False,
        paper_bgcolor = "white",
        margin        = dict(l=10, r=10, t=10, b=10),
    )

    return _apply_defaults(fig, height=320)


def resolution_bar_chart(logs: list) -> go.Figure:
    """
    Horizontal bar chart showing how many tickets were
    resolved by each method — AI auto, KB guide, escalation etc.

    Args:
        logs : List of ticket log dicts from db_logger.get_all_ticket_logs()

    Returns:
        Plotly Figure object
    """
    if not logs:
        return _empty_chart("No resolution data available")

    df = pd.DataFrame(logs)

    if "resolved_by" not in df.columns:
        return _empty_chart("No resolved_by data in logs")

    label_map = {
        "AI_AUTO"        : "AI Auto-Resolved",
        "KB+ESCALATION"  : "KB Guide + Escalated",
        "ESCALATION"     : "Escalated to Engineer",
        "ENGINEER_QUEUE" : "Engineer Queue",
    }

    color_map = {
        "AI Auto-Resolved"     : COLORS["teal"],
        "KB Guide + Escalated" : COLORS["blue"],
        "Escalated to Engineer": COLORS["amber"],
        "Engineer Queue"       : COLORS["coral"],
    }

    breakdown = (
        df["resolved_by"]
        .map(label_map)
        .fillna(df["resolved_by"])
        .value_counts()
        .reset_index()
    )
    breakdown.columns = ["method", "count"]

    colors = [
        color_map.get(m, COLORS["gray"])
        for m in breakdown["method"]
    ]

    fig = go.Figure(go.Bar(
        x             = breakdown["count"],
        y             = breakdown["method"],
        orientation   = "h",
        marker_color  = colors,
        text          = breakdown["count"],
        textposition  = "outside",
        hovertemplate = "<b>%{y}</b><br>Count: %{x}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title = "Number of Tickets",
        yaxis_title = "",
        showlegend  = False,
    )

    return _apply_defaults(fig, height=280)


def priority_distribution_chart(logs: list) -> go.Figure:
    """
    Stacked bar chart showing priority distribution
    (low / medium / high / urgent) across ticket categories.

    Args:
        logs : List of ticket log dicts from db_logger.get_all_ticket_logs()

    Returns:
        Plotly Figure object
    """
    if not logs:
        return _empty_chart("No priority data available")

    df = pd.DataFrame(logs)

    if "category" not in df.columns or "priority" not in df.columns:
        return _empty_chart("Missing category or priority columns")

    df["category"] = df["category"].str.replace("_", " ").str.title()

    pivot = (
        df.groupby(["category", "priority"])
        .size()
        .reset_index(name="count")
    )

    fig = go.Figure()

    for priority, color in PRIORITY_COLORS.items():
        subset = pivot[pivot["priority"] == priority]
        if subset.empty:
            continue
        fig.add_trace(go.Bar(
            name          = priority.title(),
            x             = subset["category"],
            y             = subset["count"],
            marker_color  = color,
            hovertemplate = (
                "<b>%{x}</b><br>"
                f"Priority: {priority.title()}<br>"
                "Count: %{y}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode     = "stack",
        xaxis_title = "",
        yaxis_title = "Tickets",
        xaxis       = dict(tickangle=-30),
    )

    return _apply_defaults(fig, height=340)


def auto_resolve_gauge(auto_rate_pct: float) -> go.Figure:
    """
    Gauge chart showing the overall AI auto-resolution rate as a percentage.
    Green zone = good (>60%), amber = average (30-60%), red = low (<30%).

    Args:
        auto_rate_pct : Auto-resolution percentage (0 to 100)

    Returns:
        Plotly Figure object
    """
    if auto_rate_pct >= 60:
        bar_color = COLORS["teal"]
    elif auto_rate_pct >= 30:
        bar_color = COLORS["amber"]
    else:
        bar_color = COLORS["red"]

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = auto_rate_pct,
        delta = dict(
            reference  = 60,
            increasing = dict(color=COLORS["teal"]),
            decreasing = dict(color=COLORS["red"]),
            suffix     = "%",
        ),
        number = dict(suffix="%", font=dict(size=28)),
        gauge  = dict(
            axis  = dict(
                range    = [0, 100],
                ticksuffix = "%",
                tickfont = dict(size=11),
            ),
            bar   = dict(color=bar_color, thickness=0.3),
            steps = [
                dict(range=[0,  30], color="#fce8e8"),
                dict(range=[30, 60], color="#fff8e6"),
                dict(range=[60, 100], color="#e6f7f1"),
            ],
            threshold = dict(
                line  = dict(color=COLORS["dark"], width=2),
                thickness = 0.8,
                value = 60,
            ),
        ),
        title = dict(
            text = "AI Auto-Resolution Rate",
            font = dict(size=13, color=COLORS["gray"]),
        ),
    ))

    fig.update_layout(
        height        = 240,
        paper_bgcolor = "white",
        margin        = dict(l=20, r=20, t=20, b=10),
    )

    return fig


def hourly_ticket_heatmap(logs: list) -> go.Figure:
    """
    Heatmap showing which hours of the day and days of the week
    receive the most tickets. Helps plan staffing schedules.

    Args:
        logs : List of ticket log dicts from db_logger.get_all_ticket_logs()

    Returns:
        Plotly Figure object
    """
    if not logs:
        return _empty_chart("No data available for heatmap")

    df = pd.DataFrame(logs)

    if "created_at" not in df.columns:
        return _empty_chart("No created_at data in logs")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"])

    df["hour"]     = df["created_at"].dt.hour
    df["day_name"] = df["created_at"].dt.day_name()

    day_order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    pivot = (
        df.groupby(["day_name", "hour"])
        .size()
        .reset_index(name="count")
    )

    heatmap_data = pivot.pivot(
        index   = "day_name",
        columns = "hour",
        values  = "count"
    ).fillna(0)

    existing_days = [d for d in day_order if d in heatmap_data.index]
    heatmap_data  = heatmap_data.reindex(existing_days)

    fig = go.Figure(data=go.Heatmap(
        z             = heatmap_data.values,
        x             = [f"{h:02d}:00" for h in heatmap_data.columns],
        y             = heatmap_data.index.tolist(),
        colorscale    = [
            [0.0, "#f0f0f0"],
            [0.3, "#B5D4F4"],
            [0.6, "#534AB7"],
            [1.0, "#26215C"],
        ],
        hovertemplate = (
            "<b>%{y}</b> at <b>%{x}</b><br>"
            "Tickets: %{z}<extra></extra>"
        ),
        showscale     = True,
        colorbar      = dict(
            title     = "Tickets",
            thickness = 12,
            len       = 0.8,
        ),
    ))

    fig.update_layout(
        xaxis_title = "Hour of Day (UTC)",
        yaxis_title = "",
    )

    return _apply_defaults(fig, height=300)


def resolution_time_histogram(logs: list) -> go.Figure:
    """
    Histogram showing distribution of ticket ages (how old
    tickets are when they get processed).
    Helps identify backlogs.

    Args:
        logs : List of ticket log dicts from db_logger.get_all_ticket_logs()

    Returns:
        Plotly Figure object
    """
    if not logs:
        return _empty_chart("No data available")

    df = pd.DataFrame(logs)

    if "created_at" not in df.columns or "updated_at" not in df.columns:
        return _empty_chart("Missing timestamp columns")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df = df.dropna(subset=["created_at", "updated_at"])

    df["resolve_mins"] = (
        (df["updated_at"] - df["created_at"]).dt.total_seconds() / 60
    ).clip(lower=0)

    fig = go.Figure(go.Histogram(
        x             = df["resolve_mins"],
        nbinsx        = 20,
        marker_color  = COLORS["purple"],
        marker_line   = dict(color="white", width=0.5),
        opacity       = 0.85,
        hovertemplate = "Time: %{x:.0f} mins<br>Count: %{y}<extra></extra>",
    ))

    mean_mins = df["resolve_mins"].mean()
    fig.add_vline(
        x           = mean_mins,
        line_dash   = "dash",
        line_color  = COLORS["coral"],
        line_width  = 2,
        annotation_text = f"Avg: {mean_mins:.0f} min",
        annotation_position = "top right",
        annotation_font = dict(color=COLORS["coral"], size=11),
    )

    fig.update_layout(
        xaxis_title = "Resolution Time (minutes)",
        yaxis_title = "Number of Tickets",
        showlegend  = False,
    )

    return _apply_defaults(fig, height=300)


def category_trend_chart(logs: list, days: int = 14) -> go.Figure:
    """
    Multi-line chart showing how each ticket category trends
    over the last N days. Helps spot emerging issues.

    Args:
        logs : List of ticket log dicts from db_logger.get_all_ticket_logs()
        days : Number of days to show

    Returns:
        Plotly Figure object
    """
    if not logs:
        return _empty_chart("No data for category trend")

    df = pd.DataFrame(logs)

    if "created_at" not in df.columns or "category" not in df.columns:
        return _empty_chart("Missing required columns")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"])
    df["date"] = df["created_at"].dt.date

    cutoff = datetime.utcnow().date() - timedelta(days=days)
    df     = df[df["date"] >= cutoff]

    if df.empty:
        return _empty_chart(f"No data in last {days} days")

    pivot = (
        df.groupby(["date", "category"])
        .size()
        .reset_index(name="count")
    )

    top_categories = (
        df["category"]
        .value_counts()
        .head(5)
        .index
        .tolist()
    )

    fig = go.Figure()

    for cat in top_categories:
        subset = pivot[pivot["category"] == cat]
        color  = CATEGORY_COLORS.get(cat, COLORS["gray"])
        label  = cat.replace("_", " ").title()

        fig.add_trace(go.Scatter(
            x          = pd.to_datetime(subset["date"]),
            y          = subset["count"],
            name       = label,
            mode       = "lines+markers",
            line       = dict(color=color, width=2),
            marker     = dict(size=6, color=color),
            hovertemplate = (
                f"<b>{label}</b><br>"
                "%{x|%d %b}<br>"
                "Count: %{y}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title = "",
        yaxis_title = "Tickets",
    )

    return _apply_defaults(fig, height=320)


def automation_success_chart(automation_logs: list) -> go.Figure:
    """
    Grouped bar chart showing automation script success vs failure
    count for each script type.

    Args:
        automation_logs : List of automation log dicts from
                          db_logger.get_recent_automation_logs()

    Returns:
        Plotly Figure object
    """
    if not automation_logs:
        return _empty_chart("No automation runs logged yet")

    df = pd.DataFrame(automation_logs)

    if "script_name" not in df.columns or "success" not in df.columns:
        return _empty_chart("Missing required columns")

    df["result"] = df["success"].apply(
        lambda x: "Success" if x == 1 else "Failed"
    )
    df["script_name"] = df["script_name"].str.replace(".ps1", "", regex=False)

    grouped = (
        df.groupby(["script_name", "result"])
        .size()
        .reset_index(name="count")
    )

    fig = go.Figure()

    for result, color in [("Success", COLORS["teal"]), ("Failed", COLORS["red"])]:
        subset = grouped[grouped["result"] == result]
        fig.add_trace(go.Bar(
            name          = result,
            x             = subset["script_name"],
            y             = subset["count"],
            marker_color  = color,
            text          = subset["count"],
            textposition  = "outside",
            hovertemplate = (
                "<b>%{x}</b><br>"
                f"Result: {result}<br>"
                "Count: %{y}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode     = "group",
        xaxis_title = "",
        yaxis_title = "Runs",
        xaxis       = dict(tickangle=-20),
    )

    return _apply_defaults(fig, height=320)


def summary_table_chart(stats: dict) -> go.Figure:
    """
    Table visualization of overall system performance stats.
    Good for a quick at-a-glance summary card.

    Args:
        stats : Dict from db_logger.get_resolution_stats()

    Returns:
        Plotly Figure object
    """
    rows = [
        ["Total Tickets Processed", str(stats.get("total", 0))],
        ["AI Auto-Resolved",        str(stats.get("ai_resolved", 0))],
        ["Escalated to Engineer",   str(stats.get("escalated", 0))],
        ["Auto-Resolution Rate",    f"{stats.get('auto_rate_pct', 0.0)}%"],
        ["Top Category",            stats.get("top_category", "N/A")
                                    .replace("_", " ").title()],
    ]

    headers = ["Metric", "Value"]

    fig = go.Figure(data=[go.Table(
        header = dict(
            values     = headers,
            fill_color = COLORS["dark"],
            font       = dict(color="white", size=13),
            align      = "left",
            height     = 36,
        ),
        cells = dict(
            values     = list(zip(*rows)),
            fill_color = [["#f9f9f9", "white"] * 10],
            font       = dict(color=COLORS["dark"], size=13),
            align      = "left",
            height     = 32,
        ),
    )])

    fig.update_layout(
        height        = 240,
        paper_bgcolor = "white",
        margin        = dict(l=0, r=0, t=10, b=0),
    )

    return fig


def _empty_chart(message: str) -> go.Figure:
    """
    Return a blank chart with a centered message.
    Used as a fallback when there is no data to display.

    Args:
        message : Text to display in the empty chart

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_annotation(
        text      = message,
        xref      = "paper",
        yref      = "paper",
        x         = 0.5,
        y         = 0.5,
        showarrow = False,
        font      = dict(
            size  = 14,
            color = COLORS["gray"],
        ),
    )

    fig.update_layout(
        height      = 280,
        xaxis       = dict(visible=False),
        yaxis       = dict(visible=False),
        plot_bgcolor  = "#fafafa",
        paper_bgcolor = "white",
        margin        = dict(l=10, r=10, t=10, b=10),
    )

    return fig


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CHARTS MODULE TEST RUN")
    print("=" * 60 + "\n")

    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from database.db_setup  import initialize_database
    from database.db_logger import (
        get_resolution_stats,
        get_all_ticket_logs,
        get_daily_stats,
        get_recent_automation_logs,
        log_ticket_action,
        log_automation,
    )

    initialize_database()

    sample_tickets = [
        ("app_install",    "high",   "Zoom installed on PC-0042",          "AI_AUTO",       "RESOLVED"),
        ("app_install",    "medium", "Chrome installed on PC-0043",        "AI_AUTO",       "RESOLVED"),
        ("antivirus",      "medium", "AV updated on LAPTOP-115",           "AI_AUTO",       "RESOLVED"),
        ("antivirus",      "high",   "AV scan triggered on LAPTOP-116",    "AI_AUTO",       "RESOLVED"),
        ("password_reset", "high",   "AD password reset for user",         "AI_AUTO",       "RESOLVED"),
        ("network",        "high",   "VPN guide sent. Escalated.",         "KB+ESCALATION", "ESCALATED"),
        ("hardware",       "high",   "Onsite inspection scheduled.",       "ESCALATION",    "ESCALATED"),
        ("email_issue",    "medium", "Outlook repair — escalated.",        "ESCALATION",    "ESCALATED"),
        ("printer",        "low",    "Print spooler restarted.",           "AI_AUTO",       "RESOLVED"),
        ("os_issue",       "medium", "SFC and DISM ran on WS-202",        "AI_AUTO",       "RESOLVED"),
    ]

    print("Inserting sample data...")
    for i, (cat, pri, action, resolver, status) in enumerate(sample_tickets, start=3001):
        log_ticket_action(
            ticket_id    = i,
            category     = cat,
            priority     = pri,
            action_taken = action,
            resolved_by  = resolver,
            status       = status,
        )

    log_automation(3001, "install_app.ps1",          "PC-0042",     True,  "Zoom installed.",          "", 42.1)
    log_automation(3002, "install_app.ps1",          "PC-0043",     True,  "Chrome installed.",        "", 38.5)
    log_automation(3003, "update_antivirus.ps1",     "LAPTOP-115",  True,  "AV updated.",              "", 65.2)
    log_automation(3004, "update_antivirus.ps1",     "LAPTOP-116",  False, "",  "Connection refused.", 10.0)
    log_automation(3005, "reset_password.ps1",       "UNKNOWN",     True,  "Password reset.",          "", 12.3)
    log_automation(3009, "restart_print_spooler.ps1","PC-0099",     True,  "Spooler restarted.",       "", 8.7)
    log_automation(3010, "clear_disk_space.ps1",     "WS-202",      True,  "SFC and DISM complete.",   "", 180.4)

    stats           = get_resolution_stats()
    all_logs        = get_all_ticket_logs(limit=100)
    daily_rows      = get_daily_stats(days=7)
    automation_logs = get_recent_automation_logs(limit=50)

    charts = [
        ("Daily Trend Chart",            daily_trend_chart(daily_rows)),
        ("Category Donut Chart",         category_donut_chart(stats["category_counts"])),
        ("Resolution Bar Chart",         resolution_bar_chart(all_logs)),
        ("Priority Distribution Chart",  priority_distribution_chart(all_logs)),
        ("Auto-Resolve Gauge",           auto_resolve_gauge(stats["auto_rate_pct"])),
        ("Hourly Heatmap",               hourly_ticket_heatmap(all_logs)),
        ("Resolution Time Histogram",    resolution_time_histogram(all_logs)),
        ("Category Trend Chart",         category_trend_chart(all_logs, days=14)),
        ("Automation Success Chart",     automation_success_chart(automation_logs)),
        ("Summary Table",                summary_table_chart(stats)),
    ]

    print(f"\nGenerated {len(charts)} charts successfully:\n")
    for name, fig in charts:
        trace_count = len(fig.data)
        print(f"  {name:<35} — {trace_count} trace(s)")

    print("\nAll charts built successfully.")
    print("Import these functions in dashboard/app.py to use them.")