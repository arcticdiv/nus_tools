from typing import Optional, Any

from .._base import BaseType, BaseTypeLoadable
from ... import reqdata, structs, ids
from ...sources import contentcdn as source_contentcdn


#####
# /<title id>/cetk
#####

class CETK(BaseTypeLoadable['source_contentcdn._BaseContentSource']):
    struct: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/cetk')
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.struct = structs.cetk.parse(raw_data)


#####
# /<title id>/tmd[.<version>]
#####

class TMD(BaseTypeLoadable['source_contentcdn._BaseContentSource']):
    struct: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput, version: Optional[int]):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/tmd' + (f'.{version}' if version is not None else ''))
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.struct = structs.tmd.parse(raw_data)

        # verify checksums
        self.struct.content_info_sha256.verify(self.struct.content_info.__raw__)
        for info in self.struct.content_info:
            if info.content_count == 0:
                continue
            contents = self.struct.contents[info.content_index:info.content_index + info.content_count]
            data = b''.join(c.__raw__ for c in contents)
            info.contents_sha256.verify(data)


#####
# /<title id>/<content id>
#####

class APP(BaseType['source_contentcdn._BaseContentSource']):
    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput, content_id: int):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08x}')  # TODO: uppercase/lowercase?
        )


#####
# /<title id>/<content id>.h3
#####

class H3(BaseType['source_contentcdn._BaseContentSource']):
    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput, content_id: int):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/{content_id:08x}.h3')
        )
