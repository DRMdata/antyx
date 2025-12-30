from setuptools import setup, find_packages

setup(
    name="antyx",
    version="0.1.3",
    packages=find_packages(),
    author="Daniel Rodrigálvarez Morente",
    author_email="drm.datos@email.com",
    description="Antyx is an automated EDA engine designed to generate fast, structured and professional exploratory reports from any tabular dataset.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/drmdata/antyx"
)
