from pathlib import Path
from sys import path
path.insert(1, str(Path(__file__).resolve().parent.parent))
import common

RESULTS_CSV = common.RESULTS_CSV
