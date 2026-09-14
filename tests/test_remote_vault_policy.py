from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from unidl.core.config import Config
from unidl.core.engine import Engine
from unidl.core.settings import SettingsStore, global_settings


def _settings(tmp_path: Path):
    config = Config({"paths": {"home": str(tmp_path)}})
    return global_settings(SettingsStore(tmp_path / "settings.json"), config=config)


def test_remote_operation_switches_narrow_the_legacy_master_gate() -> None:
    with TemporaryDirectory() as directory:
        settings = _settings(Path(directory))

        # The old master gate remains authoritative, and the defaults preserve
        # the historical behavior once it is enabled.
        assert Engine.remote_vault_operation_enabled(settings, "lookup") is False
        # Explicit Home search has always been a separate, user-triggered action.
        assert Engine.remote_vault_operation_enabled(settings, "search") is True
        settings.set("remote_vault", True, persist=False)
        assert Engine.remote_vault_operation_enabled(settings, "lookup") is True
        assert Engine.remote_vault_operation_enabled(settings, "store") is True
        assert Engine.remote_vault_operation_enabled(settings, "search") is True
        assert Engine.remote_vault_operation_enabled(settings, "manual_add") is True

        settings.set("remote_vault_auto_lookup", False, persist=False)
        settings.set("remote_vault_auto_store", False, persist=False)
        settings.set("remote_vault_home_search", False, persist=False)
        settings.set("remote_vault_manual_add", False, persist=False)

        assert Engine.remote_vault_operation_enabled(settings, "lookup") is False
        assert Engine.remote_vault_operation_enabled(settings, "store") is False
        assert Engine.remote_vault_operation_enabled(settings, "search") is False
        assert Engine.remote_vault_operation_enabled(settings, "manual_add") is False

        use_local, use_remote, _rl, _rr, _wl, write_remote = Engine.vault_targets(settings)
        assert use_local is True
        assert use_remote is False
        assert write_remote == ()


def test_remote_operation_switches_do_not_disable_local_lookup_or_write() -> None:
    with TemporaryDirectory() as directory:
        settings = _settings(Path(directory))
        settings.set("remote_vault", True, persist=False)
        settings.set("remote_vault_auto_lookup", False, persist=False)
        settings.set("remote_vault_auto_store", False, persist=False)

        use_local, use_remote, _rl, _rr, write_local, write_remote = Engine.vault_targets(settings)
        assert use_local is True
        assert use_remote is False
        assert write_local is None
        assert write_remote == ()
