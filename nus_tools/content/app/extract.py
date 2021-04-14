import os
import io
from typing import Any, Dict

from .read import AppBlockReader, AppDataReader
from .fstprocessor import FSTProcessor, FSTDirectory, FSTFile
from ... import structs


class AppExtractor:
    def __init__(self, fst_reader: AppDataReader, inputs: Dict[int, AppDataReader]):
        self.inputs = inputs

        fst = self.__load_fst(fst_reader.block_reader)
        self.root = FSTProcessor(fst).get_tree()

    def extract(self, target_path: str) -> None:
        self.__extract_directory(target_path, self.root)

    def __extract_directory(self, outer_path: str, directory: FSTDirectory) -> None:
        path = os.path.join(outer_path, directory.name)
        os.makedirs(path, exist_ok=True)

        for entry in directory.children:
            if entry.deleted:
                # deleted, skip
                continue

            if isinstance(entry, FSTDirectory):
                # directory
                self.__extract_directory(path, entry)
            else:
                # file
                self.__extract_file(path, entry)

    def __extract_file(self, outer_path: str, file: FSTFile) -> None:
        path = os.path.join(outer_path, file.name)
        print(f'extracting {path} (source: {file.secondary_index}, offset: {file.offset}, size: {file.size})')

        with open(path, 'wb') as f:
            reader = self.inputs[file.secondary_index]
            for block in reader.get_data(file.offset, file.size):
                f.write(block)

    def __load_fst(self, reader: AppBlockReader) -> Any:
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
