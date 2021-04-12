from typing import Any
from reqcli.type import BaseTypeLoadableConstruct

from ... import structs, ids


class CETK(BaseTypeLoadableConstruct):
    data: Any

    def __init__(self, title_id: ids.TTitleIDInput):
        self.__title_id = ids.TitleID.get_inst(title_id)
        super().__init__(structs.cetk)

    def _read(self, reader, config):
        raw_data = reader.read()
        self.data = self._parse_construct(raw_data, config)

        # sanity check
        assert self.data.title_id == self.__title_id


class TMD(BaseTypeLoadableConstruct):
    data: Any

    def __init__(self, title_id: ids.TTitleIDInput):
        self.__title_id = ids.TitleID.get_inst(title_id)
        super().__init__(structs.tmd.get(self.__title_id.type.platform))

    def _read(self, reader, config):
        raw_data = reader.read()
        self.data = self._parse_construct(raw_data, config)

        # sanity check
        assert self.data.title_id == self.__title_id
