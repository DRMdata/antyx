import pandas as pd
import plotly.express as px
import numpy as np
import calendar
from statsmodels.tsa.stattools import acf
import scipy.stats as stats
import plotly.graph_objects as go

from antyx.utils.utils import save_fig_json

PLOTLY_LIGHT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(color="#333")
)

PLOTLY_DARK = dict(
    paper_bgcolor="#1e1e1e",
    plot_bgcolor="#1e1e1e",
    font=dict(color="#e0e0e0")
)

# ==========================
# GENERACIÓN DE LOS GRÁFICOS
# ==========================

def _base_layout(theme_cfg, width=500, height=350, showlegend=False):
    return dict(
        width=width,
        height=height,
        **theme_cfg,
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            x=0,
            y=1.1,
            xanchor="left",
            yanchor="bottom"
        ),
        margin=dict(t=20, b=10, l=10, r=10)
    )

'''
def _base_layout(theme_cfg, width=500, height=350, showlegend=False):
    return dict(
        width=width,
        height=height,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.15)", gridwidth=1),
        **theme_cfg,
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            x=0,
            y=1.1,
            xanchor="left",
            yanchor="bottom"
        ),
        margin=dict(t=20, b=10, l=10, r=10)
    )
'''

def _default_hoverlabel():
    return dict(
        bgcolor="white",
        bordercolor="rgba(0,0,0,0.15)",
        font=dict(size=15, color="black")
    )


def plot_hist(df, col, theme_cfg):
    fig = px.histogram(df, x=col)

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_kde(df, col, theme_cfg):
    fig = px.histogram(df, x=col, histnorm="density", marginal="violin")

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_box(df, col, theme_cfg):
    fig = px.box(df, y=col)

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(
        hovertemplate="<b>%{y}</b><extra></extra>",
        hoverlabel=_default_hoverlabel()
    )

    return fig


def plot_violin(df, col, theme_cfg):
    fig = px.violin(df, y=col, box=True)

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_scatter(df, cols, theme_cfg):
    if len(cols) == 2:
        fig = px.scatter(df, x=cols[0], y=cols[1])
    elif len(cols) == 3:
        fig = px.scatter(df, x=cols[0], y=cols[1], color=cols[2])
    else:
        return None

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(
        hoverlabel=_default_hoverlabel(),
    )
    if len(df) > 20000:
        fig.update_traces(type="scattergl")

    return fig


def plot_bars(df, col, theme_cfg):
    s = df[col].astype(str).fillna("NaN").str.strip()
    counts = s.value_counts(dropna=True)
    data = counts.reset_index()
    data.columns = ["category", "count"]
    data = data.sort_values("count", ascending=False).reset_index(drop=True)

    fig = px.bar(data, x="category", y="count", text="count")

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(
        textposition="inside",
        hoverlabel=_default_hoverlabel()
    )

    return fig


def plot_heatmap(df, cols, theme_cfg):
    if len(cols) != 2:
        return None
    ct = pd.crosstab(df[cols[0]], df[cols[1]])
    fig = px.imshow(ct)

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(
        hoverlabel=_default_hoverlabel()
        # si quieres, aquí podrías usar heatmapgl, pero yo lo dejaría SVG
        # type="heatmapgl"
    )

    return fig


def plot_qq(df, col, theme_cfg):
    s = df[col].dropna()
    if s.empty:
        return None

    osm, osr = stats.probplot(s, dist="norm", fit=False)

    fig = go.Figure()

    showlegend = len(fig.data) > 1

    fig.add_trace(go.Scatter(
        x=osm,
        y=osr,
        mode="markers",
        marker=dict(color="rgba(50, 100, 200, 0.7)", size=6),
        hoverlabel=_default_hoverlabel()
    ))

    fig.add_trace(go.Scatter(
        x=osm,
        y=osm,
        mode="lines",
        line=dict(color="black", dash="dash"),
        showlegend=False
    ))

    fig.update_layout(
        xaxis_title="Theoretical quantiles",
        yaxis_title="Sample quantiles",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )

    return fig


def plot_cdf(df, col, theme_cfg):
    s = df[col].dropna().sort_values()
    if s.empty:
        return None

    y = np.linspace(0, 1, len(s))
    fig = px.line(x=s, y=y)

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title=col,
        yaxis_title="Cumulative probability",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(
        hoverlabel=_default_hoverlabel()
    )

    return fig


