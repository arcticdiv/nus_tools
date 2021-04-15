import os
import io
from typing import Any, Callable, ContextManager, List

from .read import AppBlockReader, AppDataReader
from .fstprocessor import FSTProcessor
from ... import structs, utils


class AppExtractor:
    def __init__(self, input_generator: Callable[[int], ContextManager[AppDataReader]], tmd_contents: List[Any]):
        self.input_generator = input_generator

        with input_generator(tmd_contents[0].id) as fst_reader:
            fst = self.__load_fst(fst_reader.block_reader)
        self.directories, files = FSTProcessor(fst).get_flattened()

        # sorts and groups files by their secondary index (~ app file ID),
        # then sorts the files in each of those groups by their offsets
        self.content_files_map = {
            secondary_index: sorted(group, key=lambda tup: tup[1].offset)
            for secondary_index, group
            in utils.misc.groupby_sorted(files.items(), key=lambda tup: tup[1].secondary_index)
        }

        # sanity check
        for secondary_index in self.content_files_map.keys():
            if not any(e.id == secondary_index for e in tmd_contents):
                raise RuntimeError(f'TMD does not contain content entry for ID {secondary_index} from FST')

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
        for secondary_index, files in self.content_files_map.items():
            # open .app files one by one and close them once done, avoids timeouts with streaming HTTP responses
            with self.input_generator(secondary_index) as reader:
                for file_path, file in files:
                    if file.deleted:
                        continue
                    path = os.path.join(target_path, file_path)
                    print(f'extracting {path} (source: {file.secondary_index}, offset: {file.offset}, size: {file.size})')

                    try:
                        with open(path, 'wb') as f:
                            for block in reader.get_data(file.offset, file.size):
                                f.write(block)
                    except Exception:
                        # remove (incomplete) file if exception was raised
                        if os.path.isfile(path):
                            os.unlink(path)
                        raise

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
