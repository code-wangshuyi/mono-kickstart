"""
Unit tests for mk claude show command
"""

import json
import os
from io import StringIO
from unittest.mock import patch, MagicMock, mock_open

import pytest

from mono_kickstart.cli import create_parser, cmd_claude_show, cmd_claude


class TestClaudeShowParserHelp:
    """Tests for claude show subcommand parser and help output"""

    def test_claude_show_help(self):
        """Test claude show --help displays correct information"""
        with patch("sys.argv", ["mk", "claude", "show", "--help"]):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    parser = create_parser()
                    parser.parse_args()
                assert exc_info.value.code == 0
                output = fake_out.getvalue()
                assert "展示当前项目的 Claude Code 配置信息" in output
                assert "show" in output

    def test_claude_show_in_claude_help(self):
        """Test show appears in mk claude --help output"""
        with patch("sys.argv", ["mk", "claude", "--help"]):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    parser = create_parser()
                    parser.parse_args()
                output = fake_out.getvalue()
                assert "show" in output


class TestClaudeShowParserValidation:
    """Tests for claude show argument parsing"""

    def test_parse_claude_show(self):
        """Test parsing mk claude show"""
        parser = create_parser()
        args = parser.parse_args(["claude", "show"])
        assert args.command == "claude"
        assert args.claude_action == "show"


