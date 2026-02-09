"""日志记录模块

提供统一的日志记录功能，支持控制台彩色输出和文件记录。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


# ANSI 颜色代码
class Colors:
    """ANSI 颜色代码"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


class ColoredFormatter(logging.Formatter):
    """彩色日志格式器"""
    
    # 日志级别颜色映射
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            格式化后的日志字符串
        """
        # 获取级别颜色
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        
        # 格式化消息
        message = super().format(record)
        
        # 如果是控制台输出且支持颜色，添加颜色
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            # 为级别名称添加颜色
            levelname = record.levelname
            colored_levelname = f"{level_color}{levelname}{Colors.RESET}"
            message = message.replace(levelname, colored_levelname, 1)
        
        return message


class SensitiveInfoFilter(logging.Filter):
    """敏感信息过滤器
    
    过滤日志中的敏感信息，如用户路径中的用户名。
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            是否保留该日志记录
        """
        # 替换用户主目录路径为 ~
        home_dir = str(Path.home())
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = record.msg.replace(home_dir, '~')
        
        # 替换 args 中的路径
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        new_args.append(arg.replace(home_dir, '~'))
                    elif isinstance(arg, dict):
                        new_args.append({
                            key: value.replace(home_dir, '~') if isinstance(value, str) else value
                            for key, value in arg.items()
                        })
                    else:
                        new_args.append(arg)
                record.args = tuple(new_args)
        
        return True


def setup_logger(
    name: str = "mono_kickstart",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        console_level: 控制台日志级别
        file_level: 文件日志级别
        log_dir: 日志文件目录，默认为 ~/.mono-kickstart/logs/
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置为最低级别，由 handler 控制实际输出
    
    # 清除已有的 handlers（避免重复添加）
    logger.handlers.clear()
    
    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # 控制台格式器（彩色）
    console_formatter = ColoredFormatter(
        fmt='%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加敏感信息过滤器
    console_handler.addFilter(SensitiveInfoFilter())
    
    logger.addHandler(console_handler)
    
    # 文件 handler
    if log_dir is None:
        log_dir = Path.home() / ".mono-kickstart" / "logs"
    
    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"mk-{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    
    # 文件格式器（详细格式，无颜色）
    file_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 添加敏感信息过滤器
    file_handler.addFilter(SensitiveInfoFilter())
    
    logger.addHandler(file_handler)
    
    # 记录日志文件位置
    logger.debug(f"日志文件: {log_file}")
    
    return logger


def get_logger(name: str = "mono_kickstart") -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果还没有配置，使用默认配置
    if not logger.handlers:
        return setup_logger(name)
    
    return logger
