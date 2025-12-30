import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def detect_outliers(df):
    """Generates a visualizations of the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to analyze.

    Returns:
        Visualizations of the DataFrame.
    """
    numeric = df.select_dtypes(include='number')
    num_vars = numeric.shape[1]
    cols = 4
    rows = (num_vars + cols - 1) // cols
    palette = sns.color_palette("Set2", num_vars)

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 3.5))
    axes = axes.flatten()

    fig.suptitle("Nota: Outliers detectados según el criterio de Tukey (1.5 × IQR)", fontsize=11, ha='left', x=0.01)

    for i, column in enumerate(numeric.columns):
        data = numeric[column]
        stats = data.describe()
        q1 = stats['25%']
        q3 = stats['75%']
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        median = stats['50%']
        outliers = data[(data < lower) | (data > upper)]
        outliers_pct = len(outliers) / len(data) * 100

        ax = axes[i]
        sns.violinplot(y=data, ax=ax, color=palette[i], inner=None)
        sns.stripplot(y=outliers, ax=ax, color='red', size=3, jitter=True, label='Outliers')

        ax.set_title(column, fontsize=12, fontweight='bold')
        ax.set_ylabel('')
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        stat_text = (
            f"Outliers: {len(outliers)} ({outliers_pct:.1f}%)\n\n"
            f"Upper: {upper:.2f}\n"
            f"75%: {q3:.2f}\n"
            f"Median: {median:.2f}\n"
            f"25%: {q1:.2f}\n"
            f"Lower: {lower:.2f}"
        )
        ax.text(1.05, 0.5, stat_text, transform=ax.transAxes,
                fontsize=9, va='center', ha='left', linespacing=1.5)

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=120)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f'<img src="data:image/png;base64,{encoded}"/>'
