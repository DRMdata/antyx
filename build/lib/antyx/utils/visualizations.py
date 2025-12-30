import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO

def basic_visuals(df):
    """Generates a visualisations of the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to analyze.

    Returns:
        Visualizations of the DataFrame.
    """
    numeric = df.select_dtypes(include='number')
    if numeric.shape[1] == 0:
        return "<p><strong>Visualizaciones:</strong> No hay columnas numéricas para graficar.</p>"
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(df.select_dtypes(include='number').iloc[:, 0], kde=True, ax=ax)
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{encoded}"/>'

    except Exception as e:
        return f"<p><strong>Error al generar visualizaciones:</strong> {str(e)}</p>"

    '''
    Generar una línea de gráficos para cada variable y dependiendo del tipo de variable de que se trate
    numéricas: histograma
    discrtas: barras
    continuas: lineal
    
    boxplot y violinplot para cada variable
    
    
    '''