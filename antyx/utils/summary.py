import os
import pandas as pd
from antyx.utils.types import detect_var_type


def format_number(x):
    return f"{x:,.2f}" if pd.notnull(x) else ""


def render_summary_block(title, headers, rows_html):
    return f"""
    <div class="summary-block">
        <h2 class="summary-title">{title}</h2>
        <div class="table-container">
            <table class="table-custom summary-table">
                <thead>
                    <tr>{''.join([f"<th>{h}</th>" for h in headers])}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """


# ============================================================
#  BUILD SUMMARY DATAFRAMES (TIPOS REALES)
# ============================================================

def build_summary_dataframes(df: pd.DataFrame):
    numeric_rows = []
    binary_rows = []
    categorical_rows = []
    datetime_rows = []

    for col in df.columns:
        s = df[col]
        vtype = detect_var_type(s)

        total = len(s)
        non_null = s.count()
        nulls = s.isnull().sum()
        unique = s.nunique()

        base_info = {
            "Variable": col,
            "Type": vtype,
            "Non-null": non_null,
            "Nulls": nulls,
            "Unique": unique,
        }

        if vtype == "numeric":
            desc = s.describe()
            var = s.var()
            top = s.mode().iloc[0] if not s.mode().empty else ""
            freq = s.value_counts().iloc[0] if not s.value_counts().empty else ""
            top_pct = (freq / total * 100) if total > 0 else 0

            row = {
                **base_info,
                "Top": top,
                "Freq Top": freq,
                "% Top": round(top_pct, 2),
                "Mean": desc.get("mean"),
                "Std": desc.get("std"),
                "Var": var,
                "Min": desc.get("min"),
                "25%": desc.get("25%"),
                "50%": desc.get("50%"),
                "75%": desc.get("75%"),
                "Max": desc.get("max"),
            }
            numeric_rows.append(row)

        elif vtype == "binary":
            counts = s.value_counts(dropna=True)
            top = counts.index[0] if not counts.empty else ""
            freq = counts.iloc[0] if not counts.empty else 0
            top_pct = (freq / total * 100) if total > 0 else 0

            row = {
                **base_info,
                "Top": top,
                "Freq Top": freq,
                "% Top": round(top_pct, 2),
            }
            binary_rows.append(row)

        elif vtype == "categorical":
            counts = s.value_counts(dropna=True)
            top = counts.index[0] if not counts.empty else ""
            freq = counts.iloc[0] if not counts.empty else 0
            top_pct = (freq / total * 100) if total > 0 else 0

            row = {
                **base_info,
                "Top": top,
                "Freq Top": freq,
                "% Top": round(top_pct, 2),
            }
            categorical_rows.append(row)

        elif vtype == "datetime":
            sd = s.dropna()
            min_val = sd.min() if not sd.empty else None
            max_val = sd.max() if not sd.empty else None

            row = {
                **base_info,
                "Min": min_val,
                "Max": max_val,
            }
            datetime_rows.append(row)

        # Si es "other", lo omitimos del summary principal
        # o podríamos añadir un bloque aparte si lo ves útil.

    numeric_df = pd.DataFrame(numeric_rows)
    binary_df = pd.DataFrame(binary_rows)
    categorical_df = pd.DataFrame(categorical_rows)
    datetime_df = pd.DataFrame(datetime_rows)

    return numeric_df, binary_df, categorical_df, datetime_df


# ============================================================
#  EXPORT FUNCTIONS
# ============================================================

def export_summary(numeric_df, binary_df, categorical_df, datetime_df, output_dir="."):
    numeric_csv = os.path.join(output_dir, "summary_numeric.csv")
    binary_csv = os.path.join(output_dir, "summary_binary.csv")
    categorical_csv = os.path.join(output_dir, "summary_categorical.csv")
    datetime_csv = os.path.join(output_dir, "summary_datetime.csv")
    excel_path = os.path.join(output_dir, "summary.xlsx")

    if not numeric_df.empty:
        numeric_df.to_csv(numeric_csv, index=False)
    if not binary_df.empty:
        binary_df.to_csv(binary_csv, index=False)
    if not categorical_df.empty:
        categorical_df.to_csv(categorical_csv, index=False)
    if not datetime_df.empty:
        datetime_df.to_csv(datetime_csv, index=False)

    with pd.ExcelWriter(excel_path) as writer:
        if not numeric_df.empty:
            numeric_df.to_excel(writer, sheet_name="Numeric", index=False)
        if not binary_df.empty:
            binary_df.to_excel(writer, sheet_name="Binary", index=False)
        if not categorical_df.empty:
            categorical_df.to_excel(writer, sheet_name="Categorical", index=False)
        if not datetime_df.empty:
            datetime_df.to_excel(writer, sheet_name="Datetime", index=False)

    return {
        "numeric_csv": numeric_csv if not numeric_df.empty else None,
        "binary_csv": binary_csv if not binary_df.empty else None,
        "categorical_csv": categorical_csv if not categorical_df.empty else None,
        "datetime_csv": datetime_csv if not datetime_df.empty else None,
        "excel": excel_path,
    }


# ============================================================
#  MAIN SUMMARY FUNCTION
# ============================================================

def describe_data(df, output_dir="."):
    numeric_df, binary_df, categorical_df, datetime_df = build_summary_dataframes(df)
    export_paths = export_summary(numeric_df, binary_df, categorical_df, datetime_df, output_dir)

    blocks_html = ""

    if not numeric_df.empty:
        numeric_rows = ""
        for _, row in numeric_df.iterrows():
            numeric_rows += "<tr>" + "".join(
                f"<td>{format_number(v) if isinstance(v, float) else v}</td>"
                for v in row
            ) + "</tr>"
        numeric_headers = list(numeric_df.columns)
        blocks_html += render_summary_block("Numeric data", numeric_headers, numeric_rows)

    if not binary_df.empty:
        binary_rows = ""
        for _, row in binary_df.iterrows():
            binary_rows += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
        binary_headers = list(binary_df.columns)
        blocks_html += render_summary_block("Binary data", binary_headers, binary_rows)

    if not categorical_df.empty:
        cat_rows = ""
        for _, row in categorical_df.iterrows():
            cat_rows += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
        cat_headers = list(categorical_df.columns)
        blocks_html += render_summary_block("Categorical data", cat_headers, cat_rows)

    if not datetime_df.empty:
        dt_rows = ""
        for _, row in datetime_df.iterrows():
            dt_rows += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
        dt_headers = list(datetime_df.columns)
        blocks_html += render_summary_block("Datetime data", dt_headers, dt_rows)

    # Export (icon) — mantenemos tu Excel principal
    excel_file = export_paths["excel"]

    export_html = f"""
    <div class="summary-export">
        <a class="export-icon" href="{os.path.basename(excel_file)}" download>
            <img src="antyx/icons/excel.svg" alt="Excel">
        </a>
    </div>
    """

    return export_html + blocks_html