from typing import Optional, Any

from .._base import BaseTypeLoadable
from ... import reqdata, sources, utils, ids, structs
from ...config import Configuration


#####
# /<id>/<title id>.idbe
#####

class IDBE(BaseTypeLoadable['sources.IDBEServer']):
    key_index: int
    struct: Any

    def __init__(self, source: 'sources.IDBEServer', title_id: ids.TTitleIDInput, version: Optional[int]):
        tid_str = ids.TitleID.get_str(title_id)
        self.__title_id = ids.TitleID.get_inst(title_id)

        super().__init__(
            source,
            # server seems to ignore first value, technically it wouldn't matter what is supplied here
            # based on nn_idbe.rpl .text+0x1d0
            reqdata.ReqData(path=f'{tid_str[12:14]}/{tid_str}' + (f'-{version}' if version is not None else '') + '.idbe')
        )

    def _read(self, reader):
        data = reader.read_all()

        assert data[0] == 0
        self.key_index = data[1]
        encrypted = data[2:]

        decrypted = self.__get_aes(self.key_index).decrypt(encrypted)
        struct = structs.idbe_wiiu if self.__title_id.type.platform == ids.TitlePlatform.WIIU else structs.idbe_3ds
        self.struct = struct.parse(decrypted)

        # sanity check
        assert self.struct.title_id == self.__title_id

        # verify checksum
        self.struct.checksum.verify(self.struct.__raw__)

    @staticmethod
    def __get_aes(key_index):
        return utils.crypto.AES.cbc(
            Configuration.keys.idbe_keys[key_index],
            Configuration.keys.idbe_iv
        )
