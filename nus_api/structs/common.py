from construct import \
    Struct, Const, Int32ub, Bytes, Hex, Padded, ExprAdapter

from .. import ids


# TODO: verify signatures?
signature = Padded(0x140, Struct(
    'type' / Hex(Const(0x010004, Int32ub)),  # RSA_2048 SHA256, only one type handled (for now)
    'data' / Bytes(0x100)
))


TitleID = ExprAdapter(
    Bytes(8),
    lambda data, _: ids.TitleID(data),
    lambda title_id, _: title_id.to_bytes()
)
