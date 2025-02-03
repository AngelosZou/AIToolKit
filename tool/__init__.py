import pkgutil
import importlib

# 自动加载所有命令模块
__all__ = []
for _, module_name, _ in pkgutil.iter_modules(__path__):
    if not module_name.startswith('_'):
        importlib.import_module(f'.{module_name}', __name__)
        __all__.append(module_name)