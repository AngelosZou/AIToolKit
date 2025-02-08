# 用于将缓存数据写入json文件保存或从json数据中读取数据
import json


class Configure:
    instance = None

    def __init__(self, active_model: dict = None, google_api_key: str = "", google_cse_id: str = "",
                 active_ai: str = None, openai_api_key: str = "", siliconflow_api_key: str = "",
                 max_skip_input_turn: int = -1, deepseek_api_key: str = ""):
        if active_model is None:
            active_model = {}
        self.active_model = active_model
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id
        self.active_ai: str = active_ai
        self.openai_api_key = openai_api_key
        self.siliconflow_api_key = siliconflow_api_key
        self.max_skip_input_turn: int = max_skip_input_turn # 最大连续跳过用户输入轮次。超过此轮次将强制停止AI控制。为-1时不限制
        self.deepseek_api_key = deepseek_api_key

    def save(self):
        save_cache(self)

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = load_cache()
        return cls.instance


def load_cache() -> Configure:
    """从文件加载缓存数据"""
    try:
        with open("cache.json", "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            return Configure(**cache_data)
    except Exception:
        cache_data = {}
    return Configure(**cache_data)


def save_cache(cache_data: Configure):
    """保存缓存数据到文件"""
    with open("cache.json", "w", encoding="utf-8") as f:
        json.dump(cache_data.__dict__, f, ensure_ascii=False, indent=2)


class CatchInformation:
    """用于缓存捕捉到的信息"""
    instance = None

    def __init__(self):
        self.info = ""

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance


class SearchResult:
    """用于缓存搜索结果"""
    instance = None

    def __init__(self):
        self.url = None
        self.content = None
        self.search_results = []

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance


class GlobalFlag:
    """用于全局标志位"""
    instance = None

    def __init__(self):
        self.skip_user_input = False
        self.fail_test = False
        self.force_stop = False
        self.is_communicating = False
        self.is_app_running = False
        self.finish_init = False

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance
