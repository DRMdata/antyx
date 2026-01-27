import pandas as pd
import plotly.express as px

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


def plot_hist(df, col, theme_cfg):
    fig = px.histogram(df, x=col)
    fig.update_layout(**theme_cfg)
    return fig


def plot_kde(df, col, theme_cfg):
    fig = px.histogram(df, x=col, histnorm="density", marginal="violin")
    fig.update_layout(**theme_cfg)
    return fig


def plot_box(df, col, theme_cfg):
    fig = px.box(df, y=col)
    fig.update_layout(**theme_cfg)
    return fig


def plot_violin(df, col, theme_cfg):
    fig = px.violin(df, y=col, box=True)
    fig.update_layout(**theme_cfg)
    return fig


def plot_scatter(df, cols, theme_cfg):
    if len(cols) == 2:
        fig = px.scatter(df, x=cols[0], y=cols[1])
    elif len(cols) == 3:
        fig = px.scatter(df, x=cols[0], y=cols[1], color=cols[2])
    else:
        return None
    fig.update_layout(**theme_cfg)
    return fig


def plot_bars(df, col, theme_cfg):
    # Robust handling: ensure strings, strip whitespace, sort by frequency
    s = df[col].astype(str).fillna("NaN")
    s = s.str.strip()
    counts = s.value_counts(dropna=True)
    data = counts.reset_index()
    data.columns = ["category", "count"]
    data = data.sort_values("count", ascending=False).reset_index(drop=True)

    fig = px.bar(data, x="category", y="count", text="count")
    fig.update_layout(**theme_cfg)
    fig.update_traces(textposition="outside")
    return fig


def plot_heatmap(df, cols, theme_cfg):
    if len(cols) != 2:
        return None
    ct = pd.crosstab(df[cols[0]], df[cols[1]])
    fig = px.imshow(ct)
    fig.update_layout(**theme_cfg)
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

            html_blocks.append(
                "<div class='viz-item'>"
                + fig.to_html(full_html=False, include_plotlyjs="cdn")
                + "</div>"
            )

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