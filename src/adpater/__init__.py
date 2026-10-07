"""Deprecated alias for the ``adapter`` package (the old misspelling)."""

import importlib
import importlib.abc
import importlib.util
import sys
import warnings

import adapter

warnings.warn(
    "'adpater' is a deprecated alias for 'adapter'",
    DeprecationWarning,
    stacklevel=2,
)


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, real_name: str) -> None:
        self._real_name = real_name

    def create_module(self, spec):
        return importlib.import_module(self._real_name)

    def exec_module(self, module) -> None:
        return None


class _AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        prefix = "adpater"
        if fullname != prefix and not fullname.startswith(f"{prefix}."):
            return None
        real_name = "adapter" + fullname[len(prefix) :]
        real_spec = importlib.util.find_spec(real_name)
        if real_spec is None:
            return None
        return importlib.util.spec_from_loader(
            fullname,
            _AliasLoader(real_name),
            is_package=real_spec.submodule_search_locations is not None,
        )


sys.meta_path.insert(0, _AliasFinder())
sys.modules[__name__] = adapter
