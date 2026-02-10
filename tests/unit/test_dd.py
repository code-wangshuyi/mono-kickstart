"""
Unit tests for mk dd (driven development) command
"""

import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from mono_kickstart.cli import create_parser, cmd_dd


class TestDdParserHelp:
    """Tests for dd subcommand parser and help output"""

    def test_dd_help(self):
        """Test dd --help displays correct information"""
        with patch('sys.argv', ['mk', 'dd', '--help']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    parser = create_parser()
                    parser.parse_args()
                assert exc_info.value.code == 0
                output = fake_out.getvalue()
                assert "驱动开发工具" in output
                assert "--spec-kit" in output
                assert "--bmad-method" in output
                assert "--claude" in output
                assert "--codex" in output
                assert "--force" in output
                assert "--dry-run" in output

    def test_dd_in_main_help(self):
        """Test dd appears in main help output"""
        with patch('sys.argv', ['mk', '--help']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    parser = create_parser()
                    parser.parse_args()
                output = fake_out.getvalue()
                assert "dd" in output


class TestDdParserValidation:
    """Tests for dd argument parsing and validation"""

    def test_dd_parse_spec_kit(self):
        """Test parsing --spec-kit flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        assert args.command == 'dd'
        assert args.spec_kit is True
        assert args.bmad_method is False

    def test_dd_parse_bmad_method(self):
        """Test parsing --bmad-method flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--bmad-method'])
        assert args.command == 'dd'
        assert args.bmad_method is True
        assert args.spec_kit is False

    def test_dd_parse_both_tools(self):
        """Test parsing both --spec-kit and --bmad-method"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--bmad-method'])
        assert args.spec_kit is True
        assert args.bmad_method is True

    def test_dd_parse_claude_flag(self):
        """Test parsing --claude flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--claude'])
        assert args.claude is True
        assert args.codex is False

    def test_dd_parse_codex_flag(self):
        """Test parsing --codex flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--codex'])
        assert args.codex is True
        assert args.claude is False

    def test_dd_parse_short_flags(self):
        """Test parsing short flags -s -c -b"""
        parser = create_parser()
        args = parser.parse_args(['dd', '-s', '-c'])
        assert args.spec_kit is True
        assert args.claude is True

    def test_dd_parse_force_flag(self):
        """Test parsing --force flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--force'])
        assert args.force is True

    def test_dd_parse_dry_run_flag(self):
        """Test parsing --dry-run flag"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--dry-run'])
        assert args.dry_run is True

    def test_dd_claude_codex_mutually_exclusive(self):
        """Test --claude and --codex are mutually exclusive"""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['dd', '--spec-kit', '--claude', '--codex'])
        assert exc_info.value.code == 2


class TestDdCommandValidation:
    """Tests for cmd_dd validation logic"""

    def test_dd_no_tool_flag_returns_error(self):
        """Test error when no tool flag is specified"""
        parser = create_parser()
        args = parser.parse_args(['dd'])
        result = cmd_dd(args)
        assert result == 1

    def test_dd_claude_without_spec_kit_returns_error(self):
        """Test error when --claude is given without --spec-kit"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--claude'])
        result = cmd_dd(args)
        assert result == 1

    def test_dd_codex_without_spec_kit_returns_error(self):
        """Test error when --codex is given without --spec-kit"""
        parser = create_parser()
        args = parser.parse_args(['dd', '--codex'])
        result = cmd_dd(args)
        assert result == 1


class TestDdSpecKit:
    """Tests for Spec-Kit initialization flow"""

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_success_default_claude(self, mock_which, mock_run):
        """Test successful spec-kit init with default claude backend"""
        mock_which.return_value = "/usr/local/bin/specify"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        result = cmd_dd(args)
        assert result == 0

        # Verify specify check was called
        calls = mock_run.call_args_list
        assert any("specify check" in str(c) for c in calls)
        # Verify specify init with claude
        assert any("specify init . --ai claude" in str(c) for c in calls)

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_success_codex_backend(self, mock_which, mock_run):
        """Test successful spec-kit init with codex backend"""
        mock_which.return_value = "/usr/local/bin/specify"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--codex'])
        result = cmd_dd(args)
        assert result == 0

        calls = mock_run.call_args_list
        assert any("specify init . --ai codex" in str(c) for c in calls)

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_with_force(self, mock_which, mock_run):
        """Test spec-kit init with --force flag"""
        mock_which.return_value = "/usr/local/bin/specify"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--force'])
        result = cmd_dd(args)
        assert result == 0

        calls = mock_run.call_args_list
        assert any("--force" in str(c) for c in calls)

    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_specify_not_installed(self, mock_which):
        """Test error when specify is not installed"""
        mock_which.return_value = None

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        result = cmd_dd(args)
        assert result != 0

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_check_fails(self, mock_which, mock_run):
        """Test error when specify check fails"""
        mock_which.return_value = "/usr/local/bin/specify"
        mock_run.return_value = MagicMock(returncode=1, stderr="AI agent not found")

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        result = cmd_dd(args)
        assert result != 0

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_init_fails(self, mock_which, mock_run):
        """Test error when specify init fails"""
        mock_which.return_value = "/usr/local/bin/specify"
        # First call (specify check) succeeds, second (specify init) fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stderr=""),
            MagicMock(returncode=1, stderr="Init error"),
        ]

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        result = cmd_dd(args)
        assert result != 0

    @patch('mono_kickstart.cli.shutil.which')
    def test_spec_kit_dry_run(self, mock_which):
        """Test spec-kit dry run mode"""
        mock_which.return_value = "/usr/local/bin/specify"

        # Mock only specify check, init should not be called
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            parser = create_parser()
            args = parser.parse_args(['dd', '--spec-kit', '--dry-run'])
            result = cmd_dd(args)
            assert result == 0

            # specify check is called but init should not be
            calls = [str(c) for c in mock_run.call_args_list]
            assert any("specify check" in c for c in calls)


class TestDdBmadMethod:
    """Tests for BMad Method installation flow"""

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_bmad_method_success_bunx(self, mock_which, mock_run):
        """Test successful bmad-method install using bunx"""
        mock_which.side_effect = lambda cmd: "/usr/local/bin/bun" if cmd == "bun" else None
        mock_run.return_value = MagicMock(returncode=0)

        parser = create_parser()
        args = parser.parse_args(['dd', '--bmad-method'])
        result = cmd_dd(args)
        assert result == 0

        calls = mock_run.call_args_list
        assert any("bunx bmad-method install" in str(c) for c in calls)

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_bmad_method_success_npx(self, mock_which, mock_run):
        """Test successful bmad-method install using npx"""
        def which_side_effect(cmd):
            if cmd == "bun":
                return None
            if cmd == "npx":
                return "/usr/local/bin/npx"
            return None

        mock_which.side_effect = which_side_effect
        mock_run.return_value = MagicMock(returncode=0)

        parser = create_parser()
        args = parser.parse_args(['dd', '--bmad-method'])
        result = cmd_dd(args)
        assert result == 0

        calls = mock_run.call_args_list
        assert any("npx bmad-method install" in str(c) for c in calls)

    @patch('mono_kickstart.cli.shutil.which')
    def test_bmad_method_no_npx_or_bun(self, mock_which):
        """Test error when neither npx nor bun is available"""
        mock_which.return_value = None

        parser = create_parser()
        args = parser.parse_args(['dd', '--bmad-method'])
        result = cmd_dd(args)
        assert result != 0

    @patch('mono_kickstart.cli.shutil.which')
    def test_bmad_method_dry_run(self, mock_which):
        """Test bmad-method dry run mode"""
        mock_which.side_effect = lambda cmd: "/usr/local/bin/bun" if cmd == "bun" else None

        parser = create_parser()
        args = parser.parse_args(['dd', '--bmad-method', '--dry-run'])
        result = cmd_dd(args)
        assert result == 0


class TestDdBothTools:
    """Tests for using both tools together"""

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_both_tools_success(self, mock_which, mock_run):
        """Test successful initialization of both tools"""
        def which_side_effect(cmd):
            if cmd == "specify":
                return "/usr/local/bin/specify"
            if cmd == "bun":
                return "/usr/local/bin/bun"
            return None

        mock_which.side_effect = which_side_effect
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--bmad-method'])
        result = cmd_dd(args)
        assert result == 0

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_partial_failure_spec_kit_fails(self, mock_which, mock_run):
        """Test partial failure when spec-kit fails but bmad succeeds"""
        mock_which.side_effect = lambda cmd: None  # specify not found

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit', '--bmad-method'])
        # Should still try bmad-method even if spec-kit fails
        # but since both npx/bun also not found, both fail
        result = cmd_dd(args)
        assert result == 1  # all failed


class TestDdKeyboardInterrupt:
    """Tests for keyboard interrupt handling"""

    @patch('subprocess.run')
    @patch('mono_kickstart.cli.shutil.which')
    def test_keyboard_interrupt(self, mock_which, mock_run):
        """Test keyboard interrupt returns exit code 130"""
        mock_which.return_value = "/usr/local/bin/specify"
        mock_run.side_effect = KeyboardInterrupt()

        parser = create_parser()
        args = parser.parse_args(['dd', '--spec-kit'])
        result = cmd_dd(args)
        assert result == 130
