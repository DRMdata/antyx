import seaborn as sns
import matplotlib.pyplot as plt
import os
import json
import numpy as np

def set_light_theme():
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "text.color": "black",
        "axes.labelcolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "grid.color": "#cccccc"
    })

def set_dark_theme():
    sns.set_theme(style="darkgrid")
    plt.rcParams.update({
        "figure.facecolor": "#1e1e1e",
        "axes.facecolor": "#1e1e1e",
        "savefig.facecolor": "#1e1e1e",
        "text.color": "white",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "grid.color": "#444444"
    })


def save_fig_json(fig, path):
    '''
    Creación de JSON con los datos de los gráficos
    :param fig:
    :param path:
    :return: JSON
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    obj = fig.to_plotly_json()

    # 🔥 FIX: convertir cualquier ndarray a list()
    def convert(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, dict):
            return {k: convert(v) for k, v in o.items()}
        if isinstance(o, list):
            return [convert(v) for v in o]
        return o

    obj = convert(obj)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)