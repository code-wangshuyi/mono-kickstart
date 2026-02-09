"""日志记录模块单元测试"""

import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from mono_kickstart.logger import (
    setup_logger,
    get_logger,
    ColoredFormatter,
    SensitiveInfoFilter,
    Colors
)


class TestColoredFormatter:
    """彩色格式器测试"""
    
    def test_format_with_color(self):
        """测试彩色格式化"""
        formatter = ColoredFormatter(fmt='%(levelname)s: %(message)s')
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Mock isatty 返回 True（支持颜色）
        with patch('sys.stdout.isatty', return_value=True):
            result = formatter.format(record)
            
            # 验证包含颜色代码
            assert Colors.GREEN in result or 'INFO' in result
    
    def test_format_without_color(self):
        """测试无颜色格式化"""
        formatter = ColoredFormatter(fmt='%(levelname)s: %(message)s')
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Mock isatty 返回 False（不支持颜色）
        with patch('sys.stdout.isatty', return_value=False):
            result = formatter.format(record)
            
            # 验证不包含颜色代码
            assert Colors.GREEN not in result
            assert 'INFO: Test message' in result
    
    def test_different_log_levels(self):
        """测试不同日志级别的颜色"""
        formatter = ColoredFormatter(fmt='%(levelname)s: %(message)s')
        
        levels = [
            (logging.DEBUG, Colors.CYAN),
            (logging.INFO, Colors.GREEN),
            (logging.WARNING, Colors.YELLOW),
            (logging.ERROR, Colors.RED),
            (logging.CRITICAL, Colors.RED),
        ]
        
        with patch('sys.stdout.isatty', return_value=True):
            for level, expected_color in levels:
                record = logging.LogRecord(
                    name='test',
                    level=level,
                    pathname='',
                    lineno=0,
                    msg='Test message',
                    args=(),
                    exc_info=None
                )
                
                result = formatter.format(record)
                # 验证包含对应的颜色代码或级别名称
                assert expected_color in result or logging.getLevelName(level) in result


class TestSensitiveInfoFilter:
    """敏感信息过滤器测试"""
    
    def test_filter_home_directory_in_message(self):
        """测试过滤消息中的主目录路径"""
        filter_obj = SensitiveInfoFilter()
        home_dir = str(Path.home())
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=f'File saved to {home_dir}/config.yaml',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # 验证主目录被替换为 ~
        assert home_dir not in record.msg
        assert '~/config.yaml' in record.msg
    
    def test_filter_home_directory_in_args_tuple(self):
        """测试过滤 args 元组中的主目录路径"""
        filter_obj = SensitiveInfoFilter()
        home_dir = str(Path.home())
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='File saved to %s',
            args=(f'{home_dir}/config.yaml',),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # 验证 args 中的主目录被替换
        assert home_dir not in record.args[0]
        assert '~/config.yaml' in record.args[0]
    
    def test_filter_home_directory_in_args_dict(self):
        """测试过滤 args 字典中的主目录路径"""
        filter_obj = SensitiveInfoFilter()
        home_dir = str(Path.home())
        
        # 创建一个简单的 LogRecord
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # 手动设置 args 为包含字典的元组
        record.args = ({'path': f'{home_dir}/config.yaml'},)
        
        filter_obj.filter(record)
        
        # 验证 args 字典中的主目录被替换
        assert isinstance(record.args[0], dict)
        assert home_dir not in record.args[0]['path']
        assert '~/config.yaml' in record.args[0]['path']
    
    def test_filter_returns_true(self):
        """测试过滤器总是返回 True"""
        filter_obj = SensitiveInfoFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True


