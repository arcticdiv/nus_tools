from typing import Optional, Any

from .._base import BaseTypeLoadableStruct
from ... import reqdata, sources, utils, ids, structs
from ...config import Configuration


#####
# /<id>/<title id>.idbe
#####

class IDBE(BaseTypeLoadableStruct['sources.IDBEServer']):
    key_index: int
    data: Any

    def __init__(self, source: 'sources.IDBEServer', title_id: ids.TTitleIDInput, version: Optional[int]):
        tid_str = ids.TitleID.get_str(title_id)
        self.__title_id = ids.TitleID.get_inst(title_id)

        super().__init__(
            source,
            # server seems to ignore first value, technically it wouldn't matter what is supplied here
            # based on nn_idbe.rpl .text+0x1d0
            reqdata.ReqData(path=f'{tid_str[12:14]}/{tid_str}' + (f'-{version}' if version is not None else '') + '.idbe'),
            structs.idbe.get(self.__title_id.type.platform)
        )

    def _read(self, reader):
        raw_data = reader.read_all()

        assert raw_data[0] == 0
        self.key_index = raw_data[1]
        encrypted = raw_data[2:]

        decrypted = self.__get_aes(self.key_index).decrypt(encrypted)
        self.data = self._parse_struct(decrypted)

        # sanity check
        # compare lower half since some update/DLC title IDs return their associated game's IDBE
        assert self.data.title_id.uid == self.__title_id.uid

    @staticmethod
    def __get_aes(key_index):
        return utils.crypto.AES.cbc(
            Configuration.keys.idbe_keys[key_index],
            Configuration.keys.idbe_iv
        )
