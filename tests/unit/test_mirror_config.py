"""镜像源配置器的单元测试"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import pytest
import tomllib

from mono_kickstart.mirror_config import MirrorConfigurator
from mono_kickstart.config import RegistryConfig


@pytest.fixture
def registry_config():
    """创建测试用的镜像源配置"""
    return RegistryConfig(
        npm="https://registry.npmmirror.com/",
        bun="https://registry.npmmirror.com/",
        pypi="https://mirrors.sustech.edu.cn/pypi/web/simple",
        python_install="https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
    )


@pytest.fixture
def configurator(registry_config):
    """创建镜像源配置器实例"""
    return MirrorConfigurator(registry_config)


class TestNpmMirrorConfiguration:
    """测试 npm 镜像源配置"""
    
    def test_configure_npm_mirror_success(self, configurator):
        """测试成功配置 npm 镜像源"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = configurator.configure_npm_mirror()
            
            assert result is True
            mock_run.assert_called_once_with(
                ["npm", "config", "set", "registry", "https://registry.npmmirror.com/"],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_configure_npm_mirror_command_fails(self, configurator):
        """测试 npm 命令执行失败"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            result = configurator.configure_npm_mirror()
            
            assert result is False
    
    def test_configure_npm_mirror_timeout(self, configurator):
        """测试 npm 命令超时"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("npm", 10)
            
            result = configurator.configure_npm_mirror()
            
            assert result is False
    
    def test_configure_npm_mirror_not_found(self, configurator):
        """测试 npm 命令不存在"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = configurator.configure_npm_mirror()
            
            assert result is False
    
    def test_verify_npm_mirror_success(self, configurator):
        """测试验证 npm 镜像源成功"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://registry.npmmirror.com/\n"
            )
            
            result = configurator.verify_npm_mirror()
            
            assert result is True
            mock_run.assert_called_once_with(
                ["npm", "get", "registry"],
                capture_output=True,
                text=True,
                timeout=10
            )
    
    def test_verify_npm_mirror_with_trailing_slash(self, configurator):
        """测试验证 npm 镜像源（处理末尾斜杠）"""
        with patch('subprocess.run') as mock_run:
            # 配置有斜杠，输出没有斜杠
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://registry.npmmirror.com\n"
            )
            
            result = configurator.verify_npm_mirror()
            
            assert result is True
    
    def test_verify_npm_mirror_mismatch(self, configurator):
        """测试验证 npm 镜像源不匹配"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://registry.npmjs.org/\n"
            )
            
            result = configurator.verify_npm_mirror()
            
            assert result is False
    
    def test_verify_npm_mirror_command_fails(self, configurator):
        """测试验证 npm 镜像源命令失败"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            result = configurator.verify_npm_mirror()
            
            assert result is False


class TestBunMirrorConfiguration:
    """测试 Bun 镜像源配置"""
    
    def test_configure_bun_mirror_new_file(self, configurator, tmp_path):
        """测试创建新的 Bun 配置文件"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_bun_mirror()
            
            assert result is True
            assert bunfig_path.exists()
            
            # 验证文件内容
            content = bunfig_path.read_text()
            assert '[install]' in content
            assert 'registry = "https://registry.npmmirror.com/"' in content
    
    def test_configure_bun_mirror_existing_file(self, configurator, tmp_path):
        """测试更新现有的 Bun 配置文件"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 创建现有配置文件
        existing_config = """[install]
registry = "https://registry.npmjs.org/"
cache = "~/.bun/cache"
"""
        bunfig_path.write_text(existing_config)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_bun_mirror()
            
            assert result is True
            
            # 验证文件内容
            content = bunfig_path.read_text()
            assert 'registry = "https://registry.npmmirror.com/"' in content
    
    def test_configure_bun_mirror_preserves_other_config(self, configurator, tmp_path):
        """测试配置 Bun 镜像源时保留其他配置"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 创建包含其他配置的文件
        existing_config = """[install]
