# Import tool modules so they register themselves
from tools import calculator, date_time, search, weather, tasks, memory, files  # noqa: F401
from tools.registry import registry

__all__ = ["registry"]
