import pandas as pd
import numpy as np
from antyx.utils.types import detect_var_type


# ============================================================
#  FORMAT HELPERS
# ============================================================

def format_number(x, ndigits=2):
    if pd.isna(x):
        return ""
    if isinstance(x, (int, np.integer)):
        return f"{x:,}"
    return f"{x:,.{ndigits}f}"


def render_cell(col_name, value):
    if col_name == "Quality":
        return f"<td><span class='quality-dot quality-{value}'></span>{value}</td>"
    return f"<td>{value}</td>"


# ============================================================
#  NUMERIC / CATEGORICAL / BINARY / DATETIME STATS
# ============================================================

def _numeric_stats(s: pd.Series):
    s_clean = s.dropna()
    if s_clean.empty:
        return {}

    desc = s_clean.describe()
    q1 = desc.get("25%", np.nan)
    q3 = desc.get("75%", np.nan)
    iqr = q3 - q1 if pd.notna(q3) and pd.notna(q1) else np.nan
    data_range = desc.get("max", np.nan) - desc.get("min", np.nan)

    # Outliers IQR rule
    if pd.notna(iqr) and iqr > 0:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers_mask = (s_clean < lower) | (s_clean > upper)
        outliers_count = outliers_mask.sum()
        outliers_pct = outliers_count / len(s_clean) * 100
    else:
        outliers_count = 0
        outliers_pct = 0

    mean = desc.get("mean", np.nan)
    std = desc.get("std", np.nan)
    coef_var = (std / mean) if (pd.notna(mean) and mean != 0) else np.nan

    return {
        "mean": mean,
        "median": desc.get("50%", np.nan),
        "std": std,
        "var": s_clean.var(),
        "min": desc.get("min", np.nan),
        "q1": q1,
        "q3": q3,
        "max": desc.get("max", np.nan),
        "range": data_range,
        "iqr": iqr,
        "coef_var": coef_var,
        "skew": s_clean.skew(),
        "kurt": s_clean.kurtosis(),
        "outliers": outliers_count,
        "outliers_pct": outliers_pct,
    }


def _categorical_stats(s: pd.Series):
    s_clean = s.dropna()
    if s_clean.empty:
        return {}

    total = len(s_clean)
    vc = s_clean.value_counts()
    n_unique = vc.shape[0]
    top = vc.index[0]
    top_freq = vc.iloc[0]
    top_pct = top_freq / total * 100 if total > 0 else 0

    rare = vc[vc / total < 0.01].shape[0]

    lengths = s_clean.astype(str).str.len()
    avg_len = lengths.mean()
    max_len = lengths.max()

    numeric_like_ratio = pd.to_numeric(s_clean, errors="coerce").notna().mean()
    numeric_like = numeric_like_ratio > 0.9

    datetime_like_ratio = pd.to_datetime(s_clean, errors="coerce", dayfirst=True).notna().mean()
    datetime_like = datetime_like_ratio > 0.6

    return {
        "n_unique": n_unique,
        "top": top,
        "top_freq": top_freq,
        "top_pct": top_pct,
        "rare_categories": rare,
        "avg_len": avg_len,
        "max_len": max_len,
        "numeric_like": numeric_like,
        "datetime_like": datetime_like,
    }


def _binary_stats(s: pd.Series):
    s_clean = s.dropna()
    if s_clean.empty:
        return {}

    vc = s_clean.value_counts()
    if vc.empty:
        return {}

    top = vc.index[0]
    top_freq = vc.iloc[0]
    total = vc.sum()
    top_pct = top_freq / total * 100 if total > 0 else 0

    balance = top_pct if top_pct >= 50 else 100 - top_pct

    return {
        "top": top,
        "top_freq": top_freq,
        "top_pct": top_pct,
        "balance": balance,
    }


def _datetime_stats(s: pd.Series):
    s_clean = pd.to_datetime(s.dropna(), errors="coerce", dayfirst=True)
    s_clean = s_clean.dropna()
    if s_clean.empty:
        return {}

    min_val = s_clean.min()
    max_val = s_clean.max()
    range_days = (max_val - min_val).days

    has_time = (s_clean.dt.time != pd.to_datetime("00:00:00").time()).any()
    future_dates = (s_clean > pd.Timestamp.today()).sum()

    return {
        "min": min_val,
        "max": max_val,
        "range_days": range_days,
        "has_time": has_time,
        "future_dates": future_dates,
    }


# ============================================================
#  QUALITY FLAG
# ============================================================

def _quality_flag(null_pct, high_card, outliers_pct):
    if null_pct < 5 and not high_card and outliers_pct < 5:
        return "good"
    if null_pct < 20 and outliers_pct < 15:
        return "medium"
    return "bad"


# ============================================================
#  BUILD SUMMARY DATAFRAMES
# ============================================================

