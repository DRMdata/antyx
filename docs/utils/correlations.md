# correlations.py

## **Overview**
This document provides detailed documentation for the `correlations.py` script, which is part of the **Antix** Python package. The script generates a heatmap and a list of significant correlations between numeric columns in a DataFrame.

---

## **Features**
- Generates a **heatmap** visualizing correlation coefficients.
- Identifies and lists **significant correlations** based on a user-defined threshold.
- Returns results as **HTML-formatted output** for easy integration into web applications or Jupyter notebooks.
- Handles cases where there are insufficient numeric columns.

---

## **Dependencies**
The script requires the following Python libraries:

- `matplotlib`: To generate plots without a graphical interface (Agg backend).
- `seaborn`: Used specifically for generating the correlation heatmap.
- `pandas`: Library for data manipulation and analysis.
- `base64` (standard library): Used to encode generated plots into base64 format for easy embedding in HTML.
- `BytesIO` (from io, standard library): Used to capture matplotlib plot output before encoding.

---

## **Usage Example**

### **1. Basic Usage**

```python
import pandas as pd
from antyx.utils.correlations import correlation_analysis

# Sample DataFrame
data = {
    'A': [1, 2, 3, 4],
    'B': [4, 3, 2, 1],
    'C': [5, 6, 7, 8]
}
df = pd.DataFrame(data)

# Generate correlation analysis
result_html = correlation_analysis(df)
print(result_html)  # Displays heatmap and significant correlations
```

### **2. Custom Threshold**
```python
result_html = correlation_analysis(df, threshold=0.3)  # Lower threshold for more results
```
---

## **Function: `correlation_analysis()`**

### **Purpose**
Analyzes correlations between numeric columns in a DataFrame and returns a heatmap along with a list of significant correlations.

### **Parameters**
| Parameter | Type            | Description                                                                 | Default Value |
|-----------|-----------------|-----------------------------------------------------------------------------|---------------|
| `df`      | `pd.DataFrame`  | The input DataFrame to analyze.                                            | Required      |
| `threshold` | `float`         | Minimum absolute correlation value to consider as significant.             | `0.5`         |

### **Returns**
- **HTML string** containing:
  - A heatmap of correlations (if enough numeric columns exist).
  - A list of significant correlations above/below the threshold.

---

## **Returns**

### **1. Heatmap**
- A color-coded matrix where:
  - **Red** indicates strong positive correlation.
  - **Blue** indicates strong negative correlation.
  - Values are annotated in the cells.

### **2. Significant Correlations List**
- Displays pairs of columns with correlations above/below the threshold.
- Example output:

  ```
    significant correlations (Threshold ±0.5):
    - A vs B: -1.00
    - C vs A: 1.00
  ```

---

## **Edge Cases Handled**
| Scenario | Behavior |
|----------|----------|
| **No numeric columns** | Returns a message indicating insufficient data. |
| **Single numeric column** | Skips correlation analysis (requires at least two columns). |
| **All correlations below threshold** | Lists "No significant correlations detected." |

---
