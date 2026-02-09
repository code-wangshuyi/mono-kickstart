# 需求文档

## 简介

Mono-Kickstart 是一个 Monorepo 项目模板脚手架 CLI 工具，通过一条命令快速初始化标准化的 Monorepo 工程，自动完成开发环境搭建与工具链安装，让开发者开箱即用。该工具使用 Python 3.11+ 和 Typer 框架开发，支持通过 `uv tool install mono-kickstart` 安装，提供 `mk`（短名称）和 `mono-kickstart`（完整名称）两个等价的命令入口。

## 术语表

- **CLI**: Command Line Interface，命令行界面工具
- **Monorepo**: 单一代码仓库管理多个项目或包的软件开发策略
- **NVM**: Node Version Manager，Node.js 版本管理工具
- **Conda**: Python 环境和包管理系统
- **Bun**: 高性能 JavaScript 运行时和包管理器
- **uv**: Rust 编写的高性能 Python 包管理器和项目管理工具
- **Claude_Code_CLI**: Anthropic 提供的 AI 编程助手命令行工具
- **Codex_CLI**: OpenAI 提供的 AI 编程助手命令行工具
- **Spec_Kit**: GitHub 开源的规格驱动开发工具包
- **BMad_Method**: AI 驱动的敏捷开发框架
- **镜像源**: 软件包下载的备用服务器地址，用于加速中国大陆地区的下载速度
- **幂等性**: 多次执行相同操作产生相同结果的特性
- **Shell_Completion**: 命令行自动补全功能

## 需求

### 需求 1: 开发工具检测与安装

**用户故事**: 作为开发者，我希望工具能自动检测并安装所需的开发工具链，这样我就不需要手动逐个安装和配置各种工具。

#### 验收标准

1. WHEN 执行初始化命令 THEN THE CLI SHALL 按照以下顺序检测并安装工具: NVM → Node.js → Conda → Bun → npm/Bun 镜像源配置 → uv → uv 镜像源配置 → Claude_Code_CLI → Codex_CLI → Spec_Kit → BMad_Method
2. WHEN 检测到某个工具已安装 THEN THE CLI SHALL 跳过该工具的安装步骤并继续下一个工具
3. WHEN 安装 NVM THEN THE CLI SHALL 下载并执行 NVM v0.40.4 安装脚本，并将环境变量写入 shell 配置文件
4. WHEN NVM 安装完成 THEN THE CLI SHALL 通过 NVM 安装 Node.js LTS 版本并设置为默认版本
5. WHEN 安装 Conda THEN THE CLI SHALL 根据操作系统和架构选择正确的 Miniconda 安装包（Linux x86_64 或 macOS ARM64）
6. WHEN 安装 Bun THEN THE CLI SHALL 执行官方安装脚本并验证安装成功
7. WHEN 安装 uv THEN THE CLI SHALL 执行官方安装脚本并验证安装成功
8. WHEN 安装 Claude_Code_CLI THEN THE CLI SHALL 使用原生二进制安装方式（stable 渠道）并执行 `claude doctor` 验证
9. WHEN 安装 Codex_CLI THEN THE CLI SHALL 优先使用 Bun 安装（如果 Bun 已安装），否则使用 npm 安装
10. WHEN 安装 Spec_Kit THEN THE CLI SHALL 使用 `uv tool install` 从 GitHub 仓库安装
11. WHEN 安装 BMad_Method THEN THE CLI SHALL 使用 npx 或 bunx 交互式安装到项目中
12. WHEN 某个工具安装失败 THEN THE CLI SHALL 记录错误信息并继续安装其余工具
13. WHEN 所有工具安装完成 THEN THE CLI SHALL 显示安装摘要，包括成功、跳过和失败的工具列表

### 需求 2: 中国大陆镜像源配置

**用户故事**: 作为中国大陆的开发者，我希望工具能自动配置国内镜像源，这样我就能获得更快的下载速度。

#### 验收标准

