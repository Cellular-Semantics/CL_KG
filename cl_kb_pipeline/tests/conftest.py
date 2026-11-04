import sys
from pathlib import Path

# The CI script imports 'utils.schema_test_tools' with src/ as the working
# package root, so put src/ on the path the same way.
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
