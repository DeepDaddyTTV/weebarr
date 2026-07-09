from src import version


def test_version_override_wins(monkeypatch):
    monkeypatch.setenv("WEEBARR_VERSION_OVERRIDE", "9.9.9")

    assert version.get_version() == "9.9.9"


def test_exact_tag_wins(monkeypatch):
    monkeypatch.delenv("WEEBARR_VERSION_OVERRIDE", raising=False)
    monkeypatch.setattr(version, "_git_exact_tag", lambda: "0.2.0")
    monkeypatch.setattr(version, "_git_dirty", lambda: False)
    monkeypatch.setattr(version, "_package_version", lambda: "0.2.0")

    assert version.get_version() == "0.2.0"


def test_dirty_source_tree_stays_on_current_release_line(monkeypatch):
    monkeypatch.delenv("WEEBARR_VERSION_OVERRIDE", raising=False)
    monkeypatch.setattr(version, "_git_exact_tag", lambda: None)
    monkeypatch.setattr(version, "_git_dirty", lambda: True)
    monkeypatch.setattr(version, "_package_version", lambda: None)

    assert version.get_version() == "0.2.0-dev-dirty"


def test_packaged_fallback_uses_installed_version(monkeypatch):
    monkeypatch.delenv("WEEBARR_VERSION_OVERRIDE", raising=False)
    monkeypatch.setattr(version, "_git_exact_tag", lambda: None)
    monkeypatch.setattr(version, "_git_dirty", lambda: None)
    monkeypatch.setattr(version, "_package_version", lambda: "0.2.0")

    assert version.get_version() == "0.2.0"
