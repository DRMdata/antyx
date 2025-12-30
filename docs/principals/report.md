# report.py

## Overview

The `report.py` module contains the `EDAReport` class responsible for generating exploratory data analysis (EDA) reports from data files. This class leverages the data loading functionality provided by the `load_data` module to process the data and generates an HTML report with key visualizations and statistics.

## EDAReport Class

### Attributes

| Attribute      | Type            | Description                                  |
|----------------|-----------------|----------------------------------------------|
| `file_path`    | str             | Path to the data file to be analyzed         |
| `df`           | pd.DataFrame     | DataFrame containing the loaded data          |
| `skipped_lines`| int             | Number of lines skipped during data loading  |
| `encoding`     | str             | Encoding used to read the file               |


### Methods

#### `__init__(self, file_path)`
Constructor for the EDAReport class.

**Parameters:**

- `file_path` (str): Path to the data file.

**Usage Example:**

```python
from report import EDAReport

# Create instance with path to CSV file
eda_report = EDAReport("data/example.csv")
```

#### `_load_data(self)`
Private method that loads data using the `DataLoader` class.

**Implementation Details:**

1. Creates a `DataLoader` instance with the provided path.
2. Executes the `load()` method to obtain the data.
3. Stores encoding information and skipped lines count.
4. Assigns data to the `df` attribute.

**Exceptions:**

- Raises `ValueError` if data loading fails.

#### `generate_html(self, output_path='eda_report.html', open_browser=True)`
Generates an HTML report with exploratory analysis.

**Parameters:**

- `output_path` (str): Path where to save the report. Default: `'eda_report.html'`.
- `open_browser` (bool): If True, automatically opens browser. Default: `True`.

**Implementation Details:**

1. Generates HTML content with:
   - Descriptive statistics
   - Missing values analysis
   - Correlation matrices
   - Outlier visualizations
2. Saves file to specified path.
3. Opens browser if `open_browser` is True.

**Usage Example:**

```python
# Generate report with default settings
eda_report.generate_html()

# Generate custom report
eda_report.generate_html(
    output_path="sales_report.html",
    open_browser=False
)
```

## Dependencies

- `pandas`: For data manipulation and analysis.
- `load_data`: For data file loading.
- `os`: Operating system interfaces.
- `webbrowser` (standard library): To open report in browser.

## Usage example

```python
from report import EDAReport

# 1. Create instance with file path
eda_report = EDAReport("data/sales.csv")

# 2. Generate HTML report
eda_report.generate_html(
    output_path="sales_analysis.html",
    open_browser=True
)

# 3. Access loading process information
print(f"Encoding used: {eda_report.encoding}")
print(f"Skipped lines: {eda_report.skipped_lines}")
```


