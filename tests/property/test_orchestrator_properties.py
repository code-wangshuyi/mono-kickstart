"""安装编排器的基于属性的测试

本模块使用 Hypothesis 框架测试安装编排器的通用属性。
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from hypothesis import given, settings, strategies as st, HealthCheck

from mono_kickstart.config import Config, ToolConfig, RegistryConfig, ProjectConfig
from mono_kickstart.installer_base import InstallReport, InstallResult
from mono_kickstart.orchestrator import InstallOrchestrator, INSTALL_ORDER
from mono_kickstart.platform_detector import PlatformInfo, OS, Arch, Shell


# 定义测试数据生成策略

@st.composite
def platform_info_strategy(draw):
    """生成平台信息策略"""
    os = draw(st.sampled_from([OS.MACOS, OS.LINUX]))
    arch = draw(st.sampled_from([Arch.ARM64, Arch.X86_64]))
    shell = draw(st.sampled_from([Shell.BASH, Shell.ZSH, Shell.FISH]))
    shell_config_file = f"/home/user/.{shell.value}rc"
    
    return PlatformInfo(
        os=os,
        arch=arch,
        shell=shell,
        shell_config_file=shell_config_file
    )


@st.composite
def tool_config_strategy(draw):
    """生成工具配置策略"""
    enabled = draw(st.booleans())
    version = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    install_via = draw(st.one_of(st.none(), st.sampled_from(['bun', 'npm'])))
    
    return ToolConfig(
        enabled=enabled,
        version=version,
        install_via=install_via
    )


@st.composite
def config_strategy(draw):
    """生成配置策略"""
    # 生成工具配置
    tools = {}
    # 随机选择一些工具启用
    enabled_tools = draw(st.sets(st.sampled_from(INSTALL_ORDER), min_size=0, max_size=len(INSTALL_ORDER)))
    
    for tool_name in INSTALL_ORDER:
        if tool_name in enabled_tools:
            tools[tool_name] = draw(tool_config_strategy())
        else:
            # 未启用的工具
            tools[tool_name] = ToolConfig(enabled=False)
    
    return Config(
        project=ProjectConfig(name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))),
        tools=tools,
        registry=RegistryConfig()
    )


@st.composite
def install_report_strategy(draw, tool_name):
    """生成安装报告策略"""
    result = draw(st.sampled_from([InstallResult.SUCCESS, InstallResult.SKIPPED, InstallResult.FAILED]))
    message = draw(st.text(min_size=1, max_size=100))
    version = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    error = draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))) if result == InstallResult.FAILED else None
    
    return InstallReport(
        tool_name=tool_name,
        result=result,
        message=message,
        version=version,
        error=error
    )


class TestInstallOrderConsistency:
    """测试属性 1: 工具安装顺序一致性
    
    **Validates: Requirements 1.1**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_install_order_follows_dependencies(self, config, platform_info):
        """验证工具安装顺序始终遵循依赖关系
        
        对于任何工具集合和初始安装状态，安装编排器应该按照定义的依赖顺序
        调用工具安装器。
        
        **Validates: Requirements 1.1**
        """
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
        install_order = orchestrator.get_install_order()
        
        # 验证返回的顺序是 INSTALL_ORDER 的子序列
        # 即保持相对顺序不变
        install_order_indices = []
        for tool in install_order:
            if tool in INSTALL_ORDER:
                install_order_indices.append(INSTALL_ORDER.index(tool))
        
        # 验证索引是递增的（保持原始顺序）
        for i in range(len(install_order_indices) - 1):
            assert install_order_indices[i] < install_order_indices[i + 1], \
                f"工具安装顺序不符合依赖关系: {install_order}"
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_only_enabled_tools_in_order(self, config, platform_info):
        """验证只有启用的工具出现在安装顺序中
        
        **Validates: Requirements 1.1**
        """
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
        install_order = orchestrator.get_install_order()
        
        # 验证所有返回的工具都是启用的
        for tool_name in install_order:
            tool_config = config.tools.get(tool_name, ToolConfig())
            assert tool_config.enabled, f"未启用的工具 {tool_name} 出现在安装顺序中"


class TestIdempotency:
    """测试属性 2: 幂等性
    
    **Validates: Requirements 1.2, 6.1, 6.2**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_repeated_execution_same_result(self, config, platform_info):
        """验证重复执行产生相同结果
        
        对于任何初始系统状态，执行初始化命令两次应该产生与执行一次相同的最终状态。
        
        **Validates: Requirements 1.2, 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # 模拟工具已安装的状态
            with patch.object(InstallOrchestrator, 'install_tool') as mock_install:
                # 第一次执行：模拟所有工具安装成功
                def install_side_effect_1(tool_name):
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SUCCESS,
                        message=f"{tool_name} 安装成功",
                        version="1.0.0"
                    )
                
                mock_install.side_effect = install_side_effect_1
                
                orchestrator1 = InstallOrchestrator(config, platform_info, dry_run=False)
                reports1 = orchestrator1.install_all_tools()
                
                # 第二次执行：模拟所有工具已安装（跳过）
                def install_side_effect_2(tool_name):
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SKIPPED,
                        message=f"{tool_name} 已安装",
                        version="1.0.0"
                    )
                
                mock_install.side_effect = install_side_effect_2
                
                orchestrator2 = InstallOrchestrator(config, platform_info, dry_run=False)
                reports2 = orchestrator2.install_all_tools()
                
                # 验证两次执行的工具列表相同
                assert set(reports1.keys()) == set(reports2.keys()), \
                    "两次执行的工具列表不同"
                
                # 验证第二次执行时，所有工具都被跳过（因为已安装）
                for tool_name, report in reports2.items():
                    assert report.result == InstallResult.SKIPPED, \
                        f"第二次执行时 {tool_name} 应该被跳过"


