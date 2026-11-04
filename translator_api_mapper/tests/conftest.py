import sys
from pathlib import Path

# translator_api_mapper modules import each other from src/ as top-level
# packages (that is how the Dockerfile runs them), so put src/ on the path.
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
