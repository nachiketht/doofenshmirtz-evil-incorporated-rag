import importlib
import warnings


def test_legacy_package_name_still_imports_the_same_modules():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy = importlib.import_module("adpater")
        legacy_db = importlib.import_module("adpater.database_adapter")
    import adapter
    from adapter import database_adapter

    assert legacy.DatabaseAdapter is adapter.DatabaseAdapter
    assert legacy_db is database_adapter
