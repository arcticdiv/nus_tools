from typing import Optional, Any

from .._base import BaseType, BaseTypeLoadableStruct
from ... import reqdata, structs, ids
from ...sources import contentcdn as source_contentcdn


#####
# /<title id>/cetk
#####

class CETK(BaseTypeLoadableStruct['source_contentcdn._BaseContentSource']):
    data: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput):
        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/cetk'),
            structs.cetk
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.data = self._parse_struct(raw_data)


#####
# /<title id>/tmd[.<version>]
#####

class TMD(BaseTypeLoadableStruct['source_contentcdn._BaseContentSource']):
    data: Any

    def __init__(self, source: 'source_contentcdn._BaseContentSource', title_id: ids.TTitleIDInput, version: Optional[int]):
        self.__title_id = ids.TitleID.get_inst(title_id)

        super().__init__(
            source,
            reqdata.ReqData(path=f'{ids.TitleID.get_str(title_id)}/tmd' + (f'.{version}' if version is not None else '')),
            structs.tmd.get(self.__title_id.type.platform)
        )

    def _read(self, reader):
        raw_data = reader.read_all()
        self.data = self._parse_struct(raw_data)

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
