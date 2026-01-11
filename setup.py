from setuptools import setup, find_packages

setup(
    name="antyx",
    version="0.1.6",
    packages=find_packages(),
    author="Daniel Rodrigálvarez Morente",
    author_email="drm.datos@email.com",
    description="Antyx is an automated EDA engine designed to generate fast, structured and professional exploratory reports from any tabular dataset.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/drmdata/antyx",
    install_requires = [
        # Pendiente añadir rangos de versiones
        "chardet==5.2.0",
        "Flask==3.1.2",
        "matplotlib==3.10.8",
        "numpy==2.4.0",
        "pandas==2.3.3",
        "plotly==6.5.0",
        "polars==1.36.1",
        "requests==2.32.5",
        "seaborn==0.13.2",
    ],
    extras_require = {
        "dev": ["pytest", "black"], #Revisar
        "docs": ["sphinx", "myst-parser"], #Revisar
        "all": [
            # Pendiente añadir rangos de versiones
            "chardet==5.2.0",
            "Flask==3.1.2",
            "matplotlib==3.10.8",
            "numpy==2.4.0",
            "pandas==2.3.3",
            "plotly==6.5.0",
            "polars==1.36.1",
            "requests==2.32.5",
            "seaborn==0.13.2",
        ],
    },
)
