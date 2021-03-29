import os
import abc
import contextlib
import requests
import urllib3
from requests.adapters import HTTPAdapter
from enum import Enum
from dataclasses import dataclass
from typing import Union, Optional

from ..config import Configuration
from ..reqdata import ReqData
from ..types._base import BaseType
from .. import utils, cachemanager


class StatusCheckMode(Enum):
    NONE, CHECK_ERROR, REQUIRE_200 = range(3)


class ResponseStatusError(Exception):
    status: int

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.status = status


# TODO: implement dependencies between options
@dataclass(frozen=True)
class SourceConfig:
    load_from_cache: bool = True
    store_to_cache: bool = True
    chunk_size: int = 4096  # note: with streamed requests, this value is the size of compressed chunks (i.e. the size of returned chunks may be larger)
    response_status_checking: StatusCheckMode = StatusCheckMode.REQUIRE_200
    store_failed_requests: bool = True
    store_metadata: bool = True
    http_retries: int = 3
    requests_per_second: float = 5.0


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

    def get_nocache(self, data: Union[ReqData, BaseType]) -> requests.Response:
        res = self.__get_nocache_internal(data)
        self.__check_status(res)
        return res

    @contextlib.contextmanager
    def get_reader(self, type_inst: BaseType):
        with self.__get_reader_internal(type_inst) as reader:
            if reader.metadata:  # if this is None, request was loaded from cache and successful
                self.__check_status(reader.metadata)
            yield reader

    @utils.ratelimit.limit(lambda self: self._config.requests_per_second)
    def __get_nocache_internal(self, data: Union[ReqData, BaseType]) -> requests.Response:
        if isinstance(data, BaseType):
            reqdata = data._merged_reqdata
        else:
            reqdata = self._base_reqdata + data
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
    def __get_reader_internal(self, type_inst: BaseType):
        cache_path = type_inst._cache_path
        meta_path = cachemanager.get_metadata_path(cache_path)

        # try loading from cache if configured and file exists
        if self._config.load_from_cache and type_inst.is_cached():
            metadata = None
            if os.path.isfile(meta_path):
                with open(meta_path, 'r') as fm:
                    metadata = utils.reader.Metadata.from_json(fm.read())

            with open(cache_path, 'rb') as fc:
                yield utils.reader.DataReader(fc, self._config.chunk_size, metadata)
        else:
            with self.__get_nocache_internal(type_inst) as res:
                metadata = utils.reader.Metadata.from_response(res)

                # cache data if configured, return basic reader otherwise
                if self._config.store_to_cache:
                    # additionally store metadata to separate file
                    if self._config.store_metadata:
                        utils.misc.create_dirs_for_file(meta_path)
                        with open(meta_path, 'w') as fm:
                            fm.write(metadata.to_json())

                    # avoid creating a cache file if the request failed and metadata wasn't stored.
                    # if the file were to be kept regardless of errors, it would later be impossible
                    # to distinguish successful and failed requests, as metadata wasn't written
                    # FIXME: remove once dependencies between options are implemented
                    store_on_status_error = self._config.store_metadata and self._config.store_failed_requests

                    with utils.reader.CachingReader(cache_path, store_on_status_error, res, self._config.chunk_size, metadata) as reader:
                        yield reader
                else:
                    yield utils.reader.DataReader(res, self._config.chunk_size, metadata)

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
