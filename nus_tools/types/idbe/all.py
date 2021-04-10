from typing import Any

from .._base import BaseTypeLoadableStruct
from ... import utils, ids, structs
from ...config import Configuration


class IDBE(BaseTypeLoadableStruct):
    key_index: int
    data: Any

    def __init__(self, title_id: ids.TTitleIDInput):
        self.__title_id = ids.TitleID.get_inst(title_id)
        super().__init__(structs.idbe.get(self.__title_id.type.platform))

    def _read(self, reader, config):
        raw_data = reader.read_all()

        assert raw_data[0] == 0
        self.key_index = raw_data[1]
        encrypted = raw_data[2:]

        decrypted = self.__get_aes(self.key_index).decrypt(encrypted)
        self.data = self._parse_struct(decrypted, config)

        # sanity check
        # compare lower half since some update/DLC title IDs return their associated game's IDBE
        assert self.data.title_id.uid == self.__title_id.uid

    @staticmethod
    def __get_aes(key_index):
        return utils.crypto.AES.cbc(
            Configuration.keys.idbe_keys[key_index],
            Configuration.keys.idbe_iv
        )
