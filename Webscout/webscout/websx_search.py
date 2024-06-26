from __future__ import annotations

import os
from typing import Any, Dict, Optional
import json
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from importlib import metadata

try:
    from pydantic.v1 import *  
except ImportError:
    from pydantic import *  


try:
    _PYDANTIC_MAJOR_VERSION: int = int(metadata.version("pydantic").split(".")[0])
except metadata.PackageNotFoundError:
    _PYDANTIC_MAJOR_VERSION = 0




def env_var_is_set(env_var: str) -> bool:
    """Check if an environment variable is set.

    Args:
        env_var (str): The name of the environment variable.

    Returns:
        bool: True if the environment variable is set, False otherwise.
    """
    return env_var in os.environ and os.environ[env_var] not in (
        "",
        "0",
        "false",
        "False",
    )


def get_from_dict_or_env(
    data: Dict[str, Any], key: str, env_key: str, default: Optional[str] = None
) -> str:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    else:
        return get_from_env(key, env_key, default=default)


def get_from_env(key: str, env_key: str, default: Optional[str] = None) -> str:
    """Get a value from a dictionary or an environment variable."""
    if env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {key}, please add an environment variable"
            f" `{env_key}` which contains it, or pass"
            f" `{key}` as a named parameter."
        )


def _get_default_params() -> dict:
    return {"language": "en", "format": "json"}


class WEBSXResults(dict):
    """Dict like wrapper around search api results."""

    _data: str = ""

    def __init__(self, data: str):
        """Take a raw result from WEBSX and make it into a dict like object."""
        json_data = json.loads(data)
        super().__init__(json_data)
        self.__dict__ = self

    def __str__(self) -> str:
        """Text representation of WEBSX result."""
        return self._data

    @property
    def results(self) -> Any:
        """Silence mypy for accessing this field.

        :meta private:
        """
        return self.get("results")

    @property
    def answers(self) -> Any:
        """Helper accessor on the json result."""
        return self.get("answers")


class WEBSX(BaseModel):

    _result: WEBSXResults = PrivateAttr()
    WEBSX_host: str = "https://8080-01j06maryf9vpw2mm2afqkypps.cloudspaces.litng.ai/"
    unsecure: bool = False
    params: dict = Field(default_factory=_get_default_params)
    headers: Optional[dict] = None
    engines: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    query_suffix: Optional[str] = ""
    k: int = 10
    aiosession: Optional[Any] = None

    @validator("unsecure")
    def disable_ssl_warnings(cls, v: bool) -> bool:
        """Disable SSL warnings."""
        if v:
            # requests.urllib3.disable_warnings()
            try:
                import urllib3

                urllib3.disable_warnings()
            except ImportError as e:
                print(e)  # noqa: T201

        return v

    @root_validator()
    def validate_params(cls, values: Dict) -> Dict:
        """Validate that custom WEBSX params are merged with default ones."""
        user_params = values["params"]
        default = _get_default_params()
        values["params"] = {**default, **user_params}

        engines = values.get("engines")
        if engines:
            values["params"]["engines"] = ",".join(engines)

        categories = values.get("categories")
        if categories:
            values["params"]["categories"] = ",".join(categories)

        WEBSX_host = get_from_dict_or_env(values, "WEBSX_host", "WEBSX_HOST")
        if not WEBSX_host.startswith("http"):
            print(  # noqa: T201
                f"Warning: missing the url scheme on host \
                ! assuming secure https://{WEBSX_host} "
            )
            WEBSX_host = "https://" + WEBSX_host
        elif WEBSX_host.startswith("http://"):
            values["unsecure"] = True
            cls.disable_ssl_warnings(True)
        values["WEBSX_host"] = WEBSX_host

        return values

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def _WEBSX_api_query(self, params: dict) -> WEBSXResults:
        """Actual request to WEBSX API."""
        raw_result = requests.get(
            self.WEBSX_host,
            headers=self.headers,
            params=params,
            verify=not self.unsecure,
        )
        # test if http result is ok
        if not raw_result.ok:
            raise ValueError("WEBSX API returned an error: ", raw_result.text)
        res = WEBSXResults(raw_result.text)
        self._result = res
        return res

    async def _aWEBSX_api_query(self, params: dict) -> WEBSXResults:
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.WEBSX_host,
                    headers=self.headers,
                    params=params,
                    ssl=(lambda: False if self.unsecure else None)(),
                ) as response:
                    if not response.ok:
                        raise ValueError("WEBSX API returned an error: ", response.text)
                    result = WEBSXResults(await response.text())
                    self._result = result
        else:
            async with self.aiosession.get(
                self.WEBSX_host,
                headers=self.headers,
                params=params,
                verify=not self.unsecure,
            ) as response:
                if not response.ok:
                    raise ValueError("WEBSX API returned an error: ", response.text)
                result = WEBSXResults(await response.text())
                self._result = result

        return result

    def run(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix

        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix

        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)

        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)

        res = self._WEBSX_api_query(params)

        if len(res.answers) > 0:
            toret = res.answers[0]

        # only return the content of the results list
        elif len(res.results) > 0:
            toret = "\n\n".join([r.get("content", "") for r in res.results[: self.k]])
        else:
            toret = "No good search result found"

        return toret

    async def arun(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        """Asynchronously version of `run`."""
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix

        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix

        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)

        res = await self._aWEBSX_api_query(params)

        if len(res.answers) > 0:
            toret = res.answers[0]

        # only return the content of the results list
        elif len(res.results) > 0:
            toret = "\n\n".join([r.get("content", "") for r in res.results[: self.k]])
        else:
            toret = "No good search result found"

        return toret

    def results(
        self,
        query: str,
        num_results: int,
        engines: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """Run query through WEBSX API and returns the results with metadata.

        Args:
            query: The query to search for.
            query_suffix: Extra suffix appended to the query.
            num_results: Limit the number of results to return.
            engines: List of engines to use for the query.
            categories: List of categories to use for the query.
            **kwargs: extra parameters to pass to the WEBSX API.

        Returns:
            Dict with the following keys:
            {
                snippet:  The description of the result.
                title:  The title of the result.
                link: The link to the result.
                engines: The engines used for the result.
                category: WEBSX category of the result.
            }

        """
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}
        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)
        results = self._WEBSX_api_query(params).results[:num_results]
        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]

        return [
            {
                "snippet": result.get("content", ""),
                "title": result["title"],
                "link": result["url"],
                "engines": result["engines"],
                "category": result["category"],
            }
            for result in results
        ]

    async def aresults(
        self,
        query: str,
        num_results: int,
        engines: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """Asynchronously query with json results.

        Uses aiohttp. See `results` for more info.
        """
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += " " + query_suffix
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        results = (await self._aWEBSX_api_query(params)).results[:num_results]
        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]

        return [
            {
                "snippet": result.get("content", ""),
                "title": result["title"],
                "link": result["url"],
                "engines": result["engines"],
                "category": result["category"],
            }
            for result in results
        ]

