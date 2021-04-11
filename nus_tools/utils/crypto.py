from Crypto.Cipher import AES as _AESCrypto
from Crypto.Cipher._mode_cbc import CbcMode
from typing import Any, Optional, cast


class AES:
    @classmethod
    def cbc(cls, key: bytes, iv: bytes) -> CbcMode:
        return cls.__get_inst(key, _AESCrypto.MODE_CBC, iv)

    @staticmethod
    def __get_inst(key: bytes, mode: int, iv: Optional[bytes] = None) -> Any:
        return _AESCrypto.new(key=key, mode=mode, iv=cast(bytes, iv))
