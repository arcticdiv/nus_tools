from construct import \
    Struct, Array, Byte, Bytes, CString, Int16ub, Int24ub, Int32ub, \
    Const, FlagsEnum, IfThenElse, Padding, Check, this
from constructutils import InliningStruct, Inline


# ref:
#   http://wiiubrew.org/wiki/FST
#   https://github.com/ihaveamac/wiiu-things/wiki/FST
_entry = InliningStruct(
    'type' / FlagsEnum(Byte, directory=0x01, special=0x02, deleted=0x80),
    'name_offset' / Int24ub,
    Inline(IfThenElse(
        this.type.directory,
        Struct(
            'parent_offset' / Int32ub,
            'next_entry_index' / Int32ub  # index of next entry not belonging to this directory anymore (i.e. index of last entry + 1)
        ),
        Struct(
            'offset_raw' / Int32ub,
            'size' / Int32ub
        )
    )),
    'flags' / FlagsEnum(Int16ub, offset_in_bytes=0x0004, hashed_meta=0x0040, hashed_content=0x0400),
    'secondary_index' / Int16ub
)

struct = Struct(
    Const(b'FST\0'),
    'offset_factor' / Int32ub,
    'num_secondary' / Int32ub,
    '_unk1' / Bytes(0x14),
    'secondary' / Array(this.num_secondary, Struct(
        'offset_sectors' / Int32ub,
        'size_sectors' / Int32ub,
        'title_id' / Bytes(8),
        'group_id' / Bytes(4),
        'flags' / FlagsEnum(Int16ub, hash_tmd=0x100, hash_tree=0x200),
        Padding(0x0a)
    )),
    'root' / _entry,
    Check(this.root.type.directory),
    'entries' / Array(this.root.next_entry_index - 1, _entry),
    'names' / Array(this.root.next_entry_index, CString('ascii'))
)
