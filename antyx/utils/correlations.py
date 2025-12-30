import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
import pandas as pd

def correlation_analysis(df, threshold=0.5):
    """Generates a heatmap with de correlations of the DataFrame and
    a list with correlations between the columns.

    Args:
        df (pd.DataFrame): DataFrame to analyze.
        threshold (float, optional): Threshold for the correlation.

    Returns:
        Heatmap: Heatmap with correlations between the columns.
        List: Correlations between the columns.
    """
    numeric = df.select_dtypes(include='number')
    num_columns = len(numeric.columns)

    if num_columns > 1:
        corr = numeric.corr()

        # Heatmap
        fig, ax = plt.subplots(figsize=(num_columns * 0.8, num_columns * 0.6))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', ax=ax)
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        img_html = f'<img src="data:image/png;base64,{encoded}" style="max-width:100%; height:auto;"/>'

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

        # Design
        html = """
        <div style="display: flex; flex-wrap: wrap; align-items: flex-start;">
            <div style="flex: 1; min-width: 300px;">{}</div>
            <div style="flex: 1; min-width: 250px;">{}</div>
        </div>
        """.format(img_html, list_html)

    else:
        html = "<p><strong>There are not enough numeric columns to generate a correlation matrix.</strong></p>"

    return html
