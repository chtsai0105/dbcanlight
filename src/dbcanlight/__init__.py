"""Placeholder init file for Python purposes."""
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

import dbcanlight.config as config

__name__ = "dbcanLight"
__version__ = version("dbcanLight")

# Create config folder in $HOME/.dbcanlight
config.cfg_dir.mkdir(exist_ok=True)