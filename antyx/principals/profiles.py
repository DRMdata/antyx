import numpy as np

from antyx.utils.types import detect_var_type
from antyx.utils.utils import save_fig_json

from antyx.principals.visualizations import (
    plot_hist,
    plot_box,
    plot_bars,
    plot_violin,
    plot_heatmap,
    plot_cdf,
    plot_qq,
    plot_donut,
    plot_pareto,
    plot_kde,
    plot_treemap,
    plot_scatter,
    plot_scatter_index,
    plot_datetime_heatmap,
    plot_datetime_histogram,
    plot_datetime_calendar,
    plot_acf,
    plot_lag,
    plot_timeseries,
    plot_interarrival,
    plot_hour_distribution,
    plot_month_day_heatmap,
    plot_weekday_distribution,
    PLOTLY_LIGHT,
    PLOTLY_DARK,
)


# ============================
# FIGURAS
# ============================

def profile_numeric_figs(df, col, theme_cfg):
    figs = []

    def add(title, fig):
        if fig is not None:
            figs.append((title, fig))

    add("Histogram", plot_hist(df, col, theme_cfg))
    add("Violin", plot_violin(df, col, theme_cfg))
    add("QQ-plot", plot_qq(df, col, theme_cfg))
    add("CDF", plot_cdf(df, col, theme_cfg))
    #add("Scatter vs index", plot_scatter_index(df, col, theme_cfg))

    return figs


def profile_categorical_figs(df, col, theme_cfg):
    figs = []

    def add(title, fig):
        if fig is not None:
            figs.append((title, fig))

    add("Pareto chart", plot_pareto(df, col, theme_cfg))

    return figs


def profile_binary_figs(df, col, theme_cfg):
    figs = []

    def add(title, fig):
        if fig is not None:
            figs.append((title, fig))

    add("Bar chart", plot_bars(df, col, theme_cfg))

    return figs