def plot_scatter_index(df, col, theme_cfg):
    s = df[col].dropna()
    if s.empty:
        return None

    fig = px.scatter(x=s.index, y=s.values)

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Index",
        yaxis_title=col,
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(
        hoverlabel=_default_hoverlabel(),
    )
    if len(df) > 20000:
        fig.update_traces(type="scattergl")

    return fig


def plot_treemap(df, col, theme_cfg):
    s = df[col].astype(str).fillna("NaN").str.strip()
    counts = s.value_counts().reset_index()
    counts.columns = ["category", "count"]

    fig = px.treemap(counts, path=["category"], values="count")

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_pareto(df, col, theme_cfg):
    s = df[col].astype(str).fillna("NaN").str.strip()
    counts = s.value_counts().reset_index()
    counts.columns = ["category", "count"]
    counts["cum_pct"] = counts["count"].cumsum() / counts["count"].sum()

    fig = go.Figure()

    # Barras
    fig.add_trace(go.Bar(
        x=counts["category"],
        y=counts["count"],
        name="Count",
        marker_color="rgba(50, 100, 200, 0.7)",
        hoverlabel=_default_hoverlabel()
    ))

    # Línea acumulada
    fig.add_trace(go.Scatter(
        x=counts["category"],
        y=counts["cum_pct"],
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="black"),
        hoverlabel=_default_hoverlabel()
    ))

    # Layout base
    fig.update_layout(
        yaxis=dict(
            title="Count",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.15)",
            gridwidth=1
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            range=[0, 1],
            side="right",
            showgrid=False
        ),
        xaxis=dict(showgrid=False),
        **_base_layout(theme_cfg, width=450, height=300, showlegend=True)
    )

    fig.update_xaxes(title="Category")
    fig.update_yaxes(title="Count")

    return fig


def plot_donut(df, col, theme_cfg):
    s = df[col].astype(str).fillna("NaN").str.strip()
    counts = s.value_counts().reset_index()
    counts.columns = ["category", "count"]

    fig = px.pie(counts, names="category", values="count", hole=0.5)

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def _dt_index(s):
    s = pd.to_datetime(s.dropna(), errors="coerce")
    s = s.dropna()
    if s.empty:
        return None
    df = s.to_frame(name="dt")
    df.index = df["dt"]
    return df


