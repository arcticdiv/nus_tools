import base64
from dataclasses import dataclass
from typing import Tuple


def _key_dec(val: str) -> bytes:  # tiny amount of obfuscation, seems better this way
    return base64.b64decode(val)


@dataclass
class _Keys:
    # nn_idbe.rpl: .rodata+0x4c
    idbe_iv: bytes = _key_dec('pGmHrkfYK7T6irwEUChfpA==')
    idbe_keys: Tuple[bytes, ...] = tuple(
        _key_dec(k) for k in
        ['SrmkDhRpdahLsbTz7O/Eew==', 'kKC7Hg6GSuh9E6agPSjJuA==', '/7tXwU6Y7Gl1s4T89AeGtQ==', 'gJI3mbQfNqanX7i0jJX2bw==']
    )


@dataclass
class _Configuration:
    cache_path: str = './cache/'
    default_user_agent: str = ''  # TODO
    keys: _Keys = _Keys()


Configuration = _Configuration()
