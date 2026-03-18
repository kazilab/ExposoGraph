"""Tests for ExposoGraph.config."""

from ExposoGraph.config import AppMode, get_app_mode, normalize_app_mode, persistence_enabled


class TestNormalizeAppMode:
    def test_default_is_stateless(self):
        assert normalize_app_mode(None) == AppMode.STATELESS

    def test_public_aliases_map_to_stateless(self):
        for value in ["stateless", "public", "web", "unknown"]:
            assert normalize_app_mode(value) == AppMode.STATELESS

    def test_local_aliases_map_to_local(self):
        for value in ["local", "curation", "persistent"]:
            assert normalize_app_mode(value) == AppMode.LOCAL


class TestGetAppMode:
    def test_reads_from_environment_mapping(self):
        assert get_app_mode({"ExposoGraph_MODE": "local"}) == AppMode.LOCAL
        assert get_app_mode({"ExposoGraph_MODE": "public"}) == AppMode.STATELESS


class TestPersistenceEnabled:
    def test_enabled_only_for_local_mode(self):
        assert persistence_enabled(AppMode.LOCAL) is True
        assert persistence_enabled(AppMode.STATELESS) is False
