from construct import \
    Struct, Const, Int32ub, Bytes, Hex, Padded, Adapter

from .. import ids


# TODO: verify signatures?
signature = Padded(0x140, Struct(
    'type' / Hex(Const(0x010004, Int32ub)),  # RSA_2048 SHA256, only one type handled (for now)
    'data' / Bytes(0x100)
))

sha1 = Hex(Bytes(0x14))
sha256 = Hex(Bytes(0x20))


class _TitleIDAdapter(Adapter):
    def _decode(self, obj: bytes, context, path):
        return ids.TitleID(obj)

    def _encode(self, obj: ids.TitleID, context, path):
        return obj.to_bytes()


TitleID = _TitleIDAdapter(Bytes(8))
