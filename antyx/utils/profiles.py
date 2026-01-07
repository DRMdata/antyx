import pandas as pd
from antyx.utils.visualizations import (
    plot_hist,
    plot_kde,
    plot_box,
    plot_violin,
    plot_scatter,
    plot_bars,
    plot_heatmap,
    PLOTLY_LIGHT,
    PLOTLY_DARK,
)

def detect_var_type(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    unique_ratio = series.nunique(dropna=True) / max(len(series), 1)
    if pd.api.types.is_string_dtype(series) or unique_ratio < 0.5:
        return "categorical"
    return "other"


# === FIGURAS ===

def profile_numeric_figs(df, col, theme_cfg):
    return [
        ("Histogram", plot_hist(df, col, theme_cfg)),
        ("Boxplot", plot_box(df, col, theme_cfg)),
    ]

def profile_categorical_figs(df, col, theme_cfg):
    return [("Bar chart", plot_bars(df, col, theme_cfg))]

def profile_boolean_figs(df, col, theme_cfg):
    return profile_categorical_figs(df, col, theme_cfg)

def profile_datetime_figs(df, col, theme_cfg):
    series = df[col].dropna()
    if series.empty:
        return []

    s = series.sort_values()
    counts = s.value_counts().sort_index().reset_index()
    counts.columns = [col, "count"]

    import plotly.express as px
    fig = px.line(counts, x=col, y="count")
    fig.update_layout(**theme_cfg)
    return [("Time series", fig)]


# === RESUMEN ===

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

    if vtype in ["categorical", "boolean"]:
        return {
            "n": n,
            "missing": n_missing,
            "missing_pct": missing_pct,
            "n_unique": s.nunique(dropna=True),
            "top_values": s.value_counts(dropna=True).head(3).to_dict()
        }

    if vtype == "datetime":
        if s.dropna().empty:
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
            "min": s.min(),
            "max": s.max()
        }

    return {
        "n": n,
        "missing": n_missing,
        "missing_pct": missing_pct
    }


# === HTML PRINCIPAL ===

def variable_profiles(df, theme="light"):
    is_dark = theme == "dark"
    theme_cfg = PLOTLY_DARK if is_dark else PLOTLY_LIGHT

    var_types = {"numeric": [], "categorical": [], "boolean": [], "datetime": [], "other": []}
    for col in df.columns:
        vtype = detect_var_type(df[col])
        var_types[vtype].append(col)

    # === SIDEBAR ===

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
            <ul class="vp-var-list">
                {items}
            </ul>
        </div>
        """

    sidebar_html = f"""
    <div class="vp-sidebar">
        <h3 class="vp-sidebar-title">Data types</h3>
        {render_sidebar_section("Numeric", "numeric")}
        {render_sidebar_section("Categorical", "categorical")}
        {render_sidebar_section("Boolean", "boolean")}
        {render_sidebar_section("Datetime", "datetime")}
    </div>
    """

    # === TARJETAS ===

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

        elif vtype in ["categorical", "boolean"]:
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
            figs = profile_categorical_figs(df, col, theme_cfg)

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
            fig_blocks = "".join(
                f"""
                <div class="vp-fig">
                    <div class="vp-fig-title">{title}</div>
                    {fig.to_html(full_html=False, include_plotlyjs=False)}
                </div>
                """
                for title, fig in figs
            )
            figs_html = f"<div class='vp-fig-row'>{fig_blocks}</div>"
        else:
            figs_html = "<div class='vp-no-fig'>No suitable visualization available.</div>"

        return f"""
        <div class="vp-var-card" id="var-{col}">
            <div class="vp-var-header">
                <div class="vp-var-name">{col}</div>
                <div class="vp-var-type-tag">{vtype}</div>
            </div>
            {summary_html}
            {figs_html}
        </div>
        """

    # === SECCIONES ===

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
        {render_section("Boolean variables", "boolean")}
        {render_section("Datetime variables", "datetime")}
    </div>
    """

    # === JS ===

    full_html = f"""
    <div class="vp-layout">
        {sidebar_html}
        {main_html}
    </div>

    <script>
    document.documentElement.style.scrollBehavior = "smooth";

    // Expandir/cerrar tipos
    document.querySelectorAll('.vp-type-link').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const section = btn.parentElement;
            section.classList.toggle('active');

            const targetId = btn.getAttribute('data-target');
            const el = document.getElementById(targetId);
            if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }});
    }});

    // Navegar a variables
    document.querySelectorAll('.vp-var-link').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const targetId = btn.getAttribute('data-target');
            const el = document.getElementById(targetId);
            if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }});
    }});
    </script>
    """

    return full_html