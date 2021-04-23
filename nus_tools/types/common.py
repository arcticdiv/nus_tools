import os
import sys
from typing import Any, List, Optional

from .config import NUSTypeLoadConfig
from .. import utils, structs
from ..config import Configuration


class SignatureHandler:
    __root_key: Optional[Any] = None

    @classmethod
    def maybe_verify(cls, config: NUSTypeLoadConfig, data: bytes, issuer: str, signature_struct: Any, certificate_structs: List[Any]) -> None:
        verify = config.verify_signatures
        if verify is False:
            # don't verify
            return

        root_key = cls.get_root_key()
        if root_key is None:
            msg = 'no root key set, can\'t verify signatures'
            if verify is None:
                # only print warning
                print(msg, file=sys.stderr)
                return
            else:
                raise RuntimeError(msg)

        try:
            utils.crypto.verify_chain(data, issuer, signature_struct, certificate_structs, root_key)
        except utils.crypto.MissingCertError as e:
            if verify is None:
                print(str(e) + ' - skipping signature verification')
            else:
                raise

    @classmethod
    def get_root_key(cls) -> Optional[Any]:
        if not cls.__root_key:
            path = Configuration.root_signature_key_file
            if not path:
                value = None
            elif not os.path.isfile(path):
                value = None
            else:
                value = structs.rootkey.parse_file(path)
            cls.__root_key = value
        return cls.__root_key
