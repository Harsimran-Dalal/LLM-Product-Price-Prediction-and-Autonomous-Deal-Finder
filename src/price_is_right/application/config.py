"""Runtime paths for the canonical deal-finder application."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
VECTORSTORE_DIR = DATA_DIR / "products_vectorstore"
LEGACY_MEMORY_FILE = PROJECT_ROOT / "03_autonomous_deal_finder" / "memory.json"
LEGACY_VECTORSTORE_DIR = PROJECT_ROOT / "03_autonomous_deal_finder" / "products_vectorstore"

DATA_DIR.mkdir(parents=True, exist_ok=True)
