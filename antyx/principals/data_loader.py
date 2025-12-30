import pandas as pd
import csv
import os
import chardet

class DataLoader:
    """Class for loading data from files in multiple formats (CSV, Excel, JSON, Parquet).

    This class automatically detects the encoding (for text files),
    delimiter (for CSV), and loads the data into a pandas DataFrame.

    Attributes:
        file_path (str): Path to the file to be loaded.
        encoding (str): Detected or default encoding ('utf-8').
        df (pd.DataFrame): DataFrame containing the loaded data.
        skipped_lines (int): Number of lines skipped during loading.

    Example:
        >>> loader = DataLoader("data/dataset.csv")
        >>> df = loader.load_data()
        >>> print(df.head())
    """

    def __init__(self, file_path):
        """Initializes the data loader with the file path.

        Args:
            file_path (str): Path to the file to be loaded.
        """

        self.file_path = file_path
        self.encoding = 'utf-8'
        self.df = None
        self.skipped_lines = 0

    def _check_file_exists(self):
        """Checks if the file exists at the specified path.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a file.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"El archivo no existe en la ruta: {self.file_path}")
        if not os.path.isfile(self.file_path):
            raise ValueError(f"La ruta no es un archivo: {self.file_path}")

    def _detect_encoding(self):
        """Detects the encoding of the file (for CSV/TXT files)."""
        with open(self.file_path, 'rb') as f:
            raw_data = f.read(10000)
            self.encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        print(f"Codificación detectada: {self.encoding}")

    def _detect_delimiter(self):
        """Detects the delimiter for CSV files.

        Returns:
            str: Detected delimiter (e.g., ',' or ';').
        """
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
                return dialect.delimiter
            except csv.Error:
                return ','  # Default delimiter

    def _load_csv_or_txt(self):
        """Loads CSV or TXT files into a DataFrame."""
        delimiter = self._detect_delimiter() if self.file_path.endswith('.csv') else '\t'
        self.df = pd.read_csv(
            self.file_path,
            encoding=self.encoding,
            delimiter=delimiter,
            on_bad_lines='skip',
            low_memory=False
        )

    def _load_excel(self):
        """Loads Excel (XLSX, XLS) files into a DataFrame."""
        self.df = pd.read_excel(self.file_path)

    def _load_json(self):
        """Loads JSON files into a DataFrame."""
        self.df = pd.read_json(self.file_path)

    def _load_parquet(self):
        """Loads Parquet files into a DataFrame."""
        self.df = pd.read_parquet(self.file_path)

    def load_data(self):
        """Loads the file based on its format and returns a DataFrame.

        Returns:
            pd.DataFrame: DataFrame with the loaded data.

        Raises:
            ValueError: If the file format is not supported.
        """
        try:
            self._check_file_exists()
            file_ext = os.path.splitext(self.file_path)[1].lower()

            if file_ext in ('.csv', '.txt'):
                self._detect_encoding()
                self._load_csv_or_txt()
            elif file_ext in ('.xlsx', '.xls'):
                self._load_excel()
            elif file_ext == '.json':
                self._load_json()
            elif file_ext == '.parquet':
                self._load_parquet()
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            self.skipped_lines = 0
            print(f"✅ File loaded successfully. Total lines: {len(self.df)}")
            return self.df

        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return None