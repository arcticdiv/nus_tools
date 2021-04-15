from typing import BinaryIO, Optional

from .read import AppBlockReader
from ... import utils


class AppDecryptor(AppBlockReader):
    def __init__(self, titlekey_decrypted: bytes, content_index: int, h3: Optional[bytes], app: BinaryIO, content_hash: bytes, real_app_size: int, tmd_app_size: int, verify: bool = True):
        super().__init__(h3, app, content_hash, real_app_size, tmd_app_size, verify)
        self._titlekey_decrypted = titlekey_decrypted
        self._content_index = content_index

    def _read(self, length: int) -> bytes:
        return self.__aes.decrypt(super()._read(length))

    def _init_iv(self, iv: bytes) -> None:
        self.__aes = utils.crypto.AES.cbc(self._titlekey_decrypted, iv)

    def _init_iv_unhashed(self) -> None:
        self._init_iv(self._content_index.to_bytes(2, 'big') + bytes(14))
