"""项目创建器的基于属性的测试

本模块使用 Hypothesis 框架测试项目创建器的通用属性。
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given, settings, strategies as st, HealthCheck

from mono_kickstart.project_creator import ProjectCreator


# 定义测试数据生成策略

@st.composite
def project_name_strategy(draw):
    """生成有效的项目名称策略
    
    项目名称应该是有效的目录名，不包含特殊字符
    """
    # 使用字母、数字、连字符和下划线
    return draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ),
        min_size=1,
        max_size=50
    ).filter(lambda s: s and not s.startswith('-') and not s.startswith('_')))


@st.composite
def project_path_strategy(draw, base_path):
    """生成项目路径策略
    
    Args:
        base_path: 基础临时目录路径
    """
    # 生成相对路径（可能包含子目录）
    depth = draw(st.integers(min_value=0, max_value=2))
    
    if depth == 0:
        return base_path
    
    path_parts = [draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ),
        min_size=1,
        max_size=20
    ).filter(lambda s: s and not s.startswith('-'))) for _ in range(depth)]
    
    result_path = base_path
    for part in path_parts:
        result_path = result_path / part
    
    return result_path


class TestProjectDirectoryStructureConsistency:
    """测试属性 14: 项目目录结构一致性
    
    **Validates: Requirements 3.1**
    """
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_standard_directories_always_created(self, project_name):
        """验证标准目录总是被创建
        
        对于任何项目名称，项目创建器应该生成包含标准目录
        (apps/, packages/, shared/) 的项目结构。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            assert error is None
            
            # 验证标准目录存在
            assert (project_path / "apps").exists(), "apps/ directory not created"
            assert (project_path / "apps").is_dir(), "apps/ is not a directory"
            
            assert (project_path / "packages").exists(), "packages/ directory not created"
            assert (project_path / "packages").is_dir(), "packages/ is not a directory"
            
            assert (project_path / "shared").exists(), "shared/ directory not created"
            assert (project_path / "shared").is_dir(), "shared/ is not a directory"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_standard_files_always_created(self, project_name):
        """验证标准文件总是被创建
        
        对于任何项目名称，项目创建器应该生成标准文件
        (.gitignore, README.md, package.json)。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 验证标准文件存在
            assert (project_path / ".gitignore").exists(), ".gitignore not created"
            assert (project_path / ".gitignore").is_file(), ".gitignore is not a file"
            
            assert (project_path / "README.md").exists(), "README.md not created"
            assert (project_path / "README.md").is_file(), "README.md is not a file"
            
            assert (project_path / "package.json").exists(), "package.json not created"
            assert (project_path / "package.json").is_file(), "package.json is not a file"
            
            assert (project_path / "pnpm-workspace.yaml").exists(), "pnpm-workspace.yaml not created"
            assert (project_path / "pnpm-workspace.yaml").is_file(), "pnpm-workspace.yaml is not a file"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_gitkeep_files_in_empty_directories(self, project_name):
        """验证空目录包含 .gitkeep 文件
        
        对于任何项目名称，标准目录应该包含 .gitkeep 文件
        以确保空目录被 Git 跟踪。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 验证 .gitkeep 文件存在
            assert (project_path / "apps" / ".gitkeep").exists(), "apps/.gitkeep not created"
            assert (project_path / "packages" / ".gitkeep").exists(), "packages/.gitkeep not created"
            assert (project_path / "shared" / ".gitkeep").exists(), "shared/.gitkeep not created"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_package_json_structure_consistency(self, project_name):
        """验证 package.json 结构一致性
        
        对于任何项目名称，package.json 应该包含标准字段
        (name, version, private, workspaces, scripts)。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 读取 package.json
            package_json_path = project_path / "package.json"
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_json = json.load(f)
            
            # 验证标准字段存在
            assert "name" in package_json, "package.json missing 'name' field"
            assert package_json["name"] == project_name, "package.json name doesn't match project name"
            
            assert "version" in package_json, "package.json missing 'version' field"
            assert isinstance(package_json["version"], str), "version should be a string"
            
            assert "private" in package_json, "package.json missing 'private' field"
            assert package_json["private"] is True, "package.json should be private"
            
            assert "workspaces" in package_json, "package.json missing 'workspaces' field"
            assert isinstance(package_json["workspaces"], list), "workspaces should be a list"
            assert "apps/*" in package_json["workspaces"], "workspaces missing 'apps/*'"
            assert "packages/*" in package_json["workspaces"], "workspaces missing 'packages/*'"
            
            assert "scripts" in package_json, "package.json missing 'scripts' field"
            assert isinstance(package_json["scripts"], dict), "scripts should be a dict"
            assert "dev" in package_json["scripts"], "scripts missing 'dev'"
            assert "build" in package_json["scripts"], "scripts missing 'build'"
            assert "test" in package_json["scripts"], "scripts missing 'test'"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pnpm_workspace_structure_consistency(self, project_name):
        """验证 pnpm-workspace.yaml 结构一致性
        
        对于任何项目名称，pnpm-workspace.yaml 应该包含
        标准的 workspace 配置。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 读取 pnpm-workspace.yaml
            pnpm_workspace_path = project_path / "pnpm-workspace.yaml"
            with open(pnpm_workspace_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 验证包含标准配置
            assert "packages:" in content, "pnpm-workspace.yaml missing 'packages:'"
            assert "'apps/*'" in content, "pnpm-workspace.yaml missing 'apps/*'"
            assert "'packages/*'" in content, "pnpm-workspace.yaml missing 'packages/*'"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_gitignore_contains_standard_patterns(self, project_name):
        """验证 .gitignore 包含标准忽略模式
        
        对于任何项目名称，.gitignore 应该包含常见的
        忽略模式（node_modules, dist, .env 等）。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 读取 .gitignore
            gitignore_path = project_path / ".gitignore"
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 验证包含标准忽略模式
            standard_patterns = [
                "node_modules/",
                "dist/",
                "build/",
                ".env",
                ".DS_Store",
                "__pycache__/",
                "*.log"
            ]
            
            for pattern in standard_patterns:
                assert pattern in content, f".gitignore missing pattern: {pattern}"
    
    @given(project_name=project_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_readme_contains_project_name(self, project_name):
        """验证 README.md 包含项目名称
        
        对于任何项目名称，README.md 应该包含该项目名称。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            success, error = creator.create_project()
            
            # 验证创建成功
            assert success is True, f"Project creation failed: {error}"
            
            # 读取 README.md
            readme_path = project_path / "README.md"
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 验证包含项目名称
            assert project_name in content, f"README.md doesn't contain project name: {project_name}"
    
    @given(
        project_name=project_name_strategy(),
        iterations=st.integers(min_value=2, max_value=3)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_idempotent_creation(self, project_name, iterations):
        """验证项目创建的幂等性
        
        对于任何项目名称，多次创建项目（使用 force=True）
        应该产生相同的目录结构。
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            project_path = tmp_path / project_name
            
            creator = ProjectCreator(project_name, project_path)
            
            # 多次创建项目
            for i in range(iterations):
                success, error = creator.create_project(force=True)
                assert success is True, f"Project creation failed on iteration {i}: {error}"
            
            # 验证最终结构仍然正确
            assert (project_path / "apps").exists()
            assert (project_path / "packages").exists()
            assert (project_path / "shared").exists()
            assert (project_path / "package.json").exists()
            assert (project_path / "README.md").exists()
            
            # 验证 package.json 仍然有效
            with open(project_path / "package.json", "r", encoding="utf-8") as f:
                package_json = json.load(f)
            assert package_json["name"] == project_name
    
    @given(
        project_name1=project_name_strategy(),
        project_name2=project_name_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_names_same_structure(self, project_name1, project_name2):
        """验证不同项目名称产生相同的目录结构
        
        对于任何两个不同的项目名称，应该产生相同的目录结构
        （除了项目名称本身）。
        """
        # 跳过相同名称的情况
        if project_name1 == project_name2:
            return
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # 创建第一个项目
            project_path1 = tmp_path / project_name1
            creator1 = ProjectCreator(project_name1, project_path1)
            success1, error1 = creator1.create_project()
            assert success1 is True, f"Project 1 creation failed: {error1}"
            
            # 创建第二个项目
            project_path2 = tmp_path / project_name2
            creator2 = ProjectCreator(project_name2, project_path2)
            success2, error2 = creator2.create_project()
            assert success2 is True, f"Project 2 creation failed: {error2}"
            
            # 验证两个项目有相同的目录结构
            dirs_to_check = ["apps", "packages", "shared"]
            for dir_name in dirs_to_check:
                assert (project_path1 / dir_name).exists(), f"Project 1 missing {dir_name}"
                assert (project_path2 / dir_name).exists(), f"Project 2 missing {dir_name}"
            
            # 验证两个项目有相同的文件
            files_to_check = [".gitignore", "README.md", "package.json", "pnpm-workspace.yaml"]
            for file_name in files_to_check:
                assert (project_path1 / file_name).exists(), f"Project 1 missing {file_name}"
                assert (project_path2 / file_name).exists(), f"Project 2 missing {file_name}"
            
            # 验证 package.json 结构相同（除了 name 字段）
            with open(project_path1 / "package.json", "r", encoding="utf-8") as f:
                package1 = json.load(f)
            with open(project_path2 / "package.json", "r", encoding="utf-8") as f:
                package2 = json.load(f)
            
            # 比较除 name 外的所有字段
            assert package1["version"] == package2["version"]
            assert package1["private"] == package2["private"]
            assert package1["workspaces"] == package2["workspaces"]
            assert package1["scripts"] == package2["scripts"]
