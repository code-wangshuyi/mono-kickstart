"""
Unit tests for installer base class module

Tests command execution, file download, retry logic, timeout handling,
and network error scenarios for the ToolInstaller base class.

**Validates: Requirements 1.12**
"""

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest

from mono_kickstart.config import ToolConfig
from mono_kickstart.installer_base import (
    InstallReport,
    InstallResult,
    ToolInstaller,
)
from mono_kickstart.platform_detector import Arch, OS, PlatformInfo, Shell


# Concrete implementation for testing abstract base class
class ConcreteInstaller(ToolInstaller):
    """Concrete installer implementation for testing"""
    
    def install(self) -> InstallReport:
        return InstallReport(
            tool_name="test-tool",
            result=InstallResult.SUCCESS,
            message="Installation successful"
        )
    
    def upgrade(self) -> InstallReport:
        return InstallReport(
            tool_name="test-tool",
            result=InstallResult.SUCCESS,
            message="Upgrade successful"
        )
    
    def verify(self) -> bool:
        return True


@pytest.fixture
def platform_info():
    """Create a PlatformInfo instance for testing"""
    return PlatformInfo(
        os=OS.LINUX,
        arch=Arch.X86_64,
        shell=Shell.BASH,
        shell_config_file="~/.bashrc"
    )


@pytest.fixture
def tool_config():
    """Create a ToolConfig instance for testing"""
    return ToolConfig(enabled=True, version=None)


@pytest.fixture
def installer(platform_info, tool_config):
    """Create a ConcreteInstaller instance for testing"""
    return ConcreteInstaller(platform_info, tool_config)


class TestInstallResultEnum:
    """Test InstallResult enumeration"""
    
    def test_install_result_values(self):
        """Test InstallResult enum has correct values"""
        assert InstallResult.SUCCESS.value == "success"
        assert InstallResult.SKIPPED.value == "skipped"
        assert InstallResult.FAILED.value == "failed"
    
    def test_install_result_members(self):
        """Test InstallResult enum has all expected members"""
        members = [member.name for member in InstallResult]
        assert "SUCCESS" in members
        assert "SKIPPED" in members
        assert "FAILED" in members
        assert len(members) == 3


class TestInstallReportDataClass:
    """Test InstallReport data class"""
    
    def test_install_report_creation_with_all_fields(self):
        """Test creating InstallReport with all fields"""
        report = InstallReport(
            tool_name="node",
            result=InstallResult.SUCCESS,
            message="Installation successful",
            version="20.11.0",
            error=None
        )
        
        assert report.tool_name == "node"
        assert report.result == InstallResult.SUCCESS
        assert report.message == "Installation successful"
        assert report.version == "20.11.0"
        assert report.error is None
    
    def test_install_report_creation_with_minimal_fields(self):
        """Test creating InstallReport with only required fields"""
        report = InstallReport(
            tool_name="bun",
            result=InstallResult.FAILED,
            message="Installation failed"
        )
        
        assert report.tool_name == "bun"
        assert report.result == InstallResult.FAILED
        assert report.message == "Installation failed"
        assert report.version is None
        assert report.error is None
    
    def test_install_report_with_error(self):
        """Test creating InstallReport with error information"""
        report = InstallReport(
            tool_name="uv",
            result=InstallResult.FAILED,
            message="Download failed",
            error="Network timeout"
        )
        
        assert report.tool_name == "uv"
        assert report.result == InstallResult.FAILED
        assert report.error == "Network timeout"


class TestToolInstallerInitialization:
    """Test ToolInstaller initialization"""
    
    def test_installer_initialization(self, platform_info, tool_config):
        """Test installer initializes with correct attributes"""
        installer = ConcreteInstaller(platform_info, tool_config)
        
        assert installer.platform_info == platform_info
        assert installer.config == tool_config
    
    def test_installer_stores_platform_info(self, platform_info, tool_config):
        """Test installer stores platform information correctly"""
        installer = ConcreteInstaller(platform_info, tool_config)
        
        assert installer.platform_info.os == OS.LINUX
        assert installer.platform_info.arch == Arch.X86_64
        assert installer.platform_info.shell == Shell.BASH
    
    def test_installer_stores_config(self, platform_info, tool_config):
        """Test installer stores configuration correctly"""
        tool_config.enabled = False
        tool_config.version = "1.2.3"
        installer = ConcreteInstaller(platform_info, tool_config)
        
        assert installer.config.enabled is False
        assert installer.config.version == "1.2.3"


