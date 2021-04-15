import os
import math
import hashlib
from typing import BinaryIO, Iterator, List, Optional, Tuple, cast

from ... import utils


HASH_TABLES_SIZE = 0x0400


class AppBlockReader:
    def __init__(self, h3: Optional[bytes], app: BinaryIO, content_hash: bytes, real_app_size: int, tmd_app_size: int, verify: bool = True):
        self._app = app
        self._content_hash = content_hash
        self._real_app_size = real_app_size
        self._tmd_app_size = tmd_app_size
        self._verify = verify

        assert self._real_app_size >= self._tmd_app_size

        self._h3_table = h3
        if self._h3_table and self._verify:
            utils.crypto.verify_sha1(self._h3_table, content_hash)
        self._is_hashed = self._h3_table is not None

        self.data_size = 0xfc00  # size of data blocks
        self.block_size = self.data_size  # size of physical blocks (data or (hash + data))
        if self._is_hashed:
            self.block_size += HASH_TABLES_SIZE

        self._curr_block = 0
        self._unhashed_data = None  # type: Optional[List[bytes]]

    def write_all(self, output: BinaryIO) -> None:
        '''
        Writes the entire .app file to the provided output stream
        '''

        # calculate total number of blocks
        num_blocks = math.ceil(self._real_app_size / self.block_size)

        # read and write each block
        for _ in range(num_blocks - self._curr_block):
            for data in self.load_next_block():
                output.write(data)

    def load_block(self, block_index: int) -> Tuple[bytes, bytes]:
        '''
        Loads a single block at the given index
        '''

        self.__seek_to_index(block_index)
        return self.load_next_block()

    def load_next_block(self) -> Tuple[bytes, bytes]:
        '''
        Loads the next block
        '''

        # choose hashed/unhashed based on presence of h3 table
        if self._is_hashed:
            return self.__load_next_block_hashed()
        else:
            return self.__load_next_block_unhashed()

    def _read(self, length: int) -> bytes:
        return self._app.read(length)

    def _init_iv(self, h0_hash: bytes) -> None:
        pass

    def _init_iv_unhashed(self) -> None:
        pass

    def __load_next_block_hashed(self) -> Tuple[bytes, bytes]:
        '''
        Internal function for loading the next block in a hashed .app file
        '''

        # load hash tables
        self._init_iv(bytes(16))
        hash_table_data = self._read(HASH_TABLES_SIZE)
        # split into tables
        h0_table, h1_table, h2_table = utils.misc.chunk(hash_table_data[:20 * 16 * 3], 20 * 16)

        # obtain current hashes from tables
        # TODO: no need to extract h1/h2/h3 if not verifying
        h0_hash, h1_hash, h2_hash, h3_hash = (
            utils.misc.get_chunk(table, index, 20) for table, index in
            zip((h0_table, h1_table, h2_table, cast(bytes, self._h3_table)), self.__get_hash_table_indices(self._curr_block))
        )

        # verify tree
        if self._verify:
            utils.crypto.verify_sha1(h2_table, h3_hash)
            utils.crypto.verify_sha1(h1_table, h2_hash)
            utils.crypto.verify_sha1(h0_table, h1_hash)

        # load content
        self._init_iv(h0_hash[:16])
        app_data = self._read(self.data_size)
        if self._verify:
            utils.crypto.verify_sha1(app_data, h0_hash)
        self._curr_block += 1
        return (hash_table_data, app_data)

    def __load_next_block_unhashed(self) -> Tuple[bytes, bytes]:
        '''
        Internal function for loading the next block in an unhashed .app file (i.e. without a corresponding .h3 file)
        '''

        # this part is an implementation detail and not really relevant to the actual file structure;
        # the entire file is processed at once, as the hash is calculated over the entire file.
        # this rests on the assumption that unhashed .app files will generally not be too large

        if not self._unhashed_data:
            # load entire file
            assert self._real_app_size < 128 * 1024 * 1024  # 128MB, arbitrary limit to avoid using too much memory

            self._unhashed_data = []
            self._init_iv_unhashed()
            if self._verify:
                sha1 = hashlib.sha1()
                sha1_bytes_left = self._tmd_app_size

            num_blocks = math.ceil(self._real_app_size / self.block_size)
            for _ in range(num_blocks):
                # load
                dec = self._read(self.block_size)
                self._unhashed_data.append(dec)

                # update hash
                if self._verify:
                    sha1_input_len = min(len(dec), sha1_bytes_left)
                    sha1.update(dec[:sha1_input_len])
                    sha1_bytes_left -= sha1_input_len

            # verify hash
            if self._verify:
                digest = sha1.digest()
                if digest != self._content_hash:
                    raise utils.crypto.ChecksumVerifyError('hash mismatch', self._content_hash, digest)

        # if loaded, return chunk from cache
        data = self._unhashed_data[self._curr_block]
        self._curr_block += 1
        return (b'', data)

    def __seek_to_index(self, block_index: int) -> None:
        '''
        Seeks the underlying stream to the specified block.

        If the stream is not seekable (e.g. HTTP response streams), only
        forward 'seeking' (by reading and discarding data) is supported
        '''

        if self._curr_block == block_index:
            # nothing to be done
            return

        if not self._is_hashed:
            # no need to seek for unhashed files, as they're read in one go
            return

        # seek to block
        target_offset = block_index * self.block_size
        if self._app.seekable():
            # just seek to target
            self._app.seek(target_offset, os.SEEK_SET)
        else:
            # TODO: tell() might be inaccurate for compressed HTTP response streams
            if self._app.tell() > target_offset:
                raise RuntimeError('app stream is not seekable, cannot go backwards')
            # if not seekable, read until target reached
            while True:
                left = target_offset - self._app.tell()
                if left <= 0:
                    break
                # discard data
                self._app.read(min(left, 32 * 1024))  # 32k, arbitrary maximum chunk size

    @staticmethod
    def __get_hash_table_indices(block_index: int) -> Tuple[int, int, int, int]:
        return (
            block_index >> 0 & 0xf,
            block_index >> 4 & 0xf,
            block_index >> 8 & 0xf,
            block_index >> 12 & 0xf
        )


class AppDataReader:
    def __init__(self, block_reader: AppBlockReader):
        self.block_reader = block_reader

        self.__cache = None  # type: Optional[bytes]
        self.__cache_block_index = -1

    def get_data(self, data_offset: int, length: int) -> Iterator[bytes]:
        def handle_block(block: bytes, start_offset: int) -> bytes:
            nonlocal length
            # required length or blocksize, whichever is smaller
            slice_length = min(length, len(block) - start_offset)
            length -= slice_length
            return block[start_offset:start_offset + slice_length]

        block_index = data_offset // self.block_reader.data_size
        # load new block if no block is cached or index changed
        if not self.__cache or block_index != self.__cache_block_index:
            self.__cache = self.block_reader.load_block(block_index)[1]
            self.__cache_block_index = block_index

        # add offset in first block
        offset_in_data = data_offset % self.block_reader.data_size
        yield handle_block(self.__cache, offset_in_data)

        # yield blocks until done
        while length > 0:
            self.__cache = self.block_reader.load_next_block()[1]
            self.__cache_block_index += 1
            yield handle_block(self.__cache, 0)
