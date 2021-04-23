from dataclasses import dataclass
from typing import Optional
from reqcli.type import TypeLoadConfig

from ..config import Configuration


@dataclass(frozen=True)
class NUSTypeLoadConfig(TypeLoadConfig):
    # None: try to verify, warn if no root key set
    # True: try to verify, raise exception if no root key set
    # False: don't try to verify
    verify_signatures: Optional[bool] = None


Configuration.reqcli_config.type_load_config_type = NUSTypeLoadConfig
