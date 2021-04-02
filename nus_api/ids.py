from enum import IntEnum
from typing import Union, overload


# ref: https://www.3dbrew.org/wiki/Titles
# ref: https://wiiubrew.org/wiki/Title_database

class TitlePlatform(IntEnum):
    _3DS = 0x0004
    WIIU = 0x0005


class TitleType(IntEnum):
    GAME_3DS = 0x00040000
    DEMO_3DS = 0x00040002
    UPDATE_3DS = 0x0004000e
    DLC_3DS = 0x0004008c
    DSIWARE_3DS = 0x00048004

    GAME_WIIU = 0x00050000
    DEMO_WIIU = 0x00050002
    DLC_WIIU = 0x0005000c
    UPDATE_WIIU = 0x0005000e

    @classmethod
    def from_platform_category(cls, platform: Union[TitlePlatform, int], category: int):
        if isinstance(platform, TitlePlatform):
            platform = platform.value
        return cls(((platform & 0xffff) << 16) | (category & 0xffff))

    @property
    def platform(self) -> TitlePlatform:
        return TitlePlatform(self.value >> 16)

    @property
    def category(self) -> int:
        return self.value & 0xffff


class TitleID:
    type: TitleType
    id: int

    @overload
    def __init__(self, type: TitleType, id: int):
        ...

    @overload
    def __init__(self, title_id: Union[str, int, bytes]):
        ...

    def __init__(self, type_or_title_id, id=None):
        # first overload
        if isinstance(type_or_title_id, TitleType):
            assert isinstance(id, int)
            self.type = type_or_title_id
            self.id = id
        # second overload
        else:
            title_id = type_or_title_id
            if isinstance(title_id, bytes):
                title_id = int.from_bytes(title_id, 'big')
            elif isinstance(title_id, str):
                title_id = int(title_id, 16)
            self.type = TitleType(title_id >> 32)
            self.id = title_id & 0xffffffff

    @property
    def is_game(self):
        return self.type in (TitleType.GAME_3DS, TitleType.GAME_WIIU)

    @property
    def is_update(self):
        return self.type in (TitleType.UPDATE_3DS, TitleType.UPDATE_WIIU)

    @property
    def is_dlc(self):
        return self.type in (TitleType.DLC_3DS, TitleType.DLC_WIIU)

    @property
    def game(self):
        if self.is_game:
            return self
        if self.is_update or self.is_dlc:
            return TitleID(TitleType.from_platform_category(self.type.platform, 0x0000), self.id)
        raise RuntimeError(f'unimplemented: game title ID for {self}')

    @property
    def update(self):
        if self.is_update:
            return self
        if self.is_game or self.is_dlc:
            return TitleID(TitleType.from_platform_category(self.type.platform, 0x000e), self.id)
        raise RuntimeError(f'unimplemented: update title ID for {self}')

    @property
    def dlc(self):
        if self.is_dlc:
            return self
        if self.is_game or self.is_update:
            if self.type.platform == TitlePlatform._3DS:
                return TitleID(TitleType.from_platform_category(self.type.platform, 0x008c), self.id)
            else:
                return TitleID(TitleType.from_platform_category(self.type.platform, 0x000c), self.id)
        raise RuntimeError(f'unimplemented: dlc title ID for {self}')

    def to_bytes(self) -> bytes:
        return bytes.fromhex(str(self))

    def __str__(self):
        return f'{self.type.value:08X}{self.id:08X}'

    def __repr__(self):
        return f'{type(self).__name__}(0x{str(self)})'

    def __hash__(self):
        return hash((self.type, self.id))

    def __eq__(self, other):
        return (self.type, self.id) == (other.type, other.id)


TTitleIDInput = Union[TitleID, str]


def get_str_title_id(val: TTitleIDInput) -> str:
    v = str(val) if isinstance(val, TitleID) else val.upper()
    assert len(v) == 16
    return v


# couldn't find any references for these, this is only based on observations

class ContentPlatform(IntEnum):
    _3DS = 50
    WIIU = 20


class ContentType(IntEnum):
    TITLE_3DS = 5001
    DEMO_3DS = 5003
    MOVIE_3DS = 5004
    TITLE_WIIU = 2001
    DEMO_WIIU = 2003
    MOVIE_WIIU = 2004
    DLC_WIIU = 2005

    @property
    def platform(self) -> ContentPlatform:
        return ContentPlatform(self.value // 100)  # upper two digits

    @property
    def category(self) -> int:
        return self.value % 100  # lower two digits


class ContentID:
    type: ContentType
    id: int

    @overload
    def __init__(self, type: ContentType, id: int):
        ...

    @overload
    def __init__(self, content_id: Union[str, int]):
        ...

    def __init__(self, type_or_content_id, id=None):
        # first overload
        if isinstance(type_or_content_id, ContentType):
            assert isinstance(id, int)
            self.type = type_or_content_id
            self.id = id
        # second overload
        else:
            content_id = type_or_content_id
            if isinstance(content_id, int):
                content_id = str(content_id)
            assert len(content_id) == 14
            self.type = ContentType(int(content_id[:4]))
            self.id = int(content_id[4:])

    def __str__(self):
        return f'{self.type.value:04d}{self.id:010d}'

    def __repr__(self):
        return f'{type(self).__name__}({str(self)})'

    def __hash__(self):
        return hash((self.type, self.id))

    def __eq__(self, other):
        return (self.type, self.id) == (other.type, other.id)


TContentIDInput = Union[ContentID, str]


def get_str_content_id(val: TContentIDInput) -> str:
    v = str(val) if isinstance(val, ContentID) else val
    assert len(v) == 14
    return v
