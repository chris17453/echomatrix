#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="config_manager",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A flexible configuration manager for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/config_manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pyyaml>=5.1",
    ],
    entry_points={
        'console_scripts': [
            'config_manager=config_manager.cli:main',
        ],
    },
    keywords="configuration, config, yaml, json, ini, environment, variables",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/config_manager/issues",
        "Documentation": "https://github.com/yourusername/config_manager",
        "Source Code": "https://github.com/yourusername/config_manager",
    },
    license="BSD 3-Clause License",
)
