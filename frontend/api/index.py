import os
import sys
from pathlib import Path

# Resolve the directories relative to this file
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

# Add directories to sys.path so python can resolve local imports
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

# Expose the app from backend.main
from backend.main import app