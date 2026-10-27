"""Project pytest settings enforce the per-test timeout the Tickets Watcher requires."""

import pytest


def test_pytest_timeout_plugin_is_loaded(pytestconfig: pytest.Config) -> None:
    assert pytestconfig.pluginmanager.hasplugin("timeout")


def test_pytest_timeout_is_120_seconds(pytestconfig: pytest.Config) -> None:
    assert pytestconfig.getini("timeout") == "120"


@pytest.mark.timeout(300)
def test_a_marker_sets_a_per_test_exception(request: pytest.FixtureRequest) -> None:
    marker = request.node.get_closest_marker("timeout")
    assert marker is not None
    assert marker.args == (300,)
