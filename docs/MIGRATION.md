# CLI 框架迁移指南

## 从 Typer 到 argparse

本文档记录了 Mono-Kickstart CLI 从 Typer 框架迁移到 Python 标准库 argparse 的过程和原因。

## 迁移原因

1. **减少依赖**: argparse 是 Python 标准库的一部分，无需额外安装依赖
2. **更轻量**: 移除了 `typer` 和 `rich` 依赖，减小了包体积
3. **更好的控制**: 对 CLI 行为有更精细的控制
4. **中文化支持**: 更容易自定义中文帮助信息格式

## 主要变更

### 1. 依赖变更

**移除的依赖**:
- `typer>=0.9.0`
- `rich>=13.0.0` (Typer 的依赖)

**保留的依赖**:
- `pyyaml>=6.0`
- `questionary>=2.0.0`
- `requests>=2.31.0`

### 2. CLI 实现变更

#### 命令定义

**之前 (Typer)**:
```python
import typer

app = typer.Typer()

@app.command()
def init(
    config: Optional[str] = typer.Option(None, "--config"),
    save_config: bool = typer.Option(False, "--save-config"),
):
    pass
```

**现在 (argparse)**:
```python
import argparse

def create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    
    init_parser = subparsers.add_parser('init')
    init_parser.add_argument('--config', type=str)
    init_parser.add_argument('--save-config', action='store_true')
    
    return parser
```

#### 入口点

**之前**:
```toml
[project.scripts]
mk = "mono_kickstart.cli:app"
```

**现在**:
```toml
[project.scripts]
mk = "mono_kickstart.cli:main"
```

### 3. Shell 补全变更

#### 安装方式

**之前 (Typer 自动生成)**:
```bash
mk --install-completion
mk --show-completion
```

**现在 (自定义脚本)**:
```bash
mk setup-shell
```

#### 实现方式

- **之前**: Typer 自动生成补全脚本
- **现在**: 手动编写 Bash/Zsh/Fish 补全脚本，存储在 `shell_completion.py` 模块中

### 4. 帮助信息

#### 中文化

**之前**: 使用 Typer 的 `rich_utils` 模块修改面板标题

**现在**: 使用自定义的 `ChineseHelpFormatter` 类

```python
class ChineseHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = '用法: '
        return super()._format_usage(usage, actions, groups, prefix)
```

## 功能对比

| 功能 | Typer | argparse | 状态 |
|------|-------|----------|------|
| 子命令 | ✅ | ✅ | ✅ 保持 |
| 选项参数 | ✅ | ✅ | ✅ 保持 |
| 位置参数 | ✅ | ✅ | ✅ 保持 |
| 帮助信息 | ✅ | ✅ | ✅ 保持 |
| 版本信息 | ✅ | ✅ | ✅ 保持 |
| Shell 补全 | ✅ 自动 | ✅ 手动 | ✅ 保持 |
| 中文化 | ⚠️ 部分 | ✅ 完全 | ✅ 改进 |
| 彩色输出 | ✅ Rich | ❌ | ⚠️ 移除 |

## 用户影响

### 对最终用户

**无影响** - 所有命令和参数保持不变：

```bash
# 所有这些命令仍然有效
mk init
mk init --config .kickstartrc
mk upgrade --all
mk upgrade node
mk install bun
mk --version
mk --help
```

**唯一变更**: Shell 补全安装方式

```bash
# 之前
mk --install-completion

# 现在
mk setup-shell
```

### 对开发者

1. **测试框架变更**: 从 `typer.testing.CliRunner` 改为使用 `unittest.mock` 和 `subprocess`
2. **无需 Typer 依赖**: 开发环境更轻量
3. **更容易调试**: argparse 的行为更透明

## 测试覆盖

迁移后的测试覆盖情况：

- **总测试数**: 126 个
- **通过率**: 100%
- **代码覆盖率**: 85%

### 测试模块

1. `test_cli.py` - CLI 命令和参数解析测试 (22 个测试)
2. `test_shell_completion.py` - Shell 补全脚本测试 (15 个测试)
3. `test_entry_points.py` - 命令入口点测试 (6 个测试)
4. `test_config.py` - 配置管理测试 (33 个测试)
5. `test_platform_detector.py` - 平台检测测试 (33 个测试)
6. `test_config_properties.py` - 配置属性测试 (11 个测试)
7. `test_platform_detector_properties.py` - 平台检测属性测试 (6 个测试)

## 迁移清单

- [x] 重写 `cli.py` 使用 argparse
- [x] 创建 `shell_completion.py` 模块
- [x] 创建自定义补全脚本（Bash/Zsh/Fish）
- [x] 更新 `pyproject.toml` 移除 Typer 依赖
- [x] 更新入口点配置
- [x] 创建 `__main__.py` 支持 `python -m` 执行
- [x] 重写所有 CLI 测试
- [x] 创建 Shell 补全测试
- [x] 更新 README.md
- [x] 创建 CHANGELOG.md
- [x] 验证所有测试通过
- [x] 验证代码覆盖率 >80%

## 后续工作

1. 实现核心功能模块（工具检测、安装器、编排器）
2. 集成所有模块到 CLI
3. 完善错误处理和日志记录
4. 添加集成测试
5. 完善文档

## 参考资料

- [argparse 官方文档](https://docs.python.org/3/library/argparse.html)
- [Bash 补全编程指南](https://www.gnu.org/software/bash/manual/html_node/Programmable-Completion.html)
- [Zsh 补全系统](https://zsh.sourceforge.io/Doc/Release/Completion-System.html)
- [Fish 补全教程](https://fishshell.com/docs/current/completions.html)
