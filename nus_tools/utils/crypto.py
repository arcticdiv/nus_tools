from Crypto.Cipher import AES as _AESCrypto
from Crypto.Cipher._mode_cbc import CbcMode
from typing import Any, Optional, cast

from .. import ids
from ..config import Configuration


class AES:
    @classmethod
    def cbc(cls, key: bytes, iv: bytes) -> CbcMode:
        return cls.__get_inst(key, _AESCrypto.MODE_CBC, iv)

    @staticmethod
    def __get_inst(key: bytes, mode: int, iv: Optional[bytes] = None) -> Any:
        return _AESCrypto.new(key=key, mode=mode, iv=cast(bytes, iv))


class TitleKey:
    @classmethod
    def decrypt(cls, title_key: bytes, title_id: ids.TTitleIDInput) -> bytes:
        return cls.__get_aes(title_id).decrypt(title_key)

    @classmethod
    def encrypt(cls, title_key: bytes, title_id: ids.TTitleIDInput) -> bytes:
        return cls.__get_aes(title_id).encrypt(title_key)

    @staticmethod
    def __get_aes(title_id: ids.TTitleIDInput) -> CbcMode:
        title_id = ids.TitleID.get_inst(title_id)
        if title_id.type.platform == ids.TitlePlatform.WIIU:
            common_key = Configuration.keys.common_wiiu
        elif title_id.type.platform == ids.TitlePlatform._3DS:
            raise NotImplementedError
        else:
            assert False
        return AES.cbc(common_key, bytes(title_id) + bytes(8))