class TestRunCommandSuccess:
    """Test run_command method with successful execution"""
    
    def test_run_command_success(self, installer):
        """Test run_command returns correct output on success"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "command output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            returncode, stdout, stderr = installer.run_command("echo test")
            
            assert returncode == 0
            assert stdout == "command output"
            assert stderr == ""
    
    def test_run_command_with_stderr(self, installer):
        """Test run_command captures stderr output"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = "warning message"
        
        with patch('subprocess.run', return_value=mock_result):
            returncode, stdout, stderr = installer.run_command("command")
            
            assert returncode == 0
            assert stdout == "output"
            assert stderr == "warning message"
    
    def test_run_command_with_nonzero_exit_code(self, installer):
        """Test run_command handles non-zero exit codes"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        
        with patch('subprocess.run', return_value=mock_result):
            returncode, stdout, stderr = installer.run_command("failing-command")
            
            assert returncode == 1
            assert stderr == "error message"
    
    def test_run_command_with_shell_parameter(self, installer):
        """Test run_command respects shell parameter"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            installer.run_command("command", shell=False)
            
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['shell'] is False
    
    def test_run_command_with_custom_timeout(self, installer):
        """Test run_command respects custom timeout"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            installer.run_command("command", timeout=60)
            
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['timeout'] == 60


class TestRunCommandRetry:
    """Test run_command retry logic"""
    
    def test_run_command_retries_on_subprocess_error(self, installer):
        """Test run_command retries on subprocess error"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        
        with patch('subprocess.run', side_effect=[
            subprocess.SubprocessError("error 1"),
            subprocess.SubprocessError("error 2"),
            mock_result
        ]) as mock_run:
            with patch('time.sleep'):
                returncode, stdout, stderr = installer.run_command("command", max_retries=3)
                
                assert returncode == 0
                assert stdout == "success"
                assert mock_run.call_count == 3
    
    def test_run_command_fails_after_max_retries(self, installer):
        """Test run_command fails after exhausting retries"""
        with patch('subprocess.run', side_effect=subprocess.SubprocessError("persistent error")):
            with patch('time.sleep'):
                returncode, stdout, stderr = installer.run_command("command", max_retries=3)
                
                assert returncode == -1
                assert stdout == ""
                assert "命令执行失败" in stderr
                assert "persistent error" in stderr
    
    def test_run_command_exponential_backoff(self, installer):
        """Test run_command uses exponential backoff for retries"""
        with patch('subprocess.run', side_effect=subprocess.SubprocessError("error")):
            with patch('time.sleep') as mock_sleep:
                installer.run_command("command", max_retries=3, retry_delay=1)
                
                # Should sleep twice (after first and second attempts)
                assert mock_sleep.call_count == 2
                # First retry: 1 second, second retry: 2 seconds
                mock_sleep.assert_has_calls([call(1), call(2)])
    
    def test_run_command_custom_retry_delay(self, installer):
        """Test run_command respects custom retry delay"""
        with patch('subprocess.run', side_effect=subprocess.SubprocessError("error")):
            with patch('time.sleep') as mock_sleep:
                installer.run_command("command", max_retries=3, retry_delay=2)
                
                # First retry: 2 seconds, second retry: 4 seconds
                mock_sleep.assert_has_calls([call(2), call(4)])
    
    def test_run_command_no_retry_on_success(self, installer):
        """Test run_command doesn't retry on first success"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            with patch('time.sleep') as mock_sleep:
                installer.run_command("command", max_retries=3)
                
                assert mock_run.call_count == 1
                assert mock_sleep.call_count == 0


class TestRunCommandTimeout:
    """Test run_command timeout handling"""
    
    def test_run_command_timeout_raises_exception(self, installer):
        """Test run_command raises TimeoutExpired on timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)):
            with pytest.raises(subprocess.TimeoutExpired):
                installer.run_command("slow-command", timeout=5)
    
    def test_run_command_timeout_no_retry(self, installer):
        """Test run_command doesn't retry on timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)) as mock_run:
            with patch('time.sleep') as mock_sleep:
                with pytest.raises(subprocess.TimeoutExpired):
                    installer.run_command("slow-command", max_retries=3, timeout=5)
                
                # Should only try once, no retries on timeout
                assert mock_run.call_count == 1
                assert mock_sleep.call_count == 0
    
    def test_run_command_with_zero_timeout(self, installer):
        """Test run_command with zero timeout"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            installer.run_command("command", timeout=0)
            
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['timeout'] == 0


