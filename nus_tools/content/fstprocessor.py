from dataclasses import dataclass
from typing import Any, Dict, List, Union


@dataclass(frozen=True)
class _FSTEntry:
    name: str
    deleted: bool


@dataclass(frozen=True)
class FSTDirectory(_FSTEntry):
    children: 'List[Union[FSTDirectory, FSTFile]]'


@dataclass(frozen=True)
class FSTFile(_FSTEntry):
    offset: int
    size: int
    secondary_index: int


class FSTProcessor:
    def __init__(self, fst_struct: Any):
        self._name_map = self.__get_names(fst_struct)
        self._offset_factor = fst_struct.offset_factor
        # add root entry to list
        self._entries = (fst_struct.root, *fst_struct.entries)

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
            offset,
            entry.size,
            entry.secondary_index
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
