import src.main


def test_main_imports() -> None:
    assert hasattr(src.main, "Default")
