import os
from typing import Callable, Iterator

from . import misc


class BytesIterator(Iterator[bytes]):
    def __init__(self, read_func: Callable[[], bytes]):
        self.__read_func = read_func

    def __next__(self):
        data = self.__read_func()
        if data == b'':
            raise StopIteration
        return data

    def read_all(self):
        return b''.join(self)


class CachingIterator(BytesIterator):
    def __init__(self, filename: str, read_func: Callable[[], bytes]):
        super().__init__(read_func)
        self.filename = filename
        self.tmp_filename = f'{filename}.tmp'
        self.__file = None

    def __next__(self):
        data = super().__next__()
        self.__file.write(data)
        return data

    def __enter__(self):
        misc.create_dirs_for_file(self.tmp_filename)
        self.__file = open(self.tmp_filename, 'wb')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # finish writing in case not everything was read
        for data in self:
            pass
        self.__file.close()
        self.__file = None

        # move tmp file if successful
        if exc_type is None:
            os.replace(self.tmp_filename, self.filename)
