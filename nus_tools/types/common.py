import logging
from typing import Any, List

from .config import NUSTypeLoadConfig
from .. import utils
from ..config import Configuration


_logger = logging.getLogger(__name__)


class SignatureHandler:
    @classmethod
    def maybe_verify(cls, config: NUSTypeLoadConfig, data: bytes, issuer: str, signature_struct: Any, certificate_structs: List[Any]) -> None:
        verify = config.verify_signatures
        if verify is False:
            # don't verify
            return

        root_key = Configuration.root_key_struct
        if root_key is None:
            msg = 'no root key set, can\'t verify signatures'
            if verify is None:
                # only print warning
                _logger.warning(msg)
                return
            else:
                raise RuntimeError(msg)

        try:
            utils.crypto.verify_chain(data, issuer, signature_struct, certificate_structs, root_key)
        except utils.crypto.MissingCertError as e:
            if verify is None:
                _logger.warning(str(e) + ' - skipping signature verification')
            else:
                raise
