import asyncio
from concurrent.futures import Future
from threading import Thread
import sys
from types import TracebackType
from typing import Any, Awaitable, Dict, Optional, Type, Union
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        # If WindowsSelectorEventLoopPolicy is not available, do nothing
        pass
from .webscout_search_async import AsyncWEBS


class WEBS(AsyncWEBS):
    _loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    Thread(target=_loop.run_forever, daemon=True).start()  # Start the event loop run in a separate thread.

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        proxies: Union[Dict[str, str], str, None] = None,
        timeout: Optional[int] = 10,
    ) -> None:
        super().__init__(headers=headers, proxies=proxies, timeout=timeout)
        self._exit_done = False

    def __enter__(self) -> "WEBS":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._close_session()

    def __del__(self) -> None:
        self._close_session()

    def _close_session(self) -> None:
        """Close the curl-cffi async session."""
        if self._exit_done is False:
            # Ensure self._asession.close() is a coroutine
            coro = self._asession.close()
            # Check if coro is a coroutine object
            if asyncio.iscoroutine(coro):
                self._run_async_in_thread(coro)
            self._exit_done = True

    def _run_async_in_thread(self, coro: Awaitable[Any]) -> Any:
        """Runs an async coroutine in a separate thread."""
        future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, self._loop)
        result = future.result()
        return result

    def text(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().text(*args, **kwargs))

    def images(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().images(*args, **kwargs))

    def videos(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().videos(*args, **kwargs))

    def news(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().news(*args, **kwargs))

    def answers(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().answers(*args, **kwargs))

    def suggestions(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().suggestions(*args, **kwargs))

    def maps(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().maps(*args, **kwargs))

    def translate(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_async_in_thread(super().translate(*args, **kwargs))