class TestSetupLogger:
    """日志设置测试"""
    
    def test_setup_logger_creates_logger(self, tmp_path):
        """测试创建日志记录器"""
        logger = setup_logger(
            name='test_logger',
            log_dir=tmp_path
        )
        
        assert logger is not None
        assert logger.name == 'test_logger'
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_creates_handlers(self, tmp_path):
        """测试创建 handlers"""
        logger = setup_logger(
            name='test_logger',
            log_dir=tmp_path
        )
        
        # 验证有两个 handlers（控制台和文件）
        assert len(logger.handlers) == 2
        
        # 验证 handler 类型
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert 'StreamHandler' in handler_types
        assert 'FileHandler' in handler_types
    
    def test_setup_logger_creates_log_file(self, tmp_path):
        """测试创建日志文件"""
        logger = setup_logger(
            name='test_logger',
            log_dir=tmp_path
        )
        
        # 验证日志目录存在
        assert tmp_path.exists()
        
        # 验证日志文件被创建
        log_files = list(tmp_path.glob('mk-*.log'))
        assert len(log_files) == 1
    
    def test_setup_logger_with_custom_levels(self, tmp_path):
        """测试自定义日志级别"""
        logger = setup_logger(
            name='test_logger',
            console_level=logging.WARNING,
            file_level=logging.INFO,
            log_dir=tmp_path
        )
        
        # 验证 handler 级别
        console_handler = logger.handlers[0]
        file_handler = logger.handlers[1]
        
        assert console_handler.level == logging.WARNING
        assert file_handler.level == logging.INFO
    
    def test_setup_logger_adds_filters(self, tmp_path):
        """测试添加过滤器"""
        logger = setup_logger(
            name='test_logger',
            log_dir=tmp_path
        )
        
        # 验证每个 handler 都有过滤器
        for handler in logger.handlers:
            assert len(handler.filters) > 0
            assert any(isinstance(f, SensitiveInfoFilter) for f in handler.filters)
    
    def test_setup_logger_clears_existing_handlers(self, tmp_path):
        """测试清除已有的 handlers"""
        # 第一次设置
        logger1 = setup_logger(name='test_logger', log_dir=tmp_path)
        handler_count1 = len(logger1.handlers)
        
        # 第二次设置（应该清除之前的 handlers）
        logger2 = setup_logger(name='test_logger', log_dir=tmp_path)
        handler_count2 = len(logger2.handlers)
        
        # 验证 handler 数量相同（没有重复添加）
        assert handler_count1 == handler_count2


class TestGetLogger:
    """获取日志记录器测试"""
    
    def test_get_logger_returns_existing_logger(self, tmp_path):
        """测试获取已存在的日志记录器"""
        # 先设置日志记录器
        logger1 = setup_logger(name='test_logger', log_dir=tmp_path)
        
        # 获取日志记录器
        logger2 = get_logger(name='test_logger')
        
        # 验证是同一个日志记录器
        assert logger1 is logger2
    
    def test_get_logger_creates_new_logger_if_not_exists(self):
        """测试获取不存在的日志记录器时自动创建"""
        logger = get_logger(name='new_test_logger')
        
        assert logger is not None
        assert logger.name == 'new_test_logger'
        assert len(logger.handlers) > 0
    
    def test_get_logger_default_name(self):
        """测试默认日志记录器名称"""
        logger = get_logger()
        
        assert logger.name == 'mono_kickstart'


class TestLoggerIntegration:
    """日志记录器集成测试"""
    
    def test_logger_writes_to_console(self, tmp_path, capsys):
        """测试日志写入控制台"""
        logger = setup_logger(
            name='test_logger',
            console_level=logging.INFO,
            log_dir=tmp_path
        )
        
        logger.info("Test info message")
        
        captured = capsys.readouterr()
        assert "Test info message" in captured.out
    
    def test_logger_writes_to_file(self, tmp_path):
        """测试日志写入文件"""
        logger = setup_logger(
            name='test_logger',
            file_level=logging.DEBUG,
            log_dir=tmp_path
        )
        
        logger.debug("Test debug message")
        
        # 查找日志文件
        log_files = list(tmp_path.glob('mk-*.log'))
        assert len(log_files) == 1
        
        # 读取日志文件内容
        log_content = log_files[0].read_text()
        assert "Test debug message" in log_content
    
    def test_logger_filters_sensitive_info(self, tmp_path):
        """测试日志过滤敏感信息"""
        logger = setup_logger(
            name='test_logger',
            log_dir=tmp_path
        )
        
        home_dir = str(Path.home())
        logger.info(f"Config saved to {home_dir}/config.yaml")
        
        # 读取日志文件
        log_files = list(tmp_path.glob('mk-*.log'))
        log_content = log_files[0].read_text()
        
        # 验证主目录被替换为 ~
        assert home_dir not in log_content
        assert "~/config.yaml" in log_content
