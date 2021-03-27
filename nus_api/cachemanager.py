import os
import urllib
import functools
import pathvalidate
from typing import Iterable, Tuple, Any

from .config import Configuration
from .reqdata import ReqData


__sanitize_fn = functools.partial(pathvalidate.sanitize_filename, replacement_text='_')
__sanitize_fp = functools.partial(pathvalidate.sanitize_filepath, replacement_text='_')


def __fmt_pairs(it: Iterable[Tuple[Any, Any]]):
    return '--'.join(f'{k}+{v}' for k, v in it)


def get_path(reqdata: ReqData) -> str:
    # split up request url into parts
    url = urllib.parse.urlparse(reqdata.path)
    url_path = url.path.lstrip('/')
    url_dirname = os.path.dirname(url_path)
    url_filename = os.path.basename(url_path)

    # build cache directory path
    base_path = os.path.join(
        Configuration.cache_path,
        __sanitize_fn(f'{url.scheme}__{url.netloc}'),
        __sanitize_fp(url_dirname)
    )

    # build cache filename
    name = url_filename
    if reqdata.params:
        fmt = __fmt_pairs(reqdata.params.items())
        if fmt:
            name += f'---{fmt}'
    if reqdata.headers:
        fmt = __fmt_pairs((k, v) for k, v in reqdata.headers.items() if k.lower() != 'user-agent')
        if fmt:
            name += f'---{fmt}'

    return os.path.join(base_path, __sanitize_fn(name))


def get_metadata_path(file_path: str) -> str:
    return f'{file_path}.meta'
