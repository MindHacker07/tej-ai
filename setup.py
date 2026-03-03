#!/usr/bin/env python3
"""
Tej AI - Setup Script
"""

from setuptools import setup, find_packages

setup(
    name="tej",
    version="1.0.0",
    author="Tej AI",
    description="AI-Powered Security Tool Orchestrator for Kali Linux & Windows",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/tej-ai/tej",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "tej=tej.main:main",
            "tej-gui=tej.gui:launch_gui",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Environment :: Console",
    ],
    keywords="security pentesting kali-linux ai hacking tools",
)
