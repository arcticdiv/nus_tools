import abc
import requests
from urllib.parse import urljoin
from typing import Dict

from ..config import Configuration


class BaseSource(abc.ABC):
    def __init__(self, base_url: str, *, default_params: Dict = None, verify_tls: bool = True):
        self._base_url = base_url
        self._default_params = default_params if default_params is not None else {}
        self._verify_tls = verify_tls

    # TODO: ratelimit by hostname
    def _get(self, *, path: str, params: Dict[str, str] = {}, headers: Dict[str, str] = {}, **kwargs) -> requests.Response:
        if self._default_params:
            params = {**self._default_params, **params}

        return requests.get(
            urljoin(self._base_url, path),
            headers={
                'User-Agent': Configuration.default_user_agent,
                **headers
            },
            params=params,
            verify=self._verify_tls,
            **kwargs
        )
