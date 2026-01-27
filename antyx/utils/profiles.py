import pandas as pd
import plotly.express as px

from antyx.utils.visualizations import (
    plot_hist,
    plot_box,
    plot_bars,
    PLOTLY_LIGHT,
    PLOTLY_DARK,
)
from antyx.utils.types import detect_var_type


# ============================
# FIGURAS
# ============================

def profile_numeric_figs(df, col, theme_cfg):
    return [
        ("Histogram", plot_hist(df, col, theme_cfg)),
        ("Boxplot", plot_box(df, col, theme_cfg)),
    ]


def profile_categorical_figs(df, col, theme_cfg):
    return [("Bar chart", plot_bars(df, col, theme_cfg))]


def profile_binary_figs(df, col, theme_cfg):
    return [("Bar chart", plot_bars(df, col, theme_cfg))]


# ============================================================
# Helper: convertir Serie a DataFrame con DatetimeIndex
# ============================================================

def _to_dt_index(s):
    s = pd.to_datetime(s.dropna(), dayfirst=True, errors="coerce")
    s = s.dropna()

    df = s.to_frame(name="value")
    df.index = df["value"]
    return df


# ============================================================
# 1. HISTOGRAMA TEMPORAL INTELIGENTE
# ============================================================

def fig_datetime_histogram(s, theme_cfg):
    df = _to_dt_index(s)
    if df.empty:
        return None

    range_days = (df.index.max() - df.index.min()).days

    if range_days <= 31:
        freq = "D"
    elif range_days <= 180:
        freq = "W"
    elif range_days <= 730:
        freq = "M"
    else:
        freq = "YE"

    grouped = df.groupby(pd.Grouper(freq=freq)).size().reset_index(name="count")

    fig = px.bar(grouped, x=grouped.columns[0], y="count")
    fig.update_layout(**theme_cfg)
    return ("Distribution over time", fig)


# ============================================================
# 2. HEATMAP DÍA × HORA
# ============================================================

def fig_datetime_heatmap(s, theme_cfg):
    df = _to_dt_index(s)
    if df.empty:
        return None

    if df.index.hour.nunique() <= 1:
        return None

    df2 = pd.DataFrame({
        "date": df.index.date,
        "hour": df.index.hour
    })

    heat = df2.groupby(["date", "hour"]).size().reset_index(name="count")

    fig = px.density_heatmap(
        heat,
        x="date",
        y="hour",
        z="count",
        color_continuous_scale="Blues"
    )
    fig.update_layout(**theme_cfg)
    return ("Activity heatmap (date × hour)", fig)


# ============================================================
# 3. CALENDARIO SEMANAL (tipo GitHub)
# ============================================================

def fig_datetime_calendar(s, theme_cfg):
    df = _to_dt_index(s)
    if df.empty:
        return None

    df2 = pd.DataFrame({"date": df.index.date})
    df2 = df2.groupby("date").size().reset_index(name="count")

    df2["dow"] = pd.to_datetime(df2["date"]).dt.weekday
    df2["week"] = pd.to_datetime(df2["date"]).dt.isocalendar().week

    fig = px.density_heatmap(
        df2,
        x="week",
        y="dow",
        z="count",
        color_continuous_scale="Blues",
        labels={"dow": "Day of week", "week": "Week"}
    )
    fig.update_layout(**theme_cfg)
    return ("Calendar heatmap", fig)


# ============================================================
# FUNCIÓN PRINCIPAL PARA PROFILES
# ============================================================

def profile_datetime_figs(df, col, theme_cfg):
    series = df[col].dropna()
    if series.empty:
        return []

    figs = []

    f1 = fig_datetime_histogram(series, theme_cfg)
    if f1: figs.append(f1)

    f2 = fig_datetime_heatmap(series, theme_cfg)
    if f2: figs.append(f2)

    f3 = fig_datetime_calendar(series, theme_cfg)
    if f3: figs.append(f3)

    return figs


# ============================
# RESUMEN
# ============================

def var_summary_stats(df, col, vtype):
    s = df[col]
    n = len(s)
    n_missing = s.isna().sum()
    missing_pct = (n_missing / n * 100) if n > 0 else 0

    if vtype == "numeric":
        return {
            "n": n,
            "missing": n_missing,
            "missing_pct": missing_pct,
            "mean": s.mean(),
            "median": s.median(),
            "min": s.min(),
            "max": s.max(),
        }

    if vtype in ["categorical", "binary"]:
        return {
            "n": n,
            "missing": n_missing,
            "missing_pct": missing_pct,
            "n_unique": s.nunique(dropna=True),
            "top_values": s.value_counts(dropna=True).head(3).to_dict()
        }

    if vtype == "datetime":
        sd = s.dropna()
        if sd.empty:
            return {
                "n": n,
                "missing": n_missing,
                "missing_pct": missing_pct,
                "min": None,
                "max": None
            }
        return {
            "n": n,
            "missing": n_missing,
            "missing_pct": missing_pct,
            "min": sd.min(),
            "max": sd.max()
        }

    return {
        "n": n,
        "missing": n_missing,
        "missing_pct": missing_pct
    }


# ============================
# HTML PRINCIPAL
# ============================

