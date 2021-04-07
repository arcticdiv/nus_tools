from Crypto.Cipher import AES as _AESCrypto
from typing import Optional, cast


class AES:
    @classmethod
    def cbc(cls, key: bytes, iv: bytes):
        return cls.__get_inst(key, _AESCrypto.MODE_CBC, iv)

    @staticmethod
    def __get_inst(key: bytes, mode: int, iv: Optional[bytes] = None):
        return _AESCrypto.new(key=key, mode=mode, iv=cast(bytes, iv))
