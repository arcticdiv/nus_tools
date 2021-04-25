from dataclasses import dataclass
from typing import Optional
from reqcli.type import TypeLoadConfig
from reqcli.config import Configuration as ReqCliConfig


@dataclass(frozen=True)
class NUSTypeLoadConfig(TypeLoadConfig):
    # None: try to verify, warn if missing keys/certificates
    # True: try to verify, raise exception if missing keys/certificates
    # False: don't try to verify
    verify_signatures: Optional[bool] = None


assert ReqCliConfig.type_load_config_type == TypeLoadConfig
ReqCliConfig.type_load_config_type = NUSTypeLoadConfig
