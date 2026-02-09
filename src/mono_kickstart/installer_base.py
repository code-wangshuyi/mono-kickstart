"""工具安装器基类模块

该模块定义了工具安装器的通用接口和基础功能，包括命令执行、文件下载等。
所有具体的工具安装器都应继承自 ToolInstaller 抽象基类。
"""

import subprocess
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from .config import ToolConfig
from .platform_detector import PlatformInfo


class InstallResult(Enum):
    """安装结果枚举
    
    Attributes:
        SUCCESS: 安装成功
        SKIPPED: 跳过安装（工具已存在）
        FAILED: 安装失败
    """
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class InstallReport:
    """安装报告
    
    Attributes:
        tool_name: 工具名称
        result: 安装结果
        message: 描述信息
        version: 安装的版本号（可选）
        error: 错误信息（可选）
    """
    tool_name: str
    result: InstallResult
    message: str
    version: Optional[str] = None
    error: Optional[str] = None


class ToolInstaller(ABC):
    """工具安装器抽象基类
    
    所有具体的工具安装器都应继承此类并实现抽象方法。
    
    Attributes:
        platform_info: 平台信息
        config: 工具配置
    """
    
    def __init__(self, platform_info: PlatformInfo, config: ToolConfig):
        """初始化工具安装器
        
        Args:
            platform_info: 平台信息（操作系统、架构、Shell 等）
            config: 工具配置
        """
        self.platform_info = platform_info
        self.config = config
    
    @abstractmethod
    def install(self) -> InstallReport:
        """安装工具
        
        子类必须实现此方法以提供具体的安装逻辑。
        
        Returns:
            InstallReport: 安装报告
        """
        pass
    
    @abstractmethod
    def upgrade(self) -> InstallReport:
        """升级工具
        
        子类必须实现此方法以提供具体的升级逻辑。
        
        Returns:
            InstallReport: 升级报告
        """
        pass
    
    @abstractmethod
    def verify(self) -> bool:
        """验证安装是否成功
        
        子类必须实现此方法以验证工具是否正确安装。
        
        Returns:
            bool: 如果验证成功返回 True，否则返回 False
        """
        pass
    
    def run_command(
        self,
        command: str,
        shell: bool = True,
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: int = 1
    ) -> Tuple[int, str, str]:
        """执行 shell 命令（支持重试）
        
        Args:
            command: 要执行的命令
            shell: 是否使用 shell 执行（默认为 True）
            timeout: 命令超时时间（秒），默认 300 秒
            max_retries: 最大重试次数，默认 3 次
            retry_delay: 重试延迟（秒），使用指数退避，默认初始延迟 1 秒
            
        Returns:
            Tuple[int, str, str]: (返回码, stdout, stderr)
            
        Raises:
            subprocess.TimeoutExpired: 命令执行超时
        """
        last_exception = None
        current_delay = retry_delay
        
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    command,
                    shell=shell,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                return (result.returncode, result.stdout, result.stderr)
                
            except subprocess.TimeoutExpired as e:
                # 超时错误不重试，直接抛出
                raise
                
            except subprocess.SubprocessError as e:
                last_exception = e
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(current_delay)
                    # 指数退避：每次重试延迟翻倍
                    current_delay *= 2
        
        # 所有重试都失败，返回错误信息
        error_msg = f"命令执行失败: {str(last_exception)}"
        return (-1, "", error_msg)
    
    def download_file(
        self,
        url: str,
        dest: str,
        max_retries: int = 3,
        retry_delay: int = 1,
        timeout: int = 300
    ) -> bool:
        """下载文件（支持重试）
        
        Args:
            url: 文件 URL
            dest: 目标文件路径
            max_retries: 最大重试次数，默认 3 次
            retry_delay: 重试延迟（秒），使用指数退避，默认初始延迟 1 秒
            timeout: 下载超时时间（秒），默认 300 秒
            
        Returns:
            bool: 如果下载成功返回 True，否则返回 False
        """
        dest_path = Path(dest)
        
        # 确保目标目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        last_exception = None
        current_delay = retry_delay
        
        for attempt in range(max_retries):
            try:
                # 下载文件
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    with open(dest_path, 'wb') as out_file:
                        out_file.write(response.read())
                
                # 验证文件是否存在且非空
                if dest_path.exists() and dest_path.stat().st_size > 0:
                    return True
                    
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                last_exception = e
                
                # 如果文件部分下载，删除它
                if dest_path.exists():
                    try:
                        dest_path.unlink()
                    except OSError:
                        pass
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(current_delay)
                    # 指数退避：每次重试延迟翻倍
                    current_delay *= 2
        
        # 所有重试都失败
        return False
