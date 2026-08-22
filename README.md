# Mono-Kickstart

Mono-Kickstart 是一个 Monorepo 项目模板脚手架 CLI 工具，通过一条命令快速初始化标准化的 Monorepo 工程，自动完成开发环境搭建与工具链安装，让开发者开箱即用。

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [详细使用指南](#详细使用指南)
- [配置文件](#配置文件)
- [支持的工具](#支持的工具)
- [命令参考](#命令参考)
- [常见问题](#常见问题)
- [平台支持](#平台支持)
- [开发](#开发)

## 特性

- 🚀 **一键初始化**: 一条命令完成 Monorepo 项目创建和开发环境配置
- 🛠️ **自动化工具链**: 自动检测和安装 NVM、Node.js、Conda、Bun、uv 等开发工具
- 🤖 **AI 编程助手**: 自动安装 Claude Code CLI、GitHub Copilot CLI、Codex CLI、Spec Kit、BMad Method
- 🌏 **中国镜像源**: 自动配置 npm、Bun、PyPI 镜像源，加速下载
- 🔄 **幂等性**: 可安全重复执行，不产生副作用
- 💪 **容错性**: 单个工具失败不影响整体流程
- ⚙️ **可配置**: 支持配置文件和命令行参数灵活定制
- 🌐 **跨平台**: 支持 macOS（ARM64/x86_64）和 Linux（x86_64）

## 安装

### 系统要求

- **Python**: 3.11 或更高版本
- **操作系统**: macOS (ARM64/x86_64) 或 Linux (x86_64)
- **网络**: 需要互联网连接以下载工具和依赖

### 使用 uv（推荐）

```bash
# 安装 mono-kickstart
uv tool install mono-kickstart

# 验证安装
mk --version
```

### 使用 pip

```bash
# 安装 mono-kickstart
pip install mono-kickstart

# 验证安装
mk --version
```

### 一次性执行（无需安装）

如果您只想临时使用而不想持久安装，可以使用 `uvx`：

```bash
uvx mono-kickstart init
```

### 配置 Shell 环境

安装完成后，建议运行以下命令配置 Shell 环境（PATH 和 Tab 补全）：

```bash
mk setup-shell
```

这将：
- 配置 PATH 环境变量
- 安装 Shell 自动补全脚本（支持 Bash、Zsh、Fish）
- 自动检测当前 Shell 类型并应用配置

配置完成后，重新加载 Shell 配置：

```bash
# Bash
source ~/.bashrc

# Zsh
source ~/.zshrc

# Fish
source ~/.config/fish/config.fish
```

## 快速开始

### 最简单的使用方式

```bash
# 1. 创建项目目录
mkdir my-monorepo
cd my-monorepo

# 2. 初始化项目和开发环境
mk init

# 3. 等待安装完成，开始开发！
```

这将：
1. 检测并安装所需的开发工具（NVM、Node.js、Conda、Bun、uv 等）
2. 配置中国镜像源（加速下载）
3. 安装 AI 编程助手（Claude Code CLI、GitHub Copilot CLI、Codex CLI、Spec Kit、BMad Method）
4. 创建标准化的 Monorepo 项目结构

> **注意**: 
> - GitHub Copilot CLI 需要 Node.js 22 或更高版本，且仅支持 macOS 和 Linux 平台
> - 安装完成后，需要运行 `copilot auth login` 进行 GitHub 认证才能使用

### 使用交互式配置

如果您想自定义安装选项，可以使用交互式模式：

```bash
mk init --interactive
```

交互式模式将询问：
- 项目名称
- 要安装的工具（可多选）
- Node.js 版本选项
- Python 版本选项
- 是否配置中国镜像源

### 使用配置文件

对于团队协作，推荐使用配置文件：

```bash
# 1. 创建配置文件
cat > .kickstartrc << 'EOF'
project:
  name: my-monorepo

tools:
  nvm:
    enabled: true
  node:
    enabled: true
    version: lts
  bun:
    enabled: true
  uv:
    enabled: true
  claude-code:
    enabled: true
  copilot-cli:
    enabled: true
  codex:
    enabled: false  # 不安装 Codex
  spec-kit:
    enabled: true
  bmad-method:
    enabled: true

registry:
  npm: https://registry.npmmirror.com/
  pypi: https://mirrors.sustech.edu.cn/pypi/web/simple
EOF

# 2. 使用配置文件初始化
mk init --config .kickstartrc

# 3. 保存当前配置供后续使用
mk init --save-config
```

## 详细使用指南

### 初始化项目

#### 基本用法

```bash
mk init
```

#### 高级选项

```bash
# 使用指定配置文件
mk init --config /path/to/config.yaml

# 交互式配置
mk init --interactive

# 保存配置到项目目录
mk init --save-config

# 强制覆盖已有配置
mk init --force

# 模拟运行（不实际安装）
mk init --dry-run
```

### 升级工具

#### 升级所有工具

```bash
mk upgrade --all
```

#### 升级特定工具

```bash
# 升级 Node.js
mk upgrade node

# 升级 Bun
mk upgrade bun

# 升级 uv
mk upgrade uv

# 升级 Claude Code CLI
mk upgrade claude-code
```

#### 查看可升级的工具

```bash
# 模拟运行，查看哪些工具可以升级
mk upgrade --all --dry-run
```

### 安装单个工具

如果您只想安装特定工具而不是全部：

```bash
# 安装 Bun
mk install bun

# 安装 Claude Code CLI
mk install claude-code

# 安装所有工具
mk install --all
```

### 检查工具状态

```bash
# 查看已安装的工具及其版本
mk status
```

## 配置文件

配置文件使用 YAML 格式，支持三个位置（按优先级从高到低）：

1. **命令行指定**: `--config <path>`
2. **项目配置**: `.kickstartrc`（项目根目录）
3. **用户配置**: `~/.kickstartrc`（用户主目录）

配置文件采用合并策略：高优先级配置覆盖低优先级配置，未指定的字段使用低优先级的值。

### 完整配置示例

```yaml
# 项目配置
project:
  name: my-monorepo  # 项目名称

# 工具配置
tools:
  # NVM (Node Version Manager)
  nvm:
    enabled: true  # 是否安装
    version: v0.40.4  # 指定版本（可选）
  
  # Node.js
  node:
    enabled: true
    version: lts  # lts, latest, 或指定版本号如 20.10.0
  
  # Conda (Python 环境管理)
  conda:
    enabled: true
  
  # Bun (JavaScript 运行时)
  bun:
    enabled: true
  
  # uv (Python 包管理器)
  uv:
    enabled: true
  
  # Claude Code CLI (Anthropic AI 助手)
  claude-code:
    enabled: true
  
  # GitHub Copilot CLI (GitHub AI 助手)
  # 注意：需要 Node.js 22 或更高版本，仅支持 macOS 和 Linux
  copilot-cli:
    enabled: true
  
  # Codex CLI (OpenAI AI 助手)
  codex:
    enabled: true
    install_via: bun  # bun 或 npm
  
  # Spec Kit (规格驱动开发工具)
  spec-kit:
    enabled: true
  
  # BMad Method (AI 敏捷开发框架)
  bmad-method:
    enabled: true

# 镜像源配置（中国大陆加速）
registry:
  # npm 镜像源
  npm: https://registry.npmmirror.com/
  
  # Bun 镜像源
  bun: https://registry.npmmirror.com/
  
  # PyPI 镜像源
  pypi: https://mirrors.sustech.edu.cn/pypi/web/simple
  
  # Python 安装包下载代理
  python_install: https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download
```

### 最小配置示例

如果您只想安装部分工具：

```yaml
tools:
  node:
    enabled: true
  bun:
    enabled: true
  uv:
    enabled: true
  
  # 禁用其他工具
  conda:
    enabled: false
  claude-code:
    enabled: false
  copilot-cli:
    enabled: false
  codex:
    enabled: false
  spec-kit:
    enabled: false
  bmad-method:
    enabled: false
```

### 配置字段说明

#### project 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `name` | string | 项目名称 | 当前目录名 |

#### tools 配置

每个工具支持以下字段：

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enabled` | boolean | 是否安装该工具 | true |
| `version` | string | 指定版本（可选） | 最新版本 |
| `install_via` | string | 安装方式（部分工具支持） | 自动选择 |
| `extra_options` | object | 额外选项（工具特定） | {} |

#### registry 配置

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `npm` | string | npm 镜像源 URL | https://registry.npmmirror.com/ |
| `bun` | string | Bun 镜像源 URL | https://registry.npmmirror.com/ |
| `pypi` | string | PyPI 镜像源 URL | https://mirrors.sustech.edu.cn/pypi/web/simple |
| `python_install` | string | Python 下载代理 URL | https://ghfast.top/... |

### 配置文件管理

#### 保存当前配置

```bash
# 保存到项目目录
mk init --save-config

# 保存到指定位置
mk init --config /path/to/config.yaml --save-config
```

#### 验证配置文件

```bash
# 使用 dry-run 模式验证配置
mk init --config .kickstartrc --dry-run
```

#### 配置文件优先级示例

假设有以下配置文件：

**~/.kickstartrc** (用户配置):
```yaml
tools:
  node:
    enabled: true
    version: lts
  bun:
    enabled: true
```

**.kickstartrc** (项目配置):
```yaml
tools:
  node:
    version: 20.10.0  # 覆盖用户配置的版本
  codex:
    enabled: false
```

**命令行**:
```bash
mk init --config custom.yaml
```

最终生效的配置优先级：
1. `custom.yaml` 中的配置（最高优先级）
2. `.kickstartrc` 中的配置
3. `~/.kickstartrc` 中的配置
4. 默认配置（最低优先级）

## 支持的工具

Mono-Kickstart 支持自动安装和配置以下开发工具：

### 核心工具

#### NVM (Node Version Manager)
- **用途**: Node.js 版本管理工具
- **版本**: v0.40.4
- **安装方式**: 下载并执行官方安装脚本
- **验证**: `nvm --version`
- **配置**: 自动写入 Shell 配置文件（~/.bashrc, ~/.zshrc 等）

#### Node.js
- **用途**: JavaScript 运行时环境
- **版本**: LTS（长期支持版本）或指定版本
- **安装方式**: 通过 NVM 安装
- **验证**: `node --version`
- **依赖**: 需要先安装 NVM

#### Conda (Miniconda)
- **用途**: Python 环境和包管理系统
- **版本**: 最新版本
- **安装方式**: 下载并执行官方安装脚本
- **验证**: `conda --version`
- **平台**: 根据操作系统和架构自动选择安装包

#### Bun
- **用途**: 高性能 JavaScript 运行时和包管理器
- **版本**: 最新版本
- **安装方式**: 执行官方安装脚本
- **验证**: `bun --version`
- **特性**: 比 npm 更快的包管理和脚本执行

#### uv
- **用途**: Rust 编写的高性能 Python 包管理器
- **版本**: 最新版本
- **安装方式**: 执行官方安装脚本
- **验证**: `uv --version`
- **特性**: 比 pip 快 10-100 倍

### AI 编程助手

#### Claude Code CLI
- **用途**: Anthropic 提供的 AI 编程助手命令行工具
- **版本**: stable 渠道
- **安装方式**: 原生二进制安装
- **验证**: `claude doctor`
- **特性**: 强大的代码理解和生成能力

#### GitHub Copilot CLI
- **用途**: GitHub 提供的 AI 命令行助手
- **版本**: 最新版本
- **安装方式**: 通过 npm 全局安装 (`npm install -g @github/copilot`)
- **验证**: `copilot --version`
- **依赖**: 需要 Node.js 22 或更高版本
- **平台**: 仅支持 macOS 和 Linux（不支持 Windows）
- **特性**: AI 驱动的命令行建议和代码生成
- **认证**: 安装后需要运行 `copilot auth login` 进行 GitHub 认证
- **配置**: 可通过配置文件的 `copilot-cli.enabled` 字段控制是否安装

#### Codex CLI
- **用途**: OpenAI 提供的 AI 编程助手命令行工具
- **版本**: 最新版本
- **安装方式**: 优先使用 Bun，否则使用 npm
- **验证**: `codex --version`
- **依赖**: 需要 Node.js 或 Bun

#### Spec Kit
- **用途**: GitHub 开源的规格驱动开发工具包
- **版本**: 最新版本
- **安装方式**: 通过 uv tool install 从 GitHub 安装
- **验证**: `specify --version`
- **依赖**: 需要 uv

#### BMad Method
- **用途**: AI 驱动的敏捷开发框架
- **版本**: 最新版本
- **安装方式**: 通过 npx/bunx 交互式安装
- **验证**: 检查项目中的 BMad 配置文件
- **依赖**: 需要 Node.js 或 Bun

### 镜像源配置

为了加速中国大陆地区的下载速度，Mono-Kickstart 会自动配置以下镜像源：

#### npm 镜像源
- **默认**: 淘宝 npmmirror (https://registry.npmmirror.com/)
- **配置文件**: npm 全局配置
- **验证**: `npm get registry`

#### Bun 镜像源
- **默认**: 淘宝 npmmirror (https://registry.npmmirror.com/)
- **配置文件**: `~/.bunfig.toml`
- **验证**: 检查配置文件内容

#### PyPI 镜像源
- **默认**: 南方科技大学镜像 (https://mirrors.sustech.edu.cn/pypi/web/simple)
- **配置文件**: `~/.config/uv/uv.toml`
- **验证**: 检查配置文件内容

#### Python 安装包代理
- **默认**: ghfast.top 代理
- **用途**: 加速 Python 解释器下载
- **配置文件**: `~/.config/uv/uv.toml`

### 工具安装顺序

工具按照以下依赖顺序安装：

1. **NVM** - 首先安装 Node 版本管理器
2. **Node.js** - 通过 NVM 安装
3. **Conda** - 独立安装
4. **Bun** - 独立安装
5. **npm 镜像源** - 配置 npm 镜像
6. **Bun 镜像源** - 配置 Bun 镜像
7. **uv** - 独立安装
8. **uv 镜像源** - 配置 uv 镜像
9. **Claude Code CLI** - 独立安装
10. **GitHub Copilot CLI** - 依赖 Node.js 22+
11. **Codex CLI** - 依赖 Bun 或 Node.js
12. **Spec Kit** - 依赖 uv
13. **BMad Method** - 依赖 Node.js 或 Bun

## 命令参考

### 全局选项

```bash
mk --version              # 显示版本号
mk --help                 # 显示帮助信息
```

### init 命令

初始化 Monorepo 项目和开发环境。

```bash
mk init [OPTIONS]
```

#### 选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `--config PATH` | string | 指定配置文件路径 |
| `--save-config` | flag | 保存配置到项目 .kickstartrc |
| `--interactive` | flag | 交互式配置模式 |
| `--force` | flag | 强制覆盖已有配置 |
| `--dry-run` | flag | 模拟运行，不实际安装 |
| `--help` | flag | 显示帮助信息 |

#### 示例

```bash
# 基本用法
mk init

# 使用配置文件
mk init --config .kickstartrc

# 交互式配置
mk init --interactive

# 保存配置
mk init --save-config

# 强制覆盖
mk init --force

# 模拟运行
mk init --dry-run

# 组合使用
mk init --interactive --save-config
```

### upgrade 命令

升级已安装的开发工具。

```bash
mk upgrade [TOOL] [OPTIONS]
```

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `TOOL` | string | 要升级的工具名称（可选） |

#### 选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `--all` | flag | 升级所有工具 |
| `--dry-run` | flag | 模拟运行，不实际升级 |
| `--help` | flag | 显示帮助信息 |

#### 支持的工具名称

- `nvm` - Node Version Manager
- `node` - Node.js
- `conda` - Conda
- `bun` - Bun
- `uv` - uv
- `claude-code` - Claude Code CLI
- `copilot-cli` - GitHub Copilot CLI
- `codex` - Codex CLI
- `spec-kit` - Spec Kit
- `bmad-method` - BMad Method

#### 示例

```bash
# 升级所有工具
mk upgrade --all

# 升级特定工具
mk upgrade node
mk upgrade bun
mk upgrade copilot-cli

# 模拟运行
mk upgrade --all --dry-run

# 查看可升级的工具
mk upgrade --dry-run
```

### install 命令

安装单个或多个开发工具。

```bash
mk install [TOOL] [OPTIONS]
```

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `TOOL` | string | 要安装的工具名称（可选） |

#### 选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `--all` | flag | 安装所有工具 |
| `--dry-run` | flag | 模拟运行，不实际安装 |
| `--help` | flag | 显示帮助信息 |

#### 示例

```bash
# 安装所有工具
mk install --all

# 安装特定工具
mk install bun
mk install copilot-cli
mk install claude-code

# 模拟运行
mk install --all --dry-run
```

### setup-shell 命令

配置 Shell 环境（PATH 和 Tab 补全）。

```bash
mk setup-shell
```

这将：
1. 检测当前 Shell 类型（Bash、Zsh、Fish）
2. 配置 PATH 环境变量
3. 安装 Shell 自动补全脚本
4. 更新 Shell 配置文件

#### 支持的 Shell

- **Bash**: `~/.bashrc`
- **Zsh**: `~/.zshrc`
- **Fish**: `~/.config/fish/config.fish`

#### 示例

```bash
# 配置当前 Shell
mk setup-shell

# 配置完成后重新加载 Shell
source ~/.bashrc  # Bash
source ~/.zshrc   # Zsh
```

### status 命令

查看已安装工具的状态和版本。

```bash
mk status
```

这将显示：
- 工具名称
- 安装状态（已安装/未安装）
- 当前版本
- 安装路径

#### 示例

```bash
mk status
```

输出示例：
```
工具状态:
✓ NVM         v0.40.4    ~/.nvm
✓ Node.js     v20.10.0   ~/.nvm/versions/node/v20.10.0
✓ Conda       24.1.2     ~/miniconda3
✓ Bun         1.0.25     ~/.bun
✓ uv          0.1.15     ~/.cargo/bin/uv
✓ Claude Code 1.2.0      /usr/local/bin/claude
✗ Codex       未安装
✓ Spec Kit    0.5.0      ~/.local/bin/specify
✓ BMad Method 已配置     ./bmad
```

## 常见问题

### 安装相关

#### Q: 安装失败怎么办？

A: Mono-Kickstart 具有容错性，单个工具失败不会影响其他工具的安装。您可以：

1. 查看错误信息，了解失败原因
2. 检查网络连接
3. 重新运行 `mk init`（幂等性保证安全）
4. 使用 `mk install <tool>` 单独安装失败的工具
5. 查看日志文件：`~/.mono-kickstart/logs/`

#### Q: 如何跳过某些工具的安装？

A: 使用配置文件禁用不需要的工具：

```yaml
tools:
  codex:
    enabled: false
  bmad-method:
    enabled: false
```

然后运行：
```bash
mk init --config .kickstartrc
```

#### Q: 安装需要多长时间？

A: 取决于网络速度和要安装的工具数量，通常：
- 中国大陆（使用镜像源）：3-5 分钟
- 国际网络：5-10 分钟

#### Q: 可以重复运行 init 命令吗？

A: 可以！Mono-Kickstart 具有幂等性，重复执行不会产生副作用。已安装的工具会被跳过，配置文件不会被覆盖（除非使用 `--force`）。

### 配置相关

#### Q: 配置文件放在哪里？

A: 配置文件支持三个位置（按优先级）：
1. 命令行指定：`--config <path>`
2. 项目配置：`.kickstartrc`（项目根目录）
3. 用户配置：`~/.kickstartrc`（用户主目录）

#### Q: 如何为团队创建统一配置？

A: 在项目根目录创建 `.kickstartrc` 文件并提交到 Git：

```bash
# 1. 创建配置文件
mk init --interactive --save-config

# 2. 提交到 Git
git add .kickstartrc
git commit -m "Add mono-kickstart config"

# 3. 团队成员克隆后直接运行
mk init
```

#### Q: 如何修改镜像源？

A: 在配置文件中指定自定义镜像源：

```yaml
registry:
  npm: https://registry.npmjs.org/  # 使用官方源
  pypi: https://pypi.org/simple     # 使用官方源
```

### 工具相关

#### Q: 如何升级已安装的工具？

A: 使用 upgrade 命令：

```bash
# 升级所有工具
mk upgrade --all

# 升级特定工具
mk upgrade node
mk upgrade bun
```

#### Q: 如何卸载工具？

A: Mono-Kickstart 不提供卸载功能，但您可以手动卸载：

- **NVM**: `rm -rf ~/.nvm`
- **Node.js**: `nvm uninstall <version>`
- **Conda**: `rm -rf ~/miniconda3`
- **Bun**: `rm -rf ~/.bun`
- **uv**: `rm ~/.cargo/bin/uv`
- **Claude Code**: 参考官方文档
- **GitHub Copilot CLI**: `npm uninstall -g @github/copilot`
- **Codex**: `npm uninstall -g codex` 或 `bun remove -g codex`
- **Spec Kit**: `uv tool uninstall specify-cli`

#### Q: 工具安装在哪里？

A: 各工具的默认安装位置：
- **NVM**: `~/.nvm`
- **Node.js**: `~/.nvm/versions/node/`
- **Conda**: `~/miniconda3`
- **Bun**: `~/.bun`
- **uv**: `~/.cargo/bin/`
- **Claude Code**: `/usr/local/bin/` 或 `~/.local/bin/`
- **GitHub Copilot CLI**: npm 全局目录（通常为 `~/.nvm/versions/node/<version>/bin/`）
- **Codex**: npm/bun 全局目录
- **Spec Kit**: `~/.local/bin/`

#### Q: GitHub Copilot CLI 有什么特殊要求？

A: GitHub Copilot CLI 有以下特殊要求：

**Node.js 版本要求**:
- 需要 Node.js 22 或更高版本
- 如果您的 Node.js 版本过低，请先升级：
  ```bash
  nvm install 22
  nvm use 22
  ```

**平台限制**:
- ✅ 支持 macOS（ARM64 和 x86_64）
- ✅ 支持 Linux（x86_64）
- ❌ 不支持 Windows

**安装方式**:
- 通过 npm 全局安装：`npm install -g @github/copilot`
- 安装后需要登录：`copilot auth login`

**使用前准备**:
1. 确保您有 GitHub Copilot 订阅（个人版或企业版）
2. 安装完成后运行认证命令：
   ```bash
   copilot auth login
   ```
3. 按照提示在浏览器中完成 GitHub 认证

**基本使用**:
```bash
# 获取命令建议
copilot suggest "list all files"

# 解释命令
copilot explain "git rebase -i HEAD~3"

# 交互式会话
copilot
```

**配置示例**:
```yaml
tools:
  node:
    enabled: true
    version: 22  # 或 lts（如果 LTS 版本 >= 22）
  copilot-cli:
    enabled: true
```

**常见问题**:
- 如果安装失败，检查 Node.js 版本是否满足要求
- 如果在不支持的平台上尝试安装，系统会返回错误信息
- 如果认证失败，确保您有有效的 GitHub Copilot 订阅

**升级**:
```bash
# 升级到最新版本
mk upgrade copilot-cli

# 或手动升级
npm update -g @github/copilot
```

### 平台相关

#### Q: 支持 Windows 吗？

A: 目前不支持 Windows。支持的平台：
- macOS ARM64 (Apple Silicon)
- macOS x86_64 (Intel)
- Linux x86_64

#### Q: 支持 ARM Linux 吗？

A: 目前不支持 ARM Linux（如 Raspberry Pi）。仅支持 x86_64 架构的 Linux。

#### Q: 如何检查平台兼容性？

A: 运行 `mk init`，工具会自动检测平台并提示是否支持。

### 网络相关

#### Q: 下载速度很慢怎么办？

A: 如果您在中国大陆：
1. 确保配置了镜像源（默认已配置）
2. 检查配置文件中的 `registry` 部分
3. 尝试更换镜像源

如果您在国际网络：
1. 检查网络连接
2. 考虑使用代理
3. 可以禁用镜像源配置

#### Q: 需要代理吗？

A: 通常不需要。如果您在中国大陆，工具会自动配置镜像源。如果您需要使用代理：

```bash
# 设置代理环境变量
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# 然后运行 init
mk init
```

### 错误处理

#### Q: 遇到权限错误怎么办？

A: 某些工具可能需要写入权限：

```bash
# 确保有写入权限
chmod +w ~/.bashrc ~/.zshrc

# 或者使用 sudo（不推荐）
sudo mk init
```

#### Q: Python 版本不满足要求怎么办？

A: Mono-Kickstart 需要 Python 3.11+：

```bash
# 检查 Python 版本
python --version

# 升级 Python（使用 uv）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.11

# 或使用 Conda
conda install python=3.11
```

#### Q: 如何查看详细日志？

A: 日志文件位于：`~/.mono-kickstart/logs/mk-<timestamp>.log`

```bash
# 查看最新日志
ls -lt ~/.mono-kickstart/logs/ | head -1
cat ~/.mono-kickstart/logs/mk-*.log
```

### 其他问题

#### Q: 如何贡献代码？

A: 欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

#### Q: 如何报告 Bug？

A: 请在 [GitHub Issues](https://github.com/mono-kickstart/mono-kickstart/issues) 提交问题，包括：
- 操作系统和版本
- Python 版本
- 错误信息
- 日志文件内容

#### Q: 有社区支持吗？

A: 是的！您可以：
- 在 GitHub Issues 提问
- 查看文档和示例
- 参与讨论和贡献

## 平台支持

### 支持的平台

- ✅ **macOS ARM64** (Apple Silicon - M1, M2, M3 等)
- ✅ **macOS x86_64** (Intel)
- ✅ **Linux x86_64** (Ubuntu, Debian, CentOS, Fedora 等)

### 不支持的平台

- ❌ Windows
- ❌ Linux ARM64 (Raspberry Pi 等)
- ❌ 其他架构

### 系统要求

- **Python**: 3.11 或更高版本
- **磁盘空间**: 至少 2GB 可用空间
- **内存**: 至少 2GB RAM
- **网络**: 需要互联网连接

### Shell 支持

- ✅ **Bash** (默认)
- ✅ **Zsh** (macOS 默认)
- ✅ **Fish**
- ⚠️ 其他 Shell 可能需要手动配置

## 项目结构

运行 `mk init` 后，将创建以下标准化的 Monorepo 项目结构：

```
my-monorepo/
├── .kickstartrc          # 项目配置文件
├── .gitignore            # Git 忽略文件
├── README.md             # 项目说明文档
├── package.json          # Node.js workspace 配置
├── pnpm-workspace.yaml   # pnpm workspace 配置（可选）
├── apps/                 # 应用目录
│   ├── .gitkeep
│   ├── web/              # 示例：Web 应用
│   └── api/              # 示例：API 服务
├── packages/             # 共享包目录
│   ├── .gitkeep
│   ├── ui/               # 示例：UI 组件库
│   ├── utils/            # 示例：工具函数库
│   └── types/            # 示例：TypeScript 类型定义
└── shared/               # 共享资源目录
    ├── .gitkeep
    ├── config/           # 共享配置
    └── assets/           # 共享资源文件
```

### 目录说明

#### apps/
存放独立的应用程序，每个应用都是一个可独立部署的项目。

**典型用途**：
- Web 前端应用
- 移动端应用
- API 服务
- 管理后台
- 微服务

**示例**：
```
apps/
├── web/              # Next.js/React 前端
├── mobile/           # React Native 移动端
├── admin/            # 管理后台
└── api/              # Express/Fastify API
```

#### packages/
存放可复用的共享包，这些包可以被 apps/ 中的应用引用。

**典型用途**：
- UI 组件库
- 工具函数库
- 业务逻辑库
- TypeScript 类型定义
- 配置包

**示例**：
```
packages/
├── ui/               # 共享 UI 组件
├── utils/            # 工具函数
├── types/            # TypeScript 类型
├── config/           # 共享配置
└── api-client/       # API 客户端
```

#### shared/
存放非代码的共享资源。

**典型用途**：
- 配置文件
- 静态资源
- 文档
- 脚本

**示例**：
```
shared/
├── config/           # 环境配置
├── assets/           # 图片、字体等
├── docs/             # 文档
└── scripts/          # 构建脚本
```

### Workspace 配置

#### package.json
```json
{
  "name": "my-monorepo",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint"
  }
}
```

#### pnpm-workspace.yaml
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### Git 配置

#### .gitignore
自动生成的 `.gitignore` 包含常见的忽略规则：

```gitignore
# 依赖
node_modules/
.pnp
.pnp.js

# 构建输出
dist/
build/
.next/
out/

# 环境变量
.env
.env.local
.env.*.local

# 日志
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 编辑器
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
.venv/

# Mono-Kickstart
.kickstartrc.local
```

## 开发

### 环境准备

1. **Python 3.11+**
   ```bash
   python --version  # 确保 >= 3.11
   ```

2. **uv** (推荐)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

> 💡 使用下方的一键脚本 `scripts/setenv.sh` 时，以上两步无需手工执行：
> 脚本会自动安装 uv，并由 uv 拉取所需的 Python 3.11。

### 克隆仓库

```bash
git clone https://github.com/mono-kickstart/mono-kickstart.git
cd mono-kickstart
```

### 一键配置开发环境（推荐）

```bash
bash scripts/setenv.sh
```

该脚本会依次完成：安装 uv（已有则跳过）→ 创建 Python 3.11 虚拟环境 →
按 `uv.lock` 同步依赖（含 dev）→ 将 `mk` 软链到 `/usr/local/bin`。

脚本是**幂等**的，可反复执行：已就绪的环节自动跳过；若 `.venv` 损坏
（例如解释器被删导致软链悬空）会自动识别并重建。

常用选项：

```bash
bash scripts/setenv.sh --check       # 配置完成后执行冒烟自检
bash scripts/setenv.sh --force       # 强制删除并重建 .venv
bash scripts/setenv.sh --with-ruff   # 额外安装 ruff（lint/format）
bash scripts/setenv.sh --test        # 结尾运行单元测试
bash scripts/setenv.sh --no-link     # 不创建 /usr/local/bin/mk 软链
bash scripts/setenv.sh --help        # 查看全部选项
```

### 安装开发依赖（手工方式）

若不使用上面的脚本，也可以手工安装：

```bash
# 使用 uv（推荐）
uv sync --extra dev

# 或使用 pip
pip install -e ".[dev]"
```

### 项目结构

```
mono-kickstart/
├── src/
│   └── mono_kickstart/
│       ├── __init__.py
│       ├── cli.py                    # CLI 入口
│       ├── config.py                 # 配置管理
│       ├── platform_detector.py      # 平台检测
│       ├── tool_detector.py          # 工具检测
│       ├── installer_base.py         # 安装器基类
│       ├── mirror_config.py          # 镜像源配置
│       ├── project_creator.py        # 项目创建
│       ├── orchestrator.py           # 安装编排
│       ├── interactive.py            # 交互式配置
│       └── installers/               # 具体工具安装器
│           ├── nvm_installer.py
│           ├── node_installer.py
│           ├── conda_installer.py
│           ├── bun_installer.py
│           ├── uv_installer.py
│           ├── claude_installer.py
│           ├── codex_installer.py
│           ├── spec_kit_installer.py
│           └── bmad_installer.py
├── tests/
│   ├── unit/                         # 单元测试
│   ├── property/                     # 属性测试
│   └── integration/                  # 集成测试
├── docs/                             # 文档
├── pyproject.toml                    # 项目配置
└── README.md                         # 本文件
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行属性测试
pytest tests/property/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_config.py

# 运行特定测试函数
pytest tests/unit/test_config.py::test_config_merge

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s
```

### 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
pytest --cov=mono_kickstart --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# 生成终端覆盖率报告
pytest --cov=mono_kickstart --cov-report=term

# 生成 XML 覆盖率报告（用于 CI）
pytest --cov=mono_kickstart --cov-report=xml
```

### 代码风格

项目使用以下工具保证代码质量：

```bash
# 代码格式化（Black）
black src/ tests/

# 代码检查（Flake8）
flake8 src/ tests/

# 类型检查（mypy）
mypy src/

# 导入排序（isort）
isort src/ tests/

# 一键格式化和检查
make format  # 格式化代码
make lint    # 检查代码
```

### 本地测试

在本地测试 CLI 工具：

```bash
# 方式 1: 直接运行模块
python -m mono_kickstart.cli init --help

# 方式 2: 使用 uv run
uv run mk init --help

# 方式 3: 安装到本地
uv pip install -e .
mk init --help

# 方式 4: 使用 Python 脚本
python -c "from mono_kickstart.cli import main; main()"
```

### 调试

```bash
# 使用 pdb 调试
python -m pdb -m mono_kickstart.cli init

# 使用 ipdb（更友好的调试器）
pip install ipdb
python -m ipdb -m mono_kickstart.cli init

# 在代码中设置断点
import pdb; pdb.set_trace()  # Python 3.6+
breakpoint()  # Python 3.7+
```

### 构建和发布

```bash
# 构建包
uv build

# 检查构建产物
ls dist/

# 测试安装
uv pip install dist/*.whl

# 发布到 PyPI（需要配置 PyPI token）
uv publish

# 发布到 Test PyPI
uv publish --repository testpypi
```

### 开发工作流

1. **创建分支**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **编写代码**
   - 遵循现有代码风格
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
   - 单元测试：测试具体功能
   - 属性测试：测试通用属性
   - 集成测试：测试端到端流程

4. **运行测试**
   ```bash
   pytest
   ```

5. **检查代码质量**
   ```bash
   make lint
   ```

6. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

7. **推送并创建 PR**
   ```bash
   git push origin feature/my-feature
   ```

### 贡献指南

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：
- 代码规范
- 提交信息格式
- PR 流程
- 测试要求

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

感谢以下开源项目：

- [Python](https://www.python.org/) - 编程语言
- [uv](https://github.com/astral-sh/uv) - Python 包管理器
- [pytest](https://pytest.org/) - 测试框架
- [Hypothesis](https://hypothesis.readthedocs.io/) - 属性测试框架
- [PyYAML](https://pyyaml.org/) - YAML 解析器
- [argparse](https://docs.python.org/3/library/argparse.html) - 命令行解析

## 相关链接

- **GitHub**: https://github.com/mono-kickstart/mono-kickstart
- **PyPI**: https://pypi.org/project/mono-kickstart/
- **文档**: https://mono-kickstart.readthedocs.io/
- **问题反馈**: https://github.com/mono-kickstart/mono-kickstart/issues
- **讨论**: https://github.com/mono-kickstart/mono-kickstart/discussions

### 工具指南

- **GitHub Copilot CLI 指南**: [docs/copilot-cli-guide.md](docs/copilot-cli-guide.md)
- **配置示例**: [docs/examples/](docs/examples/)

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史和变更记录。

## 支持

如有问题或需要帮助：

1. 查看 [常见问题](#常见问题) 部分
2. 搜索 [GitHub Issues](https://github.com/mono-kickstart/mono-kickstart/issues)
3. 创建新的 Issue
4. 参与 [GitHub Discussions](https://github.com/mono-kickstart/mono-kickstart/discussions)

---

**Made with ❤️ by the Mono-Kickstart Team**
