import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import plotly.graph_objects as go

def correlation_analysis(df, threshold=0.5, theme="light"):
    numeric = df.select_dtypes(include="number")

    if numeric.shape[1] < 2:
        return "<p><strong>Not enough numeric columns to compute correlations.</strong></p>"

    corr = numeric.corr(method="spearman")
    cols = corr.columns.tolist()
    n = len(cols)

    # Truncado visual
    max_len = 12
    def truncate(label):
        return label if len(label) <= max_len else label[:max_len - 1] + "…"

    short_labels = [truncate(c) for c in cols]

    # Matriz z
    z = corr.values

    # customdata: matriz NxN con (col_x_completa, col_y_completa)
    full_x = np.array([[x for x in cols] for _ in cols])   # filas: y, columnas: x
    full_y = np.array([[y for _ in cols] for y in cols])
    customdata = np.dstack((full_x, full_y))               # shape (n, n, 2)

    is_dark = theme == "dark"
    bg_color = "#1e1e1e" if is_dark else "white"
    text_color = "#e0e0e0" if is_dark else "#333"

    heatmap = go.Heatmap(
        z=z,
        x=list(range(n)),          # usamos índices numéricos
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

    fig.update_layout(
        template="plotly_dark" if is_dark else "plotly_white",
        autosize=False,
        height=500,
        margin=dict(l=80, r=20, t=40, b=120),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color)
    )

    # Ejes con etiquetas truncadas, pero usando índices como posición
    fig.update_xaxes(
        automargin=True,
        tickangle=90,
        tickmode="array",
        tickvals=list(range(n)),
        ticktext=short_labels,
        tickfont=dict(color=text_color),
        title_font=dict(color=text_color)
    )

    fig.update_yaxes(
        automargin=True,
        tickmode="array",
        tickvals=list(range(n)),
        ticktext=short_labels,
        tickfont=dict(color=text_color),
        title_font=dict(color=text_color)
    )

    corr_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"responsive": False}
    )

    # Significant correlations
    significant_correlations = corr[(corr > threshold) | (corr < -threshold)]
    significant_correlations = significant_correlations.dropna(how="all")

    significant_values = []
    for i, row in significant_correlations.iterrows():
        for j, value in row.items():
            if i != j and not pd.isna(value) and corr.index.get_loc(i) < corr.columns.get_loc(j):
                significant_values.append((i, j, value))

    list_html = "<div style='padding-left:24px;'>"
    list_html += "<strong>significant correlations (Threshold ±{:.2f}):</strong><br>".format(threshold)
    if not significant_values:
        list_html += "<em>No significant correlations have been detected.</em>"
    else:
        list_html += "<ul style='margin-top:10px;'>"
        for v1, v2, valor in significant_values:
            list_html += f"<li>{v1} vs {v2}: <strong>{valor:.2f}</strong></li>"
        list_html += "</ul>"
    list_html += "</div>"

    html = f"""
    <div style="display: flex; flex-wrap: wrap; align-items: flex-start;">
        <div style="flex: 1; min-width: 300px; max-width: 100%; overflow: hidden;">
            <div class="corr-container">{corr_html}</div>
        </div>
        <div style="flex: 1; min-width: 250px;">{list_html}</div>
    </div>
    """

    return html