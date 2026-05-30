"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

# Make `backend/` importable as the test root so `from coral_sql import ...` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