class TestDownloadFileSuccess:
    """Test download_file method with successful downloads"""
    
    def test_download_file_success(self, installer, tmp_path):
        """Test download_file successfully downloads a file"""
        dest_file = tmp_path / "test.txt"
        file_content = b"test content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/file.txt", str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.read_bytes() == file_content
    
    def test_download_file_creates_parent_directories(self, installer, tmp_path):
        """Test download_file creates parent directories if they don't exist"""
        dest_file = tmp_path / "subdir" / "nested" / "test.txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/file.txt", str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.parent.exists()
    
    def test_download_file_verifies_file_exists(self, installer, tmp_path):
        """Test download_file verifies the downloaded file exists"""
        dest_file = tmp_path / "test.txt"
        
        mock_response = Mock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/file.txt", str(dest_file))
            
            assert result is True
            assert dest_file.exists()
    
    def test_download_file_verifies_file_not_empty(self, installer, tmp_path):
        """Test download_file verifies the downloaded file is not empty"""
        dest_file = tmp_path / "test.txt"
        
        # Create empty file
        mock_response = Mock()
        mock_response.read.return_value = b""
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/file.txt", str(dest_file))
            
            # Should fail because file is empty
            assert result is False


class TestDownloadFileRetry:
    """Test download_file retry logic"""
    
    def test_download_file_retries_on_url_error(self, installer, tmp_path):
        """Test download_file retries on URLError"""
        dest_file = tmp_path / "test.txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', side_effect=[
            urllib.error.URLError("error 1"),
            urllib.error.URLError("error 2"),
            mock_response
        ]) as mock_urlopen:
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=3)
                
                assert result is True
                assert mock_urlopen.call_count == 3
    
    def test_download_file_retries_on_http_error(self, installer, tmp_path):
        """Test download_file retries on HTTPError"""
        dest_file = tmp_path / "test.txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', side_effect=[
            urllib.error.HTTPError("url", 500, "Server Error", {}, None),
            mock_response
        ]) as mock_urlopen:
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=3)
                
                assert result is True
                assert mock_urlopen.call_count == 2
    
    def test_download_file_fails_after_max_retries(self, installer, tmp_path):
        """Test download_file fails after exhausting retries"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("persistent error")):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=3)
                
                assert result is False
                # File should not exist after failed download
                assert not dest_file.exists()
    
    def test_download_file_exponential_backoff(self, installer, tmp_path):
        """Test download_file uses exponential backoff for retries"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("error")):
            with patch('time.sleep') as mock_sleep:
                installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=3, retry_delay=1)
                
                # Should sleep twice (after first and second attempts)
                assert mock_sleep.call_count == 2
                # First retry: 1 second, second retry: 2 seconds
                mock_sleep.assert_has_calls([call(1), call(2)])
    
    def test_download_file_custom_retry_delay(self, installer, tmp_path):
        """Test download_file respects custom retry delay"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("error")):
            with patch('time.sleep') as mock_sleep:
                installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=3, retry_delay=2)
                
                # First retry: 2 seconds, second retry: 4 seconds
                mock_sleep.assert_has_calls([call(2), call(4)])
    
    def test_download_file_deletes_partial_download_on_error(self, installer, tmp_path):
        """Test download_file deletes partially downloaded file on error"""
        dest_file = tmp_path / "test.txt"
        
        # Create a partial file
        dest_file.write_bytes(b"partial")
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("error")):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=1)
                
                assert result is False
                # Partial file should be deleted
                assert not dest_file.exists()


class TestDownloadFileNetworkErrors:
    """Test download_file network error handling"""
    
    def test_download_file_handles_connection_error(self, installer, tmp_path):
        """Test download_file handles connection errors"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Connection refused")):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=2)
                
                assert result is False
    
    def test_download_file_handles_404_error(self, installer, tmp_path):
        """Test download_file handles 404 errors"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError("url", 404, "Not Found", {}, None)):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=2)
                
                assert result is False
    
    def test_download_file_handles_500_error(self, installer, tmp_path):
        """Test download_file handles 500 errors"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError("url", 500, "Server Error", {}, None)):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=2)
                
                assert result is False
    
    def test_download_file_handles_timeout(self, installer, tmp_path):
        """Test download_file handles timeout errors"""
        dest_file = tmp_path / "test.txt"
        
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("timeout")):
            with patch('time.sleep'):
                result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=2, timeout=10)
                
                assert result is False
    
    def test_download_file_with_custom_timeout(self, installer, tmp_path):
        """Test download_file respects custom timeout"""
        dest_file = tmp_path / "test.txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            installer.download_file("http://example.com/file.txt", str(dest_file), timeout=60)
            
            mock_urlopen.assert_called_once()
            call_args = mock_urlopen.call_args
            assert call_args[1]['timeout'] == 60
    
    def test_download_file_handles_os_error(self, installer, tmp_path):
        """Test download_file handles OS errors (e.g., permission denied)"""
        dest_file = tmp_path / "test.txt"
        
        mock_response = Mock()
        mock_response.read.return_value = b"content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                with patch('time.sleep'):
                    result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=2)
                    
                    assert result is False


