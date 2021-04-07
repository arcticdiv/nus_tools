from typing import Optional, Any

from .._base import BaseType, BaseTypeLoadable
from ... import reqdata, structs, ids
from ...sources import contentcdn as source_contentcdn


#####
# /<title id>/cetk
#####

class CETK(BaseTypeLoadable['source_contentcdn._BaseContentSource']):
    data: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/cetk')
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.data = structs.cetk.parse(raw_data)


#####
# /<title id>/tmd[.<version>]
#####

class TMD(BaseTypeLoadable['source_contentcdn._BaseContentSource']):
    data: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput, version: Optional[int]):
        self.__title_id = ids.TitleID.get_inst(title_id)
        self.__struct = structs.tmd.get(self.__title_id.type.platform)

        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/tmd' + (f'.{version}' if version is not None else ''))
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.data = self.__struct.parse(raw_data)

        # sanity check
        assert self.data.title_id == self.__title_id


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
