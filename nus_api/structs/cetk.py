from construct import \
    Struct, Int16ub, Bytes, Byte, \
    GreedyBytes, Hex, PaddedString

from . import common


# ref:
#   https://www.3dbrew.org/wiki/Ticket
#   https://wiibrew.org/wiki/Ticket
struct = Struct(
    'signature' / common.signature,
    'issuer' / PaddedString(0x40, 'ascii'),
    'ecdh_data' / Bytes(0x3c),
    'version' / Byte,
    'ca_crl_version' / Byte,
    'signer_crl_version' / Byte,
    'titlekey_encrypted' / Hex(Bytes(16)),
    '_unk1' / Bytes(1),
    'ticket_id' / Hex(Bytes(8)),
    'console_id' / Hex(Bytes(4)),
    'title_id' / common.TitleIDAdapter(Bytes(8)),
    '_unk2' / Bytes(2),
    'title_version' / Int16ub,
    '_unk3' / Bytes(8),
    'license_type' / Byte,
    'keyY_index' / Byte,
    '_unk4' / Bytes(0x2a),
    'account_id' / Hex(Bytes(4)),
    '_unk5' / Bytes(1),
    'audit' / Byte,
    '_unk6' / Bytes(0x42),
    'limits' / Bytes(0x40),
    '_end' / GreedyBytes
)
