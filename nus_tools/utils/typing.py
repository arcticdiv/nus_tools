from typing import Mapping, TypeVar, Callable, Any, Dict, Union


TFuncAny = TypeVar('TFuncAny', bound=Callable[..., Any])

# `Mapping` since `Dict` is invariant in its value type
RequestDict = Mapping[str, Union[int, str, bytes]]
