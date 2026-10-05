import pytest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings

# Force offline/test mode for predictable test runs
settings.AI_PROVIDER = "heuristic"
settings.SEARCH_PROVIDER = "curated"
