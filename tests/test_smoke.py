def test_python_version_is_supported():
    import sys

    assert sys.version_info[:2] == (3, 12)
