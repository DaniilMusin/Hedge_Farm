from setuptools import setup, find_packages

setup(
    name="hedgefarm",
    version="0.1.0",
    description="HedgeFarm Pricer - система ценообразования для хеджирования сельхозпродуктов",
    author="HedgeFarm Team",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "numpy>=1.21.0",
        "scipy>=1.8.0",
        "pandas>=1.3.0",
        "requests>=2.28.0",
        "PyYAML>=6.0.0",
    ],
    python_requires=">=3.8",
)