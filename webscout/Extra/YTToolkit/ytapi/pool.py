import concurrent.futures
from typing import Callable, List, Any


def collect(func: Callable, args: List[Any]) -> List[Any]:
    max_workers = len(args) or 1
    with concurrent.futures.ThreadPoolExecutor(max_workers) as exe:
        return list(exe.map(func, args))
