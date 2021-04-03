from construct import \
    Struct, Container, Adapter, Array, ByteSwapped, \
    Bytes, FlagsEnum, Int32ub, PaddedString, Padding, Pass, Terminated
from constructutils import InliningStruct, InlineStruct, AttributeRawCopy

from . import common


# ref: https://www.3dbrew.org/wiki/SMDH#Application_Titles
languages = (
    'JP', 'EN', 'FR', 'DE', 'IT', 'ES', 'TW', 'KO', 'NL', 'PT', 'RU', 'CN',
    'unused1', 'unused2', 'unused3', 'unused4'
)


class TitleInfoLanguageAdapter(Adapter):
    def _decode(self, obj: list, context, path):
        assert len(languages) == len(obj)
        return Container(zip(languages, obj))

    def _encode(self, obj, context, path):
        raise NotImplementedError


# ref:
#   https://wiiubrew.org/wiki/Nn_idbe.rpl (specified length of unknown block is currently off by 4 bytes)
#   https://www.3dbrew.org/wiki/SMDH#Region_Lockout
#   https://github.com/TomEke/WiiU-Title-Key/blob/a4efc01d92f7b1f4c37bb7bf4470a42fa7bf914d/app/Title.php#L81
def __get_struct(is_wiiu: bool):
    if is_wiiu:
        swap = lambda x: x  # noop  # noqa: E731
        encoding = 'utf-16-be'
        # tga file
        icons = Struct(
            '128' / Bytes(0x2c + 128 * 128 * 4)
        )
        region_all = 0xffffffff
    else:
        swap = ByteSwapped
        encoding = 'utf-16-le'
        # raw RGB565
        icons = Struct(
            '24' / Bytes(24 * 24 * 2),
            '48' / Bytes(48 * 48 * 2)
        )
        region_all = 0x7fffffff

    return InliningStruct(
        'checksum' / common.sha256,
        AttributeRawCopy(InlineStruct(
            'title_id' / swap(common.TitleID),
            'version' / swap(Int32ub),
            '_unk1' / Bytes(4),
            'regions' / swap(FlagsEnum(Int32ub, JP=1 << 0, US=1 << 1, EU=1 << 2, AU=1 << 3, CN=1 << 4, KO=1 << 5, TW=1 << 6, ALL=region_all)),
            '_unk2' / Bytes(0x10),
            Padding(0x0c),
            'title_info' / TitleInfoLanguageAdapter(Array(16, Struct(
                'short_name' / PaddedString(0x80, encoding),
                'long_name' / PaddedString(0x100, encoding),
                'publisher' / PaddedString(0x80, encoding)
            ))),
            'icons' / icons,
            Padding(4) if is_wiiu else Pass
        )),
        Terminated
    )


struct_wiiu = __get_struct(True)
struct_3ds = __get_struct(False)
