"""
Setup script for AIMgentix SDK
"""

from setuptools import setup, find_packages

setup(
    name="aimgentix",
    version="0.1.0",
    description="Python SDK for AIMgentix Agent Audit Trail",
    author="Peter Krentel",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
