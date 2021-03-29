import os
import abc
import requests
import contextlib
from enum import Enum
from dataclasses import dataclass
from typing import Union, Optional, Iterator

from ..config import Configuration
from ..reqdata import ReqData
from ..types._base import BaseType, BaseTypeLoadable
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


class BaseSource(abc.ABC):
    def __init__(self, base_reqdata: ReqData, config: Optional[SourceConfig], *, verify_tls: bool = True):
        self._base_reqdata = ReqData(
            path='',
            headers={'User-Agent': Configuration.default_user_agent}
        )
        self._base_reqdata += base_reqdata

        self._config = config if config is not None else SourceConfig()
        self._verify_tls = verify_tls

    def get(self, data: Union[ReqData, BaseType]) -> requests.Response:
        res = self.__get_internal(data)
        self.__check_status(res)
        return res

    @contextlib.contextmanager
    def get_reader(self, type_inst: BaseType) -> Iterator[utils.reader.DataReader]:
        with self.__get_reader_internal(type_inst) as reader:
            if reader.metadata:  # if this is None, request was loaded from cache and successful
                self.__check_status(reader.metadata)
            yield reader

    # TODO: ratelimit by hostname
    def __get_internal(self, data: Union[ReqData, BaseType]) -> requests.Response:
        if isinstance(data, BaseType):
            reqdata = data._merged_reqdata
        else:
            reqdata = self._base_reqdata + data
        res = requests.get(
            url=reqdata.path,
            headers=reqdata.headers,
            params=reqdata.params,
            cert=reqdata.cert,
            verify=self._verify_tls,
            stream=True,
            allow_redirects=False
        )
        return res

    @contextlib.contextmanager
    def __get_reader_internal(self, type_inst: BaseType) -> Iterator[utils.reader.DataReader]:
        cache_path = type_inst._cache_path
        meta_path = cachemanager.get_metadata_path(cache_path)

        # try loading from cache if configured and file exists
        if self._config.load_from_cache and type_inst.is_cached():
            metadata = None
            if os.path.isfile(meta_path):
                with open(meta_path, 'r') as fm:
                    metadata = utils.reader.Metadata.from_json(fm.read())

            with open(cache_path, 'rb') as fc:
                yield utils.reader.DataReader(lambda: fc.read(self._config.chunk_size), metadata)
        else:
            with self.__get_internal(type_inst) as res:
                # create metadata and reader
                metadata = utils.reader.Metadata.from_response(res)
                res_it = res.iter_content(self._config.chunk_size)

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

                    with utils.reader.CachingReader(cache_path, store_on_status_error, lambda: next(res_it), metadata) as reader:
                        yield reader
                else:
                    yield utils.reader.DataReader(lambda: next(res_it), metadata)

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