1. WHEN Node.js 安装完成 THEN THE CLI SHALL 配置 npm 使用淘宝 npmmirror 镜像源
2. WHEN Bun 安装完成 THEN THE CLI SHALL 创建 `~/.bunfig.toml` 配置文件并设置 npmmirror 镜像源
3. WHEN uv 安装完成 THEN THE CLI SHALL 创建 `~/.config/uv/uv.toml` 配置文件并配置 PyPI 镜像源和 CPython 下载代理
4. WHEN 配置 uv 镜像源 THEN THE CLI SHALL 在 `[[index]]` 段之前添加 `python-install-mirror` 配置
5. WHEN 配置 PyPI 镜像源 THEN THE CLI SHALL 默认使用南方科技大学镜像源
6. WHEN 配置 CPython 下载代理 THEN THE CLI SHALL 使用 ghfast.top 代理地址
7. WHEN 镜像源配置完成 THEN THE CLI SHALL 验证配置是否生效（npm 通过 `npm get registry`，uv 通过检查配置文件）

### 需求 3: Monorepo 项目结构创建

**用户故事**: 作为开发者，我希望工具能创建标准化的 Monorepo 项目结构，这样我就能立即开始开发而不需要手动搭建项目骨架。

#### 验收标准

1. WHEN 执行项目创建命令 THEN THE CLI SHALL 创建标准的 Monorepo 目录结构
2. WHEN 创建项目结构 THEN THE CLI SHALL 生成包管理器的 workspace 配置文件
3. WHEN 创建项目结构 THEN THE CLI SHALL 生成通用的 `.gitignore` 文件
4. WHEN 创建项目结构 THEN THE CLI SHALL 生成项目 `README.md` 文件
5. WHEN 创建项目结构 THEN THE CLI SHALL 初始化 Git 仓库
6. WHEN 项目目录已存在 THEN THE CLI SHALL 提示用户并询问是否覆盖或合并

### 需求 4: 配置文件支持

**用户故事**: 作为开发者，我希望能通过配置文件保存和复用初始化配置，这样团队成员就能使用统一的开发环境设置。

#### 验收标准

1. WHEN 执行初始化命令 THEN THE CLI SHALL 按优先级加载配置: 命令行参数 > 项目 `.kickstartrc` > `~/.kickstartrc` > 默认值
2. WHEN 使用 `--config <path>` 参数 THEN THE CLI SHALL 从指定路径加载配置文件
3. WHEN 配置文件不存在 THEN THE CLI SHALL 使用默认配置并继续执行
4. WHEN 配置文件格式错误 THEN THE CLI SHALL 显示错误信息并终止执行
5. WHEN 使用 `--save-config` 参数 THEN THE CLI SHALL 将当前配置保存到项目根目录的 `.kickstartrc` 文件
6. WHEN 配置文件中 `tools.<name>.enabled` 为 false THEN THE CLI SHALL 跳过该工具的安装
7. WHEN 配置文件指定工具版本 THEN THE CLI SHALL 安装指定版本而非默认版本
8. WHEN 配置文件指定镜像源地址 THEN THE CLI SHALL 使用指定的镜像源而非默认镜像源
9. WHEN 合并多个配置源 THEN THE CLI SHALL 高优先级配置覆盖低优先级配置，未指定字段使用低优先级值

### 需求 5: 工具升级功能

**用户故事**: 作为开发者，我希望能一键升级所有已安装的开发工具，这样我就能保持工具链的最新状态。

#### 验收标准

