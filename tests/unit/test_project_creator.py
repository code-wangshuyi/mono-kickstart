"""
项目创建器的单元测试
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mono_kickstart.project_creator import ProjectCreator


class TestProjectCreator:
    """测试 ProjectCreator 类"""

    def test_init(self, tmp_path):
        """测试初始化"""
        project_name = "test-project"
        creator = ProjectCreator(project_name, tmp_path)

        assert creator.project_name == project_name
        assert creator.project_path == tmp_path

    def test_create_directory_structure(self, tmp_path):
        """测试创建目录结构"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        creator.create_directory_structure()

        # 验证主目录存在
        assert project_path.exists()
        assert project_path.is_dir()

        # 验证子目录存在
        assert (project_path / "apps").exists()
        assert (project_path / "packages").exists()
        assert (project_path / "shared").exists()

        # 验证 .gitkeep 文件存在
        assert (project_path / "apps" / ".gitkeep").exists()
        assert (project_path / "packages" / ".gitkeep").exists()
        assert (project_path / "shared" / ".gitkeep").exists()

    def test_create_directory_structure_idempotent(self, tmp_path):
        """测试创建目录结构的幂等性"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        # 第一次创建
        creator.create_directory_structure()
        # 第二次创建（应该不报错）
        creator.create_directory_structure()

        # 验证目录仍然存在
        assert project_path.exists()
        assert (project_path / "apps").exists()

    def test_create_workspace_config(self, tmp_path):
        """测试创建 workspace 配置文件"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        creator.create_workspace_config()

        # 验证 package.json 存在
        package_json_path = project_path / "package.json"
        assert package_json_path.exists()

        # 验证 package.json 内容
        with open(package_json_path, "r", encoding="utf-8") as f:
            package_json = json.load(f)

        assert package_json["name"] == project_name
        assert package_json["version"] == "0.1.0"
        assert package_json["private"] is True
        assert package_json["workspaces"] == ["apps/*", "packages/*"]
        assert "scripts" in package_json
        assert "dev" in package_json["scripts"]
        assert "build" in package_json["scripts"]
        assert "test" in package_json["scripts"]

        # 验证 pnpm-workspace.yaml 存在
        pnpm_workspace_path = project_path / "pnpm-workspace.yaml"
        assert pnpm_workspace_path.exists()

        # 验证 pnpm-workspace.yaml 内容
        with open(pnpm_workspace_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "packages:" in content
        assert "'apps/*'" in content
        assert "'packages/*'" in content

    def test_create_gitignore(self, tmp_path):
        """测试创建 .gitignore 文件"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        creator.create_gitignore()

        # 验证 .gitignore 存在
        gitignore_path = project_path / ".gitignore"
        assert gitignore_path.exists()

        # 验证 .gitignore 内容
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键条目
        assert "node_modules/" in content
        assert "dist/" in content
        assert ".env" in content
        assert "__pycache__/" in content
        assert ".DS_Store" in content

    def test_create_readme(self, tmp_path):
        """测试创建 README.md 文件"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        creator.create_readme()

        # 验证 README.md 存在
        readme_path = project_path / "README.md"
        assert readme_path.exists()

        # 验证 README.md 内容
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert project_name in content
        assert "项目结构" in content
        assert "开始使用" in content
        assert "pnpm install" in content

    def test_init_git_repo_success(self, tmp_path):
        """测试成功初始化 Git 仓库"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        # 创建一些文件以便提交
        (project_path / "test.txt").write_text("test")

        result = creator.init_git_repo()

        # 验证返回值
        assert result is True

        # 验证 .git 目录存在
        assert (project_path / ".git").exists()

    def test_init_git_repo_already_exists(self, tmp_path):
        """测试 Git 仓库已存在的情况"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        (project_path / ".git").mkdir()
        creator = ProjectCreator(project_name, project_path)

        result = creator.init_git_repo()

        # 验证返回值（已存在也返回 True）
        assert result is True

    def test_init_git_repo_git_not_installed(self, tmp_path):
        """测试 Git 未安装的情况"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = creator.init_git_repo()

        # 验证返回值（失败返回 False）
        assert result is False

    def test_init_git_repo_timeout(self, tmp_path):
        """测试 Git 初始化超时的情况"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            result = creator.init_git_repo()

        # 验证返回值（超时返回 False）
        assert result is False

    def test_check_existing_directory_not_exists(self, tmp_path):
        """测试检查不存在的目录"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        exists, items = creator.check_existing_directory()

        assert exists is False
        assert items == []

    def test_check_existing_directory_empty(self, tmp_path):
        """测试检查空目录"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        exists, items = creator.check_existing_directory()

        assert exists is True
        assert items == []

    def test_check_existing_directory_with_files(self, tmp_path):
        """测试检查包含文件的目录"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        (project_path / "file1.txt").write_text("test")
        (project_path / "file2.txt").write_text("test")
        (project_path / ".hidden").write_text("test")  # 隐藏文件应该被忽略
        creator = ProjectCreator(project_name, project_path)

        exists, items = creator.check_existing_directory()

        assert exists is True
        assert len(items) == 2
        assert "file1.txt" in items
        assert "file2.txt" in items
        assert ".hidden" not in items

    def test_create_project_success(self, tmp_path):
        """测试成功创建项目"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        success, error = creator.create_project()

        # 验证返回值
        assert success is True
        assert error is None

        # 验证目录结构
        assert project_path.exists()
        assert (project_path / "apps").exists()
        assert (project_path / "packages").exists()
        assert (project_path / "shared").exists()

        # 验证配置文件
        assert (project_path / "package.json").exists()
        assert (project_path / "pnpm-workspace.yaml").exists()

        # 验证其他文件
        assert (project_path / ".gitignore").exists()
        assert (project_path / "README.md").exists()

    def test_create_project_existing_directory_without_force(self, tmp_path):
        """测试在已存在目录上创建项目（不使用 force）"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        (project_path / "existing.txt").write_text("test")
        creator = ProjectCreator(project_name, project_path)

        success, error = creator.create_project(force=False)

        # 验证返回值
        assert success is False
        assert error is not None
        assert "已存在" in error
        assert "--force" in error

    def test_create_project_existing_directory_with_force(self, tmp_path):
        """测试在已存在目录上创建项目（使用 force）"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        (project_path / "existing.txt").write_text("test")
        creator = ProjectCreator(project_name, project_path)

        success, error = creator.create_project(force=True)

        # 验证返回值
        assert success is True
        assert error is None

        # 验证项目文件已创建
        assert (project_path / "package.json").exists()

    def test_create_project_empty_directory(self, tmp_path):
        """测试在空目录上创建项目"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        project_path.mkdir()
        creator = ProjectCreator(project_name, project_path)

        success, error = creator.create_project()

        # 验证返回值（空目录应该成功）
        assert success is True
        assert error is None

    def test_create_project_permission_error(self, tmp_path):
        """测试权限错误"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        with patch.object(Path, "mkdir", side_effect=PermissionError("Permission denied")):
            success, error = creator.create_project()

        # 验证返回值
        assert success is False
        assert error is not None
        assert "权限错误" in error

    def test_create_project_os_error(self, tmp_path):
        """测试文件系统错误"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        with patch.object(Path, "mkdir", side_effect=OSError("Disk full")):
            success, error = creator.create_project()

        # 验证返回值
        assert success is False
        assert error is not None
        assert "文件系统错误" in error

    def test_create_project_git_init_failure_not_fatal(self, tmp_path):
        """测试 Git 初始化失败不影响项目创建"""
        project_name = "test-project"
        project_path = tmp_path / project_name
        creator = ProjectCreator(project_name, project_path)

        with patch.object(creator, "init_git_repo", return_value=False):
            success, error = creator.create_project()

        # 验证项目仍然创建成功
        assert success is True
        assert error is None
        assert (project_path / "package.json").exists()
