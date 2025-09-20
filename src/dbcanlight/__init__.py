"""Required actions when initiating the package."""

import logging
import os

try:
    from importlib_metadata import entry_points, metadata
except ImportError:
    from importlib.metadata import entry_points, metadata
from pathlib import Path
from typing import Literal


def _map_entry_point_module(project_name):
    """Get the dictionary that map the scripts to their entry point names."""
    d = {}
    for x in entry_points().select(group="console_scripts"):
        if x.dist.name == project_name:
            d[x.module] = x.name
    return d


# Create logger for the package
logger = logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)


VERSION: str = metadata("dbcanlight")["Version"]
AUTHOR: str = metadata("dbcanlight")["Author-email"]
ENTRY_POINTS: dict[str, str] = _map_entry_point_module(metadata("dbcanlight")["Name"])
AVAIL_CPUS = int(os.environ.get("SLURM_CPUS_ON_NODE", os.cpu_count()))
DATABASE_METADATA = "https://raw.githubusercontent.com/chtsai0105/dbcanlight/refs/heads/main/database_metadata.json"

_dbcanlight_db = os.getenv("DBCANLIGHT_DB")
if _dbcanlight_db:
    CFG_DIR = Path(_dbcanlight_db)
else:
    CFG_DIR: Path = Path.home() / ".dbcanlight"
    CFG_DIR.mkdir(exist_ok=True)

DB_PATH: dict[Literal["cazyme_hmms", "subs_hmms", "subs_mapper", "diamond"], Path] = {
    "cazyme_hmms": CFG_DIR / "cazyme.hmm",
    "subs_hmms": CFG_DIR / "substrate.hmm",
    "subs_mapper": CFG_DIR / "substrate_mapping.tsv",
    "diamond": CFG_DIR / "cazydb.dmnd",
}

AVAIL_MODES = {"cazyme": "cazymes.tsv", "sub": "substrates.tsv", "diamond": "diamond.tsv"}
