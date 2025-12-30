from setuptools import setup, find_packages

setup(
    name="antyx",
    version="0.1.1",
    packages=find_packages(),
    author="Daniel Rodrigálvarez Morente",
    author_email="drm.datos@email.com",
    description="Paquete para análisis exploratorio de datos",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/drmdata/antyx",
    python_requires=">=3.8", install_requires=['seaborn', 'seaborn']
)
