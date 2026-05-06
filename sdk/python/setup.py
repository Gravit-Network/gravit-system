from setuptools import setup, find_packages

setup(
    name="gravit-sdk",
    version="1.0.0",
    description="Python SDK for Gravit Open Network",
    author="Gravit Open Network Foundation",
    author_email="info@gravitnetwork.org",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
