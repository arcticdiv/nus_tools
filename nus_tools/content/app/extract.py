import os
from typing import Dict, Tuple

from .read import AppDataReader
from .fstprocessor import FSTDirectory, FSTFile
from ... import utils


class AppExtractor:
    def __init__(self, fst_entries: Tuple[Dict[str, FSTDirectory], Dict[str, FSTFile]]):
        self.directories, files = fst_entries

        # group files by their secondary index (~ app file index),
        # then sort the files in each of those groups by their offsets
        self.files = {
            index: sorted(group, key=lambda tup: tup[1].offset)
            for index, group in
            utils.misc.groupby_sorted(files.items(), key=lambda tup: tup[1].secondary_index)
        }

    def is_required(self, content_index: int) -> bool:
        '''
        Returns true if the app file with the provided index contains any
        data specified in the FST (i.e. contains relevant data for unpacking)
        '''

        return content_index in self.files

    def create_directories(self, target_path: str) -> None:
        '''
        Creates directories used by the content file at the given index to the specified path
        '''

        for dir_path, dir in self.directories.items():
            if dir.deleted:
                continue
            path = self.__join_path(target_path, dir_path)
            print(f'creating directory {path} (source index: {dir.secondary_index})')
            os.makedirs(path, exist_ok=True)

    def extract_files(self, content_index: int, reader: AppDataReader, target_path: str) -> None:
        '''
        Extracts files contained in the content file at the given index to the specified path
        '''

        for file_path, file in self.files[content_index]:
            if file.deleted:
                continue
            path = self.__join_path(target_path, file_path)
            print(f'extracting {file_path} (source index: {file.secondary_index}, offset: {file.offset}, size: {file.size})')

            try:
                with open(path, 'wb') as f:
                    for block in reader.get_data(file.offset, file.size):
                        f.write(block)
            except Exception:
                # remove (incomplete) file if exception was raised
                if os.path.isfile(path):
                    os.unlink(path)
                raise

    @staticmethod
    def __join_path(target_path: str, other_path: str) -> str:
        path = os.path.join(target_path, other_path)

        # make sure resulting path is inside target path
        target_path_real = os.path.realpath(target_path)
        assert os.path.commonprefix((os.path.realpath(path), target_path_real)) == target_path_real

        return path
