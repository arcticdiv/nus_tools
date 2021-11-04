import os
import io
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

from .read import AppBlockReader
from ... import structs


@dataclass(frozen=True)
class _FSTEntry:
    name: str
    deleted: bool
    secondary_index: int


@dataclass(frozen=True)
class FSTDirectory(_FSTEntry):
    children: 'List[Union[FSTDirectory, FSTFile]]'


@dataclass(frozen=True)
class FSTFile(_FSTEntry):
    offset: int
    size: int


class FSTProcessor:
    def __init__(self, fst_struct: Any):
        self._name_map = self.__get_names(fst_struct)
        self._offset_factor = fst_struct.offset_factor
        # add root entry to list
        self._entries = (fst_struct.root, *fst_struct.entries)

    @classmethod
    def try_load(cls, reader: AppBlockReader) -> 'FSTProcessor':
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
        return cls(structs.fst.parse_stream(fst_stream))

    def flatten(self) -> Tuple[Dict[str, FSTDirectory], Dict[str, FSTFile]]:
        '''
        Flattens the FST into two dictionaries containing complete paths
        and entries for directories and files respectively
        '''

        directories = {}  # type: Dict[str, FSTDirectory]
        files = {}  # type: Dict[str, FSTFile]

        def process_file(entry: FSTFile, parent_path: str) -> None:
            path = os.path.join(parent_path, entry.name)
            assert path not in files
            files[path] = entry

        def process_directory(entry: FSTDirectory, parent_path: str) -> None:
            path = os.path.join(parent_path, entry.name)
            assert path not in directories
            directories[path] = entry

            for child in entry.children:
                if isinstance(child, FSTDirectory):
                    process_directory(child, path)
                else:
                    process_file(child, path)

        process_directory(self.get_tree(), '')
        return directories, files

    def get_tree(self) -> FSTDirectory:
        '''
        Returns the directory tree of the provided FST
        '''

        self._curr_index = 0
        assert self._entries[self._curr_index].type.directory
        return self.__process_directory()

    def __process_directory(self) -> FSTDirectory:
        '''
        Recursively reads the entries of the directory at the current index
        '''

        dir_entry = self._entries[self._curr_index]
        self._curr_index += 1

        children = []  # type: List[Union[FSTDirectory, FSTFile]]
        # iterate over following entries until end is reached
        while self._curr_index < dir_entry.next_entry_index:
            curr_entry = self._entries[self._curr_index]
            if curr_entry.type.directory:
                # directory
                children.append(self.__process_directory())
            else:
                # file
                children.append(self.__process_file())

        # make sure the current index equals the end index
        if self._curr_index > dir_entry.next_entry_index:
            raise RuntimeError('something went wrong, inner entry read more than it should have')

        return FSTDirectory(
            self._name_map[dir_entry.name_offset],
            dir_entry.type.deleted,
            dir_entry.secondary_index,
            children
        )

    def __process_file(self) -> FSTFile:
        '''
        Reads a file entry at the current index
        '''

        entry = self._entries[self._curr_index]
        self._curr_index += 1

        # calculate real offset
        offset = entry.offset_raw
        if not entry.flags.offset_in_bytes:
            offset *= self._offset_factor

        return FSTFile(
            self._name_map[entry.name_offset],
            entry.type.deleted,
            entry.secondary_index,
            offset,
            entry.size
        )

    def __get_names(self, fst_struct: Any) -> Dict[int, str]:
        '''
        Create mapping of 'offset -> name' based on list of names
        '''

        offset = 0
        name_map = {}
        for name in fst_struct.names:
            name_map[offset] = name
            offset += len(name) + 1  # + trailing nullbyte
        return name_map
