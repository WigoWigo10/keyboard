"""
Shim kept so that legacy `python setup.py ...` invocations keep working.

All packaging metadata lives in pyproject.toml. Prefer building with:

    python -m build
"""
from setuptools import setup

setup()
