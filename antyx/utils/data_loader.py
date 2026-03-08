import time
import logging
import pandas as pd
import csv
import os
import chardet
from pathlib import Path
from io import StringIO

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
        self.encoding = None
        self.skipped_lines = 0
        self.use_polars = use_polars and POLARS_AVAILABLE

        # CASE 1 → DataFrame provided directly
        if df is not None:
            self._load_from_dataframe(df)
            return

        # CASE 2 → File path provided
        if file_path is None:
            raise ValueError("You must provide either a file_path or a DataFrame.")

    def _log_start(self, step_name: str):
        logger.info(f"✅ Starting step '{step_name}'...")

    def _log_end(self, step_name: str, duration: float):
        logger.info(f"✅ Step '{step_name}' completed in {duration:.2f} seconds.")

    # ---------------------------------------------------------
    # Load from DataFrame (pandas or polars)
    # ---------------------------------------------------------
    def _load_from_dataframe(self, df):
        """Accept pandas or polars DataFrame."""
        self._log_start("Loading from DataFrame...")
        start_time = time.time()

        if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
            self.df = df.to_pandas()
        elif isinstance(df, pd.DataFrame):
            self.df = df.copy()
        else:
            raise TypeError("df must be a pandas or polars DataFrame.")

        duration = time.time() - start_time
        self._log_end("Load from DataFrame", duration)

    # ---------------------------------------------------------
    # File utilities
    # ---------------------------------------------------------

    def _check_file_exists(self):
        file_path = Path(self.file_path)
        self._log_start("Verifying existence of file...")
        start_time = time.time()

        if not file_path.is_file():
            logger.error(f"The file does not exist or is not a valid file: {self.file_path}")
            raise FileNotFoundError(f"The file does not exist or is not a valid file: {self.file_path}")

        duration = time.time() - start_time
        self._log_end("File verified", duration)

    def _detect_encoding(self):
        """
        Detecta automáticamente la codificación del archivo usando chardet.
        Si la confianza es baja, usa latin-1 como fallback seguro.
        """

        start_time = time.time()
        self._log_start("Detecting encoding...")

        # Solo saltar si encoding ya existe y no es None
        if self.encoding is not None:
            logger.info("Encoding already defined: %s", self.encoding)
            self._log_end("Encoding detection", time.time() - start_time)
            return

        try:
            with open(self.file_path, "rb") as f:
                raw = f.read(50_000)

            result = chardet.detect(raw)
            detected = result["encoding"]
            confidence = result["confidence"]

            if detected is None:
                logger.warning("No encoding detected. Using latin-1 as fallback.")
                self.encoding = "latin-1"

            elif confidence < 0.70:
                logger.warning(
                    "Low confidence in detected encoding (%s). "
                    "Detected: %s. Using latin-1 as fallback.",
                    confidence, detected
                )
                self.encoding = "latin-1"

            else:
                self.encoding = detected
                logger.info("Detected encoding: %s (confidence: %.2f)", detected, confidence)

        except Exception as e:
            logger.error("Error detecting encoding: %s", e)
            self.encoding = "latin-1"

        duration = time.time() - start_time
        self._log_end("Encoding detection", duration)

    def _detect_delimiter(self):
        self._log_start("Detecting delimiter...")
        start_time = time.time()

        try:
            with open(self.file_path, "r", encoding=self.encoding) as f:
                sample = f.read(5000)
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
                logger.info(f"Delimiter detected: {delimiter}")

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error: {e}. Using 'utf-8' as an alternative.")
            with open(self.file_path, "r", encoding='utf-8') as f:
                sample = f.read(4096)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error as e:
                    logger.warning(f"The delimiter could not be detected. Using comma (,): {e}")
                    delimiter = ","

        duration = time.time() - start_time
        self._log_end("Delimiter detection", duration)

        return delimiter

    # ---------------------------------------------------------
    # Loaders (pandas or polars)
    # ---------------------------------------------------------

    def _load_csv_or_txt(self):
        self._log_start("Loading CSV/TXT...")
        start_time = time.time()

        if self.encoding is None:
            self._detect_encoding()

        delimiter = self._detect_delimiter()

        try:
            if self.use_polars:
                df = pl.read_csv(
                    self.file_path,
                    separator=delimiter,
                    ignore_errors=True
                ).to_pandas()
            else:
                df = pd.read_csv(
                    self.file_path,
                    sep=delimiter,
                    encoding=self.encoding,
                    engine="python",
                    on_bad_lines="skip"
                )

        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise

        duration = time.time() - start_time
        self._log_end("Load CSV/TXT", duration)

        return df

    def _load_excel(self):

        self._log_start("Loading Excel...")
        start_time = time.time()

        try:
            if self.use_polars:
                df = pl.read_excel(self.file_path)
                self.df = df.to_pandas()
            else:
                self.df = pd.read_excel(self.file_path)

            duration = time.time() - start_time
            self._log_end("Carga de Excel", duration)

        except Exception as e:
            logger.error(f"Error loading file Excel: {e}")
            raise

    def _load_json(self):
        """Carga archivos JSON con progreso."""
        self._log_start("Loading JSON...")
        start_time = time.time()

        try:
            if self.use_polars:
                df = pl.read_json(self.file_path)
                self.df = df.to_pandas()
            else:
                self.df = pd.read_json(self.file_path)

            duration = time.time() - start_time
            self._log_end("JSON load", duration)
        except Exception as e:
            logger.error(f"Error loading file JSON: {e}")
            raise

    def _load_parquet(self):
        """Carga archivos Parquet con progreso."""
        self._log_start("Loading Parquet...")
        start_time = time.time()

        try:
            if self.use_polars:
                df = pl.read_parquet(self.file_path)
                self.df = df.to_pandas()
            else:
                self.df = pd.read_parquet(self.file_path)

            duration = time.time() - start_time
            self._log_end("Parquet load", duration)
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