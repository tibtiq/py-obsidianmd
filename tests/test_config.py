from __future__ import annotations

from pyomd.config.config import PATH_CONFIG_DEFAULT, Config


class TestConfig:
    class TestLoadConfig:
        def test_loads_default_config_when_path_is_none_and_not_in_cwd(
            self, tmp_path, monkeypatch
        ):
            monkeypatch.chdir(tmp_path)
            config = Config()

            assert config.path_cfg is None
            assert isinstance(config.cfg, dict)
            assert len(config.cfg) > 0

        def test_loads_user_config_when_path_exists(self, tmp_path):
            user_config_path = tmp_path / "custom_config.yaml"
            user_config_path.write_text("global:\n  default_meta: frontmatter\n")

            config = Config(user_config_path)

            assert config.path_cfg == user_config_path
            assert config.cfg["global"]["default_meta"] == "frontmatter"

        def test_loads_user_config_from_cwd_when_default_exists(
            self, tmp_path, monkeypatch
        ):
            monkeypatch.chdir(tmp_path)
            cwd_config_path = tmp_path / "pyomd-config.yaml"
            cwd_config_path.write_text("global:\n  default_meta: inline\n")

            config = Config()

            assert config.cfg["global"]["default_meta"] == "inline"

    class TestCreateConfigFile:
        def test_creates_config_file_at_custom_path(self, tmp_path):
            target_path = tmp_path / "new_config.yaml"
            Config.create_config_file(target_path)

            assert target_path.exists()
            assert target_path.read_text() == PATH_CONFIG_DEFAULT.read_text()

        def test_creates_config_file_at_cwd_by_default(self, tmp_path, monkeypatch):
            monkeypatch.chdir(tmp_path)
            Config.create_config_file(None)

            default_target = tmp_path / "pyomd-config.yaml"
            assert default_target.exists()
            assert default_target.read_text() == PATH_CONFIG_DEFAULT.read_text()