def build_summary_dataframes(df: pd.DataFrame):
    general_rows = []
    numeric_rows = []
    binary_rows = []
    categorical_rows = []
    datetime_rows = []
    other_rows = []

    for col in df.columns:
        s = df[col]
        vtype = detect_var_type(s)

        total = len(s)
        non_null = s.count()
        nulls = s.isnull().sum()
        null_pct = (nulls / total * 100) if total > 0 else 0
        unique = s.nunique(dropna=True)
        unique_ratio = (unique / total * 100) if total > 0 else 0

        is_constant = unique <= 1
        is_quasi_constant = (unique <= 3) and (unique_ratio < 5)
        is_high_card = unique > 50

        base_info = {
            "Variable": col,
            "Type": vtype,
            "Non-null": non_null,
            "Nulls": nulls,
            "% Nulls": round(null_pct, 2),
            "Unique": unique,
            "% Unique": round(unique_ratio, 2),
            "Constant": "Yes" if is_constant else "No",
            "Quasi-constant": "Yes" if is_quasi_constant else "No",
            "High cardinality": "Yes" if is_high_card else "No",
        }

        # NUMERIC
        if vtype == "numeric":
            stats = _numeric_stats(s)
            outliers_pct = stats.get("outliers_pct", 0) or 0
            quality = _quality_flag(null_pct, is_high_card, outliers_pct)

            general_rows.append({**base_info, "Quality": quality})

            numeric_rows.append({
                **base_info,
                "Mean": stats.get("mean"),
                "Median": stats.get("median"),
                "Std": stats.get("std"),
                "Var": stats.get("var"),
                "Min": stats.get("min"),
                "Q1": stats.get("q1"),
                "Q3": stats.get("q3"),
                "Max": stats.get("max"),
                "Range": stats.get("range"),
                "IQR": stats.get("iqr"),
                "CoefVar": stats.get("coef_var"),
                "Skew": stats.get("skew"),
                "Kurtosis": stats.get("kurt"),
                "Outliers": stats.get("outliers"),
                "% Outliers": round(outliers_pct, 2),
                "Quality": quality,
            })

        # BINARY
        elif vtype == "binary":
            stats = _binary_stats(s)
            quality = _quality_flag(null_pct, is_high_card, 0)

            general_rows.append({**base_info, "Quality": quality})

            binary_rows.append({
                **base_info,
                "Top": stats.get("top"),
                "Freq Top": stats.get("top_freq"),
                "% Top": round(stats.get("top_pct", 0), 2),
                "Balance": round(stats.get("balance", 0), 2),
                "Quality": quality,
            })

        # CATEGORICAL
        elif vtype == "categorical":
            stats = _categorical_stats(s)
            quality = _quality_flag(null_pct, is_high_card, 0)

            general_rows.append({**base_info, "Quality": quality})

            categorical_rows.append({
                **base_info,
                "Top": stats.get("top"),
                "Freq Top": stats.get("top_freq"),
                "% Top": round(stats.get("top_pct", 0), 2),
                "Rare categories": stats.get("rare_categories"),
                "Avg length": stats.get("avg_len"),
                "Max length": stats.get("max_len"),
                "Numeric-like": "Yes" if stats.get("numeric_like") else "No",
                "Datetime-like": "Yes" if stats.get("datetime_like") else "No",
                "Quality": quality,
            })

        # DATETIME
        elif vtype == "datetime":
            stats = _datetime_stats(s)
            quality = _quality_flag(null_pct, is_high_card, 0)

            general_rows.append({**base_info, "Quality": quality})

            datetime_rows.append({
                **base_info,
                "Min": stats.get("min"),
                "Max": stats.get("max"),
                "Range days": stats.get("range_days"),
                "Has time": "Yes" if stats.get("has_time") else "No",
                "Future dates": stats.get("future_dates"),
                "Quality": quality,
            })

        # OTHER
        else:
            other_rows.append({"Variable": col})

    return (
        pd.DataFrame(general_rows),
        pd.DataFrame(numeric_rows),
        pd.DataFrame(binary_rows),
        pd.DataFrame(categorical_rows),
        pd.DataFrame(datetime_rows),
        pd.DataFrame(other_rows),
    )


# ============================================================
#  HTML RENDERING
# ============================================================

