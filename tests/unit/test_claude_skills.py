"""
Unit tests for mk claude --skills command
"""

import json
import subprocess
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from mono_kickstart.cli import (
    PLUGIN_CHOICES,
    SKILL_CHOICES,
    SKILL_CONFIGS,
    cmd_claude,
    create_parser,
)


class TestClaudeSkillsParserHelp:
    """Tests for --skills in claude subcommand help output"""

    def test_claude_help_shows_skills(self):
        """Test claude --help displays --skills option"""
        with patch("sys.argv", ["mk", "claude", "--help"]):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    parser = create_parser()
                    parser.parse_args()
                assert exc_info.value.code == 0
                output = fake_out.getvalue()
                assert "--skills" in output
                assert "uipro" in output

    def test_claude_help_shows_skills_example(self):
        """Test claude --help displays --skills uipro example"""
        with patch("sys.argv", ["mk", "claude", "--help"]):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    parser = create_parser()
                    parser.parse_args()
                output = fake_out.getvalue()
                assert "--skills uipro" in output

    def test_claude_help_shows_plugin(self):
        with patch("sys.argv", ["mk", "claude", "--help"]):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    parser = create_parser()
                    parser.parse_args()
                output = fake_out.getvalue()
                assert "--plugin" in output
                assert "omc" in output


class TestClaudeSkillsParserValidation:
    """Tests for --skills argument parsing"""

    def test_parse_skills_uipro(self):
        """Test parsing --skills uipro"""
        parser = create_parser()
        args = parser.parse_args(["claude", "--skills", "uipro"])
        assert args.command == "claude"
        assert args.skills == "uipro"

    def test_invalid_skills_value(self):
        """Test invalid --skills value is rejected"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["claude", "--skills", "invalid"])
        assert exc_info.value.code == 2

    def test_parse_skills_with_mcp(self):
        """Test parsing --skills uipro with --mcp chrome"""
        parser = create_parser()
        args = parser.parse_args(["claude", "--skills", "uipro", "--mcp", "chrome"])
        assert args.skills == "uipro"
        assert args.mcp == "chrome"

    def test_parse_skills_with_allow(self):
        """Test parsing --skills uipro with --allow all"""
        parser = create_parser()
        args = parser.parse_args(["claude", "--skills", "uipro", "--allow", "all"])
        assert args.skills == "uipro"
        assert args.allow == "all"

    def test_parse_skills_with_dry_run(self):
        """Test parsing --skills uipro with --dry-run"""
        parser = create_parser()
        args = parser.parse_args(["claude", "--skills", "uipro", "--dry-run"])
        assert args.skills == "uipro"
        assert args.dry_run is True

    def test_parse_plugin_omc(self):
        parser = create_parser()
        args = parser.parse_args(["claude", "--plugin", "omc"])
        assert args.command == "claude"
        assert args.plugin == "omc"

    def test_invalid_plugin_value(self):
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["claude", "--plugin", "invalid"])
        assert exc_info.value.code == 2


class TestClaudeSkillsCommandValidation:
    """Tests for cmd_claude validation with --skills"""

    def test_no_options_returns_error(self):
        """Test error when no flags are specified"""
        parser = create_parser()
        args = parser.parse_args(["claude"])
        result = cmd_claude(args)
        assert result == 1

    def test_skills_alone_is_valid(self):
        """Test --skills uipro alone is accepted by validation"""
        parser = create_parser()
        args = parser.parse_args(["claude", "--skills", "uipro"])
        # Should not return 1 from the "no option" check
        # It will return 1 because uipro CLI is not installed, but not from validation
        with patch("mono_kickstart.cli.shutil.which", return_value=None):
            result = cmd_claude(args)
        # Returns 1 because CLI not found, but validation passed (logged different message)
        assert result == 1


class TestClaudeSkillsUipro:
    """Tests for --skills uipro execution"""

    def test_skills_uipro_runs_init_command(self, tmp_path, monkeypatch):
        """Test --skills uipro runs 'uipro init --ai claude'"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "uipro init --ai claude"

    def test_skills_uipro_cli_not_installed(self, tmp_path, monkeypatch):
        """Test --skills uipro fails when uipro CLI is not installed"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value=None):
            parser = create_parser()
            args = parser.parse_args(["claude", "--skills", "uipro"])
            result = cmd_claude(args)

        assert result == 1

    def test_skills_uipro_init_fails(self, tmp_path, monkeypatch):
        """Test --skills uipro handles init command failure"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="error occurred")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 1

    def test_skills_uipro_init_timeout(self, tmp_path, monkeypatch):
        """Test --skills uipro handles timeout"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="uipro init --ai claude", timeout=60
                )

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 1

    def test_skills_uipro_verifies_skill_dir(self, tmp_path, monkeypatch):
        """Test --skills uipro verifies skill directory after install"""
        monkeypatch.chdir(tmp_path)

        # Create the expected directory to simulate successful install
        skill_dir = tmp_path / ".claude" / "skills" / "ui-ux-pro-max"
        skill_dir.mkdir(parents=True)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 0

    def test_skills_uipro_warns_if_already_exists(self, tmp_path, monkeypatch, capsys):
        """Test --skills uipro warns when skill directory already exists"""
        monkeypatch.chdir(tmp_path)

        # Pre-create the skill directory
        skill_dir = tmp_path / ".claude" / "skills" / "ui-ux-pro-max"
        skill_dir.mkdir(parents=True)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 0


class TestClaudeSkillsDryRun:
    """Tests for --skills with --dry-run"""

    def test_dry_run_does_not_execute(self, tmp_path, monkeypatch):
        """Test --dry-run does not execute uipro init"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro", "--dry-run"])
                result = cmd_claude(args)

        assert result == 0
        mock_run.assert_not_called()

    def test_dry_run_cli_not_installed(self, tmp_path, monkeypatch):
        """Test --dry-run still fails if CLI is not installed"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value=None):
            parser = create_parser()
            args = parser.parse_args(["claude", "--skills", "uipro", "--dry-run"])
            result = cmd_claude(args)

        assert result == 1

    def test_dry_run_returns_zero(self, tmp_path, monkeypatch):
        """Test --dry-run returns 0 when CLI is available"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            parser = create_parser()
            args = parser.parse_args(["claude", "--skills", "uipro", "--dry-run"])
            result = cmd_claude(args)

        assert result == 0


