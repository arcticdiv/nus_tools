import hashlib
from construct import \
    Struct, Int64ub, Int32ub, Int16ub, Bytes, Byte, Array, \
    GreedyBytes, Hex, PaddedString, Padding, Padded, FlagsEnum, IfThenElse, this
from constructutils import ChecksumRaw, ChecksumValue, ChecksumSourceData, VerifyOrWriteChecksums

from . import common


# ref:
#   https://www.3dbrew.org/wiki/Title_metadata
#   https://wiibrew.org/wiki/Title_metadata
#   https://wiiubrew.org/wiki/Title_metadata
def __get_struct(is_wiiu: bool):
    if is_wiiu:
        content_hash = 'sha1' / Padded(0x20, ChecksumRaw(hashlib.sha1))
    else:
        content_hash = 'sha256' / ChecksumRaw(hashlib.sha256)

    return Struct(
        'signature' / common.signature,
        'issuer' / PaddedString(0x40, 'ascii'),
        'version' / Byte,
        'ca_crl_version' / Byte,
        'signer_crl_version' / Byte,
        '_unk1' / Bytes(1),
        'system_version' / Hex(Bytes(8)),
        'title_id' / common.TitleID,
        'title_type' / Hex(Bytes(4)),
        'group_id' / Hex(Bytes(2)),
        '_unk2' / Bytes(0x3e),
        'access_rights' / Hex(Bytes(4)),
        'title_version' / Int16ub,
        'content_count' / Int16ub,
        'boot_index' / Int16ub,
        Padding(2),
        'content_info_sha256' / ChecksumValue(hashlib.sha256, this.content_info),
        'content_info' / ChecksumSourceData(Array(64, Struct(
            'content_index' / Int16ub,
            'content_count' / Int16ub,
            'contents_sha256' / IfThenElse(
                this.content_count > 0,
                ChecksumValue(
                    hashlib.sha256,
                    lambda this: this._.contents[this.content_index:this.content_index + this.content_count],
                    True
                ),
                ChecksumRaw(hashlib.sha256)
            )
        ))),
        'contents' / Array(this.content_count, ChecksumSourceData(Struct(
            'id' / Hex(Int32ub),
            'index' / Int16ub,
            # 0x2000: always set (?)
            # 0x4000: appears in DLC TMDs ("optional"?)
            # 0x8000: "shared"?
            'type' / FlagsEnum(Int16ub, encrypted=0x0001, hashed=0x0002, unk1=0x2000, unk2=0x4000, unk3=0x8000),
            'size' / Int64ub,
            content_hash
        ))),
        '_end' / GreedyBytes,
        VerifyOrWriteChecksums
    )


struct_wiiu = __get_struct(True)
struct_3ds = __get_struct(False)