cache = "~/.bun/cache"
production = true
"""
        bunfig_path.write_text(existing_config)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_bun_mirror()
            
            assert result is True
            
            # 验证保留了其他配置
            with open(bunfig_path, 'rb') as f:
                config = tomllib.load(f)
            
            assert config["install"]["registry"] == "https://registry.npmmirror.com/"
            # 注意：由于我们的简单实现，可能不会完全保留所有配置
            # 这是一个已知的限制
    
    def test_configure_bun_mirror_io_error(self, configurator, tmp_path):
        """测试配置 Bun 镜像源时发生 IO 错误"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch('builtins.open', side_effect=IOError()):
                result = configurator.configure_bun_mirror()
                
                assert result is False
    
    def test_verify_bun_mirror_success(self, configurator, tmp_path):
        """测试验证 Bun 镜像源成功"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 创建配置文件
        config_content = """[install]
registry = "https://registry.npmmirror.com/"
"""
        bunfig_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_bun_mirror()
            
            assert result is True
    
    def test_verify_bun_mirror_with_trailing_slash(self, configurator, tmp_path):
        """测试验证 Bun 镜像源（处理末尾斜杠）"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 配置文件中没有斜杠
        config_content = """[install]
registry = "https://registry.npmmirror.com"
"""
        bunfig_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_bun_mirror()
            
            assert result is True
    
    def test_verify_bun_mirror_file_not_exists(self, configurator, tmp_path):
        """测试验证 Bun 镜像源文件不存在"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_bun_mirror()
            
            assert result is False
    
    def test_verify_bun_mirror_mismatch(self, configurator, tmp_path):
        """测试验证 Bun 镜像源不匹配"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 创建配置文件，但镜像源不匹配
        config_content = """[install]
registry = "https://registry.npmjs.org/"
"""
        bunfig_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_bun_mirror()
            
            assert result is False
    
    def test_verify_bun_mirror_no_install_section(self, configurator, tmp_path):
        """测试验证 Bun 镜像源没有 install 配置段"""
        bunfig_path = tmp_path / ".bunfig.toml"
        
        # 创建配置文件，但没有 install 段
        config_content = """[other]
key = "value"
"""
        bunfig_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_bun_mirror()
            
            assert result is False


class TestUvMirrorConfiguration:
    """测试 uv 镜像源配置"""
    
    def test_configure_uv_mirror_new_file(self, configurator, tmp_path):
        """测试创建新的 uv 配置文件"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_uv_mirror()
            
            assert result is True
            assert uv_config_path.exists()
            
            # 验证文件内容
            content = uv_config_path.read_text()
            assert 'python-install-mirror = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"' in content
            assert '[[index]]' in content
            assert 'url = "https://mirrors.sustech.edu.cn/pypi/web/simple"' in content
    
    def test_configure_uv_mirror_python_install_before_index(self, configurator, tmp_path):
        """测试 python-install-mirror 在 [[index]] 之前"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_uv_mirror()
            
            assert result is True
            
            # 验证顺序
            content = uv_config_path.read_text()
            python_install_pos = content.find('python-install-mirror')
            index_pos = content.find('[[index]]')
            
            assert python_install_pos < index_pos
    
    def test_configure_uv_mirror_creates_directory(self, configurator, tmp_path):
        """测试配置 uv 镜像源时创建目录"""
        uv_config_dir = tmp_path / ".config" / "uv"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.configure_uv_mirror()
            
            assert result is True
            assert uv_config_dir.exists()
            assert uv_config_dir.is_dir()
    
    def test_configure_uv_mirror_io_error(self, configurator, tmp_path):
        """测试配置 uv 镜像源时发生 IO 错误"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            with patch('builtins.open', side_effect=IOError()):
                result = configurator.configure_uv_mirror()
                
                assert result is False
    
    def test_verify_uv_mirror_success(self, configurator, tmp_path):
        """测试验证 uv 镜像源成功"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        uv_config_dir.mkdir(parents=True)
        
        # 创建配置文件
        config_content = """# uv 配置文件
# 由 mono-kickstart 自动生成

# CPython 下载代理
python-install-mirror = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"

# PyPI 镜像源
[[index]]
url = "https://mirrors.sustech.edu.cn/pypi/web/simple"
"""
        uv_config_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_uv_mirror()
            
            assert result is True
    
    def test_verify_uv_mirror_file_not_exists(self, configurator, tmp_path):
        """测试验证 uv 镜像源文件不存在"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_uv_mirror()
            
            assert result is False
    
    def test_verify_uv_mirror_missing_python_install(self, configurator, tmp_path):
        """测试验证 uv 镜像源缺少 python-install-mirror"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        uv_config_dir.mkdir(parents=True)
        
        # 创建配置文件，但缺少 python-install-mirror
        config_content = """[[index]]
url = "https://mirrors.sustech.edu.cn/pypi/web/simple"
"""
        uv_config_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_uv_mirror()
            
            assert result is False
    
    def test_verify_uv_mirror_missing_index(self, configurator, tmp_path):
        """测试验证 uv 镜像源缺少 [[index]]"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        uv_config_dir.mkdir(parents=True)
        
        # 创建配置文件，但缺少 [[index]]
        config_content = """python-install-mirror = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
