"""
Unit tests for tool detector module

Tests command availability checking, version parsing, and tool detection logic.
Uses mocks to simulate command execution without requiring actual tools.

**Validates: Requirements 1.2**
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mono_kickstart.tool_detector import ToolDetector, ToolStatus


@pytest.fixture
def detector():
    """Create a ToolDetector instance for testing"""
    return ToolDetector()


class TestCommandAvailability:
    """Test command availability checking"""
    
    def test_command_available_when_exists(self, detector):
        """Test is_command_available returns True when command exists"""
        with patch('shutil.which', return_value='/usr/bin/node'):
            assert detector.is_command_available('node') is True
    
    def test_command_not_available_when_missing(self, detector):
        """Test is_command_available returns False when command doesn't exist"""
        with patch('shutil.which', return_value=None):
            assert detector.is_command_available('nonexistent') is False
    
    def test_command_availability_with_various_commands(self, detector):
        """Test command availability with different command names"""
        commands = ['node', 'npm', 'bun', 'uv', 'conda', 'claude', 'codex']
        
        for cmd in commands:
            with patch('shutil.which', return_value=f'/usr/bin/{cmd}'):
                assert detector.is_command_available(cmd) is True
            
            with patch('shutil.which', return_value=None):
                assert detector.is_command_available(cmd) is False


class TestVersionParsing:
    """Test version number parsing from command output"""
    
    def test_parse_standard_version_format(self, detector):
        """Test parsing standard version format (1.2.3)"""
        mock_result = Mock()
        mock_result.stdout = "v1.2.3\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('node')
            assert version == "1.2.3"
    
    def test_parse_version_without_v_prefix(self, detector):
        """Test parsing version without 'v' prefix"""
        mock_result = Mock()
        mock_result.stdout = "20.11.0\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('node')
            assert version == "20.11.0"
    
    def test_parse_version_with_text_prefix(self, detector):
        """Test parsing version with 'version' text prefix"""
        mock_result = Mock()
        mock_result.stdout = "conda version 23.5.0\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('conda')
            assert version == "23.5.0"
    
    def test_parse_version_from_stderr(self, detector):
        """Test parsing version from stderr when stdout is empty"""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = "v1.0.5\n"
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('bun')
            assert version == "1.0.5"
    
    def test_parse_version_with_four_parts(self, detector):
        """Test parsing version with four parts (1.2.3.4)"""
        mock_result = Mock()
        mock_result.stdout = "1.2.3.4\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('tool')
            assert version == "1.2.3.4"
    
    def test_parse_version_with_extra_text(self, detector):
        """Test parsing version with extra text in output"""
        mock_result = Mock()
        mock_result.stdout = "Tool v2.5.1 (build 12345)\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('tool')
            assert version == "2.5.1"
    
    def test_version_parsing_timeout(self, detector):
        """Test version parsing returns None on timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)):
            version = detector.get_command_version('slow-command')
            assert version is None
    
    def test_version_parsing_subprocess_error(self, detector):
        """Test version parsing returns None on subprocess error"""
        with patch('subprocess.run', side_effect=subprocess.SubprocessError()):
            version = detector.get_command_version('broken-command')
            assert version is None
    
    def test_version_parsing_file_not_found(self, detector):
        """Test version parsing returns None when command not found"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            version = detector.get_command_version('missing-command')
            assert version is None
    
    def test_version_parsing_no_version_in_output(self, detector):
        """Test version parsing returns first line when no version pattern found"""
        mock_result = Mock()
        mock_result.stdout = "Some tool output\nMore text\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('tool')
            assert version == "Some tool output"
    
    def test_version_parsing_empty_output(self, detector):
        """Test version parsing returns None for empty output"""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            version = detector.get_command_version('tool')
            assert version is None
    
    def test_custom_version_argument(self, detector):
        """Test using custom version argument"""
        mock_result = Mock()
        mock_result.stdout = "1.5.0\n"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            version = detector.get_command_version('tool', '-v')
            assert version == "1.5.0"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ['tool', '-v']


