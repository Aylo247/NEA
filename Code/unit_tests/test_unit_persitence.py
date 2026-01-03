import pytest
from pathlib import Path
from cryptography.fernet import InvalidToken

from persistence_manager import PersistenceManager


class DummySchedule:
    def to_dict(self):
        return {"blocks": ["Maths", "Physics"]}


class DummySettings:
    def to_dict(self):
        return {"theme": "dark", "autosave": True}


@pytest.fixture
def sandboxed_pm(tmp_path, monkeypatch):
    """
    Creates a PersistenceManager that writes ONLY into tmp_path
    and never touches real user files.
    """
    pm = PersistenceManager()

    monkeypatch.setattr(pm, "data_file", tmp_path / "data.json")
    monkeypatch.setattr(pm, "settings_file", tmp_path / "settings.json")
    monkeypatch.setattr(pm, "custom_blocks_file", tmp_path / "custom_blocks.json")
    monkeypatch.setattr(pm, "key_file", tmp_path / "secret.key")

    # re-initialise encryption using sandboxed key
    from cryptography.fernet import Fernet
    pm.fernet = Fernet(pm._load_or_create_key())

    return pm


# =========================
# TESTS
# =========================

def test_save_and_load_schedule(sandboxed_pm):
    schedule = DummySchedule()

    sandboxed_pm.save_data(schedule)
    loaded = sandboxed_pm.load_data()

    assert "schedule" in loaded
    assert loaded["schedule"]["blocks"] == ["Maths", "Physics"]


def test_missing_data_file(sandboxed_pm):
    data = sandboxed_pm.load_data()
    assert data == {}


def test_save_and_load_settings(sandboxed_pm):
    settings = DummySettings()

    sandboxed_pm.save_settings(settings)
    loaded = sandboxed_pm.load_settings()

    assert loaded["theme"] == "dark"
    assert loaded["autosave"] is True


def test_corrupt_encrypted_file(sandboxed_pm):
    sandboxed_pm.data_file.write_bytes(b"not encrypted")

    data = sandboxed_pm.load_data()
    assert data == {}
