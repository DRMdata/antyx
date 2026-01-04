import pandas as pd
import os

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
#  BUILD SUMMARY DATAFRAMES (REAL SUMMARY)
# ============================================================

def build_summary_dataframes(df):
    numeric_summary = []
    non_numeric_summary = []

    for col in df.columns:
        dtype = df[col].dtype
        total = len(df)
        non_null = df[col].count()
        nulls = df[col].isnull().sum()
        unique = df[col].nunique()
        top = df[col].mode().iloc[0] if not df[col].mode().empty else ''
        freq = df[col].value_counts().iloc[0] if not df[col].value_counts().empty else ''
        top_pct = (freq / total) * 100 if total > 0 else 0

        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        if is_numeric:
            desc = df[col].describe()
            var = df[col].var()

            numeric_summary.append({
                "Variable": col,
                "Type": str(dtype),
                "Non-null": non_null,
                "Nulls": nulls,
                "Unique": unique,
                "Top": top,
                "Freq Top": freq,
                "% Top": round(top_pct, 2),
                "Mean": desc["mean"],
                "Std": desc["std"],
                "Var": var,
                "Min": desc["min"],
                "25%": desc["25%"],
                "50%": desc["50%"],
                "75%": desc["75%"],
                "Max": desc["max"]
            })

        else:
            non_numeric_summary.append({
                "Variable": col,
                "Type": str(dtype),
                "Non-null": non_null,
                "Nulls": nulls,
                "Unique": unique,
                "Top": top,
                "Freq Top": freq,
                "% Top": round(top_pct, 2)
            })

    return (
        pd.DataFrame(numeric_summary),
        pd.DataFrame(non_numeric_summary)
    )

# ============================================================
#  EXPORT FUNCTIONS (EXPORT REAL SUMMARY)
# ============================================================

def export_summary(numeric_df, non_numeric_df, output_dir="."):
    numeric_csv = os.path.join(output_dir, "summary_numeric.csv")
    non_numeric_csv = os.path.join(output_dir, "summary_non_numeric.csv")
    excel_path = os.path.join(output_dir, "summary.xlsx")

    numeric_df.to_csv(numeric_csv, index=False)
    non_numeric_df.to_csv(non_numeric_csv, index=False)

    with pd.ExcelWriter(excel_path) as writer:
        numeric_df.to_excel(writer, sheet_name="Numeric", index=False)
        non_numeric_df.to_excel(writer, sheet_name="NonNumeric", index=False)

    return numeric_csv, non_numeric_csv, excel_path

# ============================================================
#  MAIN SUMMARY FUNCTION
# ============================================================

def describe_data(df, output_dir="."):
    numeric_df, non_numeric_df = build_summary_dataframes(df)
    numeric_csv, non_numeric_csv, excel_file = export_summary(numeric_df, non_numeric_df, output_dir)

    numeric_rows = ""
    for _, row in numeric_df.iterrows():
        numeric_rows += "<tr>" + "".join([f"<td>{format_number(v) if isinstance(v, float) else v}</td>" for v in row]) + "</tr>"

    non_numeric_rows = ""
    for _, row in non_numeric_df.iterrows():
        non_numeric_rows += "<tr>" + "".join([f"<td>{v}</td>" for v in row]) + "</tr>"

    numeric_headers = list(numeric_df.columns)
    non_numeric_headers = list(non_numeric_df.columns)

    numeric_block = render_summary_block("Numerical data", numeric_headers, numeric_rows)
    non_numeric_block = render_summary_block("Non-numerical data", non_numeric_headers, non_numeric_rows)

    export_html = f"""
    <div class="summary-export">
        <a class="export-icon" href="{os.path.basename(excel_file)}" download>
            <img src="antyx/icons/excel.svg" alt="Excel">
        </a>
    </div>
    """

    return export_html + numeric_block + non_numeric_block