from theme_manager import ThemeManager


def test_theme_manager_missing_file(tmp_path):
    tm = ThemeManager(themes_file=tmp_path / "missing.json")

    assert tm.themes == {}

    qss = tm.get_theme("dark")
    assert isinstance(qss, str)
    assert len(qss) > 0


def test_get_theme_dict_unknown_theme():
    tm = ThemeManager()
    assert tm.get_theme_dict("nonexistent") == {}


def test_get_font_fallback():
    tm = ThemeManager()
    assert tm.get_font("nonexistent", fallback="Arial") == "Arial"