class TestClaudeShowFunctionality:
    """Tests for claude show command functionality"""

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_all_found(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show when all configs exist and Claude is installed"""
        # Mock Claude Code installed
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.2.3"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        # Mock all files exist
        mock_exists.return_value = True
        mock_getsize.return_value = 1234

        # Mock file contents
        settings_content = {"permissions": {"allow": ["Bash(*)"]}}
        mcp_content = {"mcpServers": {"chrome-devtools": {"command": "npx"}}}

        def mock_open_side_effect(path, *args, **kwargs):
            if "settings.json" in path:
                return mock_open(read_data=json.dumps(settings_content))()
            elif "mcp.json" in path:
                return mock_open(read_data=json.dumps(mcp_content))()
            return mock_open(read_data="{}")()

        # Create parser before patching open
        parser = create_parser()
        args = parser.parse_args(["claude", "show"])

        # Patch open only during cmd_claude_show execution
        with patch("builtins.open", side_effect=mock_open_side_effect):
            result = cmd_claude_show(args)

        assert result == 0
        # Verify logger was called with expected messages
        logger_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Claude Code 已安装" in str(call) for call in logger_calls)
        assert any("1.2.3" in str(call) for call in logger_calls)

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    def test_claude_show_nothing_found(self, mock_exists, MockDetector, mock_logger):
        """Test show when no configs exist and Claude not installed"""
        # Mock Claude Code not installed
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = False
        mock_detector.detect_claude_code.return_value = mock_status

        # Mock no files exist
        mock_exists.return_value = False

        parser = create_parser()
        args = parser.parse_args(["claude", "show"])
        result = cmd_claude_show(args)

        assert result == 0
        # Verify logger was called with "not found" messages
        logger_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("未安装" in str(call) for call in logger_calls)
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("未找到" in str(call) for call in info_calls)

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_partial_configs(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show when some files exist, some don't"""
        # Mock Claude Code installed
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.0.0"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        # Only some files exist
        def exists_side_effect(path):
            return path in ["CLAUDE.md", ".claude/settings.json"]

        mock_exists.side_effect = exists_side_effect
        mock_getsize.return_value = 500

        # Mock file contents
        with patch(
            "builtins.open", mock_open(read_data='{"permissions": {"allow": []}}')
        ):
            parser = create_parser()
            args = parser.parse_args(["claude", "show"])
            result = cmd_claude_show(args)

        assert result == 0

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    def test_claude_show_invalid_json(self, mock_exists, MockDetector, mock_logger):
        """Test show handles invalid JSON gracefully"""
        # Mock Claude Code installed
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.0.0"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        # Settings file exists
        mock_exists.side_effect = (
            lambda p: p == ".claude/settings.json" or p == ".mcp.json"
        )

        # Mock invalid JSON
        with patch("builtins.open", mock_open(read_data="not valid json{{{")):
            parser = create_parser()
            args = parser.parse_args(["claude", "show"])
            result = cmd_claude_show(args)

        assert result == 0
        # Verify logger was called with warning about invalid JSON
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("无法读取文件内容" in str(call) for call in warning_calls)

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    def test_claude_show_returns_zero(self, mock_exists, MockDetector, mock_logger):
        """Test show always returns 0 (success)"""
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = False
        mock_detector.detect_claude_code.return_value = mock_status

        mock_exists.return_value = False

        parser = create_parser()
        args = parser.parse_args(["claude", "show"])
        result = cmd_claude_show(args)

        assert result == 0

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_displays_settings_content(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show displays settings.json content"""
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.0.0"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        mock_exists.side_effect = lambda p: p == ".claude/settings.json"
        mock_getsize.return_value = 100

        settings_content = {
            "permissions": {"allow": ["Bash(*)"]},
            "permissionMode": "plan",
        }

        with patch(
            "builtins.open", mock_open(read_data=json.dumps(settings_content))
        ):
            parser = create_parser()
            args = parser.parse_args(["claude", "show"])
            result = cmd_claude_show(args)

        assert result == 0
        # Verify JSON content was logged
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("permissions" in str(call) for call in info_calls)

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_displays_mcp_content(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show displays mcp.json content"""
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.0.0"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        mock_exists.side_effect = lambda p: p == ".mcp.json"
        mock_getsize.return_value = 100

        mcp_content = {
            "mcpServers": {
                "chrome-devtools": {"command": "npx", "args": ["chrome-devtools-mcp"]}
            }
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mcp_content))):
            parser = create_parser()
            args = parser.parse_args(["claude", "show"])
            result = cmd_claude_show(args)

        assert result == 0
        # Verify MCP content was logged
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("mcpServers" in str(call) for call in info_calls)

    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_checks_claude_md(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show checks CLAUDE.md in both root and .claude/"""
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = False
        mock_detector.detect_claude_code.return_value = mock_status

        # Only root CLAUDE.md exists
        mock_exists.side_effect = lambda p: p == "CLAUDE.md"
        mock_getsize.return_value = 2048

        parser = create_parser()
        args = parser.parse_args(["claude", "show"])
        result = cmd_claude_show(args)

        assert result == 0
        # Verify both paths were checked
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("项目根目录" in str(call) for call in info_calls)
        assert any("项目 .claude 目录" in str(call) for call in info_calls)


    @patch("mono_kickstart.cli.logger")
    @patch("mono_kickstart.tool_detector.ToolDetector")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_claude_show_displays_settings_local(
        self, mock_getsize, mock_exists, MockDetector, mock_logger
    ):
        """Test show displays .claude/settings.local.json"""
        mock_detector = MagicMock()
        MockDetector.return_value = mock_detector
        mock_status = MagicMock()
        mock_status.installed = True
        mock_status.version = "1.0.0"
        mock_status.path = "/usr/local/bin/claude"
        mock_detector.detect_claude_code.return_value = mock_status

        mock_exists.side_effect = lambda p: p == ".claude/settings.local.json"
        mock_getsize.return_value = 200

        settings_local_content = {
            "permissions": {"allow": ["Read", "Write"]},
            "mcpServers": {"context7": {"command": "npx"}},
        }

        with patch(
            "builtins.open", mock_open(read_data=json.dumps(settings_local_content))
        ):
            parser = create_parser()
            args = parser.parse_args(["claude", "show"])
            result = cmd_claude_show(args)

        assert result == 0
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("项目级本地设置" in str(call) for call in info_calls)
        assert any("settings.local.json" in str(call) for call in info_calls)
        assert any("permissions" in str(call) for call in info_calls)


class TestClaudeShowRouting:
    """Tests for routing from cmd_claude to cmd_claude_show"""

    @patch("mono_kickstart.cli.cmd_claude_show")
    def test_cmd_claude_routes_to_show(self, mock_show):
        """Test cmd_claude routes to cmd_claude_show when action is show"""
        mock_show.return_value = 0

        parser = create_parser()
        args = parser.parse_args(["claude", "show"])
        result = cmd_claude(args)

        assert result == 0
        mock_show.assert_called_once_with(args)


class TestClaudeBackwardCompatibility:
    """Tests that existing claude functionality still works"""

    def test_claude_existing_flags_still_work(self, tmp_path, monkeypatch):
        """Test mk claude --mcp chrome still works after adding show"""
        monkeypatch.chdir(tmp_path)

        parser = create_parser()
        args = parser.parse_args(["claude", "--mcp", "chrome", "--dry-run"])
        result = cmd_claude(args)

        assert result == 0

    def test_claude_no_args_shows_error(self):
        """Test mk claude with no args still shows error"""
        parser = create_parser()
        args = parser.parse_args(["claude"])
        result = cmd_claude(args)
        assert result == 1
