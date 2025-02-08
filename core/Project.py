from pathlib import Path


class Project:
    """项目类"""
    instance = None

    def __init__(self, name: str):
        self.name = name
        self.root_path = Path(f"./projects/{self.name}")
        self.dirs = {
            "history": self.root_path / "history",
            "ref": self.root_path / "ref_space",
            "code": self.root_path / "code_space"
        }
        Project.instance = self

    def setup(self):
        """创建项目目录结构"""
        self.root_path.mkdir(parents=True, exist_ok=True)
        for d in self.dirs.values():
            d.mkdir(exist_ok=True)

    @classmethod
    def list_projects(cls) -> list[str]:
        """获取所有项目列表"""
        projects_dir = Path("./projects")
        return [d.name for d in projects_dir.iterdir() if d.is_dir()]
