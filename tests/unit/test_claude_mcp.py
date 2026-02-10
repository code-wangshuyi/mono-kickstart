"""
Unit tests for mk claude --mcp command
"""

import json
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from mono_kickstart.cli import create_parser, cmd_claude, MCP_SERVER_CONFIGS, ALLOW_ALL_PERMISSIONS


class TestClaudeParserHelp:
    """Tests for claude subcommand parser and help output"""

    def test_claude_help(self):
        """Test claude --help displays correct information"""
        with patch('sys.argv', ['mk', 'claude', '--help']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    parser = create_parser()
                    parser.parse_args()
                assert exc_info.value.code == 0
                output = fake_out.getvalue()
                assert "Claude Code" in output
                assert "--mcp" in output
                assert "--allow" in output
                assert "--mode" in output
                assert "--dry-run" in output
                assert "chrome" in output
                assert "context7" in output

    def test_claude_in_main_help(self):
        """Test claude appears in main help output"""
        with patch('sys.argv', ['mk', '--help']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    parser = create_parser()
                    parser.parse_args()
                output = fake_out.getvalue()
                assert "claude" in output


class TestClaudeParserValidation:
    """Tests for claude argument parsing"""

    def test_parse_mcp_chrome(self):
        """Test parsing --mcp chrome"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--mcp', 'chrome'])
        assert args.command == 'claude'
        assert args.mcp == 'chrome'

    def test_parse_mcp_context7(self):
        """Test parsing --mcp context7"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--mcp', 'context7'])
        assert args.command == 'claude'
        assert args.mcp == 'context7'

    def test_parse_allow_all(self):
        """Test parsing --allow all"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all'])
        assert args.command == 'claude'
        assert args.allow == 'all'

    def test_parse_mode_plan(self):
        """Test parsing --mode plan"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan'])
        assert args.command == 'claude'
        assert args.mode == 'plan'

    def test_parse_allow_with_mcp(self):
        """Test parsing --allow all with --mcp"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all', '--mcp', 'chrome'])
        assert args.allow == 'all'
        assert args.mcp == 'chrome'

    def test_parse_allow_with_mode(self):
        """Test parsing --allow all with --mode plan"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all', '--mode', 'plan'])
        assert args.allow == 'all'
        assert args.mode == 'plan'

    def test_invalid_allow_mode(self):
        """Test invalid --allow value is rejected"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['claude', '--allow', 'invalid'])
        assert exc_info.value.code == 2

    def test_invalid_mode(self):
        """Test invalid --mode value is rejected"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['claude', '--mode', 'invalid'])
        assert exc_info.value.code == 2

    def test_parse_dry_run(self):
        """Test parsing --dry-run"""
        parser = create_parser()
        args = parser.parse_args(['claude', '--mcp', 'chrome', '--dry-run'])
        assert args.dry_run is True

    def test_invalid_mcp_server(self):
        """Test invalid MCP server name is rejected"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['claude', '--mcp', 'invalid-server'])
        assert exc_info.value.code == 2


class TestClaudeCommandValidation:
    """Tests for cmd_claude validation logic"""

    def test_no_mcp_flag_returns_error(self):
        """Test error when no --mcp flag is specified"""
        parser = create_parser()
        args = parser.parse_args(['claude'])
        result = cmd_claude(args)
        assert result == 1


class TestClaudeMcpChrome:
    """Tests for MCP chrome-devtools configuration"""

    def test_mcp_chrome_creates_config(self, tmp_path, monkeypatch):
        """Test --mcp chrome creates .claude/settings.local.json"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()

        config = json.loads(settings_file.read_text())
        assert "mcpServers" in config
        assert "chrome-devtools" in config["mcpServers"]
        assert config["mcpServers"]["chrome-devtools"]["command"] == "npx"
        assert config["mcpServers"]["chrome-devtools"]["args"] == ["chrome-devtools-mcp@latest"]

    def test_mcp_chrome_merges_with_existing_config(self, tmp_path, monkeypatch):
        """Test --mcp chrome merges with existing settings.local.json"""
        monkeypatch.chdir(tmp_path)

        # Create existing config
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "permissions": {
                "allow": ["Bash(python -m pytest:*)"]
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        # Existing config preserved
        assert "permissions" in config
        assert "allow" in config["permissions"]
        # MCP config added
        assert "mcpServers" in config
        assert "chrome-devtools" in config["mcpServers"]

    def test_mcp_chrome_merges_with_existing_mcp(self, tmp_path, monkeypatch):
        """Test --mcp chrome merges with existing mcpServers"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "mcpServers": {
                "other-server": {
                    "command": "node",
                    "args": ["other-mcp"]
                }
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert "other-server" in config["mcpServers"]
        assert "chrome-devtools" in config["mcpServers"]

    def test_mcp_chrome_overwrites_existing(self, tmp_path, monkeypatch):
        """Test --mcp chrome overwrites existing chrome-devtools config"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "mcpServers": {
                "chrome-devtools": {
                    "command": "node",
                    "args": ["old-version"]
                }
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        # Config should be overwritten with latest
        assert config["mcpServers"]["chrome-devtools"]["command"] == "npx"
        assert config["mcpServers"]["chrome-devtools"]["args"] == ["chrome-devtools-mcp@latest"]

    def test_mcp_chrome_handles_corrupt_json(self, tmp_path, monkeypatch):
        """Test --mcp chrome handles corrupt settings.local.json"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.local.json").write_text("not valid json{{{")

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        # Should create fresh config
        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert "mcpServers" in config
        assert "chrome-devtools" in config["mcpServers"]


class TestClaudeMcpDryRun:
    """Tests for dry run mode"""

    def test_dry_run_does_not_write_file(self, tmp_path, monkeypatch):
        """Test --dry-run does not create config file"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--mcp', 'chrome', '--dry-run'])
        result = cmd_claude(args)

        assert result == 0
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert not settings_file.exists()


class TestClaudeMcpWithClaude:
    """Tests for claude CLI integration"""

    def test_runs_claude_mcp_add_when_available(self, tmp_path, monkeypatch):
        """Test runs claude mcp add when claude CLI is available"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.shutil.which', return_value="/usr/local/bin/claude"):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                parser = create_parser()
                args = parser.parse_args(['claude', '--mcp', 'chrome'])
                result = cmd_claude(args)

        assert result == 0

        # Verify claude mcp add was called
        calls = [str(c) for c in mock_run.call_args_list]
        assert any("claude mcp add" in c for c in calls)

    def test_succeeds_even_if_claude_mcp_add_fails(self, tmp_path, monkeypatch):
        """Test succeeds even if claude mcp add command fails"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.shutil.which', return_value="/usr/local/bin/claude"):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=1)

                parser = create_parser()
                args = parser.parse_args(['claude', '--mcp', 'chrome'])
                result = cmd_claude(args)

        # Should still succeed (config file was written)
        assert result == 0
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()


class TestClaudeMcpKeyboardInterrupt:
    """Tests for keyboard interrupt handling"""

    def test_keyboard_interrupt(self, tmp_path, monkeypatch):
        """Test keyboard interrupt returns exit code 130"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.Path.mkdir', side_effect=KeyboardInterrupt()):
            with patch('mono_kickstart.cli.shutil.which', return_value=None):
                parser = create_parser()
                args = parser.parse_args(['claude', '--mcp', 'chrome'])
                result = cmd_claude(args)

        assert result == 130


class TestMcpServerConfigs:
    """Tests for MCP server configuration registry"""

    def test_chrome_config_exists(self):
        """Test chrome config is registered"""
        assert "chrome" in MCP_SERVER_CONFIGS

    def test_chrome_config_structure(self):
        """Test chrome config has required fields"""
        config = MCP_SERVER_CONFIGS["chrome"]
        assert "name" in config
        assert "display_name" in config
        assert "config" in config
        assert "claude_mcp_add_cmd" in config
        assert config["name"] == "chrome-devtools"
        assert "command" in config["config"]
        assert "args" in config["config"]

    def test_context7_config_exists(self):
        """Test context7 config is registered"""
        assert "context7" in MCP_SERVER_CONFIGS

    def test_context7_config_structure(self):
        """Test context7 config has required fields"""
        config = MCP_SERVER_CONFIGS["context7"]
        assert "name" in config
        assert "display_name" in config
        assert "config" in config
        assert "claude_mcp_add_cmd" in config
        assert config["name"] == "context7"
        assert config["config"]["command"] == "npx"
        assert config["config"]["args"] == ["-y", "@upstash/context7-mcp@latest"]


class TestClaudeMcpContext7:
    """Tests for MCP context7 configuration"""

    def test_mcp_context7_creates_config(self, tmp_path, monkeypatch):
        """Test --mcp context7 creates .claude/settings.local.json"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--mcp', 'context7'])
            result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()

        config = json.loads(settings_file.read_text())
        assert "mcpServers" in config
        assert "context7" in config["mcpServers"]
        assert config["mcpServers"]["context7"]["command"] == "npx"
        assert config["mcpServers"]["context7"]["args"] == ["-y", "@upstash/context7-mcp@latest"]


class TestClaudeAllowAll:
    """Tests for --allow all permission configuration"""

    def test_allow_all_creates_config(self, tmp_path, monkeypatch):
        """Test --allow all creates .claude/settings.local.json with all permissions"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all'])
        result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()

        config = json.loads(settings_file.read_text())
        assert "permissions" in config
        assert "allow" in config["permissions"]
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS

    def test_allow_all_merges_with_existing_mcp(self, tmp_path, monkeypatch):
        """Test --allow all preserves existing mcpServers"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "mcpServers": {
                "chrome-devtools": {
                    "command": "npx",
                    "args": ["chrome-devtools-mcp@latest"]
                }
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all'])
        result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert "mcpServers" in config
        assert "chrome-devtools" in config["mcpServers"]
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS

    def test_allow_all_overwrites_existing_permissions(self, tmp_path, monkeypatch):
        """Test --allow all overwrites existing permissions.allow"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "permissions": {
                "allow": [
                    "Bash(python -m pytest:*)",
                    "Bash(pip install:*)"
                ]
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all'])
        result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS

    def test_allow_all_dry_run(self, tmp_path, monkeypatch):
        """Test --allow all --dry-run does not write file"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all', '--dry-run'])
        result = cmd_claude(args)

        assert result == 0
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert not settings_file.exists()

    def test_allow_all_with_mcp(self, tmp_path, monkeypatch):
        """Test --allow all --mcp chrome configures both"""
        monkeypatch.chdir(tmp_path)

        with patch('mono_kickstart.cli.shutil.which', return_value=None):
            parser = create_parser()
            args = parser.parse_args(['claude', '--allow', 'all', '--mcp', 'chrome'])
            result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        config = json.loads(settings_file.read_text())
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS
        assert "chrome-devtools" in config["mcpServers"]

    def test_allow_all_handles_corrupt_json(self, tmp_path, monkeypatch):
        """Test --allow all handles corrupt settings.local.json"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.local.json").write_text("not valid json{{{")

        parser = create_parser()
        args = parser.parse_args(['claude', '--allow', 'all'])
        result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS


class TestClaudeMode:
    """Tests for --mode plan permission configuration"""

    def test_mode_plan_creates_config(self, tmp_path, monkeypatch):
        """Test --mode plan creates .claude/settings.local.json with permissionMode"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan'])
        result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert settings_file.exists()

        config = json.loads(settings_file.read_text())
        assert config["permissionMode"] == "plan"

    def test_mode_plan_merges_with_existing(self, tmp_path, monkeypatch):
        """Test --mode plan preserves existing config"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {
            "mcpServers": {
                "chrome-devtools": {
                    "command": "npx",
                    "args": ["chrome-devtools-mcp@latest"]
                }
            },
            "permissions": {
                "allow": ["Bash(*)"]
            }
        }
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan'])
        result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert "mcpServers" in config
        assert "chrome-devtools" in config["mcpServers"]
        assert config["permissions"]["allow"] == ["Bash(*)"]
        assert config["permissionMode"] == "plan"

    def test_mode_plan_dry_run(self, tmp_path, monkeypatch):
        """Test --mode plan --dry-run does not write file"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan', '--dry-run'])
        result = cmd_claude(args)

        assert result == 0
        settings_file = tmp_path / ".claude" / "settings.local.json"
        assert not settings_file.exists()

    def test_mode_plan_overwrites_existing_mode(self, tmp_path, monkeypatch):
        """Test --mode plan overwrites existing permissionMode"""
        monkeypatch.chdir(tmp_path)

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        existing = {"permissionMode": "default"}
        (claude_dir / "settings.local.json").write_text(json.dumps(existing))

        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan'])
        result = cmd_claude(args)

        assert result == 0

        config = json.loads((claude_dir / "settings.local.json").read_text())
        assert config["permissionMode"] == "plan"

    def test_mode_plan_with_allow_all(self, tmp_path, monkeypatch):
        """Test --mode plan --allow all configures both"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(['claude', '--mode', 'plan', '--allow', 'all'])
        result = cmd_claude(args)

        assert result == 0

        settings_file = tmp_path / ".claude" / "settings.local.json"
        config = json.loads(settings_file.read_text())
        assert config["permissions"]["allow"] == ALLOW_ALL_PERMISSIONS
        assert config["permissionMode"] == "plan"
