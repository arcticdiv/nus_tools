import os
import abc
import contextlib
import requests
import urllib3
from requests.adapters import HTTPAdapter
from enum import Enum
from dataclasses import dataclass
from typing import Generic, TypeVar, Union, Optional, overload

from .. import utils, cachemanager
from ..config import Configuration
from ..reqdata import ReqData
from ..types._base import TypeLoadConfig, BaseType, BaseTypeLoadable


class StatusCheckMode(Enum):
    NONE, CHECK_ERROR, REQUIRE_200 = range(3)


class ResponseStatusError(Exception):
    status: int

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


_TBaseType = TypeVar('_TBaseType', bound=BaseType)
_TBaseTypeLoadable = TypeVar('_TBaseTypeLoadable', bound=BaseTypeLoadable)


class UnloadableType(Generic[_TBaseType]):
    def __init__(self, source: 'BaseSource', reqdata: ReqData):
        self.source = source
        self.reqdata = reqdata

    @contextlib.contextmanager
    def get_reader(self):
        yield from self.source.get_reader(self.reqdata)


# TODO: implement dependencies between options
@dataclass(frozen=True)
class SourceConfig:
    load_from_cache: bool = True
    store_to_cache: bool = True
    chunk_size: int = Configuration.default_chunk_size  # note: with streamed requests, this value is the size of compressed chunks (i.e. the size of returned chunks may be larger)
    response_status_checking: StatusCheckMode = StatusCheckMode.REQUIRE_200
    store_failed_requests: bool = True
    store_metadata: bool = True
    http_retries: int = 3
    requests_per_second: float = 5.0
    type_load_config: TypeLoadConfig = TypeLoadConfig()


class BaseSource(abc.ABC):
    def __init__(self, base_reqdata: ReqData, config: Optional[SourceConfig], *, verify_tls: bool = True):
        # build base request data
        self._base_reqdata = ReqData(
            path='',
            headers={'User-Agent': Configuration.default_user_agent}
        )
        self._base_reqdata += base_reqdata

        # use supplied config or default
        self._config = config if config is not None else SourceConfig()

        # set up retries
        self._session = requests.Session()
        self._session.verify = verify_tls
        adapter = HTTPAdapter(
            max_retries=urllib3.util.retry.Retry(
                total=self._config.http_retries,
                backoff_factor=0.5,
                redirect=False,
                raise_on_redirect=False,
                status_forcelist={420, 429, *range(500, 520)},
                raise_on_status=False
            )
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)

    @overload
    def _create_type(self, loadable_inst: _TBaseTypeLoadable, reqdata: ReqData) -> _TBaseTypeLoadable:
        ...

    @overload
    def _create_type(self, reqdata: ReqData) -> UnloadableType:
        ...

    def _create_type(self, loadable_or_reqdata, reqdata=None):
        if isinstance(loadable_or_reqdata, BaseTypeLoadable):
            with self.get_reader(reqdata) as reader:
                return loadable_or_reqdata.load(reader, self._config.type_load_config)
        else:
            return UnloadableType(self, loadable_or_reqdata)

    def get_nocache(self, reqdata: ReqData) -> requests.Response:
        res = self.__get_nocache_internal(reqdata)
        self.__check_status(res)
        return res

    @contextlib.contextmanager
    def get_reader(self, reqdata: ReqData):
        with self.__get_reader_internal(reqdata) as reader:
            if reader.metadata:  # if this is None, request was loaded from cache and successful
                self.__check_status(reader.metadata)
            yield reader

    # TODO: ratelimit by cls instead of self
    @utils.ratelimit.limit(lambda self: self._config.requests_per_second)
    def __get_nocache_internal(self, reqdata: ReqData, already_merged: bool = False) -> requests.Response:
        # optimization to avoid having to merge twice
        if not already_merged:
            reqdata = self._base_reqdata + reqdata

        res = self._session.get(
            url=reqdata.path,
            headers=reqdata.headers,
            params=reqdata.params,
            cert=reqdata.cert,
            stream=True,
            allow_redirects=False
        )
        return res

    @contextlib.contextmanager
    def __get_reader_internal(self, reqdata: ReqData):
        merged_reqdata = self._base_reqdata + reqdata
        cache_path = cachemanager.get_path(merged_reqdata)
        meta_path = cachemanager.get_metadata_path(cache_path)

        # try loading from cache if configured and file exists
        if self._config.load_from_cache and os.path.isfile(cache_path):
            metadata = None
            if os.path.isfile(meta_path):
                metadata = utils.reader.Metadata.from_file(meta_path)

            with open(cache_path, 'rb') as fc:
                yield utils.reader.IOReader(fc, self._config.chunk_size, metadata)
        else:
            with self.__get_nocache_internal(merged_reqdata, True) as res:
                metadata = utils.reader.Metadata.from_response(res)
                res_reader = utils.reader.ResponseReader(res, self._config.chunk_size, metadata)

                # cache data if configured, return basic reader otherwise
                if self._config.store_to_cache:
                    # additionally store metadata to separate file
                    if self._config.store_metadata:
                        utils.misc.create_dirs_for_file(meta_path)
                        metadata.write_file(meta_path)

                    # avoid creating a cache file if the request failed and metadata wasn't stored.
                    # if the file were to be kept regardless of errors, it would later be impossible
                    # to distinguish successful and failed requests, as metadata wasn't written
                    # FIXME: remove once dependencies between options are implemented
                    store_on_status_error = self._config.store_metadata and self._config.store_failed_requests

                    with utils.reader.CachingReader(res_reader, cache_path, [ResponseStatusError] if store_on_status_error else []) as reader:
                        yield reader
                else:
                    yield res_reader

    def __check_status(self, obj: Union[requests.Response, utils.reader.Metadata]) -> None:
        status_check = self._config.response_status_checking
        if status_check is StatusCheckMode.NONE:
            pass
        elif status_check in (StatusCheckMode.CHECK_ERROR, StatusCheckMode.REQUIRE_200):
            if isinstance(obj, requests.Response):
                status = obj.status_code
            else:
                status = obj.status

            # simple error check
            if status >= 400:
                raise ResponseStatusError(f'got status code {status} for url {obj.url}', status=status)
            # more restrictive check for status code 200
            if status_check is StatusCheckMode.REQUIRE_200 and status != 200:
                raise ResponseStatusError(f'expected status code 200, got {status} for url {obj.url}', status=status)
        else:
            assert False  # should never happen
