import os
import urllib
import functools
import pathvalidate
from typing import Iterable, Tuple, Any

from . import sources, types
from .config import Configuration


__sanitize_fn = functools.partial(pathvalidate.sanitize_filename, replacement_text='_')
__sanitize_fp = functools.partial(pathvalidate.sanitize_filepath, replacement_text='_')


def __fmt_pairs(it: Iterable[Tuple[Any, Any]]):
    return '--'.join(f'{k}+{v}' for k, v in it)


def get_path_for_source(src: 'sources._base.BaseSource') -> str:
    url = urllib.parse.urlparse(src._base_url)
    return os.path.join(
        Configuration.cache_path,
        __sanitize_fn(f'{url.scheme}__{url.netloc}'),
        __sanitize_fp(url.path.lstrip('/'))
    )


def get_path_for_type(inst: 'types._base.BaseType') -> str:
    base_path = get_path_for_source(inst._source)

    dirname = os.path.dirname(inst._reqdata.path)
    filename = os.path.basename(inst._reqdata.path)

    base_path = os.path.join(base_path, __sanitize_fp(dirname))
    name = filename
    for vals in [{**inst._source._default_params, **inst._reqdata.params}, inst._reqdata.headers]:
        if vals:
            name += '---'
            name += __fmt_pairs(vals.items())

    return os.path.join(base_path, __sanitize_fn(name))
