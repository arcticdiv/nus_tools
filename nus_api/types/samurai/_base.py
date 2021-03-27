import abc

from .._base import BaseType
from ... import reqdata, sources, utils


class SamuraiListBaseType(BaseType['sources.Samurai'], abc.ABC):
    length: int
    offset: int
    total: int

    def __init__(self, source: 'sources.Samurai', offset: int, limit: int, other_params: dict):
        super().__init__(
            source,
            reqdata.ReqData(path=self._get_req_path(), params={'offset': offset, 'limit': limit, **other_params})
        )

    def _read(self, reader):
        el = utils.xml.load_from_reader(reader)
        self.length = int(el.get('length'))
        self.offset = int(el.get('offset'))
        self.total = int(el.get('total'))

        self._read_list(el)

    @abc.abstractmethod
    def _read_list(self, xml):
        pass

    @classmethod
    @abc.abstractmethod
    def _get_req_path(cls) -> str:
        pass
