import logging
import pandas as pd
import csv
import os
import chardet
from pathlib import Path


try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


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
        file_path = Path(self.file_path)

        if not file_path.is_file():
            logger.error(f"The file does not exist or is not a valid file: {self.file_path}")
            raise FileNotFoundError(f"The file does not exist or is not a valid file: {self.file_path}")

    def _detect_encoding(self):
        """
        Detecta automáticamente la codificación de un archivo usando `chardet`.

        Esta función intenta detectar la codificación del archivo ubicado en `self.file_path`.
        Si no se puede determinar con suficiente confianza, se usa `'utf-8'` como predeterminado.

        Notas:
            - Si `self.encoding` ya está definido, esta función no hace nada.
            - Usa `logging` para registrar mensajes de información y errores.
        """

        # Verificar si ya está definida la codificación
        if hasattr(self, 'encoding'):
            logger.info("Coding already defined: %s", self.encoding)
            return

        try:
            with open(self.file_path, "rb") as f:
                raw = f.read(5000)
                result = chardet.detect(raw)

                # Usar 'utf-8' como predeterminado si la confianza es baja o no se detecta
                if result["confidence"] < 0.7:
                    self.encoding = "utf-8"
                    logger.warning("Encoding detected with low confidence (%s). Using 'utf-8'.",
                                   result["confidence"])
                else:
                    self.encoding = result["encoding"] or "utf-8"
                    logger.info("Detected encoding: %s (confidence: %.2f)", self.encoding, result["confidence"])

        except FileNotFoundError:
            logger.error(f"The file {self.file_path} does not exist")
            raise ValueError(f"The file {self.file_path} does not exist")
        except Exception as e:
            logger.error("Error detecting encoding: %s", e)
            self.encoding = "utf-8"

    def _detect_delimiter(self):
        try:
            with open(self.file_path, "r", encoding=self.encoding) as f:
                sample = f.read(5000)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    return dialect.delimiter
                except csv.Error:
                    return ","
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error: {e}. Using “utf-8” as an alternative.")
            with open(self.file_path, "r", encoding='utf-8') as f:
                sample = f.read(4096)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    return dialect.delimiter
                except csv.Error as e:
                    logger.warning(f"The delimiter could not be detected. Using comma (,): {e}")
                    return ","

    # ---------------------------------------------------------
    # Loaders (pandas or polars)
    # ---------------------------------------------------------
    def _load_csv_or_txt(self):
        # Asegurarse de que la codificación esté detectada
        if not hasattr(self, 'encoding'):
            self._detect_encoding()

        delimiter = self._detect_delimiter()

        if self.use_polars:
            df = pl.read_csv(self.file_path, separator=delimiter, ignore_errors=True)
            return df.to_pandas()

        # Contar líneas totales y cargar datos en un solo proceso
        try:
            with pd.read_csv(
                    self.file_path,
                    encoding=self.encoding,
                    sep=delimiter,
                    on_bad_lines="skip",
                    low_memory=True,
                    chunksize=1
            ) as reader:
                total_lines = sum(1 for _ in reader)

            df = pd.read_csv(
                self.file_path,
                encoding=self.encoding,
                sep=delimiter,
                on_bad_lines="skip",
                low_memory=True
            )
        except Exception as e:
            logger.error(f"Error al cargar el archivo: {e}")
            raise

        # Calcular líneas omitidas
        self.skipped_lines = total_lines - len(df)

        return df

    def _load_excel(self):
        try:
            if self.use_polars:
                df = pl.read_excel(self.file_path)
                return df.to_pandas()
            return pd.read_excel(self.file_path)
        except Exception as e:
            logger.error(f"Error loading file Excel: {e}")
            raise

    def _load_json(self):
        try:
            if self.use_polars:
                df = pl.read_json(self.file_path)
                return df.to_pandas()
            return pd.read_json(self.file_path)
        except Exception as e:
            logger.error(f"EError loading file JSON: {e}")
            raise

    def _load_parquet(self):
        try:
            if self.use_polars:
                df = pl.read_parquet(self.file_path)
                return df.to_pandas()
            return pd.read_parquet(self.file_path)
        except Exception as e:
            logger.error(f"Error loading file Parquet: {e}")
            raise

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