def render_summary_block(title, headers, rows_html, block_class=""):
    extra_class = f" {block_class}" if block_class else ""

    tooltip_map = {
        "% Nulls": "Percentage of missing values in the column.",
        "% Unique": "Percentage of unique values relative to total rows.",
        "Constant": "Column has only one unique value.",
        "Quasi-constant": "Column has very low variability.",
        "High cardinality": "Column has more than 50 unique values.",
        "Quality": "Heuristic quality score based on nulls, cardinality and outliers.",
        "% Outliers": "Percentage of values outside the IQR rule.",
        "Rare categories": "Categories representing less than 1% of the data.",
        "Numeric-like": "Text values that look numeric.",
        "Datetime-like": "Text values that look like dates.",
        "Range days": "Difference between max and min date.",
    }

    def render_header(h):
        if h in tooltip_map:
            return f"""{h}
                <span class="sum-tip">ⓘ
                    <span class="sum-tip-text">{tooltip_map[h]}</span>
                </span>"""
        return h

    header_html = "".join(f"<th>{render_header(h)}</th>" for h in headers)

    return f"""
    <div class="summary-block{extra_class}">
        <h2 class="summary-title">{title}</h2>
        <div class="table-container">
            <table class="table-custom summary-table">
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """


def _render_quality_insights(general_df: pd.DataFrame):
    if general_df.empty:
        return ""

    many_nulls = general_df[general_df["% Nulls"] > 20]["Variable"].tolist()
    high_card = general_df[general_df["High cardinality"] == "Yes"]["Variable"].tolist()
    constants = general_df[general_df["Constant"] == "Yes"]["Variable"].tolist()
    quasi_constants = general_df[general_df["Quasi-constant"] == "Yes"]["Variable"].tolist()
    bad_quality = general_df[general_df["Quality"] == "bad"]["Variable"].tolist()

    def render_list(title, items):
        if not items:
            return ""
        li = "".join(f"<li>{v}</li>" for v in items)
        return f"""
        <div class="summary-quality-group">
            <h4>{title}</h4>
            <ul>{li}</ul>
        </div>
        """

    return f"""
    <section class="summary-quality">
        <h2 class="summary-title">Data quality insights</h2>
        <div class="summary-quality-grid">
            {render_list("Variables with > 20% nulls", many_nulls)}
            {render_list("High-cardinality variables", high_card)}
            {render_list("Constant variables", constants)}
            {render_list("Quasi-constant variables", quasi_constants)}
            {render_list("Low-quality variables", bad_quality)}
        </div>
    </section>
    """


# ============================================================
#  MAIN SUMMARY FUNCTION
# ============================================================

def describe_data(df, output_dir="."):
    general_df, numeric_df, binary_df, categorical_df, datetime_df, other_df = build_summary_dataframes(df)

    blocks_html = ""

    # 1. Data quality insights
    blocks_html += _render_quality_insights(general_df)

    # 2. Variable catalog (general)
    if not general_df.empty:
        rows = ""
        for _, row in general_df.iterrows():
            rows += "<tr>" + "".join(
                f"<td>{format_number(v) if isinstance(v, (float, np.floating)) else v}</td>"
                for v in row
            ) + "</tr>"
        headers = list(general_df.columns)
        blocks_html += render_summary_block("Variable catalog", headers, rows, block_class="summary-general")

    # 3. Numeric summary
    if not numeric_df.empty:
        rows = ""
        for _, row in numeric_df.iterrows():
            rows += "<tr>" + "".join(
                f"<td>{format_number(v, ndigits=3) if isinstance(v, (float, np.floating)) else v}</td>"
                for v in row
            ) + "</tr>"
        headers = list(numeric_df.columns)
        blocks_html += render_summary_block("Numeric variables", headers, rows)

    # 4. Categorical summary
    if not categorical_df.empty:
        rows = ""
        for _, row in categorical_df.iterrows():
            rows += "<tr>" + "".join(
                f"<td>{format_number(v, ndigits=3) if isinstance(v, (float, np.floating)) else v}</td>"
                for v in row
            ) + "</tr>"
        headers = list(categorical_df.columns)
        blocks_html += render_summary_block("Categorical variables", headers, rows)

    # 5. Binary summary
    if not binary_df.empty:
        rows = ""
        for _, row in binary_df.iterrows():
            rows += "<tr>" + "".join(
                f"<td>{format_number(v, ndigits=3) if isinstance(v, (float, np.floating)) else v}</td>"
                for v in row
            ) + "</tr>"
        headers = list(binary_df.columns)
        blocks_html += render_summary_block("Binary variables", headers, rows)

    # 6. Datetime summary
    if not datetime_df.empty:
        rows = ""
        for _, row in datetime_df.iterrows():
            rows += "<tr>" + "".join(
                render_cell(col_name, format_number(v) if isinstance(v, (float, np.floating)) else v)
                for col_name, v in row.items()
            ) + "</tr>"
        headers = list(datetime_df.columns)
        blocks_html += render_summary_block("Datetime variables", headers, rows)

    # 7. Other variables
    if not other_df.empty:
        rows = "".join(f"<tr><td>{row['Variable']}</td></tr>" for _, row in other_df.iterrows())
        blocks_html += render_summary_block("Other variables", ["Variable"], rows)

    return blocks_html