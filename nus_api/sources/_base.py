import abc
import requests
import contextlib
from dataclasses import dataclass
from typing import Union, Optional, Iterator

from ..config import Configuration
from ..reqdata import ReqData
from ..types._base import BaseType
from .. import utils


@dataclass(frozen=True)
class SourceConfig:
    load_from_cache: bool = True
    store_to_cache: bool = True
    chunk_size: int = 4096
    cache_headers: bool = True


class BaseSource(abc.ABC):
    def __init__(self, base_reqdata: ReqData, config: Optional[SourceConfig], *, verify_tls: bool = True):
        self._base_reqdata = ReqData(
            path='',
            headers={'User-Agent': Configuration.default_user_agent}
        )
        self._base_reqdata += base_reqdata

        self._config = config if config is not None else SourceConfig()
        self._verify_tls = verify_tls

    # TODO: ratelimit by hostname
    def _get(self, data: Union[ReqData, BaseType]) -> requests.Response:
        if isinstance(data, BaseType):
            reqdata = data._merged_reqdata
        else:
            reqdata = self._base_reqdata + data
        return requests.get(
            url=reqdata.path,
            headers=reqdata.headers,
            params=reqdata.params,
            cert=reqdata.cert,
            verify=self._verify_tls,
            stream=True,
            allow_redirects=False
        )

    @contextlib.contextmanager
    def get_iterator(self, type_inst: BaseType) -> Iterator[utils.BytesIterator]:
        cache_path = type_inst._cache_path
        if self._config.load_from_cache and type_inst.is_cached():
            with open(cache_path, 'rb') as f:
                yield utils.BytesIterator(lambda: f.read(self._config.chunk_size))
        else:
            with type_inst._download() as res:
                res_it = res.iter_content(self._config.chunk_size)
                if self._config.store_to_cache:
                    if self._config.cache_headers:
                        self.__cache_headers(res, f'{cache_path}.headers')
                    with utils.CachingIterator(cache_path, lambda: next(res_it)) as it:
                        yield it
                else:
                    yield utils.BytesIterator(lambda: next(res_it))

    @staticmethod
    def __cache_headers(response: requests.Response, path: str) -> None:
        # it's surprisingly difficult to get raw response headers
        # this code is partially based on requests-toolbelt: https://github.com/requests/toolbelt/blob/69e2487494b7f8a5951ed92ed014137b8381814c/requests_toolbelt/utils/dump.py#L88

        utils.create_dirs_for_file(path)
        with open(path, 'wb') as f:
            f.write(b'HTTP/' + {9: b'0.9', 10: b'1.0', 11: b'1.1'}[response.raw.version])
            f.write(b' ' + str(response.status_code).encode() + b' ' + response.reason.encode())
            f.write(b'\r\n')

            headers = response.raw.headers
            for key in headers:
                for value in headers.getlist(key):
                    f.write(key.encode() + b': ' + value.encode() + b'\r\n')
            f.write(b'\r\n')
