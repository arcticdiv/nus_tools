import math
import hashlib
from typing import BinaryIO, List, Optional, Tuple, Union, cast

from .. import utils


HASH_TABLES_SIZE = 0x0400
DATA_SIZE = 0xfc00
BLOCK_SIZE = HASH_TABLES_SIZE + DATA_SIZE


class AppDecryptor:
    def __init__(self, titlekey_decrypted: bytes, h3: Optional[Union[BinaryIO, bytes]], app: BinaryIO, content_index: int, content_hash: bytes, real_app_size: int, tmd_app_size: int, verify: bool = True):
        self.titlekey_decrypted = titlekey_decrypted
        self.app = app
        self.content_index = content_index
        self.content_hash = content_hash
        self.real_app_size = real_app_size
        self.tmd_app_size = tmd_app_size
        self.verify = verify

        assert self.real_app_size >= self.tmd_app_size

        self.h3_table = self.__get_h3_table(h3, content_hash)

        self._curr_block = 0
        self._unhashed_decrypted = None  # type: Optional[List[bytes]]

    def decrypt_all(self, output: BinaryIO) -> None:
        '''
        Decrypts the entire .app file to the provided output stream
        '''

        # calculate total number of blocks
        num_blocks = math.ceil(self.real_app_size / BLOCK_SIZE)

        # decrypt and write each block
        for _ in range(num_blocks):
            output.write(self.decrypt_next_block())

    def decrypt_block(self, block_index: int) -> bytes:
        '''
        Decrypts a single block at the given index
        '''

        # seek to block (no need to seek for unhashed files, as they're read in one go)
        if self.h3_table:
            self.app.seek(block_index * BLOCK_SIZE)
        self._curr_block = block_index
        # decrypt block
        return self.decrypt_next_block()

    def decrypt_next_block(self) -> bytes:
        '''
        Decrypts the next block
        '''

        # choose hashed/unhashed based on presence of h3 table
        if self.h3_table:
            return self.__decrypt_next_block_hashed()
        else:
            return self.__decrypt_next_block_unhashed()

    def __decrypt_next_block_hashed(self) -> bytes:
        '''
        Internal function for decrypting the next block in a hashed .app file
        '''

        # decrypt hash tables
        hash_table_data = self.__aes(bytes(16)).decrypt(self.app.read(HASH_TABLES_SIZE))
        # split into tables
        h0_table, h1_table, h2_table = utils.misc.chunk(hash_table_data[:20 * 16 * 3], 20 * 16)

        # obtain current hashes from tables
        h0_hash, h1_hash, h2_hash, h3_hash = (
            utils.misc.get_chunk(table, index, 20) for table, index in
            zip((h0_table, h1_table, h2_table, cast(bytes, self.h3_table)), self.__get_hash_table_indices(self._curr_block))
        )

        # verify tree
        if self.verify:
            utils.crypto.verify_sha1(h2_table, h3_hash)
            utils.crypto.verify_sha1(h1_table, h2_hash)
            utils.crypto.verify_sha1(h0_table, h1_hash)

        # decrypt content
        app_data = self.__aes(h0_hash[:16]).decrypt(self.app.read(DATA_SIZE))
        if self.verify:
            utils.crypto.verify_sha1(app_data, h0_hash)
        self._curr_block += 1
        return hash_table_data + app_data  # TODO

    def __decrypt_next_block_unhashed(self) -> bytes:
        '''
        Internal function for decrypting the next block in an unhashed .app file (i.e. without a corresponding .h3 file)
        '''

        # this part is an implementation detail and not really relevant to the actual decryption;
        # the entire file is processed at once, as the hash is calculated over the entire file.
        # this rests on the assumption that unhashed .app files will generally not be too large

        if not self._unhashed_decrypted:
            # decrypt entire file
            assert self.real_app_size < 256 * 1024 * 1024  # 256MB, arbitrary limit to avoid using too much memory

            self._unhashed_decrypted = []
            aes = self.__aes(self.content_index.to_bytes(2, 'big') + bytes(14))
            if self.verify:
                sha1 = hashlib.sha1()
                sha1_bytes_left = self.tmd_app_size

            # block size doesn't really matter here
            num_blocks = math.ceil(self.real_app_size / BLOCK_SIZE)
            for _ in range(num_blocks):
                # decrypt
                dec = aes.decrypt(self.app.read(BLOCK_SIZE))
                self._unhashed_decrypted.append(dec)

                # update hash
                if self.verify:
                    sha1_input_len = min(len(dec), sha1_bytes_left)
                    sha1.update(dec[:sha1_input_len])
                    sha1_bytes_left -= sha1_input_len

            # verify hash
            if self.verify:
                digest = sha1.digest()
                if digest != self.content_hash:
                    raise utils.crypto.ChecksumVerifyError('hash mismatch', self.content_hash, digest)

        # if decrypted, return chunk from cache
        data = self._unhashed_decrypted[self._curr_block]
        self._curr_block += 1
        return data

    def __aes(self, iv: bytes) -> utils.crypto.CbcMode:
        return utils.crypto.AES.cbc(self.titlekey_decrypted, iv)

    def __get_h3_table(self, h3: Optional[Union[BinaryIO, bytes]], hash: bytes) -> Optional[bytes]:
        if h3:
            h3_table = h3 if isinstance(h3, bytes) else h3.read()
            if self.verify:
                utils.crypto.verify_sha1(h3_table, hash)
            return h3_table
        else:
            return None

    @staticmethod
    def __get_hash_table_indices(block_index: int) -> Tuple[int, int, int, int]:
        return (
            block_index >> 0 & 0xf,
            block_index >> 4 & 0xf,
            block_index >> 8 & 0xf,
            block_index >> 12 & 0xf
        )
