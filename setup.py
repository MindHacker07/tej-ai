#!/usr/bin/env python3
"""
TejStrike AI - Setup Script
"""

from setuptools import setup, find_packages

setup(
    name="tejstrike-ai",
    version="2.0.0",
    author="TejStrike AI",
    description="AI-Powered Security Tool Orchestrator with Multi-Model LLM Support",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/MindHacker07/tej-ai",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "anthropic": ["anthropic>=0.30.0"],
        "openai": ["openai>=1.0.0"],
        "groq": ["groq>=0.5.0"],
        "all-llm": ["anthropic>=0.30.0", "openai>=1.0.0", "groq>=0.5.0"],
    },
    entry_points={
        "console_scripts": [
            "tejstrike=tej.main:main",
            "tejstrike-gui=tej.gui:launch_gui",
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
    keywords="security pentesting kali-linux ai hacking tools llm claude gpt",
)
