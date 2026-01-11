import pandas as pd


def detect_var_type(series: pd.Series) -> str:
    """
    Clasifica una serie en:
    - 'numeric'
    - 'datetime'
    - 'binary'
    - 'categorical'
    - 'other'
    Reglas:
      1) Primero dtypes nativos (bool, numeric, datetime64)
      2) Fechas por NOMBRE de columna (fecha/date/...) + intento de parseo
      3) Binarias numéricas y textuales
      4) Categóricas por nº de categorías
    """

    s = series.dropna()
    if s.empty:
        return "other"

    col_name = str(series.name or "").lower()

    # ---------- 1. Tipos nativos ----------
    # Bool → binary
    if pd.api.types.is_bool_dtype(series):
        return "binary"

    # Numérico
    if pd.api.types.is_numeric_dtype(series):
        unique_vals = set(s.unique())
        if unique_vals.issubset({0, 1}):
            return "binary"
        return "numeric"

    # Datetime nativo
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # ---------- 2. Fechas por nombre de columna ----------
    # Si el nombre contiene "fecha", "date", etc., intentamos parsear
    date_name_hints = ["fecha", "date", "fec", "fch", "fechaventa"]
    if any(h in col_name for h in date_name_hints):
        # Asumimos formato "europeo" por defecto (dayfirst=True) para casos como FECHAVENTA
        parsed = pd.to_datetime(s, errors="coerce", dayfirst=True)
        non_na_ratio = parsed.notna().mean()
        # Si al menos el 50% se parsean bien, lo consideramos datetime
        if non_na_ratio >= 0.5:
            return "datetime"

    # (Opcional) Si quisieras intentar detectar fechas genéricas por patrón de texto,
    # podríamos añadir aquí una heurística más agresiva. De momento la dejamos fuera
    # para no generar falsos positivos ni warnings.

    # ---------- 3. Binarias textuales ----------
    unique_vals_str = {str(v).strip().lower() for v in s.unique()}
    binary_sets = [
        {"0", "1"},
        {"yes", "no"},
        {"y", "n"},
        {"true", "false"},
        {"t", "f"},
        {"si", "no"},
        {"sí", "no"},
        {"male", "female"},
        {"m", "f"},
    ]
    if 1 <= len(unique_vals_str) <= 2:
        for bset in binary_sets:
            if unique_vals_str.issubset(bset):
                return "binary"

    # ---------- 4. Categórica vs other ----------
    nunique = s.nunique()
    ratio_unique = nunique / len(s)

    # Heurística: pocas categorías absolutas o relativas → categorical
    if nunique <= 30 or ratio_unique <= 0.1:
        return "categorical"

    return "other"