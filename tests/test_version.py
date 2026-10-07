from rag.version import normalize_version, version_key


def test_version_key_sorts_numerically_and_tolerates_junk():
    assert sorted(["10.0", "2.0", "1.5"], key=version_key) == ["1.5", "2.0", "10.0"]
    assert version_key("beta") == (-1,)


def test_normalize_version():
    assert normalize_version("2") == "2.0"
    assert normalize_version("v3") == "3.0"
    assert normalize_version("1.0") == "1.0"
    assert normalize_version(" ") == ""
