import os
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
    def _get(self, data: Union[ReqData, BaseType], **kwargs) -> requests.Response:
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
            **kwargs
        )

    @contextlib.contextmanager
    def get_iterator(self, type_inst: BaseType) -> Iterator[utils.BytesIterator]:
        cache_path = type_inst._cache_path
        if self._config.load_from_cache and os.path.isfile(cache_path):
            with open(cache_path, 'rb') as f:
                yield utils.BytesIterator(lambda: f.read(self._config.chunk_size))
        else:
            with type_inst._download() as res:
                res_it = res.iter_content(self._config.chunk_size)
                if self._config.store_to_cache:
                    # TODO: save response headers as well?
                    with utils.CachingIterator(cache_path, lambda: next(res_it)) as it:
                        yield it
                else:
                    yield utils.BytesIterator(lambda: next(res_it))
