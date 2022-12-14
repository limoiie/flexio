__all__ = ['FilePointer', 'flex_open']

try:
    import importlib.metadata as _importlib_metadata
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    import importlib_metadata as _importlib_metadata

try:
    __version__ = _importlib_metadata.version("flexio")
except _importlib_metadata.PackageNotFoundError:
    __version__ = "unknown version"

from .flexio import FilePointer, flex_open
