from typing import Union, List, TypeVar

__T = TypeVar('__T')

OneOrList = Union[__T, List[__T]]
