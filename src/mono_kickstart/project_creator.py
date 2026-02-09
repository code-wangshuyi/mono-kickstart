"""
项目创建器模块

负责创建 Monorepo 项目结构，包括：
- 目录结构创建（apps/、packages/、shared/）
- workspace 配置文件生成（package.json、pnpm-workspace.yaml）
- .gitignore 文件生成
- README.md 文件生成
- Git 仓库初始化
- 已存在目录的处理逻辑
"""

import json
import subprocess
from pathlib import Path
from typing import Optional


class ProjectCreator:
    """项目创建器"""

    def __init__(self, project_name: str, project_path: Path):
        """
        初始化项目创建器

        Args:
            project_name: 项目名称
            project_path: 项目路径
        """
        self.project_name = project_name
        self.project_path = Path(project_path)

    def create_directory_structure(self) -> None:
        """创建目录结构"""
        # 创建主目录
        self.project_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        directories = ["apps", "packages", "shared"]
        for directory in directories:
            dir_path = self.project_path / directory
            dir_path.mkdir(exist_ok=True)
            # 创建 .gitkeep 文件以确保空目录被 Git 跟踪
            (dir_path / ".gitkeep").touch()

    def create_workspace_config(self) -> None:
        """创建 workspace 配置文件"""
        # 创建 package.json
        package_json = {
            "name": self.project_name,
            "version": "0.1.0",
            "private": True,
            "workspaces": ["apps/*", "packages/*"],
            "scripts": {
                "dev": "echo 'Add your dev script here'",
                "build": "echo 'Add your build script here'",
                "test": "echo 'Add your test script here'",
            },
            "devDependencies": {},
        }

        package_json_path = self.project_path / "package.json"
        with open(package_json_path, "w", encoding="utf-8") as f:
            json.dump(package_json, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # 创建 pnpm-workspace.yaml
        pnpm_workspace_content = """packages:
  - 'apps/*'
  - 'packages/*'
"""
        pnpm_workspace_path = self.project_path / "pnpm-workspace.yaml"
        with open(pnpm_workspace_path, "w", encoding="utf-8") as f:
            f.write(pnpm_workspace_content)

    def create_gitignore(self) -> None:
        """创建 .gitignore 文件"""
        gitignore_content = """# Dependencies
node_modules/
.pnp
.pnp.js

# Testing
coverage/
*.log

# Production
dist/
build/
out/

# Misc
.DS_Store
*.pem

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Local env files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/
ENV/

# Conda
.conda/
"""
        gitignore_path = self.project_path / ".gitignore"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)

    def create_readme(self) -> None:
        """创建 README.md 文件"""
        readme_content = f"""# {self.project_name}

这是一个使用 Mono-Kickstart 创建的 Monorepo 项目。

## 项目结构

```
{self.project_name}/
├── apps/          # 应用目录
├── packages/      # 共享包目录
├── shared/        # 共享资源目录
├── package.json   # Node.js workspace 配置
└── pnpm-workspace.yaml  # pnpm workspace 配置
```

## 开始使用

### 安装依赖

```bash
pnpm install
```

### 开发

```bash
pnpm dev
```

### 构建

```bash
pnpm build
```

### 测试

```bash
pnpm test
```

## 添加新应用

在 `apps/` 目录下创建新的应用：

```bash
cd apps
mkdir my-app
cd my-app
pnpm init
```

## 添加新包

在 `packages/` 目录下创建新的共享包：

```bash
cd packages
mkdir my-package
cd my-package
pnpm init
```

## 工作区依赖

在应用或包中引用工作区内的其他包：

```json
{{
  "dependencies": {{
    "my-package": "workspace:*"
  }}
}}
```

## 更多信息

- [pnpm workspaces](https://pnpm.io/workspaces)
- [Monorepo 最佳实践](https://monorepo.tools/)
"""
        readme_path = self.project_path / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

    def init_git_repo(self) -> bool:
        """
        初始化 Git 仓库

        Returns:
            bool: 是否成功初始化
        """
        try:
            # 检查是否已经是 Git 仓库
            git_dir = self.project_path / ".git"
            if git_dir.exists():
                return True

            # 初始化 Git 仓库
            result = subprocess.run(
                ["git", "init"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # 添加初始提交
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit from mono-kickstart"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return True
            else:
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Git 未安装或执行失败
            return False

    def check_existing_directory(self) -> tuple[bool, list[str]]:
        """
        检查目录是否已存在以及包含哪些文件

        Returns:
            tuple[bool, list[str]]: (目录是否存在, 现有文件列表)
        """
        if not self.project_path.exists():
            return False, []

        # 获取目录中的所有文件和目录（排除隐藏文件）
        existing_items = [
            item.name
            for item in self.project_path.iterdir()
            if not item.name.startswith(".")
        ]

        return True, existing_items

    def create_project(self, force: bool = False) -> tuple[bool, Optional[str]]:
        """
        创建完整项目

        Args:
            force: 是否强制覆盖已存在的目录

        Returns:
            tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        try:
            # 检查目录是否已存在
            exists, existing_items = self.check_existing_directory()

            if exists and existing_items and not force:
                return (
                    False,
                    f"目录 {self.project_path} 已存在且不为空。使用 --force 参数强制覆盖。",
                )

            # 创建目录结构
            self.create_directory_structure()

            # 创建配置文件
            self.create_workspace_config()

            # 创建 .gitignore
            self.create_gitignore()

            # 创建 README
            self.create_readme()

            # 初始化 Git 仓库
            git_success = self.init_git_repo()
            if not git_success:
                # Git 初始化失败不是致命错误，只是警告
                pass

            return True, None

        except PermissionError as e:
            return False, f"权限错误: {e}"
        except OSError as e:
            return False, f"文件系统错误: {e}"
        except Exception as e:
            return False, f"未知错误: {e}"
