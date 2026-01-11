import pandas as pd
import csv
import os
import chardet

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


class DataLoader:
    """
    Universal DataLoader supporting:
    - CSV, TXT, Excel, JSON, Parquet
    - pandas DataFrame input
    - polars DataFrame input (converted to pandas)
    - optional Polars engine for faster file loading
    """

    def __init__(self, file_path=None, df=None, use_polars=False):
        """
        Args:
            file_path (str): Path to the file to be loaded.
            df (pandas.DataFrame or polars.DataFrame): Direct DataFrame input.
            use_polars (bool): Whether to use Polars for loading files.
        """

        self.file_path = file_path
        self.df = None
        self.encoding = "utf-8"
        self.skipped_lines = 0
        self.use_polars = use_polars and POLARS_AVAILABLE

        # CASE 1 → DataFrame provided directly
        if df is not None:
            self.df = self._load_from_dataframe(df)
            return

        # CASE 2 → File path provided
        if file_path is None:
            raise ValueError("You must provide either a file_path or a DataFrame.")

    # ---------------------------------------------------------
    # Load from DataFrame (pandas or polars)
    # ---------------------------------------------------------
    def _load_from_dataframe(self, df):
        """Accept pandas or polars DataFrame."""
        if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
            return df.to_pandas()
        elif isinstance(df, pd.DataFrame):
            return df.copy()
        else:
            raise TypeError("df must be a pandas or polars DataFrame.")

    # ---------------------------------------------------------
    # File utilities
    # ---------------------------------------------------------
    def _check_file_exists(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The file does not exist: {self.file_path}")
        if not os.path.isfile(self.file_path):
            raise ValueError(f"The path is not a file: {self.file_path}")

    def _detect_encoding(self):
        with open(self.file_path, "rb") as f:
            raw = f.read(10000)
            self.encoding = chardet.detect(raw)["encoding"] or "utf-8"

    def _detect_delimiter(self):
        with open(self.file_path, "r", encoding=self.encoding) as f:
            sample = f.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample)
                return dialect.delimiter
            except csv.Error:
                return ","

    # ---------------------------------------------------------
    # Loaders (pandas or polars)
    # ---------------------------------------------------------
    def _load_csv_or_txt(self):
        delimiter = self._detect_delimiter() if self.file_path.endswith(".csv") else "\t"

        if self.use_polars:
            df = pl.read_csv(self.file_path, separator=delimiter, ignore_errors=True)
            return df.to_pandas()

        # Contamos líneas totales antes de leer (para CSV/TXT)
        with open(self.file_path, "r", encoding=self.encoding) as f:
            total_lines = sum(1 for _ in f)

        df = pd.read_csv(
            self.file_path,
            encoding=self.encoding,
            sep=delimiter,
            on_bad_lines="skip",
            low_memory=False,
        )
        # Calculamos cuántas filas se perdieron
        self.skipped_lines = total_lines - len(df)

        return df

    def _load_excel(self):
        if self.use_polars:
            df = pl.read_excel(self.file_path)
            return df.to_pandas()
        return pd.read_excel(self.file_path)

    def _load_json(self):
        if self.use_polars:
            df = pl.read_json(self.file_path)
            return df.to_pandas()
        return pd.read_json(self.file_path)

    def _load_parquet(self):
        if self.use_polars:
            df = pl.read_parquet(self.file_path)
            return df.to_pandas()
        return pd.read_parquet(self.file_path)

    # ---------------------------------------------------------
    # Main loader
    # ---------------------------------------------------------
    def load_data(self):
        if self.df is not None:
            return self.df  # Already loaded from DataFrame

        self._check_file_exists()
        ext = os.path.splitext(self.file_path)[1].lower()

        try:
            if ext in (".csv", ".txt"):
                self._detect_encoding()
                self.df = self._load_csv_or_txt()
            elif ext in (".xlsx", ".xls"):
                self.df = self._load_excel()
            elif ext == ".json":
                self.df = self._load_json()
            elif ext == ".parquet":
                self.df = self._load_parquet()
            else:
                raise ValueError(f"Unsupported file format: {ext}")

            self.skipped_lines = 0
            return self.df

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return None