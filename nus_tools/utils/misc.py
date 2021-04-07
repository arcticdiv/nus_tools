import os
import functools
from typing import TypeVar, Callable, TYPE_CHECKING


def create_dirs_for_file(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def get_bool(text: str) -> bool:
    text = text.lower()
    if text in ['true', 'yes', 'y', '1']:
        return True
    elif text in ['false', 'no', 'n', '0']:
        return False
    raise ValueError(text)


_TCacheSig = TypeVar('_TCacheSig', bound=Callable)


def cache(func: _TCacheSig) -> _TCacheSig:
    return functools.lru_cache(maxsize=None)(func)  # type: ignore


# make the type checker believe that `cachedproperty` is a type alias of `property`, which fixes IDE type hints and autocompletion
if TYPE_CHECKING:
    cachedproperty = property
else:
    cachedproperty = lambda func: property(cache(func))  # noqa: E731
