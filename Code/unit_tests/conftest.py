import sys
from pathlib import Path

# add the parent directory (Code/) to python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