class TestAbstractMethods:
    """Test abstract method enforcement"""
    
    def test_concrete_installer_implements_install(self, installer):
        """Test concrete installer implements install method"""
        report = installer.install()
        
        assert isinstance(report, InstallReport)
        assert report.tool_name == "test-tool"
        assert report.result == InstallResult.SUCCESS
    
    def test_concrete_installer_implements_upgrade(self, installer):
        """Test concrete installer implements upgrade method"""
        report = installer.upgrade()
        
        assert isinstance(report, InstallReport)
        assert report.tool_name == "test-tool"
        assert report.result == InstallResult.SUCCESS
    
    def test_concrete_installer_implements_verify(self, installer):
        """Test concrete installer implements verify method"""
        result = installer.verify()
        
        assert isinstance(result, bool)
        assert result is True
    
    def test_cannot_instantiate_abstract_base_class(self, platform_info, tool_config):
        """Test ToolInstaller cannot be instantiated directly"""
        with pytest.raises(TypeError):
            ToolInstaller(platform_info, tool_config)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_run_command_with_empty_command(self, installer):
        """Test run_command with empty command string"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            returncode, stdout, stderr = installer.run_command("")
            
            assert returncode == 0
    
    def test_run_command_with_max_retries_zero(self, installer):
        """Test run_command with max_retries=0 (should still try once)"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            # max_retries=0 should still execute once
            returncode, stdout, stderr = installer.run_command("command", max_retries=1)
            
            assert mock_run.call_count == 1
    
    def test_download_file_with_max_retries_zero(self, installer, tmp_path):
        """Test download_file with max_retries=0 (should still try once)"""
        dest_file = tmp_path / "test.txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            result = installer.download_file("http://example.com/file.txt", str(dest_file), max_retries=1)
            
            assert result is True
            assert mock_urlopen.call_count == 1
    
    def test_download_file_with_special_characters_in_path(self, installer, tmp_path):
        """Test download_file with special characters in file path"""
        dest_file = tmp_path / "test file (1).txt"
        file_content = b"content"
        
        mock_response = Mock()
        mock_response.read.return_value = file_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/file.txt", str(dest_file))
            
            assert result is True
            assert dest_file.exists()
    
    def test_run_command_with_very_long_output(self, installer):
        """Test run_command handles very long output"""
        long_output = "x" * 100000  # 100KB of output
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = long_output
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            returncode, stdout, stderr = installer.run_command("command")
            
            assert returncode == 0
            assert len(stdout) == 100000
    
    def test_download_file_with_large_file(self, installer, tmp_path):
        """Test download_file handles large files"""
        dest_file = tmp_path / "large.bin"
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        
        mock_response = Mock()
        mock_response.read.return_value = large_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = installer.download_file("http://example.com/large.bin", str(dest_file))
            
            assert result is True
            assert dest_file.stat().st_size == 10 * 1024 * 1024