class TestNVMDetection:
    """Test NVM detection logic"""
    
    def test_nvm_detected_with_version(self, detector):
        """Test NVM detection when nvm.sh exists and version can be retrieved"""
        nvm_path = Path.home() / ".nvm" / "nvm.sh"
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "0.40.4\n"
        mock_result.stderr = ""
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_nvm()
                
                assert status.name == "nvm"
                assert status.installed is True
                assert status.version == "0.40.4"
                assert status.path == str(nvm_path)
    
    def test_nvm_detected_without_version(self, detector):
        """Test NVM detection when nvm.sh exists but version cannot be retrieved"""
        nvm_path = Path.home() / ".nvm" / "nvm.sh"
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_nvm()
                
                assert status.name == "nvm"
                assert status.installed is True
                assert status.version is None
                assert status.path == str(nvm_path)
    
    def test_nvm_not_detected_when_missing(self, detector):
        """Test NVM detection when nvm.sh doesn't exist"""
        with patch.object(Path, 'exists', return_value=False):
            status = detector.detect_nvm()
            
            assert status.name == "nvm"
            assert status.installed is False
            assert status.version is None
            assert status.path is None
    
    def test_nvm_detection_timeout(self, detector):
        """Test NVM detection handles timeout gracefully"""
        nvm_path = Path.home() / ".nvm" / "nvm.sh"
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)):
                status = detector.detect_nvm()
                
                assert status.name == "nvm"
                assert status.installed is True
                assert status.version is None
                assert status.path == str(nvm_path)
    
    def test_nvm_detection_subprocess_error(self, detector):
        """Test NVM detection handles subprocess error gracefully"""
        nvm_path = Path.home() / ".nvm" / "nvm.sh"
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.SubprocessError()):
                status = detector.detect_nvm()
                
                assert status.name == "nvm"
                assert status.installed is True
                assert status.version is None
                assert status.path == str(nvm_path)