def plot_timeseries(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    range_days = (base.index.max() - base.index.min()).days
    if range_days <= 31:
        freq = "D"
    elif range_days <= 180:
        freq = "W"
    elif range_days <= 730:
        freq = "M"
    else:
        freq = "Y"

    grouped = base.resample(freq).size().reset_index(name="count")

    fig = px.line(grouped, x="dt", y="count")

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Count",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_datetime_histogram(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    range_days = (base.index.max() - base.index.min()).days
    if range_days <= 31:
        freq = "D"
    elif range_days <= 180:
        freq = "W"
    elif range_days <= 730:
        freq = "M"
    else:
        freq = "Y"

    grouped = base.resample(freq).size().reset_index(name="count")

    fig = px.bar(grouped, x="dt", y="count")

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Count",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_hour_distribution(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    hours = base.index.hour.value_counts().sort_index()
    data = hours.reset_index()
    data.columns = ["hour", "count"]

    fig = px.bar(data, x="hour", y="count")

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="Count",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_weekday_distribution(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    weekday_names = list(calendar.day_name)
    counts = base.index.weekday.value_counts().sort_index()
    data = counts.reset_index()
    data.columns = ["weekday", "count"]
    data["weekday"] = data["weekday"].map(lambda x: weekday_names[x])

    fig = px.bar(
        data,
        x="weekday",
        y="count",
        category_orders={"weekday": weekday_names}
    )

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Day of week",
        yaxis_title="Count",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_datetime_heatmap(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None
    if base.index.hour.nunique() <= 1:
        return None

    weekday_names = list(calendar.day_name)

    df2 = pd.DataFrame({
        "weekday": base.index.weekday,
        "hour": base.index.hour
    })
    df2["weekday_name"] = df2["weekday"].map(lambda d: weekday_names[d])
    df2["weekday_name"] = pd.Categorical(
        df2["weekday_name"],
        categories=weekday_names,
        ordered=True
    )

    heat = df2.groupby(["weekday_name", "hour"]).size().reset_index(name="count")

    fig = px.density_heatmap(
        heat,
        x="weekday_name",
        y="hour",
        z="count",
        color_continuous_scale="Blues",
        category_orders={"weekday_name": weekday_names}
    )

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_datetime_calendar(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    df2 = pd.DataFrame({"date": base.index.date})
    df2 = df2.groupby("date").size().reset_index(name="count")

    weekday_names = list(calendar.day_name)
    df2["dow"] = pd.to_datetime(df2["date"]).dt.weekday
    df2["dow_name"] = df2["dow"].map(lambda d: weekday_names[d])
    df2["dow_name"] = pd.Categorical(
        df2["dow_name"],
        categories=weekday_names,
        ordered=True
    )

    df2["week"] = pd.to_datetime(df2["date"]).dt.isocalendar().week

    fig = px.density_heatmap(
        df2,
        x="week",
        y="dow_name",
        z="count",
        color_continuous_scale="Blues",
        category_orders={"dow_name": weekday_names}
    )

    showlegend = len(fig.data) > 1

    fig.update_layout(**_base_layout(theme_cfg, showlegend=showlegend))
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_acf(df, col, theme_cfg, nlags=40):
    base = _dt_index(df[col])
    if base is None:
        return None

    daily = base.resample("D").size()
    acf_vals = acf(daily, nlags=nlags, fft=True)

    fig = px.bar(x=list(range(len(acf_vals))), y=acf_vals)

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Lag",
        yaxis_title="ACF",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_lag(df, col, theme_cfg, lag=1):
    base = _dt_index(df[col])
    if base is None:
        return None

    daily = base.resample("D").size()
    if len(daily) <= lag:
        return None

    fig = px.scatter(x=daily[:-lag], y=daily[lag:])

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Value(t)",
        yaxis_title=f"Value(t+{lag})",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(
        hoverlabel=_default_hoverlabel(),
    )
    if len(df) > 20000:
        fig.update_traces(type="scattergl")

    return fig


def plot_month_day_heatmap(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    df2 = pd.DataFrame({
        "month": base.index.month,
        "day": base.index.day
    })

    heat = df2.groupby(["month", "day"]).size().reset_index(name="count")

    fig = px.density_heatmap(
        heat,
        x="day",
        y="month",
        z="count",
        color_continuous_scale="Blues"
    )

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Day",
        yaxis_title="Month",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig


def plot_interarrival(df, col, theme_cfg):
    base = _dt_index(df[col])
    if base is None:
        return None

    diffs = base.index.to_series().diff().dropna().dt.total_seconds() / 3600
    if diffs.empty:
        return None

    fig = px.histogram(diffs, nbins=30)

    showlegend = len(fig.data) > 1

    fig.update_layout(
        xaxis_title="Inter-arrival time (hours)",
        yaxis_title="Count",
        **_base_layout(theme_cfg, showlegend=showlegend)
    )
    fig.update_traces(hoverlabel=_default_hoverlabel())

    return fig



def visualizations(df, theme="light"):
    options = "".join([f"<option value='{col}'>{col}</option>" for col in df.columns])

    html = f"""
    <div class="viz-controls">

        <label>Select variables:</label>
        <select id="viz-var-select" multiple class="viz-select">
            {options}
        </select>

        <div class="viz-buttons">
            <button onclick="setVizType('hist')">Histogram</button>
            <button onclick="setVizType('kde')">KDE</button>
            <button onclick="setVizType('box')">Boxplot</button>
            <button onclick="setVizType('violin')">Violin</button>
            <button onclick="setVizType('scatter')">Scatter</button>
            <button onclick="setVizType('bars')">Bars</button>
            <button onclick="setVizType('heatmap')">Heatmap</button>
        </div>

    </div>

    <div id="viz-output" class="viz-grid"></div>

    <script>

    let currentVizType = null;

    function setVizType(type) {{
        currentVizType = type;
        updateVisualizations();
    }}

    async function updateVisualizations() {{
        const vars = Array.from(document.getElementById("viz-var-select").selectedOptions)
                          .map(o => o.value);

        try {{
            const r = await fetch("/viz", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json"
                }},
                body: JSON.stringify({{
                    type: currentVizType,
                    vars: vars
                }})
            }});

            const html = await r.text();
            const container = document.getElementById("viz-output");
            container.innerHTML = html;

            // Helper: ensure Plotly is loaded (returns a Promise)
            function ensurePlotly() {{
              return new Promise((resolve, reject) => {{
                if (window.Plotly) return resolve();
                const existing = Array.from(document.scripts).find(s => s.src && s.src.includes('plotly.min.js'));
                if (existing) {{
                  existing.addEventListener('load', () => resolve());
                  existing.addEventListener('error', (e) => reject(e));
                  return;
                }}
                const s = document.createElement('script');
                s.src = '/antyx/static/plotly.min.js';
                s.onload = () => resolve();
                s.onerror = (e) => reject(e);
                document.head.appendChild(s);
              }});
            }}

            try {{
              await ensurePlotly();
            }} catch (e) {{
              console.error('Failed to load Plotly:', e);
              return;
            }}

            // Re-execute scripts inside the returned HTML (inline and external)
            const scripts = Array.from(container.querySelectorAll('script'));
            for (const old of scripts) {{
              const s = document.createElement('script');
              for (let i = 0; i < old.attributes.length; i++) {{
                const attr = old.attributes[i];
                s.setAttribute(attr.name, attr.value);
              }}
              if (old.src) {{
                await new Promise((res) => {{
                  s.onload = () => res();
                  s.onerror = (e) => {{
                    console.error('Error loading script', old.src, e);
                    res();
                  }};
                  document.body.appendChild(s);
                }});
              }} else {{
                s.text = old.innerHTML;
                document.body.appendChild(s);
              }}
              old.remove();
            }}

            // Small delay to let Plotly initialize traces, then resize
            requestAnimationFrame(() => {{
              setTimeout(() => {{
                if (window.Plotly) {{
                  container.querySelectorAll('.plotly-graph-div').forEach(g => {{
                    try {{ Plotly.Plots.resize(g); }} catch (e) {{}}
                  }});
                }}
              }}, 120);
            }});

        }} catch (err) {{
            console.error('fetch /viz error', err);
            document.getElementById("viz-output").innerHTML = "<p>Error loading visualizations</p>";
        }}
    }}

    </script>

    <!-- LAZY LOADING PARA VISUALIZATIONS -->
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

    function lazyLoadViz() {{
        const figs = document.querySelectorAll(".viz-fig");
        const observer = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    loadPlotlyFigure(entry.target);
                }}
            }});
        }}, {{ rootMargin: "200px" }});

        figs.forEach(fig => observer.observe(fig));
    }}

    document.addEventListener("DOMContentLoaded", lazyLoadViz);
    </script>
    """
    return html


def generate_viz_html(df, vars, type, theme):
    is_dark = theme == "dark"
    theme_cfg = PLOTLY_DARK if is_dark else PLOTLY_LIGHT

    html_blocks = []

    if not vars:
        return "<p>Please select one or more variables.</p>"

    if type in ["hist", "kde", "box", "violin", "bars"]:
        for col in vars:
            if col not in df.columns:
                continue

            series = df[col]

            if pd.api.types.is_numeric_dtype(series):
                if type == "hist":
                    fig = plot_hist(df, col, theme_cfg)
                elif type == "kde":
                    fig = plot_kde(df, col, theme_cfg)
                elif type == "box":
                    fig = plot_box(df, col, theme_cfg)
                elif type == "violin":
                    fig = plot_violin(df, col, theme_cfg)
                else:
                    continue
            else:
                if type == "bars":
                    fig = plot_bars(df, col, theme_cfg)
                else:
                    continue

            json_path = f"viz_figs/{col}_{type}.json"
            save_fig_json(fig, json_path)

            html_blocks.append(f"""
            <div class='viz-item'>
                <div id="viz-{col}-{type}" class="viz-fig" data-json="{json_path}"></div>
            </div>
            """)

        return "".join(html_blocks)

    if type == "scatter":
        if len(vars) < 2:
            return "<p>Please select at least 2 numeric variables for scatter.</p>"

        fig = plot_scatter(df, vars, theme_cfg)
        if fig is None:
            return "<p>Scatter requires 2 or 3 numeric variables.</p>"

        return (
            "<div class='viz-item'>"
            + fig.to_html(full_html=False, include_plotlyjs="cdn")
            + "</div>"
        )

    if type == "heatmap":
        if len(vars) != 2:
            return "<p>Heatmap requires exactly 2 categorical variables.</p>"

        fig = plot_heatmap(df, vars, theme_cfg)
        if fig is None:
            return "<p>Heatmap requires 2 categorical variables.</p>"

        return (
            "<div class='viz-item'>"
            + fig.to_html(full_html=False, include_plotlyjs="cdn")
            + "</div>"
        )

    return "<p>Unknown visualization type.</p>"