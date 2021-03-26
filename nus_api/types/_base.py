import os
import abc
import requests
import lxml.objectify
from dataclasses import dataclass
from typing import Optional, Tuple, Type, TypeVar, Generic, Dict, Any

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
    def _read(self, iterator: utils.iterator.BytesIterator) -> None:
        pass

    def _download(self) -> requests.Response:
        return self._source._get(self)

    def load(self: _T) -> _T:
        if not self.__loaded:
            with self.get_iterator() as it:
                self._read(it)
            self.__loaded = True
        return self

    def get_iterator(self):
        return self._source.get_iterator(self)

    def is_cached(self) -> bool:
        return os.path.isfile(self._cache_path)

    @utils.misc.cached_property
    def _merged_reqdata(self) -> ReqData:
        return self._source._base_reqdata + self._reqdata

    @utils.misc.cached_property
    def _cache_path(self) -> str:
        return cachemanager.get_path(self._merged_reqdata)


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
