import os
from typing import Generic, TypeVar, Callable, Any


def create_dirs_for_file(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def get_bool(text: str) -> bool:
    text = text.lower()
    if text in ['true', 'yes', 'y', '1']:
        return True
    elif text in ['false', 'no', 'n', '0']:
        return False
    raise ValueError(text)


_TCached = TypeVar('_TCached')


# adapted from https://stackoverflow.com/a/4037979/5080607
class cached_property(Generic[_TCached]):
    def __init__(self, factory: Callable[[Any], _TCached]):
        self._factory = factory
        self.__doc__ = getattr(factory, '__doc__')

    def __get__(self, obj, objtype):
        val = self._factory(obj)
        setattr(obj, self._factory.__name__, val)
        return val
