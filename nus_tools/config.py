import hashlib
from construct import Container
from configparser import ConfigParser
from typing import Any, Dict, Optional


class IniKey:
    def __init__(self, section: str, name: str, sha1: str):
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

    def load_ini(self, path: str) -> None:
        p = ConfigParser()
        if not p.read(path):
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
    # encryption/decryption keys
    keys: _Keys = _Keys()
    # any certificates that may be used for verifying signatures (type: elements of `structs.common.certificates`)
    certificate_structs: Dict[str, Container] = {}

    def __init__(self):
        self.__keys_file = 'keys.ini'
        self.__root_key_struct = None

    # path to keys.ini
    @property
    def keys_file(self) -> str:
        return self.__keys_file

    @keys_file.setter
    def keys_file(self, value: str) -> None:
        self.__keys_file = value
        # reload ini
        self.keys.load_ini(self.__keys_file)

    # 'Root' public key used to sign other certificates (type: `structs.rootkey`)
    @property
    def root_key_struct(self) -> Optional[Container]:
        return self.__root_key_struct

    @root_key_struct.setter
    def root_key_struct(self, value: Optional[Container]) -> None:
        if value:
            data = value.modulus + int.to_bytes(value.exponent, 4, 'big')
            if hashlib.sha1(data).hexdigest() != '076bed301a9bcf40706330213470f53c78ff67f2':
                raise RuntimeError('unexpected hash for \'Root\' publickey')
        self.__root_key_struct = value


Configuration = _Configuration()
# initialize keys
Configuration.keys.load_ini(Configuration.keys_file)
