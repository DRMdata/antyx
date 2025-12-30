# outlers.py

This module provides functionality to visualize outliers in numerical columns of a DataFrame using the Tukey method (1.5 × IQR).

## Features

- Automatic detection of numerical columns
- Visual representation using violin plots with outlier highlighting
- Statistical summary for each variable
- Percentage of outliers per column
- Clean, publication-quality visualizations

## Dependencies

- `pandas`: For data manipulation and analysis
- `matplotlib.pyplot`: For creating visualizations
- `seaborn`: For statistical data visualization (violin plots)
- `base64` (standard library): For encoding the generated plot into base64 format
- `BytesIO` (from `io`, standard library): For capturing the plot output in memory

## Usage Example

```python
import pandas as pd
from outliers import detect_outliers

# Load your data
df = pd.read_csv('your_data.csv')

# Generate outlier visualization
visualization = detect_outliers(df)

# Display in Jupyter notebook or save to HTML
with open('outliers_report.html', 'w') as f:
    f.write(f"""
    <html>
        <head><title>Outlier Report</title></head>
        <body>
            {visualization}
        </body>
    </html>
    """)
```

## **Function:* `detect_outliers()`**:

### **Purpose**

1. Identifies all numerical columns in the DataFrame
2. For each column:
   - Calculates quartiles (Q1, Q3) and interquartile range (IQR)
   - Determines outlier bounds (1.5 × IQR below Q1 and above Q3)
   - Identifies actual outliers
   - Creates a violin plot with red dots marking outliers
   - Displays key statistics in the plot margin

### **Parameters**
| Parameter | Type     | Description                                                                 | Default Value |
|-----------|----------|-----------------------------------------------------------------------------|---------------|
| `df`      | `pd.DataFrame` | The input DataFrame to analyze.                                            | Required      |

### **Returns**

- Visualizations of the DataFrame.

## **Returns**

- **Violin plots**: Show the distribution of each variable
- **Red dots**: Represent individual outlier values
- **Statistics panel**:
  - Outliers count and percentage
  - Upper and lower bounds for outlier detection
  - Quartile values (25%, 50%, 75%)
```