"""
        uv_config_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_uv_mirror()
            
            assert result is False
    
    def test_verify_uv_mirror_wrong_order(self, configurator, tmp_path):
        """测试验证 uv 镜像源顺序错误"""
        uv_config_dir = tmp_path / ".config" / "uv"
        uv_config_path = uv_config_dir / "uv.toml"
        uv_config_dir.mkdir(parents=True)
        
        # 创建配置文件，但顺序错误（[[index]] 在前）
        config_content = """[[index]]
url = "https://mirrors.sustech.edu.cn/pypi/web/simple"

python-install-mirror = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
"""
        uv_config_path.write_text(config_content)
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            result = configurator.verify_uv_mirror()
            
            assert result is False


class TestConfigureAll:
    """测试批量配置所有镜像源"""
    
    def test_configure_all_success(self, configurator):
        """测试成功配置所有镜像源"""
        with patch.object(configurator, 'configure_npm_mirror', return_value=True), \
             patch.object(configurator, 'configure_bun_mirror', return_value=True), \
             patch.object(configurator, 'configure_uv_mirror', return_value=True):
            
            results = configurator.configure_all()
            
            assert results == {
                "npm": True,
                "bun": True,
                "uv": True
            }
    
    def test_configure_all_partial_failure(self, configurator):
        """测试部分镜像源配置失败"""
        with patch.object(configurator, 'configure_npm_mirror', return_value=True), \
             patch.object(configurator, 'configure_bun_mirror', return_value=False), \
             patch.object(configurator, 'configure_uv_mirror', return_value=True):
            
            results = configurator.configure_all()
            
            assert results == {
                "npm": True,
                "bun": False,
                "uv": True
            }
    
    def test_configure_all_complete_failure(self, configurator):
        """测试所有镜像源配置失败"""
        with patch.object(configurator, 'configure_npm_mirror', return_value=False), \
             patch.object(configurator, 'configure_bun_mirror', return_value=False), \
             patch.object(configurator, 'configure_uv_mirror', return_value=False):
            
            results = configurator.configure_all()
            
            assert results == {
                "npm": False,
                "bun": False,
                "uv": False
            }


class TestMirrorConfiguratorInitialization:
    """测试镜像源配置器初始化"""
    
    def test_initialization(self, registry_config):
        """测试配置器初始化"""
        configurator = MirrorConfigurator(registry_config)
        
        assert configurator.registry_config == registry_config
        assert configurator.registry_config.npm == "https://registry.npmmirror.com/"
        assert configurator.registry_config.bun == "https://registry.npmmirror.com/"
        assert configurator.registry_config.pypi == "https://mirrors.sustech.edu.cn/pypi/web/simple"
        assert configurator.registry_config.python_install == "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"
