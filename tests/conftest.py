"""Shared pytest fixtures and path setup for the test suite."""

import os
import sys

# Make src/ importable the same way the app runs it (flat imports like
# `from data_fetcher import ...`).
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
