"""
RITUAL - Hermetic LLM Context Management Portal
Setup configuration for PyPI distribution
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ritual",
    version="1.0.0",
    author="RITUAL Contributors",
    author_email="contact@ritual-lang.dev",
    description="Hermetic LLM Context Management Portal",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ritual-lang/ritual",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    keywords="llm context-management mcm fastapi portal mystical hermetic",
    python_requires=">=3.10",
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "pydantic==2.5.0",
        "pyyaml==6.0.1",
        "cryptography==41.0.7",
        "requests==2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ritual=backend.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
