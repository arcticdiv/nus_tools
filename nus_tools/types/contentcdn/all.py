from typing import Any

from .._base import BaseTypeLoadableStruct
from ... import structs, ids


class CETK(BaseTypeLoadableStruct):
    data: Any

    def __init__(self, title_id: ids.TTitleIDInput):
        self.__title_id = ids.TitleID.get_inst(title_id)
        super().__init__(structs.cetk)

    def _read(self, reader, config):
        raw_data = reader.read_all()
        self.data = self._parse_struct(raw_data, config)



class TMD(BaseTypeLoadableStruct):
    data: Any

    def __init__(self, title_id: ids.TTitleIDInput):
        self.__title_id = ids.TitleID.get_inst(title_id)
        super().__init__(structs.tmd.get(self.__title_id.type.platform))

    def _read(self, reader, config):
        raw_data = reader.read_all()
        self.data = self._parse_struct(raw_data, config)

        # sanity check
        assert self.data.title_id == self.__title_id
