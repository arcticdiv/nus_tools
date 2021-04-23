import hashlib
from configparser import ConfigParser
from typing import Any, Optional
from reqcli.config import Configuration as ReqCliConfig


class IniKey:
    def __init__(self, section, name, sha1):
        self.section = section
        self.name = name
        self.sha1 = bytes.fromhex(sha1)
        self.__value = None  # type: Optional[bytes]

    def __get__(self, obj: Any, objtype: Any = None) -> bytes:
        if self.__value is None:
            raise RuntimeError(f'missing key: {self._var_name!r} (ini: {self.section}.{self.name})')
        return self.__value

    def __set__(self, obj: Any, value: bytes) -> None:
        if hashlib.sha1(value).digest() != self.sha1:
            raise RuntimeError(f'unexpected hash for key {self._var_name!r} (ini: {self.section}.{self.name})')
        self.__value = value

    def __set_name__(self, obj: Any, name: str) -> None:
        self._var_name = name


class _Keys:
    common_wiiu = IniKey('common', 'common_key_wiiu', '6a0b87fc98b306ae3366f0e0a88d0b06a2813313')
    # nn_idbe.rpl: .rodata+0x4c
    idbe_iv = IniKey('idbe', 'iv', '3db78243a8c9a89b399cc8e7511f06cbde9fa10b')
    idbe_keys = [
        IniKey('idbe', 'key0', '1ec1f7927524e8027985a1a3b2345b4d06c92152'),
        IniKey('idbe', 'key1', '0fae601895044799eaaf5ce91f0f00509073824b'),
        IniKey('idbe', 'key2', 'db73e30940500dcefdc3efe1b880af131fb7b745'),
        IniKey('idbe', 'key3', '0bd3a8b30b8416afecd58dce4669c0e3e82a4ee7')
    ]

    def __init__(self):
        p = ConfigParser()
        if not p.read('keys.ini'):
            return

        for name, key in list(type(self).__dict__.items()):
            # try to get value from ini
            if isinstance(key, IniKey):
                # single key
                ini_value = p.get(key.section, key.name, fallback=None)
                if ini_value is not None:
                    setattr(self, name, bytes.fromhex(ini_value))
            elif isinstance(key, list):
                # possible list of keys
                for i, el in enumerate(key):
                    if not isinstance(el, IniKey):
                        continue
                    ini_value = p.get(el.section, el.name, fallback=None)
                    if ini_value is not None:
                        key[i] = bytes.fromhex(ini_value)


class _Configuration:
    keys: _Keys = _Keys()
    root_signature_key_file: Optional[str] = None

    @property
    def reqcli_config(self):
        return ReqCliConfig


Configuration = _Configuration()
# TODO: set user agent
