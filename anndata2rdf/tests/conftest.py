import sys
from pathlib import Path

# anndata2rdf modules live in src/ and import each other as top-level modules
# (that is how the Dockerfile runs them), so put src/ on the path.
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
