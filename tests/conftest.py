import sys
from pathlib import Path

# Ensure project root is on sys.path so that `import src` works regardless of
# where the test runner is invoked.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT)) 