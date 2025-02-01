# 用于将缓存数据写入json文件保存或从json数据中读取数据
import json


class Cache:
    instance = None

    def __init__(self, models: list = None, active_model: str = None):
        if models is None:
            models = []
        self.models = models
        self.active_model = active_model

    def save(self):
        save_cache(self)

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = load_cache()
        return cls.instance

def load_cache()-> Cache:
    """从文件加载缓存数据"""
    try:
        with open("cache.json", "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            return Cache(**cache_data)
    except Exception:
        cache_data = {}
    return Cache(**cache_data)

def save_cache(cache_data: Cache):
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