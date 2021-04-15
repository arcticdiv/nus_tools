import functools
import itertools
from typing import Callable, Iterable, Iterator, List, Dict, Any, Tuple, TypeVar, TYPE_CHECKING

from .typing import TFuncAny


class dotdict(Dict[str, Any]):
    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)

    def __delattr__(self, attr):
        self.__delitem__(attr)


def get_bool(text: str) -> bool:
    text = text.lower()
    if text in {'true', 'yes', 'y', '1'}:
        return True
    elif text in {'false', 'no', 'n', '0'}:
        return False
    raise ValueError(text)


def chunk(data: bytes, n: int) -> List[bytes]:
    if len(data) % n != 0:
        raise RuntimeError(f'length of data ({len(data)}) is not divisible by chunk size ({n})')
    return [get_chunk(data, i, n) for i in range(len(data) // n)]


def get_chunk(data: bytes, i: int, chunk_size: int) -> bytes:
    return data[i * chunk_size:(i + 1) * chunk_size]


_TGroupBy = TypeVar('_TGroupBy')
_TGroupByKey = TypeVar('_TGroupByKey')


def groupby_sorted(it: Iterable[_TGroupBy], key: Callable[[_TGroupBy], _TGroupByKey]) -> Iterator[Tuple[_TGroupByKey, Iterator[_TGroupBy]]]:
    return itertools.groupby(sorted(it, key=key), key=key)  # type: ignore


def cache(func: TFuncAny) -> TFuncAny:
    return functools.lru_cache(maxsize=None)(func)  # type: ignore


cachedproperty = lambda func: property(cache(func))  # noqa: E731
# make the type checker believe that `cachedproperty` is a type alias of `property`, which fixes IDE type hints and autocompletion
if TYPE_CHECKING:
    cachedproperty = property
