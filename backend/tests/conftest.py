PIPELINE_TEST_FILES = {
    "test_control_tower.py",
    "test_cycle1.py",
    "test_cycle2.py",
    "test_cycle3.py",
    "test_cycle4.py",
    "test_cycle6.py",
    "test_cycle7.py",
    "test_cycle8.py",
    "test_cycle9.py",
    "test_cycle10.py",
}


def pytest_collection_modifyitems(items) -> None:
    import pytest

    for item in items:
        if item.fspath.basename in PIPELINE_TEST_FILES:
            item.add_marker(pytest.mark.pipeline)