def variable_profiles(df, theme="light"):

    is_dark = theme == "dark"
    theme_cfg = PLOTLY_DARK if is_dark else PLOTLY_LIGHT

    var_types = {
        "numeric": [],
        "categorical": [],
        "binary": [],
        "datetime": [],
        "other": [],
    }

    for col in df.columns:
        vtype = detect_var_type(df[col])
        if vtype in var_types:
            var_types[vtype].append(col)
        else:
            var_types["other"].append(col)

    def render_sidebar_section(title, vtype_key):
        vars_ = var_types[vtype_key]
        if not vars_:
            return ""
        items = "".join(
            f"<li><button class='vp-var-link' data-target='var-{col}'>{col}</button></li>"
            for col in vars_
        )
        return f"""
        <div class="vp-side-section">
            <button class="vp-type-link" data-target="section-{vtype_key}">
                {title} <span class="vp-count">({len(vars_)})</span>
            </button>
            <ul class="vp-var-list">{items}</ul>
        </div>
        """

    sidebar_html = f"""
    <div class="vp-sidebar">
        <h3 class="vp-sidebar-title">Data types</h3>
        {render_sidebar_section("Numeric", "numeric")}
        {render_sidebar_section("Categorical", "categorical")}
        {render_sidebar_section("Binary", "binary")}
        {render_sidebar_section("Datetime", "datetime")}
    </div>
    """

    def render_var_card(col, vtype):
        stats = var_summary_stats(df, col, vtype)

        if vtype == "numeric":
            summary_html = f"""
            <div class="vp-summary">
                <div><strong>Count:</strong> {stats['n']}</div>
                <div><strong>Missing:</strong> {stats['missing']} ({stats['missing_pct']:.1f}%)</div>
                <div><strong>Mean:</strong> {stats['mean']:.3f}</div>
                <div><strong>Median:</strong> {stats['median']:.3f}</div>
                <div><strong>Min:</strong> {stats['min']}</div>
                <div><strong>Max:</strong> {stats['max']}</div>
            </div>
            """
            figs = profile_numeric_figs(df, col, theme_cfg)

        elif vtype in ["categorical", "binary"]:
            top_vals = "".join(f"<li>{k}: {v}</li>" for k, v in stats["top_values"].items())
            summary_html = f"""
            <div class="vp-summary">
                <div><strong>Count:</strong> {stats['n']}</div>
                <div><strong>Missing:</strong> {stats['missing']} ({stats['missing_pct']:.1f}%)</div>
                <div><strong>Unique:</strong> {stats['n_unique']}</div>
                <div><strong>Top values:</strong></div>
                <ul class="vp-top-values">{top_vals}</ul>
            </div>
            """
            figs = profile_binary_figs(df, col, theme_cfg) if vtype == "binary" else profile_categorical_figs(df, col, theme_cfg)

        elif vtype == "datetime":
            summary_html = f"""
            <div class="vp-summary">
                <div><strong>Count:</strong> {stats['n']}</div>
                <div><strong>Missing:</strong> {stats['missing']} ({stats['missing_pct']:.1f}%)</div>
                <div><strong>Min:</strong> {stats['min']}</div>
                <div><strong>Max:</strong> {stats['max']}</div>
            </div>
            """
            figs = profile_datetime_figs(df, col, theme_cfg)

        else:
            summary_html = f"""
            <div class="vp-summary">
                <div><strong>Count:</strong> {stats['n']}</div>
                <div><strong>Missing:</strong> {stats['missing']} ({stats['missing_pct']:.1f}%)</div>
                <div>Type not directly supported.</div>
            </div>
            """
            figs = []

        if figs:
            fig_blocks = ""
            for title, fig in figs:
                extra_class = "calendar" if "Calendar" in title else ""
                fig_blocks += f"""
                    <div class="vp-fig {extra_class}">
                        <div class="vp-fig-title">{title}</div>
                        {fig.to_html(full_html=False, include_plotlyjs="cdn")}
                    </div>
                """
            figs_html = f"<div class='vp-fig-row'>{fig_blocks}</div>"
        else:
            figs_html = "<div class='vp-no-fig'>No suitable visualization available.</div>"

        return f"""
        <div class="vp-var-card" id="var-{col}">
            <div class="vp-var-header">
                <div class="vp-var-name">{col}</div>
                <div class="vp-var-type-tag">{vtype.capitalize()}</div>
            </div>
            {summary_html}
            {figs_html}
        </div>
        """

    def render_section(title, vtype_key):
        vars_ = var_types[vtype_key]
        if not vars_:
            return ""
        cards = "".join(render_var_card(col, vtype_key) for col in vars_)
        return f"""
        <section class="vp-section" id="section-{vtype_key}">
            <h2 class="vp-section-title">{title}</h2>
            {cards}
        </section>
        """

    main_html = f"""
    <div class="vp-main">
        {render_section("Numeric variables", "numeric")}
        {render_section("Categorical variables", "categorical")}
        {render_section("Binary variables", "binary")}
        {render_section("Datetime variables", "datetime")}
    </div>
    """

    back_to_top_button = """
    <button class="vp-back-to-top" id="vp-back-to-top">↑ Top</button>
    """

    script = """
    <script>
    document.documentElement.style.scrollBehavior = "smooth";

    document.querySelectorAll('.vp-type-link').forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.parentElement;
            section.classList.toggle('active');

            const targetId = btn.getAttribute('data-target');
            const el = document.getElementById(targetId);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    document.querySelectorAll('.vp-var-link').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const el = document.getElementById(targetId);

            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    const backToTop = document.getElementById("vp-back-to-top");

    window.addEventListener("scroll", () => {
        if (window.scrollY > 300) {
            backToTop.classList.add("visible");
        } else {
            backToTop.classList.remove("visible");
        }
    });

    backToTop.addEventListener("click", () => {
        document.getElementById("prof").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    </script>
    """

    return f"""
    <div class="vp-layout">
        {sidebar_html}
        {main_html}
    </div>
    {back_to_top_button}
    {script}
    """