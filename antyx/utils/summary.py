import pandas as pd

def format_number(x):
    return f"{x:,.2f}" if pd.notnull(x) else ""

def describe_data(df):
    """Generates a statistical summary of the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to analyze.

    Returns:
        str: HTML with the statistical summary.
    """
    numeric_rows = []
    non_numeric_rows = []

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
            row = f"""
            <tr>
                <td title="{col}">{col}</td>
                <td title="{dtype}">{dtype}</td>
                <td class="group1" title="{non_null:,}">{non_null:,}</td>
                <td class="group1" title="{nulls:,}">{nulls:,}</td>
                <td class="group1" title="{unique:,}">{unique:,}</td>
                <td class="group2" title="{top}">{top}</td>
                <td class="group2" title="{freq:,}">{freq:,}</td>
                <td class="group2" title="{top_pct:.2f}%">{top_pct:.2f}%</td>
                <td class="group3" title="{format_number(desc['mean'])}">{format_number(desc['mean'])}</td>
                <td class="group3" title="{format_number(desc['std'])}">{format_number(desc['std'])}</td>
                <td class="group3" title="{format_number(var)}">{format_number(var)}</td>
                <td class="group4" title="{format_number(desc['min'])}">{format_number(desc['min'])}</td>
                <td class="group4" title="{format_number(desc['25%'])}">{format_number(desc['25%'])}</td>
                <td class="group4" title="{format_number(desc['50%'])}">{format_number(desc['50%'])}</td>
                <td class="group4" title="{format_number(desc['75%'])}">{format_number(desc['75%'])}</td>
                <td class="group4" title="{format_number(desc['max'])}">{format_number(desc['max'])}</td>

            </tr>
            """
            numeric_rows.append(row)
        else:
            row = f"""
            <tr>
                <td title="{col}">{col}</td>
                <td title="{dtype}">{dtype}</td>
                <td class="group1" title="{non_null:,}">{non_null:,}</td>
                <td class="group1" title="{nulls:,}">{nulls:,}</td>
                <td class="group1" title="{unique:,}">{unique:,}</td>
                <td class="group2" title="{top}">{top}</td>
                <td class="group2" title="{freq:,}">{freq:,}</td>
                <td class="group2" title="{top_pct:.2f}%">{top_pct:.2f}%</td>
            </tr>
            """
            non_numeric_rows.append(row)

    # Encabezados
    numeric_headers = [
        "Variable", "Type", "Non-null", "Nulls", "Unique",
        "Top", "Freq Top", "% Top", "Mean", "Std", "Var",
        "Min", "25%", "50%", "75%", "Max"
    ]
    non_numeric_headers = [
        "Variable", "Type", "Non-null", "Nulls", "Únicos",
        "Top", "Freq Top", "% Top"
    ]

    numeric_table = f"""
    <h2>Numerical data</h2>
    <table class="table-custom">
        <tr>{''.join([f"<th>{h}</th>" for h in numeric_headers])}</tr>
        {''.join(numeric_rows)}
    </table>
    """

    non_numeric_table = f"""
    <h2>Non-numerical data</h2>
    <table class="table-custom">
        <tr>{''.join([f"<th>{h}</th>" for h in non_numeric_headers])}</tr>
        {''.join(non_numeric_rows)}
    </table>
    """

    return numeric_table + non_numeric_table
