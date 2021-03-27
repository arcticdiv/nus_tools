import os
import json
import requests
from dataclasses import asdict, dataclass
from typing import Callable, Iterator, Optional, Dict, List

from . import misc
from .. import sources


@dataclass(frozen=True)
class Metadata:
    http_version: str
    status: int
    status_reason: str
    response_headers: Dict[str, List[str]]
    url: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, str) -> 'Metadata':
        return cls(**json.loads(str))

    @classmethod
    def from_response(cls, response: requests.Response) -> 'Metadata':
        headers = response.raw.headers
        return cls(
            http_version={9: '0.9', 10: '1.0', 11: '1.1'}[response.raw.version],
            status=response.status_code,
            status_reason=response.reason,
            response_headers={k: headers.getlist(k) for k in headers},
            url=response.url
        )


class DataReader(Iterator[bytes]):
    metadata: Optional[Metadata]

    def __init__(self, read_func: Callable[[], bytes], meta: Optional[Metadata]):
        self.__read_func = read_func
        self.metadata = meta

    def __next__(self):
        data = self.__read_func()
        if data == b'':
            raise StopIteration
        return data

    def read_all(self):
        return b''.join(self)


class CachingReader(DataReader):
    def __init__(self, filename: str, store_on_status_error: bool, read_func: Callable[[], bytes], meta: Optional[Metadata]):
        super().__init__(read_func, meta)
        self.filename = filename
        self.store_on_status_error = store_on_status_error

        self.tmp_filename = f'{filename}.tmp'
        self.__file = None

    def __next__(self):
        data = super().__next__()
        self.__file.write(data)
        return data

    def __enter__(self):
        misc.create_dirs_for_file(self.tmp_filename)
        assert self.__file is None
        self.__file = open(self.tmp_filename, 'wb')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        write_file = exc_type is None or (self.store_on_status_error and exc_type is sources.ResponseStatusError)
        if write_file:
            # finish writing in case not everything was read
            for _ in self:
                pass
        self.__file.close()
        self.__file = None

        # move tmp file if successful
        if write_file:
            os.replace(self.tmp_filename, self.filename)
        else:
            os.unlink(self.tmp_filename)
