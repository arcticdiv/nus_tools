import os
import abc
import requests
import lxml.objectify
from dataclasses import dataclass
from typing import Optional, Tuple, Type, TypeVar, Generic, Dict, Any

from ..sources import _base
from ..reqdata import ReqData
from .. import utils, cachemanager


_TSource = TypeVar('_TSource', bound='_base.BaseSource')


class BaseType(Generic[_TSource]):
    def __init__(self, source: _TSource, reqdata: ReqData):
        self._source = source
        self._reqdata = reqdata
        self.__loaded = False

    def _download_nocache(self) -> requests.Response:
        return self._source.get_nocache(self)

    def _get_reader(self):
        return self._source.get_reader(self)

    def is_cached(self) -> bool:
        return os.path.isfile(self._cache_path)

    @utils.misc.cached_property
    def _merged_reqdata(self) -> ReqData:
        return self._source._base_reqdata + self._reqdata

    @utils.misc.cached_property
    def _cache_path(self) -> str:
        return cachemanager.get_path(self._merged_reqdata)


_T = TypeVar('_T', bound='BaseTypeLoadable')


class BaseTypeLoadable(BaseType[_TSource], abc.ABC):
    def __init__(self, source: _TSource, reqdata: ReqData):
        super().__init__(source, reqdata)
        self.__loaded = False

    @abc.abstractmethod
    def _read(self, reader: utils.reader.DataReader) -> None:
        pass

    def load(self: _T) -> _T:
        if not self.__loaded:
            with self._get_reader() as reader:
                self._read(reader)
            self.__loaded = True
        return self


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