class TestNodeDetection:
    """Test Node.js detection logic"""
    
    def test_node_detected_successfully(self, detector):
        """Test Node.js detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "v20.11.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/bin/node'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_node()
                
                assert status.name == "node"
                assert status.installed is True
                assert status.version == "20.11.0"
                assert status.path == "/usr/bin/node"
    
    def test_node_not_detected_when_missing(self, detector):
        """Test Node.js detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_node()
            
            assert status.name == "node"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestCondaDetection:
    """Test Conda detection logic"""
    
    def test_conda_detected_successfully(self, detector):
        """Test Conda detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "conda 23.5.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/opt/conda/bin/conda'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_conda()
                
                assert status.name == "conda"
                assert status.installed is True
                assert status.version == "23.5.0"
                assert status.path == "/opt/conda/bin/conda"
    
    def test_conda_not_detected_when_missing(self, detector):
        """Test Conda detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_conda()
            
            assert status.name == "conda"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestBunDetection:
    """Test Bun detection logic"""
    
    def test_bun_detected_successfully(self, detector):
        """Test Bun detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "1.0.25\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/bun'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_bun()
                
                assert status.name == "bun"
                assert status.installed is True
                assert status.version == "1.0.25"
                assert status.path == "/usr/local/bin/bun"
    
    def test_bun_not_detected_when_missing(self, detector):
        """Test Bun detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_bun()
            
            assert status.name == "bun"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestUVDetection:
    """Test uv detection logic"""
    
    def test_uv_detected_successfully(self, detector):
        """Test uv detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "uv 0.1.5\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/uv'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_uv()
                
                assert status.name == "uv"
                assert status.installed is True
                assert status.version == "0.1.5"
                assert status.path == "/usr/local/bin/uv"
    
    def test_uv_not_detected_when_missing(self, detector):
        """Test uv detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_uv()
            
            assert status.name == "uv"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestClaudeCodeDetection:
    """Test Claude Code CLI detection logic"""
    
    def test_claude_code_detected_successfully(self, detector):
        """Test Claude Code CLI detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "claude 1.0.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/claude'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_claude_code()
                
                assert status.name == "claude-code"
                assert status.installed is True
                assert status.version == "1.0.0"
                assert status.path == "/usr/local/bin/claude"
    
    def test_claude_code_not_detected_when_missing(self, detector):
        """Test Claude Code CLI detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_claude_code()
            
            assert status.name == "claude-code"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestCodexDetection:
    """Test Codex CLI detection logic"""
    
    def test_codex_detected_successfully(self, detector):
        """Test Codex CLI detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "codex 2.1.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/codex'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_codex()
                
                assert status.name == "codex"
                assert status.installed is True
                assert status.version == "2.1.0"
                assert status.path == "/usr/local/bin/codex"
    
    def test_codex_not_detected_when_missing(self, detector):
        """Test Codex CLI detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_codex()
            
            assert status.name == "codex"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestSpecKitDetection:
    """Test Spec Kit detection logic"""
    
    def test_spec_kit_detected_successfully(self, detector):
        """Test Spec Kit detection when installed (command name is 'specify')"""
        mock_result = Mock()
        mock_result.stdout = "specify 1.5.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/specify'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_spec_kit()
                
                assert status.name == "spec-kit"
                assert status.installed is True
                assert status.version == "1.5.0"
                assert status.path == "/usr/local/bin/specify"
    
    def test_spec_kit_not_detected_when_missing(self, detector):
        """Test Spec Kit detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_spec_kit()
            
            assert status.name == "spec-kit"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestBMadDetection:
    """Test BMad Method detection logic"""
    
    def test_bmad_detected_successfully(self, detector):
        """Test BMad Method detection when installed"""
        mock_result = Mock()
        mock_result.stdout = "bmad 3.0.0\n"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value='/usr/local/bin/bmad'):
            with patch('subprocess.run', return_value=mock_result):
                status = detector.detect_bmad()
                
                assert status.name == "bmad-method"
                assert status.installed is True
                assert status.version == "3.0.0"
                assert status.path == "/usr/local/bin/bmad"
    
    def test_bmad_not_detected_when_missing(self, detector):
        """Test BMad Method detection when not installed"""
        with patch('shutil.which', return_value=None):
            status = detector.detect_bmad()
            
            assert status.name == "bmad-method"
            assert status.installed is False
            assert status.version is None
            assert status.path is None


class TestDetectAllTools:
    """Test batch detection of all tools"""
    
    def test_detect_all_tools_returns_all_tools(self, detector):
        """Test detect_all_tools returns status for all tools"""
        # Mock all detection methods
        with patch.object(detector, 'detect_nvm') as mock_nvm, \
             patch.object(detector, 'detect_node') as mock_node, \
             patch.object(detector, 'detect_conda') as mock_conda, \
             patch.object(detector, 'detect_bun') as mock_bun, \
             patch.object(detector, 'detect_uv') as mock_uv, \
             patch.object(detector, 'detect_claude_code') as mock_claude, \
             patch.object(detector, 'detect_codex') as mock_codex, \
             patch.object(detector, 'detect_spec_kit') as mock_spec, \
             patch.object(detector, 'detect_bmad') as mock_bmad:
            
            # Set return values
            mock_nvm.return_value = ToolStatus("nvm", True, "0.40.4", "/path/nvm")
            mock_node.return_value = ToolStatus("node", True, "20.11.0", "/usr/bin/node")
            mock_conda.return_value = ToolStatus("conda", False)
            mock_bun.return_value = ToolStatus("bun", True, "1.0.25", "/usr/local/bin/bun")
            mock_uv.return_value = ToolStatus("uv", False)
            mock_claude.return_value = ToolStatus("claude-code", False)
            mock_codex.return_value = ToolStatus("codex", False)
            mock_spec.return_value = ToolStatus("spec-kit", False)
            mock_bmad.return_value = ToolStatus("bmad-method", False)
            
            # Call detect_all_tools
            result = detector.detect_all_tools()
            
            # Verify all tools are in result
            assert len(result) == 9
            assert "nvm" in result
            assert "node" in result
            assert "conda" in result
            assert "bun" in result
            assert "uv" in result
            assert "claude-code" in result
            assert "codex" in result
            assert "spec-kit" in result
            assert "bmad-method" in result
            
            # Verify specific statuses
            assert result["nvm"].installed is True
            assert result["nvm"].version == "0.40.4"
            assert result["node"].installed is True
            assert result["conda"].installed is False
            assert result["bun"].installed is True
    
    def test_detect_all_tools_calls_all_detection_methods(self, detector):
        """Test detect_all_tools calls all individual detection methods"""
        with patch.object(detector, 'detect_nvm') as mock_nvm, \
             patch.object(detector, 'detect_node') as mock_node, \
             patch.object(detector, 'detect_conda') as mock_conda, \
             patch.object(detector, 'detect_bun') as mock_bun, \
             patch.object(detector, 'detect_uv') as mock_uv, \
             patch.object(detector, 'detect_claude_code') as mock_claude, \
             patch.object(detector, 'detect_codex') as mock_codex, \
             patch.object(detector, 'detect_spec_kit') as mock_spec, \
             patch.object(detector, 'detect_bmad') as mock_bmad:
            
            # Set default return values
            for mock in [mock_nvm, mock_node, mock_conda, mock_bun, mock_uv,
                        mock_claude, mock_codex, mock_spec, mock_bmad]:
                mock.return_value = ToolStatus("tool", False)
            
            # Call detect_all_tools
            detector.detect_all_tools()
            
            # Verify all methods were called
            mock_nvm.assert_called_once()
            mock_node.assert_called_once()
            mock_conda.assert_called_once()
            mock_bun.assert_called_once()
            mock_uv.assert_called_once()
            mock_claude.assert_called_once()
            mock_codex.assert_called_once()
            mock_spec.assert_called_once()
            mock_bmad.assert_called_once()
    
    def test_detect_all_tools_with_mixed_installation_states(self, detector):
        """Test detect_all_tools with some tools installed and some not"""
        with patch.object(detector, 'detect_nvm', return_value=ToolStatus("nvm", True, "0.40.4")), \
             patch.object(detector, 'detect_node', return_value=ToolStatus("node", True, "20.11.0")), \
             patch.object(detector, 'detect_conda', return_value=ToolStatus("conda", False)), \
             patch.object(detector, 'detect_bun', return_value=ToolStatus("bun", False)), \
             patch.object(detector, 'detect_uv', return_value=ToolStatus("uv", True, "0.1.5")), \
             patch.object(detector, 'detect_claude_code', return_value=ToolStatus("claude-code", False)), \
             patch.object(detector, 'detect_codex', return_value=ToolStatus("codex", False)), \
             patch.object(detector, 'detect_spec_kit', return_value=ToolStatus("spec-kit", True, "1.5.0")), \
             patch.object(detector, 'detect_bmad', return_value=ToolStatus("bmad-method", False)):
            
            result = detector.detect_all_tools()
            
            # Count installed vs not installed
            installed_count = sum(1 for status in result.values() if status.installed)
            not_installed_count = sum(1 for status in result.values() if not status.installed)
            
            assert installed_count == 4  # nvm, node, uv, spec-kit
            assert not_installed_count == 5  # conda, bun, claude-code, codex, bmad-method


class TestToolStatusDataClass:
    """Test ToolStatus data class"""
    
    def test_tool_status_creation_with_all_fields(self):
        """Test creating ToolStatus with all fields"""
        status = ToolStatus(
            name="node",
            installed=True,
            version="20.11.0",
            path="/usr/bin/node"
        )
        
        assert status.name == "node"
        assert status.installed is True
        assert status.version == "20.11.0"
        assert status.path == "/usr/bin/node"
    
    def test_tool_status_creation_with_minimal_fields(self):
        """Test creating ToolStatus with only required fields"""
        status = ToolStatus(name="tool", installed=False)
        
        assert status.name == "tool"
        assert status.installed is False
        assert status.version is None
        assert status.path is None
    
    def test_tool_status_equality(self):
        """Test ToolStatus equality comparison"""
        status1 = ToolStatus("node", True, "20.11.0", "/usr/bin/node")
        status2 = ToolStatus("node", True, "20.11.0", "/usr/bin/node")
        status3 = ToolStatus("node", True, "18.0.0", "/usr/bin/node")
        
        assert status1 == status2
        assert status1 != status3
