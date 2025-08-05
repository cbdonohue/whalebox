#!/usr/bin/env python3
"""
Setup script for QEMU Runner
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="qemu-runner",
    version="1.0.0",
    author="Open Source Community",
    author_email="",
    description="A simple command line utility for running QEMU virtual machines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/qemu-runner",
    py_modules=["qemu_runner"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Emulation",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "qemu-runner=qemu_runner:main",
            "qr=qemu_runner:main",
        ],
    },
    keywords="qemu virtual machine vm virtualization emulation",
    project_urls={
        "Bug Reports": "https://github.com/your-username/qemu-runner/issues",
        "Source": "https://github.com/your-username/qemu-runner",
    },
)