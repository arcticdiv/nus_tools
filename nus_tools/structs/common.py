from enum import IntEnum
from construct import \
    Construct, Struct, Int32ub, Bytes, \
    PaddedString, Aligned, ExprAdapter, this
from constructutils import EnumConvert, SwitchNoDefault, StrictGreedyRange
from typing import Callable

from .. import ids


# TODO: verify signatures?

# ref: https://www.3dbrew.org/wiki/Certificates#Public_Key
class SignatureAlgorithm(IntEnum):
    RSA4096 = 0
    RSA2048 = 1
    ECDSA = 2

    @property
    def mod_size(self) -> int:
        return {
            SignatureAlgorithm.RSA4096: 0x200,
            SignatureAlgorithm.RSA2048: 0x100,
            SignatureAlgorithm.ECDSA: 0x3c
        }[self]

    @property
    def construct(self) -> Construct:
        if self in (SignatureAlgorithm.RSA4096, SignatureAlgorithm.RSA2048):
            return Struct(
                'modulus' / Bytes(self.mod_size),
                'exponent' / Int32ub
            )
        elif self == SignatureAlgorithm.ECDSA:
            return Bytes(self.mod_size)
        else:
            assert False


# ref: https://www.3dbrew.org/wiki/Certificates#Signature
class SignatureType(IntEnum):
    RSA4096_SHA1 = 0x010000
    RSA2048_SHA1 = 0x010001
    ECDSA_SHA1 = 0x010002
    RSA4096_SHA256 = 0x010003
    RSA2048_SHA256 = 0x010004
    ECDSA_SHA256 = 0x010005

    @property
    def signature_alg(self) -> SignatureAlgorithm:
        return SignatureAlgorithm[self.name.split('_')[0]]

    @property
    def hash_alg(self) -> str:
        return self.name.split('_')[1]


signature = Aligned(0x40, Struct(
    'type' / EnumConvert(Int32ub, SignatureType),
    'data' / Bytes(lambda this: this.type.signature_alg.mod_size)
))
certificates = StrictGreedyRange(Aligned(0x40, Struct(
    'signature' / signature,
    'issuer' / PaddedString(0x40, 'ascii'),
    'key_type' / EnumConvert(Int32ub, SignatureAlgorithm),
    'name' / PaddedString(0x40, 'ascii'),
    '_unk1' / Int32ub,  # might be a timestamp?
    'key' / SwitchNoDefault(
        this.key_type,
        {t: t.construct for t in SignatureAlgorithm}
    )
)))


TitleID = ExprAdapter(
    Bytes(8),
    lambda data, _: ids.TitleID(data),
    lambda title_id, _: title_id.to_bytes()
)


class PlatformSpecific:
    _3ds: Construct
    wiiu: Construct

    # expected signature: `func(is_wiiu: bool) -> Construct`
    def __init__(self, func: Callable[[bool], Construct]):
        self._3ds = func(False)
        self.wiiu = func(True)

    def get(self, platform: ids.AnyPlatform) -> Construct:
        return {
            ids.TitlePlatform._3DS: self._3ds,
            ids.ContentPlatform._3DS: self._3ds,
            ids.TitlePlatform.WIIU: self.wiiu,
            ids.ContentPlatform.WIIU: self.wiiu
        }[platform]
