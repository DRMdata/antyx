# data_loader.py

## Overview

The `data_loader.py` module contents the `DataLoader` class for loading data from multiple file formats (CSV, Excel, JSON, Parquet).

This class automatically detects:

- File encoding (for text files).
- Delimiter (for CSV files).
- Loads data into a pandas DataFrame.

## Attributes

| Attribute          | Type       | Description                                  |
|-------------------|------------|----------------------------------------------|
| `file_path`       | `str`      | Path to the file to load.                    |
| `encoding`        | `str`      | Detected encoding (default 'utf-8').         |
| `df`              | `pd.DataFrame` | DataFrame with loaded data.                 |
| `skipped_lines`   | `int`      | Number of lines skipped during loading.     |

## Methods

### `__init__(self, file_path)`
Initializes the data loader with the file path.

**Parameters:**

- `file_path` (`str`): Path to the file to load.

---

### `_check_file_exists(self)`
Checks if the file exists at the specified path.

**Exceptions:**

- `FileNotFoundError`: If the file does not exist.
- `ValueError`: If the path is not a valid file.

---

### `_detect_encoding(self)`
Detects the encoding of the file (for CSV/TXT).

---

### `_detect_delimiter(self)`
Detects the delimiter of CSV files.

**Returns:**

- `str`: Detected delimiter (e.g., `','` or `';'`).

---

### `_load_csv_or_txt(self)`
Loads CSV or TXT files into a DataFrame.

---

### `_load_excel(self)`
Loads Excel (.xlsx, .xls) files into a DataFrame.

---

### `_load_json(self)`
Loads JSON files into a DataFrame.

---

### `_load_parquet(self)`
Loads Parquet files into a DataFrame.

---

### `load_data(self)`
Loads the file according to its format and returns a DataFrame.

**Returns:**

- `pd.DataFrame`: DataFrame with loaded data.

**Exceptions:**

- `ValueError`: If the file format is not supported.


## Supported Formats

| Extension | Description          |
|-----------|----------------------|
| `.csv`    | CSV files            |
| `.txt`    | Text files           |
| `.xlsx`   | Excel (2007+)        |
| `.xls`    | Excel (97-2003)      |
| `.json`   | JSON                 |
| `.parquet`| Parquet              |

## Dependencies

- `pandas`: For data manipulation and analysis.
- `CSV`: Standard library (built-in)
- `os`: Operating system interfaces.
- `chardet`: Universal character encoding detector

## Usage Example

```python
from data_loader import DataLoader

# Load a CSV
loader = DataLoader("data/dataset.csv")
df = loader.load_data()
print(df.head())

# Load an Excel file
loader_excel = DataLoader("data/file.xlsx")
df_excel = loader_excel.load_data()

# Load a JSON file
loader_json = DataLoader("data/data.json")
df_json = loader_json.load_data()
```

## Notes

- For CSV/TXT files, encoding and delimiter are automatically detected.
- Corrupt lines in CSV files are skipped (`on_bad_lines='skip'`).