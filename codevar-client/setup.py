from setuptools import find_packages, setup

setup(
    name="codevar-client",
    version="0.1.0",
    description="Exception capture middleware and event reporter for CodeVAR, a mini error-tracker for FastAPI apps",
    packages=find_packages(include=["codevar_client", "codevar_client.*"]),
    install_requires=[
        "starlette",
        "requests",
    ],
    python_requires=">=3.9",
)
