"""
run.py - Root launcher for Shan Shui (山水) Py5 Standalone Application
"""

import sys
from pathlib import Path

# Ensure shanshui package is on python path
sys.path.insert(0, str(Path(__file__).parent))

from shanshui.main import run

if __name__ == "__main__":
    run()
