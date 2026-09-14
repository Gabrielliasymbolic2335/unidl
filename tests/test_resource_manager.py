from __future__ import annotations

from tempfile import TemporaryDirectory

from unidl.core.config import Config
from unidl.tui.app import UnidlApp
from unidl.tui.resource_manager import ResourceManagerScreen, VaultPolicyScreen


def test_vault_policy_close_mark_persists_remote_gate() -> None:
    """Closing Vault policy with the top-right mark must apply its edits."""

    async def exercise() -> None:
        with TemporaryDirectory() as directory:
            app = UnidlApp(Config({"paths": {"home": directory}}))
            async with app.run_test(size=(120, 42)) as pilot:
                await pilot.pause()
                app.push_screen(VaultPolicyScreen(app.globals))
                await pilot.pause()
                policy = app.screen
                remote = policy.query_one("#resource-policy-remote")
                assert remote.value is False
                remote.value = True

                await pilot.click("#resource-policy-close")
                await pilot.pause()
                assert app.screen is not policy
                assert app.globals.get("remote_vault") is True

                app.push_screen(VaultPolicyScreen(app.globals))
                await pilot.pause()
                assert app.screen.query_one("#resource-policy-remote").value is True
            app.vaults.close()

    import asyncio

    asyncio.run(exercise())


def test_vault_policy_persists_each_remote_operation_switch() -> None:
    async def exercise() -> None:
        with TemporaryDirectory() as directory:
            app = UnidlApp(Config({"paths": {"home": directory}}))
            async with app.run_test(size=(120, 42)) as pilot:
                await pilot.pause()
                app.push_screen(VaultPolicyScreen(app.globals))
                await pilot.pause()
                policy = app.screen
                ids = (
                    "#resource-policy-home-search",
                    "#resource-policy-manual-add",
                    "#resource-policy-auto-store",
                    "#resource-policy-auto-lookup",
                )
                for selector in ids:
                    checkbox = policy.query_one(selector)
                    assert checkbox.value is True
                    checkbox.value = False
                await pilot.click("#resource-policy-apply")
                await pilot.pause()

                assert all(app.globals.get(key) is False for key in (
                    "remote_vault_home_search",
                    "remote_vault_manual_add",
                    "remote_vault_auto_store",
                    "remote_vault_auto_lookup",
                ))
            app.vaults.close()

    import asyncio

    asyncio.run(exercise())


def test_vault_policy_controls_are_visible_and_selectable() -> None:
    """Policy containers must leave a content row for every control.

    A full border on a two-row Textual container consumes both rows.  Keep
    this as a layout regression test so a theme change cannot silently bring
    back an empty-looking policy panel.
    """

    async def exercise() -> None:
        with TemporaryDirectory() as directory:
            app = UnidlApp(Config({"paths": {"home": directory}}))
            async with app.run_test(size=(120, 42)) as pilot:
                await pilot.pause()
                app.push_screen(VaultPolicyScreen(app.globals))
                await pilot.pause()
                policy = app.screen
                operation_ids = (
                    "#resource-policy-home-search",
                    "#resource-policy-manual-add",
                    "#resource-policy-auto-store",
                    "#resource-policy-auto-lookup",
                )
                for selector in operation_ids:
                    control = policy.query_one(selector)
                    assert control.region.height > 0
                    assert control.content_region.height > 0
                for selector in (
                    "#resource-policy-read",
                    "#resource-policy-write",
                    "#resource-policy-search",
                    "#resource-policy-read-button",
                    "#resource-policy-write-button",
                    "#resource-policy-search-button",
                ):
                    control = policy.query_one(selector)
                    assert control.region.height > 0
                    assert control.content_region.height > 0
            app.vaults.close()

    import asyncio

    asyncio.run(exercise())


def test_clicking_remote_vault_selects_it_without_toggling_enabled_state() -> None:
    async def exercise() -> None:
        with TemporaryDirectory() as directory:
            config = Config(
                {
                    "paths": {"home": directory},
                    "key_vaults": [
                        {"type": "sqlite", "name": "local"},
                        {
                            "type": "HTTP",
                            "name": "remote",
                            "host": "https://vault.example.test",
                            "password": "secret",
                        },
                    ],
                }
            )
            app = UnidlApp(config)
            async with app.run_test(size=(120, 42)) as pilot:
                await pilot.pause()
                app.push_screen(ResourceManagerScreen())
                await pilot.pause()
                await pilot.click("#resource-tab-vault")
                await pilot.pause()
                screen = app.screen
                index = next(
                    index
                    for index, row in enumerate(screen._rows)
                    if row is not None and row.kind == "vault-remote"
                )
                # Click the actual remote row.  A click must only select it so
                # the Edit button can be used without changing its state.
                await pilot.click("#resource-list", offset=(5, index))
                await pilot.pause()
                assert screen._selected().name == "remote"
                assert config.vault_specs()[1].get("enabled", True) is True
            app.vaults.close()

    import asyncio

    asyncio.run(exercise())
