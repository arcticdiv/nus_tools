from construct import \
    Struct, Container, Adapter, Array, \
    Bytes, Const, FlagsEnum, Int32ub, PaddedString, Padding, Terminated

from . import common


# ref: https://www.3dbrew.org/wiki/SMDH#Application_Titles
languages = ('JP', 'EN', 'FR', 'DE', 'IT', 'ES', 'TW', 'KO', 'NL', 'PT', 'RU', 'CN', 'unused1', 'unused2', 'unused3', 'unused4')


class TitleInfoLanguageAdapter(Adapter):
    def _decode(self, obj: list, context, path):
        assert len(languages) == len(obj)
        return Container(zip(languages, obj))

    def _encode(self, obj, context, path):
        raise NotImplementedError


# ref:
#   https://wiiubrew.org/wiki/Nn_idbe.rpl (specified length of unknown block is currently off by 4 bytes)
#   https://github.com/TomEke/WiiU-Title-Key/blob/a4efc01d92f7b1f4c37bb7bf4470a42fa7bf914d/app/Title.php#L81
# only tested with WiiU files, does not work for 3DS since it uses little endian and different icon sizes
struct = Struct(
    'checksum' / common.sha256,
    'title_id' / common.TitleID,
    'version' / Int32ub,
    '_unk1' / Bytes(4),
    'regions' / FlagsEnum(Int32ub, JP=1 << 0, US=1 << 1, EU=1 << 2, AU=1 << 3, CN=1 << 4, KO=1 << 5, TW=1 << 6, unk=1 << 7),
    '_unk2' / Bytes(0x0c),
    Const(b'\xc0' * 4),
    Padding(0x0c),
    'title_info' / TitleInfoLanguageAdapter(Array(16, Struct(
        'short_name' / PaddedString(0x80, 'utf-16-be'),
        'long_name' / PaddedString(0x100, 'utf-16-be'),
        'publisher' / PaddedString(0x80, 'utf-16-be')
    ))),
    'icon_tga' / Bytes(0x2c + 128 * 128 * 4),
    Padding(4),
    Terminated
)
