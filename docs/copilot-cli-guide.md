# GitHub Copilot CLI 安装和使用指南

本指南详细介绍如何使用 mono-kickstart 安装和配置 GitHub Copilot CLI。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [配置选项](#配置选项)
- [使用指南](#使用指南)
- [常见问题](#常见问题)
- [故障排除](#故障排除)

## 系统要求

### 必需条件

- **Node.js**: 22 或更高版本
- **操作系统**: macOS (ARM64/x86_64) 或 Linux (x86_64)
- **GitHub Copilot 订阅**: 个人版或企业版
- **网络**: 需要互联网连接

### 平台支持

| 平台 | 支持状态 |
|------|---------|
| macOS ARM64 (Apple Silicon) | ✅ 支持 |
| macOS x86_64 (Intel) | ✅ 支持 |
| Linux x86_64 | ✅ 支持 |
| Windows | ❌ 不支持 |
| Linux ARM64 | ❌ 不支持 |

## 快速开始

### 方式 1: 使用默认配置

```bash
# 1. 创建项目目录
mkdir my-project
cd my-project

# 2. 初始化（会自动安装 Copilot CLI）
mk init

# 3. 等待安装完成
# 系统会自动：
# - 安装 NVM
# - 安装 Node.js 22+
# - 通过 npm 安装 GitHub Copilot CLI

# 4. 验证安装
copilot --version

# 5. 登录 GitHub
copilot auth login
```

### 方式 2: 使用配置文件

```bash
# 1. 创建配置文件
cat > .kickstartrc << 'EOF'
tools:
  node:
    enabled: true
    version: 22
  copilot-cli:
    enabled: true
EOF

# 2. 使用配置文件初始化
mk init --config .kickstartrc

# 3. 验证和登录
copilot --version
copilot auth login
```

### 方式 3: 单独安装

如果您已经有 Node.js 22+，可以单独安装 Copilot CLI：

```bash
# 安装 Copilot CLI
mk install copilot-cli

# 验证和登录
copilot --version
copilot auth login
```

## 配置选项

### 基本配置

```yaml
tools:
  copilot-cli:
    enabled: true  # 是否安装 Copilot CLI
```

### 完整配置示例

```yaml
project:
  name: my-copilot-project

tools:
  # Node.js 配置（Copilot CLI 的依赖）
  nvm:
    enabled: true
  
  node:
    enabled: true
    version: 22  # 必须 >= 22
  
  # Copilot CLI 配置
  copilot-cli:
    enabled: true
  
  # 其他工具（可选）
  bun:
    enabled: true
  
  uv:
    enabled: true

# 镜像源配置（加速下载）
registry:
  npm: https://registry.npmmirror.com/
```

### 禁用 Copilot CLI

如果您不想安装 Copilot CLI：

```yaml
tools:
  copilot-cli:
    enabled: false
```

## 使用指南

### 认证

安装完成后，首次使用需要进行 GitHub 认证：

```bash
# 启动认证流程
copilot auth login

# 按照提示操作：
# 1. 系统会显示一个设备码
# 2. 在浏览器中打开 https://github.com/login/device
# 3. 输入设备码
# 4. 授权 GitHub Copilot CLI 访问您的账户
```

### 基本命令

#### 获取命令建议

```bash
# 描述您想做什么，Copilot 会建议命令
copilot suggest "list all files in current directory"
copilot suggest "find large files"
copilot suggest "compress all images"
```

#### 解释命令

```bash
# 解释复杂的命令
copilot explain "git rebase -i HEAD~3"
copilot explain "find . -name '*.log' -mtime +7 -delete"
copilot explain "docker run -d -p 8080:80 nginx"
```

#### 交互式会话

```bash
# 启动交互式会话
copilot

# 在交互模式中：
# - 输入自然语言描述
# - Copilot 会建议命令
# - 您可以选择执行或修改
# - 输入 'exit' 退出
```

### 高级用法

#### 使用别名

为常用命令创建别名：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias cps='copilot suggest'
alias cpe='copilot explain'
alias cpi='copilot'

# 使用别名
cps "create a new git branch"
cpe "awk '{print $1}' file.txt"
```

#### 集成到工作流

```bash
# 在脚本中使用 Copilot
#!/bin/bash

# 获取命令建议并执行
COMMAND=$(copilot suggest "backup database" --format json | jq -r '.command')
echo "Executing: $COMMAND"
eval "$COMMAND"
```

## 常见问题

### Q: 如何检查 Node.js 版本是否满足要求？

```bash
# 检查当前 Node.js 版本
node --version

# 如果版本低于 22，升级：
nvm install 22
nvm use 22
nvm alias default 22
```

### Q: 安装失败怎么办？

**检查 Node.js 版本**:
```bash
node --version  # 必须 >= v22.0.0
```

**检查平台支持**:
```bash
uname -s  # 应该是 Darwin (macOS) 或 Linux
uname -m  # 应该是 arm64, x86_64, 或 amd64
```

**手动安装**:
```bash
# 如果自动安装失败，可以手动安装
npm install -g @github/copilot
```

### Q: 认证失败怎么办？

**检查 GitHub Copilot 订阅**:
1. 访问 https://github.com/settings/copilot
2. 确认您有活跃的 Copilot 订阅

**重新认证**:
```bash
# 登出
copilot auth logout

# 重新登录
copilot auth login
```

### Q: 如何升级 Copilot CLI？

```bash
# 方式 1: 使用 mono-kickstart
mk upgrade copilot-cli

# 方式 2: 使用 npm
npm update -g @github/copilot

# 验证新版本
copilot --version
```

### Q: 如何卸载 Copilot CLI？

```bash
# 使用 npm 卸载
npm uninstall -g @github/copilot

# 验证卸载
which copilot  # 应该没有输出
```

### Q: Copilot CLI 支持哪些 Shell？

Copilot CLI 支持以下 Shell：
- Bash
- Zsh
- Fish
- PowerShell (Windows，但 mono-kickstart 不支持 Windows)

### Q: 如何配置代理？

如果您需要通过代理访问 GitHub：

```bash
# 设置 npm 代理
npm config set proxy http://proxy.example.com:8080
npm config set https-proxy http://proxy.example.com:8080

# 然后安装
mk install copilot-cli
```

## 故障排除

### 问题 1: 命令未找到

**症状**:
```bash
copilot --version
# bash: copilot: command not found
```

**解决方案**:
```bash
# 检查 npm 全局目录是否在 PATH 中
npm config get prefix

# 添加到 PATH（添加到 ~/.bashrc 或 ~/.zshrc）
export PATH="$(npm config get prefix)/bin:$PATH"

# 重新加载 Shell 配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### 问题 2: Node.js 版本过低

**症状**:
```
Error: GitHub Copilot CLI requires Node.js 22 or higher
```

**解决方案**:
```bash
# 安装 Node.js 22
nvm install 22
nvm use 22
nvm alias default 22

# 验证版本
node --version  # 应该显示 v22.x.x

# 重新安装 Copilot CLI
mk install copilot-cli
```

### 问题 3: 平台不支持

**症状**:
```
Error: GitHub Copilot CLI installer only supports macOS and Linux
```

**解决方案**:
- 如果您在 Windows 上，Copilot CLI 目前不支持通过 mono-kickstart 安装
- 如果您在 Linux ARM64 上，也不支持
- 请使用支持的平台（macOS 或 Linux x86_64）

### 问题 4: 认证超时

**症状**:
```
Error: Authentication timeout
```

**解决方案**:
```bash
# 检查网络连接
ping github.com

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 重试认证
copilot auth login
```

### 问题 5: 权限错误

**症状**:
```
Error: EACCES: permission denied
```

**解决方案**:
```bash
# 方式 1: 修复 npm 权限（推荐）
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH

# 方式 2: 使用 sudo（不推荐）
sudo npm install -g @github/copilot
```

## 更多资源

- **官方文档**: https://docs.github.com/en/copilot/github-copilot-in-the-cli
- **npm 包**: https://www.npmjs.com/package/@github/copilot
- **GitHub Copilot**: https://github.com/features/copilot
- **mono-kickstart**: https://github.com/mono-kickstart/mono-kickstart

## 反馈和支持

如有问题或建议：
- 提交 Issue: https://github.com/mono-kickstart/mono-kickstart/issues
- 查看文档: https://mono-kickstart.readthedocs.io/
- 参与讨论: https://github.com/mono-kickstart/mono-kickstart/discussions

---

**最后更新**: 2024-02-11
