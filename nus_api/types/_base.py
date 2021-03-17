from dataclasses import dataclass
import os
import abc
import contextlib
import requests
import lxml.objectify
from typing import Iterator, Optional, Tuple, Type, TypeVar, Generic, Dict, Any

from ..sources import _base
from ..reqdata import ReqData
from .. import utils, cachemanager


_T = TypeVar('_T', bound='BaseType')
_TSource = TypeVar('_TSource', bound='_base.BaseSource')


class BaseType(Generic[_TSource], abc.ABC):
    def __init__(self, source: _TSource, reqdata: ReqData):
        self._source = source
        self._reqdata = reqdata
        self.__loaded = False

    @abc.abstractmethod
    def _read(self, iterator: utils.BytesIterator) -> None:
        pass

    def _download(self) -> requests.Response:
        res = self._source._get(
            path=self._reqdata.path,
            params=self._reqdata.params,
            headers=self._reqdata.headers,
            cert=self._reqdata.cert
        )
        res.raise_for_status()
        return res

    def load(self: _T, load_cached: bool = True, chunk_size: int = 4096) -> _T:
        if self.__loaded:
            return self

        with self.get_iterator(load_cached, chunk_size) as it:
            self._read(it)
        self.__loaded = True
        return self

    @contextlib.contextmanager
    def get_iterator(self, load_cached: bool, chunk_size: int) -> Iterator[utils.BytesIterator]:
        cache_path = self.cache_path
        if load_cached and os.path.isfile(cache_path):
            with open(cache_path, 'rb') as f:
                yield utils.BytesIterator(lambda: f.read(chunk_size))
        else:
            with self._download() as res:
                res_it = res.iter_content(chunk_size)
                # TODO: save response headers as well?
                with utils.CachingIterator(cache_path, lambda: next(res_it)) as it:
                    yield it

    @property
    def cache_path(self) -> str:
        return cachemanager.get_path_for_type(self)


_TXml = TypeVar('_TXml', bound='XmlBaseType')


class XmlBaseType(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _parse_internal(cls: Type[_TXml], xml: lxml.objectify.ObjectifiedElement) -> Dict[str, Any]:
        pass

    @classmethod
    def _get_schema(cls) -> Optional[Tuple[dict, bool]]:
        return None

    @classmethod
    def _parse(cls: Type[_TXml], xml: lxml.objectify.ObjectifiedElement) -> _TXml:
        schema_tup = cls._get_schema()
        if schema_tup is not None:
            schema, superset = schema_tup
            utils.xml.validate_schema(xml, schema, superset)

        return cls(**cls._parse_internal(xml))  # type: ignore


@dataclass
class IDName:
    id: str
    name: str
