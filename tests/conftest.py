"""
conftest.py
------------
Ensures the project root is on sys.path so `from src import ...` works
when running pytest from the project root or from within tests/.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
