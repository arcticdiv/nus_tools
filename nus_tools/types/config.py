from dataclasses import dataclass
from typing import Optional
from reqcli.type import TypeLoadConfig


@dataclass(frozen=True)
class NUSTypeLoadConfig(TypeLoadConfig):
    # None: try to verify, warn if no root key set
    # True: try to verify, raise exception if no root key set
    # False: don't try to verify
    verify_signatures: Optional[bool] = None