1. WHEN 执行 `mk upgrade` 命令 THEN THE CLI SHALL 检测所有已安装工具的当前版本和最新版本
2. WHEN 检测到可用更新 THEN THE CLI SHALL 显示升级清单，包括工具名称、当前版本和最新版本
3. WHEN 用户确认升级 THEN THE CLI SHALL 按照工具特定的升级命令逐个升级工具
4. WHEN 执行 `mk upgrade <tool-name>` 命令 THEN THE CLI SHALL 仅升级指定的工具
5. WHEN 升级 NVM THEN THE CLI SHALL 重新执行 NVM 安装脚本
6. WHEN 升级 Node.js THEN THE CLI SHALL 执行 `nvm install --lts && nvm alias default lts/*`
7. WHEN 升级 Conda THEN THE CLI SHALL 下载最新安装包并使用 `-b -u -p` 参数覆盖安装
8. WHEN 升级 Bun THEN THE CLI SHALL 执行 `bun upgrade`
9. WHEN 升级 uv THEN THE CLI SHALL 执行 `uv self update`
10. WHEN 升级 Claude_Code_CLI THEN THE CLI SHALL 重新执行官方安装脚本
11. WHEN 升级 Codex_CLI THEN THE CLI SHALL 根据原安装方式执行相应的升级命令
12. WHEN 升级 Spec_Kit THEN THE CLI SHALL 执行 `uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git`
13. WHEN 某个工具升级失败 THEN THE CLI SHALL 记录错误信息并继续升级其余工具
14. WHEN 所有工具升级完成 THEN THE CLI SHALL 显示升级摘要，包括成功和失败的工具列表

### 需求 6: 幂等性与容错性

**用户故事**: 作为开发者，我希望工具能安全地重复执行而不产生副作用，这样我就能在安装失败后重新运行而不用担心破坏已有配置。

#### 验收标准

1. WHEN 重复执行初始化命令 THEN THE CLI SHALL 产生与首次执行相同的最终状态
2. WHEN 某个工具已安装 THEN THE CLI SHALL 不修改该工具的现有配置
3. WHEN 某个工具安装失败 THEN THE CLI SHALL 不影响其他工具的安装流程
4. WHEN 配置文件已存在 THEN THE CLI SHALL 不覆盖现有配置文件（除非使用 `--force` 参数）
5. WHEN 执行过程中发生错误 THEN THE CLI SHALL 显示清晰的错误信息，包括失败的工具名称和原因
6. WHEN 执行过程中发生错误 THEN THE CLI SHALL 提供恢复建议或手动安装指引
7. WHEN 安装工具时 THEN THE CLI SHALL 显示当前进度，包括正在安装的工具名称和进度百分比

### 需求 7: Shell 自动补全

**用户故事**: 作为开发者，我希望命令行能提供 Tab 自动补全功能，这样我就能更快地输入命令和参数。

#### 验收标准

1. WHEN 执行 `mk --install-completion` THEN THE CLI SHALL 检测当前 Shell 类型并安装相应的补全脚本
2. WHEN 执行 `mk --show-completion` THEN THE CLI SHALL 输出当前 Shell 的补全脚本内容而不安装
3. WHEN 执行 `mk --show-completion <shell>` THEN THE CLI SHALL 输出指定 Shell 的补全脚本内容
4. WHEN 补全脚本已安装 THEN THE CLI SHALL 支持子命令补全（init、upgrade、help 等）
5. WHEN 补全脚本已安装 THEN THE CLI SHALL 支持工具名称补全（在 `mk upgrade <Tab>` 时）
6. WHEN 补全脚本已安装 THEN THE CLI SHALL 支持选项补全（在 `mk init --<Tab>` 时）
7. WHEN 补全脚本已安装 THEN THE CLI SHALL 支持配置文件路径补全（在 `mk init --config <Tab>` 时）
8. WHEN 使用 `mk` 或 `mono-kickstart` 命令 THEN THE CLI SHALL 两个命令均提供相同的补全功能

### 需求 8: 命令行界面与用户交互

**用户故事**: 作为开发者，我希望工具提供清晰友好的命令行界面，这样我就能轻松理解工具的功能和使用方法。

#### 验收标准

1. WHEN 执行 `mk --help` THEN THE CLI SHALL 显示所有可用命令和选项的帮助信息
2. WHEN 执行 `mk init --help` THEN THE CLI SHALL 显示 init 子命令的详细帮助信息
3. WHEN 执行 `mk upgrade --help` THEN THE CLI SHALL 显示 upgrade 子命令的详细帮助信息
4. WHEN 执行 `mk --version` THEN THE CLI SHALL 显示 CLI 工具的当前版本号
5. WHEN 执行需要用户确认的操作 THEN THE CLI SHALL 显示清晰的提示信息并等待用户输入
6. WHEN 显示进度信息 THEN THE CLI SHALL 使用进度条或百分比显示当前进度
7. WHEN 显示错误信息 THEN THE CLI SHALL 使用红色或醒目的格式突出显示错误
8. WHEN 显示成功信息 THEN THE CLI SHALL 使用绿色或醒目的格式突出显示成功
9. WHEN 显示警告信息 THEN THE CLI SHALL 使用黄色或醒目的格式突出显示警告