class TestFaultTolerance:
    """测试属性 5: 容错性
    
    **Validates: Requirements 1.12, 5.13, 6.3**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy(),
        # 随机选择一些工具失败
        failed_tools=st.sets(st.sampled_from(INSTALL_ORDER), min_size=0, max_size=3)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_continues_after_failure(self, config, platform_info, failed_tools):
        """验证部分工具失败后继续安装其余工具
        
        对于任何工具子集的安装失败，安装编排器应该继续安装其余工具，
        并在最终报告中记录所有失败的工具及其错误信息。
        
        **Validates: Requirements 1.12, 5.13, 6.3**
        """
        with patch.object(InstallOrchestrator, 'install_tool') as mock_install:
            # 模拟部分工具失败
            def install_side_effect(tool_name):
                if tool_name in failed_tools:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.FAILED,
                        message=f"{tool_name} 安装失败",
                        error="模拟错误"
                    )
                else:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SUCCESS,
                        message=f"{tool_name} 安装成功",
                        version="1.0.0"
                    )
            
            mock_install.side_effect = install_side_effect
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.install_all_tools()
            
            # 验证所有启用的工具都被尝试安装
            enabled_tools = [t for t in INSTALL_ORDER if config.tools.get(t, ToolConfig()).enabled]
            assert set(reports.keys()) == set(enabled_tools), \
                "并非所有启用的工具都被尝试安装"
            
            # 验证失败的工具有错误信息
            for tool_name in failed_tools:
                if tool_name in reports:
                    report = reports[tool_name]
                    assert report.result == InstallResult.FAILED, \
                        f"{tool_name} 应该标记为失败"
                    assert report.error is not None, \
                        f"{tool_name} 的失败报告应该包含错误信息"


class TestInstallSummaryCompleteness:
    """测试属性 6: 安装摘要完整性
    
    **Validates: Requirements 1.13, 5.14**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_summary_contains_all_tools(self, config, platform_info):
        """验证安装摘要包含所有工具的状态信息
        
        对于任何安装结果集合（成功、跳过、失败），最终摘要应该包含所有工具的状态信息。
        
        **Validates: Requirements 1.13, 5.14**
        """
        with patch.object(InstallOrchestrator, 'install_tool') as mock_install:
            # 模拟随机的安装结果
            def install_side_effect(tool_name):
                import random
                result = random.choice([InstallResult.SUCCESS, InstallResult.SKIPPED, InstallResult.FAILED])
                return InstallReport(
                    tool_name=tool_name,
                    result=result,
                    message=f"{tool_name} {result.value}",
                    version="1.0.0" if result != InstallResult.FAILED else None,
                    error="错误信息" if result == InstallResult.FAILED else None
                )
            
            mock_install.side_effect = install_side_effect
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.install_all_tools()
            
            # 验证所有启用的工具都在报告中
            enabled_tools = [t for t in INSTALL_ORDER if config.tools.get(t, ToolConfig()).enabled]
            assert set(reports.keys()) == set(enabled_tools), \
                "安装摘要缺少某些工具"
            
            # 验证每个报告都包含必要的信息
            for tool_name, report in reports.items():
                assert report.tool_name == tool_name, "工具名称不匹配"
                assert report.result in [InstallResult.SUCCESS, InstallResult.SKIPPED, InstallResult.FAILED], \
                    "安装结果无效"
                assert report.message, "缺少描述信息"
                
                # 如果失败，应该有错误信息
                if report.result == InstallResult.FAILED:
                    assert report.error is not None, f"{tool_name} 失败但没有错误信息"


