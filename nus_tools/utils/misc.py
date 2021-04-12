import functools
from typing import TYPE_CHECKING, Dict, Any

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


def cache(func: TFuncAny) -> TFuncAny:
    return functools.lru_cache(maxsize=None)(func)  # type: ignore


cachedproperty = lambda func: property(cache(func))  # noqa: E731
# make the type checker believe that `cachedproperty` is a type alias of `property`, which fixes IDE type hints and autocompletion
if TYPE_CHECKING:
    cachedproperty = property