### 需求 9: 平台兼容性

**用户故事**: 作为开发者，我希望工具能在我的操作系统上正常运行，这样我就不需要切换到特定平台才能使用。

#### 验收标准

1. WHEN 在 macOS ARM64 系统上运行 THEN THE CLI SHALL 正确检测架构并安装 ARM64 版本的工具
2. WHEN 在 macOS x86_64 系统上运行 THEN THE CLI SHALL 正确检测架构并安装 x86_64 版本的工具
3. WHEN 在 Linux x86_64 系统上运行 THEN THE CLI SHALL 正确检测架构并安装 x86_64 版本的工具
4. WHEN 在不支持的平台上运行 THEN THE CLI SHALL 显示错误信息并列出支持的平台
5. WHEN 检测操作系统类型 THEN THE CLI SHALL 正确识别 macOS 和 Linux 系统
6. WHEN 检测 Shell 类型 THEN THE CLI SHALL 正确识别 Bash、Zsh 和 Fish
7. WHEN 安装需要特定系统依赖的工具 THEN THE CLI SHALL 检查依赖是否存在并提供安装指引

### 需求 10: 安装与分发

**用户故事**: 作为开发者，我希望能通过简单的命令安装和使用工具，这样我就不需要复杂的配置过程。

#### 验收标准

1. WHEN 执行 `uv tool install mono-kickstart` THEN THE CLI SHALL 从 PyPI 安装并注册 `mk` 和 `mono-kickstart` 命令
2. WHEN 执行 `pip install mono-kickstart` THEN THE CLI SHALL 从 PyPI 安装并注册 `mk` 和 `mono-kickstart` 命令
3. WHEN 执行 `uvx mono-kickstart init` THEN THE CLI SHALL 临时下载并执行 init 命令而不持久安装
4. WHEN CLI 安装完成 THEN THE CLI SHALL 在 PATH 中可用，用户可直接执行 `mk` 或 `mono-kickstart` 命令
5. WHEN 执行 `uv tool install mono-kickstart --upgrade` THEN THE CLI SHALL 升级到最新版本
6. WHEN 执行 `pip install --upgrade mono-kickstart` THEN THE CLI SHALL 升级到最新版本
7. WHEN CLI 需要 Python 3.11+ THEN THE CLI SHALL 在 Python 版本不满足时显示错误信息
8. WHEN 使用 `mk` 或 `mono-kickstart` 命令 THEN THE CLI SHALL 两个命令提供完全相同的功能

### 需求 11: 交互式配置（可选功能）

**用户故事**: 作为开发者，我希望能通过交互式问答选择需要安装的工具和配置选项，这样我就能根据项目需求定制开发环境。

#### 验收标准

1. WHEN 执行 `mk init --interactive` THEN THE CLI SHALL 启动交互式配置向导
2. WHEN 进入交互式配置 THEN THE CLI SHALL 询问项目名称并提供默认值（当前目录名）
3. WHEN 进入交互式配置 THEN THE CLI SHALL 询问需要安装的工具并提供多选列表
4. WHEN 进入交互式配置 THEN THE CLI SHALL 询问 Node.js 版本选项（LTS、Latest 或指定版本）
5. WHEN 进入交互式配置 THEN THE CLI SHALL 询问 Python 版本选项
6. WHEN 进入交互式配置 THEN THE CLI SHALL 询问是否配置中国大陆镜像源
7. WHEN 交互式配置完成 THEN THE CLI SHALL 显示配置摘要并询问是否继续
8. WHEN 使用 `--save-config` 参数 THEN THE CLI SHALL 将交互式配置结果保存到 `.kickstartrc` 文件
9. WHEN 配置文件已存在 THEN THE CLI SHALL 使用配置文件中的值作为交互式问答的默认值
