# summary.md

This module generates a statistical summary of the DataFrame.

## Features

### Numerical Data
For each numerical column, the following is calculated and displayed:
- Data type
- Count of non-null/null values
- Number of unique values
- Most frequent value (Top) and its percentage frequency
- Complete descriptive statistics:
  - Mean
  - Standard deviation (Std)
  - Variance (Var)
  - Percentiles (Min, 25%, 50%, 75%)
  - Maximum (Max)

### Non-Numerical Data
For non-numerical columns, the following is shown:
- Data type
- Count of non-null/null values
- Number of unique values
- Most frequent value (Top) and its absolute/percentage frequency

## Dependencies

- `pandas`: For data manipulation and analysis

## Usage Example

```python
import pandas as pd
from antix.summary import describe_data

# Create example DataFrame
data = {
    'age': [25, 30, None, 45, 50],
    'gender': ['M', 'F', 'M', 'F', None],
    'income': [50000, 60000, None, 80000, 90000]
}
df = pd.DataFrame(data)

# Generate summary
summary_html = describe_data(df)
print(summary_html)  # Displays HTML with summary tables
```

## **Function: `describe_data()`**:

### **Purpose**

Generates a comprehensive statistical summary of a DataFrame, organizing information into two main sections:
- **Numerical data**: Complete descriptive statistics
- **Non-numerical data**: Information about unique values and frequencies

### **Parameters**
| Parameter | Type     | Description                                                                 | Default Value |
|-----------|----------|-----------------------------------------------------------------------------|---------------|
| `df`      | `pd.DataFrame` | The input DataFrame to analyze.                                            | Required      |

### **Returns**

The function returns an HTML string with two organized tables:

1. **Numerical Data Table**:
   - Headers: Variable, Type, Non-null, Nulls, Unique, Top, Freq Top, % Top, Mean, Std, Var, Min, 25%, 50%, 75%, Max
   - Each row represents a numerical column from the DataFrame

2. **Non-Numerical Data Table**:
   - Headers: Variable, Type, Non-null, Nulls, Unique, Top, Freq Top, % Top
   - Each row represents a non-numerical column from the DataFrame

## Important Notes

1. **Null value handling**:
   - Correctly counts null values
   - Statistical calculations automatically ignore null values

2. **Number formatting**:
   - Numbers formatted with thousand separators (e.g., 50,000)
   - Two decimal places for continuous values

3. **Unique values**:
   - For non-numerical columns, shows most frequent value and percentage
   - Useful for identifying dominant categories in categorical data

4. **Compatibility**:
   - Works with any pandas DataFrame
   - Handles different data types correctly (int, float, object, etc.)