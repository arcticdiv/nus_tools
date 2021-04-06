from construct import \
    Construct, Struct, Const, Int32ub, Bytes, Hex, Padded, ExprAdapter
from typing import Callable, Union

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


class PlatformSpecific:
    _3ds: Construct
    wiiu: Construct

    # expected signature: `func(is_wiiu: bool) -> Construct`
    def __init__(self, func: Callable[[bool], Construct]):
        self._3ds = func(False)
        self.wiiu = func(True)

    def get(self, platform: Union[ids.TitlePlatform, ids.ContentPlatform]) -> Construct:
        return {
            ids.TitlePlatform._3DS: self._3ds,
            ids.ContentPlatform._3DS: self._3ds,
            ids.TitlePlatform.WIIU: self.wiiu,
            ids.ContentPlatform.WIIU: self.wiiu
        }[platform]