def profile_datetime_figs(df, col, theme_cfg):
    figs = []

    def add(title, fig):
        if fig is not None:
            figs.append((title, fig))

    add("Distribution over time", plot_datetime_histogram(df, col, theme_cfg))
    if np.issubdtype(df[col].dtype, np.datetime64):
        ser = df[col].dropna()
        if ser.dt.hour.nunique() > 1 or ser.dt.minute.nunique() > 1:
            add("Hour distribution", plot_hour_distribution(df, col, theme_cfg))
    add("Weekday distribution", plot_weekday_distribution(df, col, theme_cfg))
    add("Activity heatmap (weekday × hour)", plot_datetime_heatmap(df, col, theme_cfg))
    add("Month × day heatmap", plot_month_day_heatmap(df, col, theme_cfg))
    #add("Weekday x week distribution", plot_datetime_calendar(df, col, theme_cfg))
    #add("Autocorrelation (ACF)", plot_acf(df, col, theme_cfg))
    #add("Lag plot", plot_lag(df, col, theme_cfg))

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

    tooltip_viz_map = {
        "Histogram": (
            "A histogram shows the distribution of a numerical variable by grouping values "
            "into bins and counting how many observations fall into each bin. It helps reveal "
            "the shape of the distribution, detect skewness, identify outliers, and understand "
            "where values are concentrated."
        ),

        "Boxplot": (
            "A boxplot summarizes a numeric variable using the minimum, first quartile, median, "
            "third quartile, and maximum. It highlights the central tendency, spread, and potential "
            "outliers, making it ideal for detecting skewness and comparing distributions."
        ),

        "Bar chart": (
            "A bar chart displays the frequency of each category in a categorical variable. "
            "It helps identify the most common categories, rare categories, and imbalances in the "
            "distribution, as well as potential data quality issues such as inconsistent labels."
        ),

        "Violin": (
            "A violin plot combines a boxplot with a kernel density estimate, showing both the "
            "summary statistics and the full shape of the distribution. It is useful for detecting "
            "multimodality, density concentration, and complex distribution patterns."
        ),

        "Heatmap": (
            "A heatmap visualizes the frequency of combinations of two categorical variables. "
            "It highlights interactions, co-occurrence patterns, dominant category pairs, and "
            "sparse or empty combinations."
        ),

        "CDF": (
            "A Cumulative Distribution Function (CDF) plot shows the cumulative probability of a "
            "numeric variable. For any value x, the CDF indicates the proportion of observations "
            "less than or equal to x. It is useful for understanding percentiles, thresholds, and "
            "how quickly the distribution accumulates."
        ),

        "QQ-plot": (
            "A QQ-plot compares the quantiles of the data to the quantiles of a theoretical normal "
            "distribution. If the points follow a straight line, the data is approximately normal. "
            "Deviations indicate skewness, heavy tails, or outliers."
        ),

        "Donut chart": (
            "A donut chart displays the proportion of each category as segments of a circular ring. "
            "It is useful for visualizing simple categorical distributions, especially binary or "
            "low-cardinality variables."
        ),

        "Pareto chart": (
            "A Pareto chart combines a bar chart with a cumulative percentage line. It highlights "
            "the most influential categories and follows the 80/20 principle, showing how a small "
            "number of categories often account for most of the total frequency."
        ),

        "KDE": (
            "A Kernel Density Estimate (KDE) plot is a smoothed version of a histogram that estimates "
            "the probability density function of a numeric variable. It helps identify peaks, "
            "multimodality, and the overall shape of the distribution without binning artifacts."
        ),

        "Treemap": (
            "A treemap represents categories as nested rectangles sized according to their frequency. "
            "It is ideal for visualizing many categories at once and identifying dominant or rare "
            "categories in a compact layout."
        ),

        "Scatter plot": (
            "A scatter plot visualizes the relationship between two or three numeric variables. "
            "It reveals correlation, clusters, nonlinear patterns, heteroscedasticity, and outliers. "
            "If a third variable is included, it is encoded using color."
        ),

        "Scatter vs index": (
            "This plot shows the values of a numeric variable against their row index. It is useful "
            "for detecting trends, drifts, sudden jumps, periodic patterns, or anomalies in ordered "
            "data, even when the column is not a timestamp."
        ),

        "Activity heatmap (weekday × hour)": (
            "A weekday × hour heatmap shows event counts across days of the week and hours of the day. "
            "It reveals daily and weekly activity patterns, peak usage windows, and unusual time blocks."
        ),

        "Distribution over time": (
            "A datetime histogram groups timestamps into time buckets (daily, weekly, monthly, or yearly) "
            "and counts events in each bucket. It helps identify periods of high or low activity, "
            "long-term changes, and temporal density patterns."
        ),

        "Weekday x week distribution": (
            "A weekday x week distribution displays event counts per day in a GitHub-style weekly layout. "
            "It reveals long-term temporal patterns, seasonal cycles, daily variations, and anomalies "
            "across weeks and months."
        ),

        "Autocorrelation (ACF)": (
            "An autocorrelation plot (ACF) shows how a time series correlates with itself at different "
            "lags. It helps detect periodicity, seasonality, memory effects, and whether the process "
            "is random or structured."
        ),

        "Lag plot": (
            "A lag plot visualizes the relationship between a time series value at time t and its value "
            "at time t + lag. It is useful for detecting serial correlation, nonlinear relationships, "
            "and randomness. A linear pattern indicates strong autocorrelation."
        ),

        "plot_timeseries": (
            "A time series plot shows how event counts evolve over time, aggregated at an appropriate "
            "frequency (daily, weekly, monthly, or yearly). It reveals trends, seasonality, bursts of "
            "activity, and anomalies."
        ),

        "Inter-arrival histogram": (
            "An inter-arrival histogram shows the distribution of time differences between consecutive "
            "events. It is ideal for analyzing event frequency, detecting bursts or pauses, and "
            "understanding system load or arrival processes."
        ),

        "Hour distribution": (
            "This plot shows how events are distributed across the 24 hours of the day. It helps identify "
            "peak hours, night-time or daytime patterns, and human or system activity cycles."
        ),

        "Month × day heatmap": (
            "A month × day heatmap shows event counts for each day of each month. It reveals annual "
            "seasonality, monthly patterns, special days, and differences between months."
        ),

        "Weekday distribution": (
            "This plot shows how events are distributed across the days of the week. It highlights "
            "weekday vs weekend patterns, operational cycles, and weekly seasonality."
        ),
    }


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
            figs = profile_binary_figs(df, col, theme_cfg) if vtype == "binary" else profile_categorical_figs(df, col,
                                                                                                              theme_cfg)

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

        # FIGURAS
        if figs:
            fig_blocks = ""

            for title, fig in figs:
                extra_class = "calendar" if "Calendar" in title else ""

                help_text = tooltip_viz_map.get(title, "")
                help_icon = f"""
                    <span class='vp-fig-help'>
                        ℹ️
                        <span class='vp-fig-help-text'>{help_text}</span>
                    </span>
                """ if help_text else ""

                # NUEVO: externalizar datos
                div_id = f"fig-{col}-{title.replace(' ', '_')}"
                json_path = f"figs/{col}/{title.replace(' ', '_')}.json"

                save_fig_json(fig, json_path)

                fig_blocks += f"""
                    <div id="{div_id}" class="vp-fig {extra_class}" data-json="{json_path}">
                        <div class="vp-fig-title">
                            {title} {help_icon}
                        </div>
                        <div class="vp-fig-plot"></div>
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
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
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

    <!-- LAZY LOADING DE PLOTLY -->
    <script>
    function loadPlotlyFigure(div) {{
        const url = div.dataset.json;
        if (!url || div.dataset.loaded === "1") return;

        fetch(url)
            .then(r => r.json())
            .then(obj => {{
                Plotly.newPlot(div.id, obj.data, obj.layout);
                div.dataset.loaded = "1";
            }});
    }}

    function lazyLoadPlots() {{
        const figs = document.querySelectorAll(".vp-fig");
        const observer = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    loadPlotlyFigure(entry.target);
                }}
            }});
        }}, {{ rootMargin: "200px" }});

        figs.forEach(fig => observer.observe(fig));
    }}

    document.addEventListener("DOMContentLoaded", lazyLoadPlots);
    </script>
    """