class TestToolEnabledConfiguration:
    """测试属性 10: 工具启用配置生效
    
    **Validates: Requirements 4.6**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_disabled_tools_not_installed(self, config, platform_info):
        """验证禁用的工具不会被安装
        
        对于任何配置中 tools.<name>.enabled 设置为 false 的工具，
        安装编排器不应该尝试安装该工具。
        
        **Validates: Requirements 4.6**
        """
        orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
        install_order = orchestrator.get_install_order()
        
        # 验证禁用的工具不在安装顺序中
        for tool_name in INSTALL_ORDER:
            tool_config = config.tools.get(tool_name, ToolConfig())
            if not tool_config.enabled:
                assert tool_name not in install_order, \
                    f"禁用的工具 {tool_name} 不应该出现在安装顺序中"
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_only_enabled_tools_attempted(self, config, platform_info):
        """验证只有启用的工具被尝试安装
        
        **Validates: Requirements 4.6**
        """
        with patch.object(InstallOrchestrator, 'install_tool') as mock_install:
            mock_install.return_value = InstallReport(
                tool_name="test",
                result=InstallResult.SUCCESS,
                message="成功"
            )
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.install_all_tools()
            
            # 验证所有被安装的工具都是启用的
            for tool_name in reports.keys():
                tool_config = config.tools.get(tool_name, ToolConfig())
                assert tool_config.enabled, \
                    f"禁用的工具 {tool_name} 不应该被尝试安装"


class TestSingleToolUpgradeIsolation:
    """测试属性 11: 单工具升级隔离性
    
    **Validates: Requirements 5.4**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy(),
        target_tool=st.sampled_from(INSTALL_ORDER)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_single_tool_upgrade_only_affects_target(self, config, platform_info, target_tool):
        """验证单工具升级只影响目标工具
        
        对于任何指定的工具名称，执行 upgrade <tool-name> 应该仅升级该工具，
        不影响其他工具。
        
        **Validates: Requirements 5.4**
        """
        with patch.object(InstallOrchestrator, 'upgrade_tool') as mock_upgrade:
            mock_upgrade.return_value = InstallReport(
                tool_name=target_tool,
                result=InstallResult.SUCCESS,
                message=f"{target_tool} 升级成功",
                version="2.0.0"
            )
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.run_upgrade(tool_name=target_tool)
            
            # 验证只有目标工具被升级
            assert len(reports) == 1, "应该只升级一个工具"
            assert target_tool in reports, f"升级报告中缺少目标工具 {target_tool}"
            
            # 验证 upgrade_tool 只被调用一次，且参数正确
            mock_upgrade.assert_called_once_with(target_tool)


class TestErrorMessageCompleteness:
    """测试属性 12: 错误信息完整性
    
    **Validates: Requirements 6.5**
    """
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy(),
        # 随机选择一些工具失败
        failed_tools=st.sets(st.sampled_from(INSTALL_ORDER), min_size=1, max_size=3)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_error_reports_contain_tool_name_and_reason(self, config, platform_info, failed_tools):
        """验证错误报告包含工具名称和错误原因
        
        对于任何安装或升级过程中发生的错误，错误报告应该包含失败的工具名称和错误原因。
        
        **Validates: Requirements 6.5**
        """
        with patch.object(InstallOrchestrator, 'install_tool') as mock_install:
            # 模拟部分工具失败
            def install_side_effect(tool_name):
                if tool_name in failed_tools:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.FAILED,
                        message=f"{tool_name} 安装失败",
                        error=f"模拟错误: {tool_name} 无法安装"
                    )
                else:
                    return InstallReport(
                        tool_name=tool_name,
                        result=InstallResult.SUCCESS,
                        message=f"{tool_name} 安装成功"
                    )
            
            mock_install.side_effect = install_side_effect
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.install_all_tools()
            
            # 验证所有失败的工具都有完整的错误信息
            for tool_name in failed_tools:
                if tool_name in reports:
                    report = reports[tool_name]
                    
                    # 验证包含工具名称
                    assert report.tool_name == tool_name, \
                        "错误报告缺少工具名称"
                    
                    # 验证包含错误原因
                    assert report.error is not None, \
                        f"{tool_name} 的错误报告缺少错误原因"
                    assert len(report.error) > 0, \
                        f"{tool_name} 的错误原因为空"
                    
                    # 验证消息不为空
                    assert report.message, \
                        f"{tool_name} 的错误报告缺少描述信息"
    
    @given(
        config=config_strategy(),
        platform_info=platform_info_strategy(),
        failed_tool=st.sampled_from(INSTALL_ORDER)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
    def test_upgrade_error_reports_complete(self, config, platform_info, failed_tool):
        """验证升级错误报告的完整性
        
        **Validates: Requirements 6.5**
        """
        with patch.object(InstallOrchestrator, 'upgrade_tool') as mock_upgrade:
            mock_upgrade.return_value = InstallReport(
                tool_name=failed_tool,
                result=InstallResult.FAILED,
                message=f"{failed_tool} 升级失败",
                error=f"升级错误: {failed_tool} 版本不兼容"
            )
            
            orchestrator = InstallOrchestrator(config, platform_info, dry_run=False)
            reports = orchestrator.run_upgrade(tool_name=failed_tool)
            
            # 验证错误报告完整
            assert failed_tool in reports, "升级报告中缺少失败的工具"
            report = reports[failed_tool]
            
            assert report.tool_name == failed_tool, "工具名称不匹配"
            assert report.result == InstallResult.FAILED, "应该标记为失败"
            assert report.error is not None, "缺少错误原因"
            assert len(report.error) > 0, "错误原因为空"
            assert report.message, "缺少描述信息"
