import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))   # modules, loader, config
sys.path.insert(0, str(HERE))                  # reference.py