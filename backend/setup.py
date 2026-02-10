"""Setup script for script_to_doc package."""

from setuptools import setup, find_packages

setup(
    name="script_to_doc",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.0",
        "uvicorn[standard]==0.27.0",
        "azure-ai-documentintelligence==1.0.0b1",
        "azure-identity==1.15.0",
        "azure-storage-blob==12.19.0",
        "azure-cosmos==4.5.1",
        "azure-servicebus==7.11.4",
        "openai==1.10.0",
        "python-docx==1.1.0",
        "nltk==3.8.1",
        "pydantic==2.5.3",
        "pydantic-settings==2.1.0",
    ],
    python_requires=">=3.9",
)

