import pandas as pd
import plotly.express as px
import os

# THEMES

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

# GRAPH FUNCTIONS

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
    counts = df[col].value_counts(dropna=True)
    data = counts.reset_index()
    data.columns = ["category", "count"]

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


# EXPORT

def export_figure(fig, output_dir=".", name="visualization"):
    path = os.path.join(output_dir, f"{name}.png")
    fig.write_image(path)
    return path


# HTML GENERATION FOR VISUALIZATIONS TAB

def visualizations(df, theme="light"):
    """
    Returns the HTML block for the Visualizations tab.
    Includes:
    - selector múltiple
    - botones de tipo de gráfico
    - contenedor de gráficos
    - JS para fetch("/viz") y fetch("/viz-export")
    """

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

    function updateVisualizations() {{
        const vars = Array.from(document.getElementById("viz-var-select").selectedOptions)
                          .map(o => o.value);

        fetch("/viz", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{
                type: currentVizType,
                vars: vars
            }})
        }})
        .then(r => r.text())
        .then(html => {{
            document.getElementById("viz-output").innerHTML = html;
            // Execute Plotly intern scripts
            document.querySelectorAll("#viz-output script").forEach(oldScript => {{
                const newScript = document.createElement("script");
                if (oldScript.src) {{
                    newScript.src = oldScript.src;
                }} else {{
                    newScript.textContent = oldScript.textContent;
                }}
                oldScript.replaceWith(newScript);
            }});

        }});
    }}

    </script>
    """

    return html


# DYNAMIC GRAPH GENERATION FOR /viz

def generate_viz_html(df, vars, type, theme):
    is_dark = theme == "dark"
    theme_cfg = PLOTLY_DARK if is_dark else PLOTLY_LIGHT

    html_blocks = []

    if not vars:
        return "<p>Please select one or more variables.</p>"

    # UNIVARIATE GRAPHS
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
                f"<div class='viz-item'>{fig.to_html(full_html=False, include_plotlyjs=False)}</div>"
            )

        return "".join(html_blocks)

    # SCATTER (2–3 variables)
    if type == "scatter":
        if len(vars) < 2:
            return "<p>Please select at least 2 numeric variables for scatter.</p>"

        fig = plot_scatter(df, vars, theme_cfg)
        if fig is None:
            return "<p>Scatter requires 2 or 3 numeric variables.</p>"

        return f"<div class='viz-item'>{fig.to_html(full_html=False, include_plotlyjs=False)}</div>"

    # HEATMAP (2 categorical)
    if type == "heatmap":
        if len(vars) != 2:
            return "<p>Heatmap requires exactly 2 categorical variables.</p>"

        fig = plot_heatmap(df, vars, theme_cfg)
        if fig is None:
            return "<p>Heatmap requires 2 categorical variables.</p>"

        return f"<div class='viz-item'>{fig.to_html(full_html=False, include_plotlyjs=False)}</div>"

    return "<p>Unknown visualization type.</p>"

