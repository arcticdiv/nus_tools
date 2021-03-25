from construct import \
    Struct, Int64ub, Int32ub, Int16ub, Bytes, Byte, Array, \
    GreedyBytes, Hex, PaddedString, Padding, FlagsEnum, this

from . import common


# ref:
#   https://www.3dbrew.org/wiki/Title_metadata
#   https://wiibrew.org/wiki/Title_metadata
#   https://wiiubrew.org/wiki/Title_metadata
# this is only tested with WiiU TMDs and will likely not work well with 3DS TMDs
struct = Struct(
    'signature' / common.signature,
    'issuer' / PaddedString(0x40, 'ascii'),
    'version' / Byte,
    'ca_crl_version' / Byte,
    'signer_crl_version' / Byte,
    '_unk1' / Bytes(1),
    'system_version' / Hex(Bytes(8)),
    'title_id' / Hex(Bytes(8)),
    'title_type' / Hex(Bytes(4)),
    'group_id' / Hex(Bytes(2)),
    '_unk2' / Bytes(0x3e),
    'access_rights' / Hex(Bytes(4)),
    'title_version' / Int16ub,
    'content_count' / Int16ub,
    'boot_index' / Int16ub,
    Padding(2),
    'content_info_sha256' / common.sha256,  # TODO: verify hashes?
    'content_info' / Array(64, Struct(
        'content_index' / Int16ub,
        'content_count' / Int16ub,
        'contents_sha256' / common.sha256
    )),
    'contents' / Array(this.content_count, Struct(
        'id' / Hex(Int32ub),
        'index' / Int16ub,
        # 0x2000: always set (?)
        # 0x4000: appears in DLC TMDs ("optional"?)
        # 0x8000: "shared"?
        'type' / FlagsEnum(Int16ub, encrypted=0x0001, hashed=0x0002, unk1=0x2000, unk2=0x4000, unk3=0x8000),
        'size' / Int64ub,
        'sha1' / common.sha1,
        Padding(0x0c)
    )),
    '_end' / GreedyBytes
)
