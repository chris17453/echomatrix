# audio_manager/setup.py
#!/usr/bin/env python3
"""
Setup script for the audio_manager package.
"""

from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define package metadata
setup(
    name="audio_manager",
    version="0.1.0",
    author="Charles Watkins",
    author_email="chris@watkinslabs.com",
    description="A comprehensive audio recording management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chris17453/echomatrix_audio_manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: System :: Archiving",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.1.0",      # For CLI interface
        "boto3>=1.20.0",     # For S3 support
        "paramiko>=2.9.0",   # For SCP support
        "pyyaml>=6.0",       # For configuration
        "openai>=1.1.0",     # For OpenAI API integration 
        "soundfile>=0.12.1", # For audio file handling
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "audio_manager=audio_manager.cli:cli",
        ],
    },
    package_data={
        "audio_manager": ["py.typed"],  # For type checking support
    },
    include_package_data=True,
    zip_safe=False,
    license="BSD 3-Clause",
)

#51570b45-6cf8-48a3-8964-dba640c62793