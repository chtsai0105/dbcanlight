"""Required actions when initiating the package."""

try:
    from importlib.metadata import entry_points, metadata
except ImportError:
    from importlib_metadata import metadata, entry_points

import dbcanlight._config as _config


def map_entry_point_module(project_name):
    """Get the dictionary that map the scripts to their entry point names."""
    d = {}
    for x in entry_points().select(group="console_scripts"):
        if x.dist.name == project_name:
            d[x.value.split(":")[0]] = x.name
    return d


meta = metadata("dbcanlight")
__version__ = meta["Version"]
__author__ = meta["Author-email"]

entry_point_map = map_entry_point_module(meta["Name"])

# Create config folder in $HOME/.dbcanlight
_config.cfg_dir.mkdir(exist_ok=True)
