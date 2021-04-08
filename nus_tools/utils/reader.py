import os
import json
import time
import requests
from dataclasses import asdict, dataclass
from typing import Iterator, Optional, Dict, List, Union, BinaryIO

from . import misc
from .. import sources


@dataclass(frozen=True)
class Metadata:
    http_version: str
    status: int
    status_reason: str
    response_headers: Dict[str, List[str]]
    url: str
    timestamp: int
    elapsed_ms: int

    def write_file(self, path: str) -> None:
        with open(path, 'w') as f:
            return json.dump(asdict(self), f)

    @classmethod
    def from_file(cls, path: str) -> 'Metadata':
        with open(path, 'r') as f:
            return cls(**json.load(f))

    @classmethod
    def from_response(cls, response: requests.Response) -> 'Metadata':
        headers = response.raw.headers
        return cls(
            http_version={9: '0.9', 10: '1.0', 11: '1.1'}[response.raw.version],
            status=response.status_code,
            status_reason=response.reason,
            response_headers={k: headers.getlist(k) for k in headers},
            url=response.url,
            timestamp=int(time.time()),
            elapsed_ms=int(response.elapsed.total_seconds() * 1000)
        )


class DataReader(Iterator[bytes]):
    metadata: Optional[Metadata]
    size: Optional[int]  # *compressed* size (for HTTP responses), see `SourceConfig.chunk_size`

    def __init__(self, resource: Union[requests.Response, BinaryIO], chunk_size: int, meta: Optional[Metadata]):
        self.metadata = meta

        if isinstance(resource, requests.Response):
            res_it = resource.iter_content(chunk_size)
            self.__func_read = lambda: next(res_it)
            self.__func_get_offset = resource.raw.tell
            self.size = resource.raw.length_remaining
        else:
            _resource = resource  # https://mypy.readthedocs.io/en/latest/common_issues.html#narrowing-and-inner-functions
            self.__func_read = lambda: _resource.read(chunk_size)
            self.__func_get_offset = resource.tell
            orig_offset = resource.tell()
            self.size = resource.seek(0, os.SEEK_END)
            resource.seek(orig_offset, os.SEEK_SET)

    def __next__(self):
        data = self.__func_read()
        if data == b'':
            raise StopIteration
        return data

    def read_all(self) -> bytes:
        return b''.join(self)

    @property
    def current_offset(self) -> int:
        # *compressed* size (for HTTP responses), see `SourceConfig.chunk_size`
        return self.__func_get_offset()


class CachingReader(DataReader):
    def __init__(self, filename: str, store_on_status_error: bool, resource: Union[requests.Response, BinaryIO], chunk_size: int, meta: Optional[Metadata]):
        super().__init__(resource, chunk_size, meta)
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
