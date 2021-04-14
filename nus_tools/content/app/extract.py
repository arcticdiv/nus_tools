import os
import io
from typing import Any, Dict

from .read import AppBlockReader, AppDataReader
from .fstprocessor import FSTProcessor
from ... import structs


class AppExtractor:
    def __init__(self, fst_reader: AppDataReader, inputs: Dict[int, AppDataReader]):
        self.inputs = inputs

        fst = self.__load_fst(fst_reader.block_reader)
        self.directories, files = FSTProcessor(fst).get_flattened()

        # sort files based on offset, which enables extracting non-seekable streams
        # (sorts globally instead of per .app file (which would suffice), but that doesn't really matter)
        self.files = sorted(files.items(), key=lambda tup: tup[1].offset)

    def extract(self, target_path: str) -> None:
        '''
        Creates directories and extracts files to the specified path
        '''

        # create directories
        for dir_path, dir in self.directories.items():
            if dir.deleted:
                continue
            path = os.path.join(target_path, dir_path)
            os.makedirs(path, exist_ok=True)

        # extract files
        for file_path, file in self.files:
            if file.deleted:
                continue
            path = os.path.join(target_path, file_path)
            print(f'extracting {path} (source: {file.secondary_index}, offset: {file.offset}, size: {file.size})')

            with open(path, 'wb') as f:
                reader = self.inputs[file.secondary_index]
                for block in reader.get_data(file.offset, file.size):
                    f.write(block)

    def __load_fst(self, reader: AppBlockReader) -> Any:
        '''
        Loads the FST from the provided reader

        Raises an exception if the data does not represent a valid FST
        '''

        # check first block before loading entire file
        block = reader.load_next_block()[1]
        if block[:4] != b'FST\0':
            raise RuntimeError('first input does not contain FST')

        # write previously read block to stream, then read remaining blocks
        fst_stream = io.BytesIO()
        fst_stream.write(block)
        reader.write_all(fst_stream)
        fst_stream.seek(0, os.SEEK_SET)

        # parse FST from stream
        return structs.fst.parse_stream(fst_stream)
