import abc

from .._base import BaseTypeLoadable
from ... import utils


class SamuraiListBaseType(BaseTypeLoadable, abc.ABC):
    length: int
    offset: int
    total: int

    def _read(self, reader, config):
        el = utils.xml.load_from_reader(reader)
        self.length = int(el.get('length'))
        self.offset = int(el.get('offset'))
        self.total = int(el.get('total'))

        self._read_list(el)

    @abc.abstractmethod
    def _read_list(self, xml):
        pass
