import os
import io
from dataclasses import dataclass
from typing import Any, Dict, List

from . import decrypt
from .. import structs


@dataclass
class AppExtractorInput:
    id: int
    reader: decrypt.AppReader
    # hashed: bool


class AppExtractor:
    def __init__(self, inputs: List[AppExtractorInput]):
        fst_input, *inputs = inputs
        self.inputs = {i.id: i for i in inputs}

        self.fst = self.__load_fst(fst_input)
        # add root entry to list
        self.fst.entries.insert(0, self.fst.root)

        # calculate name offsets
        self.name_map = self.__get_names()

    def extract(self, target_path: str) -> None:
        self.curr_index = 0
        assert self.fst.entries[0].type.directory
        self.__extract_directory(target_path)

    def __extract_directory(self, outer_path: str) -> None:
        dir_entry = self.fst.entries[self.curr_index]
        self.curr_index += 1

        path = os.path.join(outer_path, self.name_map[dir_entry.name_offset])
        os.makedirs(path, exist_ok=True)

        while True:
            if self.curr_index == dir_entry.next_entry_index:
                # extracted all entries of current directory
                break
            elif self.curr_index > dir_entry.next_entry_index:
                raise RuntimeError('something went wrong, inner entry read more than it should have')

            curr_entry = self.fst.entries[self.curr_index]
            if curr_entry.type.deleted:
                # deleted, skip
                self.curr_index += 1
            elif curr_entry.type.directory:
                # directory
                self.__extract_directory(path)
            else:
                # file
                self.__extract_file(path)

    def __extract_file(self, outer_path: str) -> None:
        entry = self.fst.entries[self.curr_index]
        path = os.path.join(outer_path, self.name_map[entry.name_offset])

        with open(path, 'wb') as f:
            offset = entry.offset_raw
            if not entry.flags.offset_in_bytes:
                offset *= self.fst.offset_factor

            reader = self.inputs[entry.secondary_index].reader
            for block in reader.get_data(offset, entry.size):
                f.write(block)

        self.curr_index += 1

    def __load_fst(self, input: AppExtractorInput) -> Any:
        # check first block before loading entire file
        block = input.reader.load_next_block()[1]
        if block[:4] != b'FST\0':
            raise RuntimeError('first input does not contain FST')

        # write previously read block to stream, then read remaining blocks
        fst_stream = io.BytesIO()
        fst_stream.write(block)
        input.reader.write_all(fst_stream)
        fst_stream.seek(0, os.SEEK_SET)

        # parse FST from stream
        return structs.fst.parse_stream(fst_stream)

    def __get_names(self) -> Dict[int, str]:
        offset = 0
        name_map = {}
        for name in self.fst.names:
            name_map[offset] = name
            offset += len(name) + 1  # + trailing nullbyte
        return name_map
