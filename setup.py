#!/usr/bin/env python3
"""
Setup script for Music Tools API

This script provides an alternative installation method for environments
that don't support pyproject.toml or prefer traditional setup.py.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="music-tools-api",
    version="1.0.0",
    author="Adar Bahar",
    author_email="adar@bahar.co.il",
    description="A standalone REST API service for YouTube to MP3 conversion and AI-powered audio stem separation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/music-tools-api",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/music-tools-api/issues",
        "Documentation": "https://github.com/yourusername/music-tools-api#readme",
        "Source Code": "https://github.com/yourusername/music-tools-api",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "music-tools-api=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.conf"],
    },
    keywords=[
        "audio",
        "music",
        "youtube",
        "mp3",
        "stem-separation",
        "demucs",
        "api",
        "fastapi",
        "ai",
    ],
    license="MIT",
)
