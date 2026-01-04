import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ============================
#  PLOTLY THEMES (LIGHT/DARK)
# ============================

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


# ============================
#  MAIN FUNCTION
# ============================

def correlation_analysis(df, threshold=0.5, theme="light"):
    numeric = df.select_dtypes(include="number")

    if numeric.shape[1] < 2:
        return "<p><strong>Not enough numeric columns to compute correlations.</strong></p>"

    corr = numeric.corr(method="spearman")
    cols = corr.columns.tolist()
    n = len(cols)

    # ----------------------------
    #  Truncate long labels
    # ----------------------------
    max_len = 12
    def truncate(label):
        return label if len(label) <= max_len else label[:max_len - 1] + "…"

    short_labels = [truncate(c) for c in cols]

    # ----------------------------
    #  Heatmap matrix
    # ----------------------------
    z = corr.values

    # customdata for hover
    full_x = np.array([[x for x in cols] for _ in cols])
    full_y = np.array([[y for _ in cols] for y in cols])
    customdata = np.dstack((full_x, full_y))

    # ----------------------------
    #  Theme selection
    # ----------------------------
    is_dark = theme == "dark"
    theme_cfg = PLOTLY_DARK if is_dark else PLOTLY_LIGHT

    # ----------------------------
    #  Heatmap
    # ----------------------------
    heatmap = go.Heatmap(
        z=z,
        x=list(range(n)),
        y=list(range(n)),
        colorscale="RdBu",
        zmin=-1,
        zmax=1,
        colorbar=dict(title="corr"),
        customdata=customdata,
        hovertemplate=(
            "X: %{customdata[0]}<br>"
            "Y: %{customdata[1]}<br>"
            "corr=%{z:.2f}<extra></extra>"
        )
    )

    fig = go.Figure(data=heatmap)

    # ----------------------------
    #  Layout (NO plotly_dark)
    # ----------------------------
    fig.update_layout(
        autosize=False,
        height=500,
        margin=dict(l=80, r=20, t=40, b=120),
        paper_bgcolor=theme_cfg["paper_bgcolor"],
        plot_bgcolor=theme_cfg["plot_bgcolor"],
        font=theme_cfg["font"]
    )

    # ----------------------------
    #  Axes
    # ----------------------------
    fig.update_xaxes(
        automargin=True,
        tickangle=90,
        tickmode="array",
        tickvals=list(range(n)),
        ticktext=short_labels,
        tickfont=theme_cfg["font"],
        title_font=theme_cfg["font"]
    )

    fig.update_yaxes(
        automargin=True,
        tickmode="array",
        tickvals=list(range(n)),
        ticktext=short_labels,
        tickfont=theme_cfg["font"],
        title_font=theme_cfg["font"]
    )

    # ----------------------------
    #  Convert Plotly figure to HTML
    # ----------------------------
    corr_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"responsive": False}
    )

    # ============================
    #  SIGNIFICANT CORRELATIONS
    # ============================

    significant_correlations = corr[(corr > threshold) | (corr < -threshold)]
    significant_correlations = significant_correlations.dropna(how="all")

    significant_values = []
    for i, row in significant_correlations.iterrows():
        for j, value in row.items():
            if i != j and not pd.isna(value) and corr.index.get_loc(i) < corr.columns.get_loc(j):
                significant_values.append((i, j, value))

    # ----------------------------
    #  TABLE HTML
    # ----------------------------
    if significant_values:
        table_html = """
        <table class="corr-table">
            <thead>
                <tr>
                    <th>Variable X</th>
                    <th>Variable Y</th>
                    <th>Correlation</th>
                </tr>
            </thead>
            <tbody>
        """
        for v1, v2, valor in significant_values:
            table_html += f"""
                <tr>
                    <td>{v1}</td>
                    <td>{v2}</td>
                    <td>{valor:.2f}</td>
                </tr>
            """
        table_html += """
            </tbody>
        </table>
        """
    else:
        table_html = "<em>No significant correlations have been detected.</em>"

    # ----------------------------
    #  FINAL HTML BLOCK
    # ----------------------------
    html = f"""
    <div class="corr-wrapper">
        <div class="corr-container">{corr_html}</div>
        <div class="corr-side">
            <div class="corr-list">
                <strong>Significant correlations (Threshold ±{threshold:.2f}):</strong><br>
                {table_html}
            </div>
        </div>
    </div>
    """

    return html