# Mono-Kickstart

Mono-Kickstart 是一个 Monorepo 项目模板脚手架 CLI 工具，通过一条命令快速初始化标准化的 Monorepo 工程，自动完成开发环境搭建与工具链安装，让开发者开箱即用。

## 特性

- 🚀 **一键初始化**: 一条命令完成 Monorepo 项目创建和开发环境配置
- 🛠️ **自动化工具链**: 自动检测和安装 NVM、Node.js、Conda、Bun、uv 等开发工具
- 🤖 **AI 编程助手**: 自动安装 Claude Code CLI、Codex CLI、Spec Kit、BMad Method
- 🌏 **中国镜像源**: 自动配置 npm、Bun、PyPI 镜像源，加速下载
- 🔄 **幂等性**: 可安全重复执行，不产生副作用
- 💪 **容错性**: 单个工具失败不影响整体流程
- ⚙️ **可配置**: 支持配置文件和命令行参数灵活定制
- 🌐 **跨平台**: 支持 macOS（ARM64/x86_64）和 Linux（x86_64）

## 安装

### 使用 uv（推荐）

```bash
uv tool install mono-kickstart
```

### 使用 pip

```bash
pip install mono-kickstart
```

### 一次性执行（无需安装）

```bash
uvx mono-kickstart init
```

## 快速开始

### 初始化新项目

```bash
mk init
```

或使用完整命令名：

```bash
mono-kickstart init
```

### 交互式配置

```bash
mk init --interactive
```

### 使用配置文件

```bash
mk init --config .kickstartrc
```

### 保存配置

```bash
mk init --save-config
```

## 升级工具

### 升级所有工具

```bash
mk upgrade --all
```

### 升级特定工具

```bash
mk upgrade node
mk upgrade bun
```

## 配置文件

配置文件使用 YAML 格式，支持三个位置（按优先级）：

1. 命令行指定: `--config <path>`
2. 项目配置: `.kickstartrc`
3. 用户配置: `~/.kickstartrc`

### 配置示例

```yaml
project:
  name: my-monorepo

tools:
  nvm:
    enabled: true
  node:
    enabled: true
    version: lts
  conda:
    enabled: true
  bun:
    enabled: true
  uv:
    enabled: true
  claude-code:
    enabled: true
  codex:
    enabled: true
    install_via: bun
  spec-kit:
    enabled: true
  bmad-method:
    enabled: true

registry:
  npm: https://registry.npmmirror.com/
  bun: https://registry.npmmirror.com/
  pypi: https://mirrors.sustech.edu.cn/pypi/web/simple
  python_install: https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download
```

## 支持的工具

- **NVM**: Node Version Manager
- **Node.js**: JavaScript 运行时
- **Conda**: Python 环境和包管理
- **Bun**: 高性能 JavaScript 运行时
- **uv**: Rust 编写的 Python 包管理器
- **Claude Code CLI**: Anthropic AI 编程助手
- **Codex CLI**: OpenAI AI 编程助手
- **Spec Kit**: 规格驱动开发工具包
- **BMad Method**: AI 驱动的敏捷开发框架

## 命令参考

### init 命令

```bash
mk init [OPTIONS]
```

选项：
- `--config PATH`: 指定配置文件路径
- `--save-config`: 保存配置到项目 .kickstartrc
- `--interactive`: 交互式配置
- `--force`: 强制覆盖已有配置
- `--dry-run`: 模拟运行，不实际安装
- `--help`: 显示帮助信息

### upgrade 命令

```bash
mk upgrade [TOOL] [OPTIONS]
```

参数：
- `TOOL`: 要升级的工具名称（可选）

选项：
- `--all`: 升级所有工具
- `--dry-run`: 模拟运行，不实际升级
- `--help`: 显示帮助信息

### 其他命令

```bash
mk --version              # 显示版本号
mk --help                 # 显示帮助信息
mk --install-completion   # 安装 Shell 自动补全
mk --show-completion      # 显示补全脚本
```

## 平台支持

- macOS ARM64 (Apple Silicon)
- macOS x86_64 (Intel)
- Linux x86_64

## 要求

- Python 3.11 或更高版本

## 开发

### 克隆仓库

```bash
git clone https://github.com/mono-kickstart/mono-kickstart.git
cd mono-kickstart
```

### 安装开发依赖

```bash
uv pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 运行测试并生成覆盖率报告

```bash
pytest --cov=mono_kickstart --cov-report=html
```

## 许可证

MIT License

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 问题反馈

如有问题或建议，请在 [GitHub Issues](https://github.com/mono-kickstart/mono-kickstart/issues) 提交。
