# Mono-Kickstart 项目需求文档

> 一个 Monorepo 项目模板脚手架 CLI 工具

## 项目定位

通过一条命令快速初始化一个标准化的 Monorepo 工程，自动完成开发环境搭建与工具链安装，让开发者开箱即用。

- **技术栈**: Python 3.11+（CLI 框架基于 Typer）
- **运行时依赖**: Python 3.11+、uv（推荐）或 pip
- **分发与安装**:
  - 推荐方式（通过 uv tool 全局安装）:
    ```
    uv tool install mono-kickstart
    ```
  - 一次性执行（不安装）:
    ```
    uvx mono-kickstart init
    ```
  - pip 安装: `pip install mono-kickstart`
  - 开发模式: `uv pip install -e .`（clone 仓库后）
- **命令名称**: 安装后提供 `mk` 作为主命令（短名称，日常使用），同时保留 `mono-kickstart` 作为完整命令名（两者完全等价）
  ```
  mk init            # 等价于 mono-kickstart init
  mk upgrade bun     # 等价于 mono-kickstart upgrade bun
  ```
- **升级 CLI 自身**: `uv tool install mono-kickstart --upgrade` 或 `pip install --upgrade mono-kickstart`

---

## 功能清单

### F1 - 环境初始化

- 检测并安装 NVM（Node Version Manager，当前最新版 v0.40.4）
  - 安装脚本: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash`
  - 安装后自动向 shell 配置文件（`.bashrc` / `.zshrc`）写入环境变量：
    ```
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    ```
  - 升级 NVM 自身: 重新运行安装脚本（同安装命令）
- 通过 NVM 安装并配置指定版本的 Node.js
  - 默认安装最新 LTS 版本: `nvm install --lts`
  - 设为默认版本: `nvm alias default lts/*`
  - 升级 Node.js: `nvm install --lts && nvm alias default lts/*`
- 检测并安装 Conda（通过 Miniconda，Python 环境管理）
  - Linux x86_64: `https://mirrors.sustech.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh`
  - macOS ARM64: `https://mirrors.sustech.edu.cn/anaconda/miniconda/Miniconda3-latest-MacOSX-arm64.sh`
  - 升级 Conda: 重新拉取最新安装包，使用 `-u` 参数覆盖安装（保留已有环境和包）
    - Linux: `wget <mirror>/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && rm ~/miniconda3/miniconda.sh`
    - macOS: `curl -o ~/miniconda3/miniconda.sh <mirror>/Miniconda3-latest-MacOSX-arm64.sh && bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && rm ~/miniconda3/miniconda.sh`
    - 关键参数: `-b`（静默模式）、`-u`（覆盖更新已有安装）、`-p`（指定安装路径）
- 检测并安装 Claude Code CLI
  - 推荐方式（原生二进制安装）:
    - 安装 stable 版本（默认）: `curl -fsSL https://claude.ai/install.sh | bash`
    - 安装 latest 版本: `curl -fsSL https://claude.ai/install.sh | bash -s latest`
    - 安装指定版本: `curl -fsSL https://claude.ai/install.sh | bash -s <version>`
  - 备选方式:
    - npm: `npm install -g @anthropic-ai/claude-code`（已标记为 deprecated）
    - Homebrew: `brew upgrade claude-code`
  - ⚠️ 不支持通过 Bun 安装: npm 包 `@anthropic-ai/claude-code` 与 Bun 运行时存在已知兼容性问题（v1.0.72+ 崩溃），请使用原生安装方式
  - 系统要求: macOS 10.15+ / Ubuntu 20.04+ / Debian 10+
  - 安装后运行 `claude doctor` 检查安装状态
  - 升级: 原生安装默认自动更新；手动升级可重新运行安装脚本，Homebrew 用户使用 `brew upgrade claude-code`
- 检测并安装 OpenAI Codex CLI
  - Bun 安装（推荐，已安装 Bun 时优先使用）: `bun install -g @openai/codex`
  - npm 安装: `npm i -g @openai/codex`
  - Homebrew 安装: `brew install --cask codex`
  - 也可从 GitHub Releases 下载对应平台的二进制文件:
    - `https://github.com/openai/codex/releases`
    - 常用平台: `codex-x86_64-unknown-linux-musl`、`codex-aarch64-apple-darwin` 等
    - 下载后需重命名为 `codex` 并赋予执行权限
  - 支持平台: macOS、Linux
  - 首次运行 `codex` 后通过 ChatGPT 账号或 API Key 认证
  - 升级: `bun update -g @openai/codex`（Bun 安装时）、`npm update -g @openai/codex`（npm 安装时）或 `brew upgrade --cask codex`（Homebrew 安装时）
- 检测并安装 Bun（高性能 JavaScript 运行时 & 包管理器，内置 `bunx`）
  - 推荐方式: `curl -fsSL https://bun.sh/install | bash`
  - 安装指定版本: `curl -fsSL https://bun.sh/install | bash -s "bun-v1.x.y"`
  - 备选方式:
    - Homebrew: `brew install oven-sh/bun/bun`
    - npm: `npm install -g bun`
  - Linux 前置依赖: 需要 `unzip`（`sudo apt install unzip`），内核版本建议 5.6+（最低 5.1）
  - 安装目录: `~/.bun/bin`，安装脚本会自动写入 shell 配置文件
  - 安装后验证: `bun --version`
  - 升级: `bun upgrade`
  - `bunx` 随 Bun 一起安装，用于直接执行 npm 包（等价于 `npx`）
- 检测并安装 uv（Rust 编写的高性能 Python 包管理器 & 项目管理工具，Spec Kit 的前置依赖）
  - 推荐方式: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - 安装指定版本: `curl -LsSf https://astral.sh/uv/0.9.26/install.sh | sh`
  - 备选方式:
    - Homebrew: `brew install uv`
    - pip: `pip install uv`（建议在隔离环境中安装）
  - 安装后自动写入 `~/.local/bin`，并更新 shell 配置文件
  - 安装后验证: `uv --version`
  - 升级: `uv self update`
  - 附带 `uvx` 命令，用于直接执行 Python 包（等价于 `pipx run`）
  - Python 版本管理（可作为 Conda 的轻量补充）:
    - 安装 Python: `uv python install 3.12`（从 python-build-standalone 下载）
    - 查看已安装版本: `uv python list`
    - 固定项目 Python 版本: `uv python pin 3.12`
  - 项目与虚拟环境管理:
    - 初始化新项目: `uv init my-project`
    - 创建虚拟环境: `uv venv`（默认 `.venv`）
    - 添加依赖: `uv add requests flask`
    - 安装锁定依赖: `uv sync`
    - 运行脚本: `uv run python main.py`
  - 工具安装（全局 CLI 工具，类似 pipx）:
    - 安装工具: `uv tool install ruff`
    - 一次性执行: `uvx black .`
  - 全局配置文件路径: `~/.config/uv/uv.toml`（macOS/Linux）
  - ⚠️ uv 与 pip 的配置完全独立，镜像源需单独配置（见下方镜像源配置章节）
- 检测并安装 Spec Kit（GitHub 开源的 Spec-Driven Development 工具包）
  - 仓库地址: `https://github.com/github/spec-kit`
  - 前置依赖: uv、Python 3.11+、Git、至少一个受支持的 AI 编程代理（Claude Code / Codex CLI 等）
  - 安装方式（通过 uv tool 持久安装）:
    ```
    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
    ```
  - 一次性运行（不安装）:
    ```
    uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
    ```
  - 安装后验证: `specify check`（检测已安装的 AI 编程工具）
  - 升级: `uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git`
  - 初始化项目示例:
    ```
    specify init my-project --ai claude
    specify init . --ai codex --force
    ```
  - 核心 Slash 命令（在 AI 代理中使用）:
    - `/speckit.constitution` — 创建项目治理原则
    - `/speckit.specify` — 定义需求规格
    - `/speckit.plan` — 生成技术实现方案
    - `/speckit.tasks` — 分解可执行任务
    - `/speckit.implement` — 按计划执行实现
- 检测并安装 BMad Method（AI 驱动的敏捷开发框架，提供专业化代理与结构化工作流）
  - 仓库地址: `https://github.com/bmad-code-org/BMAD-METHOD`
  - npm 包: `bmad-method`
  - 前置依赖: Node.js v20+、AI 编程 IDE（Claude Code / Cursor / Windsurf 等）
  - 安装方式（通过 npx 交互式安装到项目中）:
    ```
    npx bmad-method install
    ```
  - 也可使用 bunx（已安装 Bun 时）:
    ```
    bunx bmad-method install
    ```
  - 安装指定版本: `npx bmad-method@<version> install`（如回退 v4: `npx bmad-method@4.44.3 install`）
  - 安装后在 AI IDE 中使用 `/bmad-help` 获取引导
  - 升级: 在项目中重新执行 `npx bmad-method install`
  - 可选扩展模块（安装时按需选择）:
    - BMad Builder（`bmad-builder`）— 自定义代理与工作流创建
    - Test Architect（`bmad-method-test-architecture-enterprise`）— 企业级测试策略
    - Game Dev Studio（`bmad-game-dev-studio`）— 游戏开发工作流
    - Creative Intelligence Suite（`bmad-creative-intelligence-suite`）— 创意思维与头脑风暴
  - 核心工作流命令:
    - 快速路径: `/quick-spec` → `/dev-story` → `/code-review`
    - 完整规划: `/product-brief` → `/create-prd` → `/create-architecture` → `/create-epics-and-stories` → `/sprint-planning` → `/create-story` → `/dev-story` → `/code-review`
- **安装顺序策略**: NVM → Node.js → Conda → Bun → npm/Bun 镜像源配置 → uv → uv 镜像源配置 → Claude Code CLI → Codex CLI → Spec Kit → BMad Method
  - Bun 应优先于 Codex CLI 安装，这样后续可通过 `bun install -g` 安装 npm 包
  - uv 安装后应立即配置 PyPI 镜像和 CPython 下载代理，确保后续 `uv python install` 和 `uv tool install` 使用加速源
  - uv 应优先于 Spec Kit 安装，因为 Spec Kit 依赖 uv tool 进行安装
  - Spec Kit 和 BMad Method 依赖 AI 编程代理，应在它们之后安装
  - BMad Method 通过 npx/bunx 安装到具体项目中，属于项目级工具（区别于全局工具）
- **中国大陆镜像源配置**（地址可通过 `.kickstartrc` 的 `registry` 字段自定义）:
  - npm 镜像: 安装 Node.js 后立即配置淘宝 npmmirror 镜像源
    ```
    npm config set registry https://registry.npmmirror.com/
    ```
  - Bun 镜像: 安装 Bun 后创建全局配置文件 `~/.bunfig.toml`
    ```toml
    [install]
    registry = "https://registry.npmmirror.com/"
    ```
  - 验证配置:
    - npm: `npm get registry`（应输出 `https://registry.npmmirror.com/`）
    - Bun: 无内置查询命令，检查 `~/.bunfig.toml` 文件内容即可
  - uv PyPI 镜像: 安装 uv 后创建全局配置文件 `~/.config/uv/uv.toml`
    ```toml
    # CPython 下载代理（用于 uv python install，必须在 [[index]] 上方）
    python-install-mirror = "https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download"

    # PyPI 镜像源（南方科技大学）
    [[index]]
    url = "https://mirrors.sustech.edu.cn/pypi/web/simple"
    default = true
    ```
  - 可选镜像地址:
    - 南方科技大学: `https://mirrors.sustech.edu.cn/pypi/web/simple`（推荐，与 Conda 镜像同源）
    - 清华大学: `https://pypi.tuna.tsinghua.edu.cn/simple/`
    - 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
    - 中国科学技术大学: `https://mirrors.ustc.edu.cn/pypi/simple/`
  - 验证 PyPI 镜像: `uv pip install --dry-run requests -v`（日志中应显示镜像地址而非 pypi.org）
  - 验证 CPython 代理: `uv python install 3.12 -v`（日志中应显示代理地址）
  - 也可通过环境变量临时设置: `export UV_DEFAULT_INDEX="https://mirrors.sustech.edu.cn/pypi/web/simple"`
  - 恢复官方源（如有需要）:
    - npm: `npm config set registry https://registry.npmjs.org/`
    - Bun: 删除或注释 `~/.bunfig.toml` 中的 `registry` 行
    - uv: 删除 `~/.config/uv/uv.toml` 中的 `[[index]]` 段和 `python-install-mirror` 行
- 所有工具安装前先检测是否已存在，已存在则跳过

### F2 - Monorepo 工程创建

- 创建标准化的 Monorepo 项目目录结构
- 初始化包管理器与 workspace 配置
- 生成通用的 `.gitignore`、`README.md` 等基础文件
- 初始化 Git 仓库

### F3 - 交互式配置（待定）

- 支持通过交互式问答选择需要安装的工具
- 支持自定义项目名称
- 支持选择 Node.js 版本
- 支持选择 Python 版本
- 交互结果可通过 `--save-config` 写入 `.kickstartrc`（参见 F6）

### F4 - 幂等与容错

- 重复执行不会产生副作用
- 单个工具安装失败不影响其余流程
- 提供清晰的安装进度与错误提示

### F5 - 升级子命令（`mk upgrade`）

- 提供 `mk upgrade` 子命令，一键检查并升级所有已安装的工具
- 逐项检测各工具是否有可用更新，汇总展示升级清单
- 各工具升级策略:

| 工具 | 升级命令 |
|------|----------|
| NVM | 重新运行安装脚本 `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh \| bash` |
| Node.js | `nvm install --lts && nvm alias default lts/*` |
| Conda | 重新拉取最新安装包，`bash miniconda.sh -b -u -p ~/miniconda3` 覆盖安装 |
| Claude Code CLI | 原生安装自动更新；手动: 重新运行 `curl -fsSL https://claude.ai/install.sh \| bash` |
| Codex CLI | `bun update -g @openai/codex`（Bun）/ `npm update -g @openai/codex`（npm）/ `brew upgrade --cask codex` |
| Bun | `bun upgrade` |
| uv | `uv self update` |
| Spec Kit | `uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git` |
| BMad Method | 在项目中重新执行 `npx bmad-method install` 或 `bunx bmad-method install` |

- 支持升级单个工具: `mk upgrade <tool-name>`（如 `mk upgrade bun`）
- 升级前展示当前版本与最新版本的对比
- 单个工具升级失败不影响其余工具的升级流程

### F6 - 配置文件（`.kickstartrc`）

支持通过项目根目录或用户主目录下的 `.kickstartrc` 配置文件记录偏好，实现可复用、可共享的初始化配置。

- **文件格式**: YAML
- **加载优先级**（从高到低）:
  1. 命令行参数（`--config <path>` 指定自定义路径）
  2. 当前项目目录下的 `.kickstartrc`
  3. 用户主目录下的 `~/.kickstartrc`
  4. 内置默认值
- **合并策略**: 高优先级配置覆盖低优先级，未指定的字段回退到下一级
- **配置文件结构示例**:

```yaml
# .kickstartrc

# 项目基本信息
project:
  name: my-monorepo

# 工具开关与版本配置
tools:
  nvm:
    enabled: true
    version: v0.40.4           # NVM 自身版本
  node:
    enabled: true
    version: lts               # lts | latest | 具体版本号如 20.11.0
  conda:
    enabled: true
    mirror: https://mirrors.sustech.edu.cn/anaconda/miniconda
  claude-code:
    enabled: true
    channel: stable             # stable | latest
  codex:
    enabled: true
    install_via: bun            # bun | npm | brew | binary
  bun:
    enabled: true
  uv:
    enabled: true
    python_version: "3.12"      # uv python install 安装的版本
    pypi_mirror: https://mirrors.sustech.edu.cn/pypi/web/simple
    python_install_mirror: https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download
  spec-kit:
    enabled: true
    ai: claude                  # claude | codex | gemini | copilot 等
  bmad-method:
    enabled: true
    modules:                    # 可选扩展模块
      - bmad-builder
      - bmad-method-test-architecture-enterprise

# 镜像源配置
registry:
  npm: https://registry.npmmirror.com/
  bun: https://registry.npmmirror.com/
  pypi: https://mirrors.sustech.edu.cn/pypi/web/simple
  python_install: https://ghfast.top/https://github.com/astral-sh/python-build-standalone/releases/download
```

- **核心字段说明**:

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project.name` | string | 当前目录名 | 项目名称 |
| `tools.<name>.enabled` | bool | `true` | 是否安装该工具 |
| `tools.nvm.version` | string | `v0.40.4` | NVM 版本 |
| `tools.node.version` | string | `lts` | Node.js 版本策略 |
| `tools.conda.mirror` | string | 南科大镜像 | Miniconda 下载镜像地址 |
| `tools.claude-code.channel` | string | `stable` | Claude Code 安装渠道 |
| `tools.codex.install_via` | string | `bun` | Codex CLI 安装方式 |
| `tools.uv.enabled` | bool | `true` | 是否安装 uv |
| `tools.uv.python_version` | string | `3.12` | uv python install 安装的 Python 版本 |
| `tools.uv.pypi_mirror` | string | 南科大镜像 | uv 的 PyPI 镜像源地址 |
| `tools.uv.python_install_mirror` | string | ghfast 代理 | CPython 下载代理地址（用于 `uv python install`）|
| `tools.spec-kit.enabled` | bool | `true` | 是否安装 Spec Kit |
| `tools.spec-kit.ai` | string | `claude` | Spec Kit 默认使用的 AI 代理 |
| `tools.bmad-method.enabled` | bool | `true` | 是否安装 BMad Method |
| `tools.bmad-method.modules` | list | `[]` | 额外安装的 BMad 扩展模块 |
| `registry.npm` | string | npmmirror | npm registry 地址 |
| `registry.bun` | string | npmmirror | Bun registry 地址 |
| `registry.pypi` | string | 南科大镜像 | uv 的 PyPI 镜像源地址（写入 `uv.toml`）|
| `registry.python_install` | string | ghfast 代理 | CPython 下载代理（写入 `uv.toml`）|

- **初始化命令生成配置文件**: `mk init --save-config` 在交互式问答结束后将选择结果写入 `.kickstartrc`
- **团队共享**: 将 `.kickstartrc` 提交至 Git 仓库，团队成员 clone 后执行 `mk init` 即可复用同一套配置

### F7 - 命令行补全（Shell Completion）

为 `mk`（`mono-kickstart`）CLI 提供子命令、参数、选项的 Tab 补全能力，提升日常使用效率。

- **支持的 Shell**: Bash、Zsh、Fish
- **补全范围**:
  - 子命令补全: `mk <Tab>` → `init`、`upgrade`、`help` 等
  - 工具名补全: `mk upgrade <Tab>` → `nvm`、`node`、`conda`、`bun`、`uv`、`claude-code`、`codex`、`spec-kit`、`bmad-method` 等
  - 选项补全: `mk init --<Tab>` → `--config`、`--save-config`、`--skip-tools`、`--dry-run` 等
  - 配置文件路径补全: `mk init --config <Tab>` → 文件路径补全
- **安装方式**:
  - Typer 内置方式（推荐，自动检测当前 Shell）:
    ```
    mk --install-completion
    ```
  - 查看补全脚本（不安装，仅输出）:
    ```
    mk --show-completion
    ```
  - 手动安装到指定 Shell:
    ```
    # Bash（写入 ~/.bashrc）
    mk --show-completion bash >> ~/.bashrc

    # Zsh（写入 ~/.zshrc）
    mk --show-completion zsh >> ~/.zshrc

    # Fish
    mk --show-completion fish > ~/.config/fish/completions/mk.fish
    ```
- **自动安装**: `mk init` 执行时检测当前 Shell 类型，提示用户是否自动安装补全脚本
- **双命令补全**: `mk` 和 `mono-kickstart` 两个入口均注册补全脚本，确保无论使用哪个命令都能正常补全
- **实现说明**: CLI 基于 Typer 开发，补全功能由 Typer 原生支持（底层基于 `click.shell_completion`），无需额外依赖。Typer 会自动为所有已注册的命令、参数和选项生成补全脚本

---

## 设计约束

- **CLI 开发语言**: Python 3.11+
- **CLI 框架**: Typer（基于 Click，内置补全与帮助生成）
- **包管理与构建**: 使用 `pyproject.toml` + uv 管理依赖与构建
- **分发渠道**: PyPI（支持 `uv tool install` / `pip install` / `uvx`）
- **命令入口**: 安装后注册 `mk`（主命令）和 `mono-kickstart`（完整命令）两个入口点，在 `pyproject.toml` 中通过 `[project.scripts]` 配置
- **目标平台**: macOS（ARM64 / x86_64）、Linux（x86_64）；不支持 Windows
- **Python 运行时**: CLI 自身依赖 Python 3.11+，可通过 uv 自动管理 Python 版本，无需用户预装系统 Python

---

## 待讨论

- [ ] Monorepo 内默认包含哪些子包（apps / packages / shared）？
- [ ] 是否集成 CI/CD 模板（GitHub Actions 等）？
