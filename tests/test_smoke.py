import src.main


def test_main_imports() -> None:
    assert callable(src.main.main)