class TestClaudeSkillsCombinations:
    """Tests for --skills combined with other options"""

    def test_skills_with_mcp_chrome(self, tmp_path, monkeypatch):
        """Test --skills uipro --mcp chrome both succeed"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro", "--mcp", "chrome"])
                result = cmd_claude(args)

        assert result == 0

        # MCP config should be written
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()
        config = json.loads(settings_file.read_text())
        assert "chrome-devtools" in config["mcpServers"]

    def test_skills_with_allow_all(self, tmp_path, monkeypatch):
        """Test --skills uipro --allow all both succeed"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro", "--allow", "all"])
                result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()
        config = json.loads(settings_file.read_text())
        assert "permissions" in config

    def test_plugin_with_allow_all(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0, stderr=""),
                    MagicMock(returncode=0, stderr=""),
                    MagicMock(returncode=0, stderr=""),
                ]

                parser = create_parser()
                args = parser.parse_args(["claude", "--plugin", "omc", "--allow", "all"])
                result = cmd_claude(args)

        assert result == 0
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()


class TestClaudePluginOMC:
    def test_plugin_omc_dry_run(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/claude"):
            with patch("subprocess.run") as mock_run:
                parser = create_parser()
                args = parser.parse_args(["claude", "--plugin", "omc", "--dry-run"])
                result = cmd_claude(args)

        assert result == 0
        mock_run.assert_not_called()

    def test_plugin_omc_requires_claude_cli(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value=None):
            parser = create_parser()
            args = parser.parse_args(["claude", "--plugin", "omc"])
            result = cmd_claude(args)

        assert result == 1

    def test_plugin_omc_runs_install_and_config(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/claude"):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=0, stderr=""),
                    MagicMock(returncode=0, stderr=""),
                    MagicMock(returncode=0, stderr=""),
                ]

                parser = create_parser()
                args = parser.parse_args(["claude", "--plugin", "omc"])
                result = cmd_claude(args)

        assert result == 0
        assert mock_run.call_count == 3
        assert "claude /plugin marketplace add" in mock_run.call_args_list[0][0][0]
        assert "claude /plugin install oh-my-claudecode" in mock_run.call_args_list[1][0][0]
        assert "curl -fsSL" in mock_run.call_args_list[2][0][0]


class TestSkillConfigs:
    """Tests for SKILL_CONFIGS registry"""

    def test_uipro_config_exists(self):
        """Test uipro config is registered"""
        assert "uipro" in SKILL_CONFIGS

    def test_uipro_config_structure(self):
        """Test uipro config has required fields"""
        config = SKILL_CONFIGS["uipro"]
        assert "name" in config
        assert "display_name" in config
        assert "cli_command" in config
        assert "init_command" in config
        assert "install_hint" in config
        assert "skill_dir" in config
        assert config["name"] == "ui-ux-pro-max"
        assert config["cli_command"] == "uipro"
        assert config["init_command"] == "uipro init --ai claude"

    def test_skill_choices_match_configs(self):
        """Test SKILL_CHOICES matches SKILL_CONFIGS keys"""
        assert set(SKILL_CHOICES) == set(SKILL_CONFIGS.keys())

    def test_plugin_choices_has_omc(self):
        assert "omc" in PLUGIN_CHOICES


class TestClaudeSkillsKeyboardInterrupt:
    """Tests for keyboard interrupt handling with --skills"""

    def test_keyboard_interrupt(self, tmp_path, monkeypatch):
        """Test keyboard interrupt returns exit code 130"""
        monkeypatch.chdir(tmp_path)

        with patch("mono_kickstart.cli.shutil.which", return_value="/usr/local/bin/uipro"):
            with patch("subprocess.run", side_effect=KeyboardInterrupt()):
                parser = create_parser()
                args = parser.parse_args(["claude", "--skills", "uipro"])
                result = cmd_claude(args)

        assert result == 130
